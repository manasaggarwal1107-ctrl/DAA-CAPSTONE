"""End-to-end workflow: validate -> graph -> depot reachability -> sort -> knapsack -> destinations -> route.

One function, ``run_pipeline``, is shared by the API, the PDF report and the
benchmark-independent integration tests, so all modules use the same data
structures.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Any, Optional

from ..algorithms.graph import dijkstra
from ..algorithms.knapsack import knapsack_01
from ..algorithms.sorting import get_sorter
from ..algorithms.tsp import Leg, nearest_neighbour_route
from ..models import DEADLINE_FORMAT
from .store import build_graph

ACTIVE = ("pending",)

# Why a parcel cannot be delivered (``category`` of an undeliverable parcel).
UNKNOWN_DESTINATION = "unknown_destination"      # destination is not a location of the road network
UNREACHABLE_DESTINATION = "unreachable_destination"  # no road path from the depot
TOUR_UNREACHABLE = "tour_unreachable"            # reachable from the depot, but not from the previous stop (one-way roads)


def parcel_priority_key(p: dict) -> tuple:
    """Higher priority first, earlier deadline first, parcel ID as tie-breaker."""
    return (-p["priority"], p["deadline"], p["id"])


def effective_value(p: dict) -> int:
    """Priority-weighted delivery value = value x priority."""
    return p["value"] * p["priority"]


def sort_parcels(parcels: list[dict], sorter: str = "merge", *, trace: Optional[list] = None,
                 stats: Optional[dict] = None) -> list[dict]:
    fn = get_sorter(sorter)
    kwargs: dict[str, Any] = {}
    if trace is not None:
        kwargs.update(trace=trace, label=lambda p: p["id"])
    if stats is not None:
        kwargs["stats"] = stats
    return fn(parcels, key=parcel_priority_key, **kwargs)


def _leg_dict(leg: Leg, cumulative: float) -> dict:
    return {"from": leg.origin, "to": leg.destination, "distance": round(leg.distance, 3),
            "path": leg.path, "cumulative": round(cumulative, 3)}


def _ms(t0: float) -> float:
    return round((time.perf_counter() - t0) * 1000, 4)


def run_pipeline(parcels: list[dict], graph_data: dict, settings: dict, *,
                 capacity: Optional[int] = None, depot: Optional[str] = None,
                 sorter: str = "merge", include_table: bool = True) -> dict:
    """Run the full optimisation workflow and return a JSON-serialisable result."""
    timings: dict[str, float] = {}
    warnings: list[str] = []
    t_all = time.perf_counter()
    capacity = settings["capacity"] if capacity is None else capacity
    depot = depot or settings["depot"]

    # 1. Validation: only pending parcels take part; the depot must exist.
    t0 = time.perf_counter()
    names = {l["name"] for l in graph_data["locations"]}
    if depot not in names:
        raise ValueError(f"Depot '{depot}' is not in the road network")
    active = [p for p in parcels if p["status"] in ACTIVE]
    skipped = len(parcels) - len(active)
    if skipped:
        warnings.append(f"{skipped} parcel(s) with status delivered/cancelled were excluded.")
    timings["validation"] = _ms(t0)

    # 2. Graph construction and depot reachability (BEFORE any parcel selection)
    t0 = time.perf_counter()
    graph = build_graph(graph_data)
    timings["graph"] = _ms(t0)
    t0 = time.perf_counter()
    from_depot = dijkstra(graph, depot)
    undeliverable: list[dict] = []
    deliverable_ids: set[str] = set()
    for p in active:
        if not graph.has_node(p["destination"]):
            undeliverable.append({**p, "category": UNKNOWN_DESTINATION,
                                  "reason": f"undeliverable: '{p['destination']}' is not a location in the road network"})
        elif not from_depot.reachable(p["destination"]):
            undeliverable.append({**p, "category": UNREACHABLE_DESTINATION,
                                  "reason": f"undeliverable: no road path from depot '{depot}' to '{p['destination']}'"})
        else:
            deliverable_ids.add(p["id"])
    timings["reachability"] = _ms(t0)

    # 3. Sorting (all pending parcels, so the prioritised list is complete)
    t0 = time.perf_counter()
    stats: dict = {}
    ordered = sort_parcels(active, sorter, stats=stats)
    timings["sorting"] = _ms(t0)

    # 4-6. Knapsack on DELIVERABLE parcels only, destination extraction, Nearest Neighbour tour.
    # With one-way roads a destination can be reachable from the depot yet unreachable from the previous
    # stop. Such parcels are moved to ``undeliverable`` and the selection is recomputed, so the packing plan,
    # the route and every total always describe the same set of parcels.
    pool = [p for p in ordered if p["id"] in deliverable_ids]
    timings["knapsack"] = timings["selection"] = timings["routing"] = 0.0
    replans = 0
    while True:
        t0 = time.perf_counter()
        kn = knapsack_01([p["weight"] for p in pool], [effective_value(p) for p in pool],
                         capacity, record_table=include_table)
        timings["knapsack"] += _ms(t0)
        chosen = set(kn.selected)
        selected = [pool[i] for i in kn.selected]
        rejected = [p for i, p in enumerate(pool) if i not in chosen]
        rejected_out = [{**p, "reason": "heavier than vehicle capacity" if p["weight"] > capacity
                         else "lower priority-weighted value per kg than the chosen set"} for p in rejected]

        t0 = time.perf_counter()
        by_dest: dict[str, list[dict]] = {}
        for p in selected:
            by_dest.setdefault(p["destination"], []).append(p)
        stops = [d for d in by_dest if d != depot]
        timings["selection"] += _ms(t0)

        t0 = time.perf_counter()
        route = nearest_neighbour_route(graph, depot, stops)
        timings["routing"] += _ms(t0)

        stuck = set(route.unreachable)
        if not stuck:
            break
        replans += 1
        for p in pool:
            if p["destination"] in stuck:
                undeliverable.append({**p, "category": TOUR_UNREACHABLE,
                                      "reason": f"undeliverable: no road path to '{p['destination']}' from the previous stop"})
        warnings.append(f"Destination(s) {', '.join(sorted(stuck))} are reachable from the depot but not from the "
                        f"previous stop (one-way roads); their parcels were excluded and the selection was recomputed.")
        pool = [p for p in pool if p["destination"] not in stuck]

    # Assemble route legs, ETAs and per-stop deliveries
    legs, cumulative = [], 0.0
    for leg in route.legs:
        cumulative += leg.distance
        legs.append(_leg_dict(leg, cumulative))
    return_leg = None
    if route.return_leg is not None:
        return_leg = _leg_dict(route.return_leg, cumulative + route.return_leg.distance)
    total_distance = round(route.total_distance, 3)

    start = datetime.strptime(settings["dispatch_time"], DEADLINE_FORMAT)
    deliveries, on_time, late = [], 0, 0
    if depot in by_dest:
        deliveries.append({"destination": depot, "parcels": [p["id"] for p in by_dest[depot]],
                           "weight": sum(p["weight"] for p in by_dest[depot]),
                           "value": sum(effective_value(p) for p in by_dest[depot]),
                           "cumulative_km": 0.0, "eta": start.strftime(DEADLINE_FORMAT), "late": []})
    for idx, leg in enumerate(legs, start=1):
        dest = leg["to"]
        minutes = leg["cumulative"] / settings["speed_kmph"] * 60 + idx * settings["service_minutes"]
        eta = start + timedelta(minutes=minutes)
        late_ids = [p["id"] for p in by_dest[dest] if eta.strftime(DEADLINE_FORMAT) > p["deadline"]]
        on_time += len(by_dest[dest]) - len(late_ids)
        late += len(late_ids)
        deliveries.append({"destination": dest, "parcels": [p["id"] for p in by_dest[dest]],
                           "weight": sum(p["weight"] for p in by_dest[dest]),
                           "value": sum(effective_value(p) for p in by_dest[dest]),
                           "cumulative_km": leg["cumulative"], "eta": eta.strftime(DEADLINE_FORMAT),
                           "late": late_ids})

    undeliverable.sort(key=lambda p: (p["destination"], p["id"]))
    unreachable_dests = sorted({p["destination"] for p in undeliverable})
    for d in unreachable_dests:
        ids = [p["id"] for p in undeliverable if p["destination"] == d]
        warnings.append(f"Destination '{d}' cannot be reached from depot '{depot}': {len(ids)} parcel(s) "
                        f"({', '.join(ids)}) are undeliverable. They were excluded before the knapsack, so they "
                        f"use no capacity, add no value and are not on the route.")
    if route.legs and not route.returned_to_depot:
        warnings.append("No road path back to the depot exists from the last stop; the return leg is omitted.")
    if not active:
        warnings.append("There are no pending parcels to optimise.")
    elif not pool:
        warnings.append("No pending parcel has a destination that can be reached from the depot.")
    elif not selected:
        warnings.append("No parcel could be selected (capacity is too small for every parcel).")
    if late:
        warnings.append(f"{late} parcel(s) are estimated to arrive after their deadline.")

    used = sum(p["weight"] for p in selected)
    if not active:
        status = "no_parcels"
    elif not pool:
        status = "nothing_deliverable"
    elif not selected:
        status = "nothing_selected"
    elif undeliverable:
        status = "partial_route"
    else:
        status = "optimised"
    timings["total"] = _ms(t_all)

    return {
        "status": status,
        "ran_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "algorithms": {"sort": sorter, "knapsack": "dp_01_1d", "shortest_path": "dijkstra_binary_heap",
                       "tour": "nearest_neighbour"},
        "capacity": capacity, "depot": depot,
        "original_order": [p["id"] for p in active],
        "sorted_parcels": ordered,
        "sort_comparisons": stats.get("comparisons", 0),
        "selected": selected, "rejected": rejected_out, "undeliverable": undeliverable,
        "counts": {"pending": len(active), "deliverable": len(pool),
                   "selected": len(selected), "rejected": len(rejected_out), "undeliverable": len(undeliverable),
                   "replans": replans},
        "used_weight": used, "remaining_capacity": capacity - used,
        "utilisation": round(used / capacity * 100, 2) if capacity else 0.0,
        "total_value": sum(effective_value(p) for p in selected),
        "raw_value": sum(p["value"] for p in selected),
        "dp": {"cells": kn.cells, "table": kn.table, "table_note": kn.table_note,
               "order": [p["id"] for p in pool], "weights": [p["weight"] for p in pool],
               "values": [effective_value(p) for p in pool]},
        "destinations": stops, "unreachable": unreachable_dests,
        "route": {"depot": depot, "order": route.visit_order, "legs": legs, "return_leg": return_leg,
                  "returned_to_depot": route.returned_to_depot, "total_distance": total_distance,
                  "dijkstra_runs": route.dijkstra_runs, "deliveries": deliveries,
                  "on_time": on_time, "late": late,
                  "note": "Nearest Neighbour is a greedy approximation; the tour is not guaranteed to be the shortest possible."},
        "timings_ms": timings,
        "warnings": warnings,
    }
