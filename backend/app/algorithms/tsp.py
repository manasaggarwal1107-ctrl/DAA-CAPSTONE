"""Nearest Neighbour TSP heuristic on top of Dijkstra shortest road distances.

Starting at the depot, repeatedly drive to the closest (by shortest road path)
unvisited stop, then return to the depot if a path exists.

This is an APPROXIMATION: it is greedy and gives no optimality guarantee
(on general metrics the tour can be O(log n) times worse than optimal).
Complexity: k stops -> k Dijkstra runs, O(k (V+E) log V), plus an O(k) linear minimum scan per step
(O(k^2) in total); no sorting is used to choose the next stop.  Ties on distance go to the smaller name.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional

from .errors import UnknownNodeError
from .graph import Graph, dijkstra


@dataclass
class Leg:
    origin: str
    destination: str
    distance: float
    path: list[str]          # every road node from origin to destination inclusive


@dataclass
class RouteResult:
    depot: str
    legs: list[Leg] = field(default_factory=list)       # delivery legs in order
    return_leg: Optional[Leg] = None
    visit_order: list[str] = field(default_factory=list)
    unreachable: list[str] = field(default_factory=list)
    returned_to_depot: bool = False
    dijkstra_runs: int = 0
    steps: list[dict] = field(default_factory=list)

    @property
    def total_distance(self) -> float:
        total = sum(l.distance for l in self.legs)
        if self.return_leg is not None:
            total += self.return_leg.distance
        return total


def nearest_neighbour_route(graph: Graph, depot: str, stops: Iterable[str], *,
                            return_to_depot: bool = True, trace: bool = False) -> RouteResult:
    """Build a delivery tour visiting each reachable stop exactly once."""
    if not graph.has_node(depot):
        raise UnknownNodeError(f"Unknown depot '{depot}'")
    remaining = {s for s in stops if s != depot}
    result = RouteResult(depot=depot)
    unknown = sorted(s for s in remaining if not graph.has_node(s))
    result.unreachable.extend(unknown)           # not even in the network
    remaining -= set(unknown)

    current = depot
    while remaining:
        sp = dijkstra(graph, current)
        result.dijkstra_runs += 1
        # Linear scan for the nearest stop: O(k) per step.  Strict ``<`` on (distance, name) makes the
        # choice deterministic: equal distances go to the lexicographically smaller location name.
        best: Optional[tuple[float, str]] = None
        unreached: list[str] = []
        for s in remaining:
            if sp.reachable(s):
                cand = (sp.dist[s], s)
                if best is None or cand < best:
                    best = cand
            else:
                unreached.append(s)
        if trace:      # the sorted candidate list is built for display only, never for selection
            result.steps.append({"from": current,
                                 "candidates": [{"stop": s, "distance": round(sp.dist[s], 4)}
                                                for s in sorted(remaining, key=lambda n: (sp.dist.get(n, float("inf")), n))
                                                if sp.reachable(s)],
                                 "unreachable": sorted(unreached),
                                 "chosen": best[1] if best else None})
        if best is None:
            result.unreachable.extend(sorted(remaining))
            break
        dist, nxt = best
        result.legs.append(Leg(current, nxt, dist, sp.path_to(nxt) or [current, nxt]))
        result.visit_order.append(nxt)
        remaining.discard(nxt)
        current = nxt

    if return_to_depot and result.legs:
        sp = dijkstra(graph, current, target=depot)
        result.dijkstra_runs += 1
        path = sp.path_to(depot)
        if path is not None:
            result.return_leg = Leg(current, depot, sp.dist[depot], path)
            result.returned_to_depot = True
    return result
