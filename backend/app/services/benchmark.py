"""Benchmark laboratory: real measurements with time.perf_counter().

Nothing here is estimated: each stage is executed ``repeats`` times and the
median / min / mean wall-clock times are reported.  Peak memory comes from a
separate tracemalloc run (tracemalloc slows code, so it is never mixed into
the timing runs).
"""

from __future__ import annotations

import platform
import statistics
import time
import tracemalloc
from datetime import datetime
from typing import Callable

from ..algorithms.graph import dijkstra
from ..algorithms.knapsack import knapsack_01
from ..algorithms.sorting import merge_sort
from ..algorithms.tsp import nearest_neighbour_route
from . import datasets
from .pipeline import effective_value, parcel_priority_key
from .store import build_graph

DP_CAPACITY_CAP = 600          # kg; keeps n * capacity <= 3M decision cells at n = 5000
STAGES = ("sorting", "knapsack", "dijkstra", "routing")

THEORY = {
    "sorting": "Merge Sort: O(n log n)",
    "knapsack": "0/1 Knapsack DP: O(n * W)",
    "dijkstra": "Dijkstra (binary heap): O((V + E) log V)",
    "routing": "Nearest Neighbour: O(k * (V + E) log V) for k stops",
}


def _time(fn: Callable[[], object], repeats: int) -> dict:
    samples = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - t0) * 1000)
    return {"median_ms": round(statistics.median(samples), 4), "min_ms": round(min(samples), 4),
            "mean_ms": round(statistics.fmean(samples), 4), "repeats": repeats}


def _peak_kb(fn: Callable[[], object]) -> float:
    tracemalloc.start()
    try:
        fn()
        return round(tracemalloc.get_traced_memory()[1] / 1024, 1)
    finally:
        tracemalloc.stop()


def run_benchmark(sizes: list[int], repeats: int = 5, seed: int = 42) -> dict:
    rows = []
    for n in sizes:
        locs = min(max(8, n // 10), 150)
        graph_data = datasets.generate_graph_data(locs, seed + n)
        graph = build_graph(graph_data)
        dests = [l["name"] for l in graph_data["locations"] if l["name"] != "Depot"]
        parcels = datasets.generate_parcels(n, dests, seed + n)
        total_w = sum(p["weight"] for p in parcels)
        capacity = max(1, min(round(total_w * 0.25), DP_CAPACITY_CAP))
        reps = repeats if n <= 500 else min(repeats, 3)

        sort_fn = lambda: merge_sort(parcels, key=parcel_priority_key)
        ordered = sort_fn()
        weights = [p["weight"] for p in ordered]
        values = [effective_value(p) for p in ordered]
        kn_fn = lambda: knapsack_01(weights, values, capacity)
        kn = kn_fn()
        stops = sorted({ordered[i]["destination"] for i in kn.selected})
        dj_fn = lambda: dijkstra(graph, "Depot")
        route_fn = lambda: nearest_neighbour_route(graph, "Depot", stops)

        row = {"n": n, "locations": locs, "roads": len(graph_data["roads"]), "capacity": capacity,
               "selected": len(kn.selected), "stops": len(stops), "dp_cells": kn.cells}
        for name, fn in (("sorting", sort_fn), ("knapsack", kn_fn), ("dijkstra", dj_fn), ("routing", route_fn)):
            row[name] = {**_time(fn, reps), "peak_kb": _peak_kb(fn)}
        rows.append(row)
    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "parameters": {"sizes": sizes, "repeats": repeats, "seed": seed,
                       "dp_capacity_cap_kg": DP_CAPACITY_CAP,
                       "capacity_rule": "25% of total parcel weight, capped at 600 kg",
                       "locations_rule": "min(max(8, n/10), 150)"},
        "environment": {"python": platform.python_version(), "platform": platform.platform(),
                        "processor": platform.processor() or platform.machine()},
        "theory": THEORY,
        "rows": rows,
        "note": "All times are measured on this machine; theoretical complexities are given separately and are not measurements.",
    }
