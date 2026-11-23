"""Educational content and small interactive demos for the Algorithm Learning Centre.

The demos call the real algorithm implementations (no second copy of any
algorithm) and return step traces for the UI to animate.
"""

from __future__ import annotations

from ..algorithms.graph import Graph, dijkstra
from ..algorithms.knapsack import knapsack_01
from ..algorithms.sorting import merge_sort
from ..algorithms.tsp import nearest_neighbour_route

CONTENT = [
    {
        "id": "merge-sort", "name": "Merge Sort", "phase": "Phase 2",
        "role": "Orders parcels: higher priority first, then earlier deadline, then parcel ID.",
        "concept": "A divide-and-conquer sorting algorithm. It splits the list in half, sorts each half recursively and merges the two sorted halves.",
        "principle": [
            "Split the list into a left and a right half until each piece has one element.",
            "A one-element list is already sorted.",
            "Merge two sorted lists by repeatedly taking the smaller front element (ties take the left element, which makes the sort stable).",
            "Merging is linear, and there are log2(n) levels of splitting, giving O(n log n).",
        ],
        "pseudocode": "MERGE-SORT(A):\n  if length(A) <= 1: return A\n  mid <- length(A) / 2\n  L <- MERGE-SORT(A[0 .. mid))\n  R <- MERGE-SORT(A[mid .. end))\n  return MERGE(L, R)\n\nMERGE(L, R):\n  result <- empty list; i <- 0; j <- 0\n  while i < |L| and j < |R|:\n    if key(L[i]) <= key(R[j]): append L[i]; i <- i + 1\n    else:                      append R[j]; j <- j + 1\n  append remaining elements of L and R\n  return result",
        "recurrence": "T(n) = 2 T(n/2) + Theta(n)   =>   T(n) = Theta(n log n)  (Master theorem, case 2)",
        "time": {"best": "O(n log n)", "average": "O(n log n)", "worst": "O(n log n)"},
        "space": "O(n) auxiliary",
        "notes": ["Stable: equal keys keep their input order.", "The sort key here is the tuple (-priority, deadline, id), so a single comparison handles all three rules."],
    },
    {
        "id": "knapsack", "name": "0/1 Knapsack (Dynamic Programming)", "phase": "Phase 2",
        "role": "Chooses the parcel set that maximises priority-weighted value within the vehicle capacity.",
        "concept": "Each parcel is taken whole or not at all. Value = delivery value x priority; weight = parcel weight. Overlapping sub-problems (best value for the first i parcels and capacity w) are solved once and reused.",
        "principle": [
            "dp[w] = best value achievable with capacity w using the parcels processed so far.",
            "For each parcel, update capacities from high to low so the same parcel is never counted twice.",
            "Record a decision bit keep[i][w] whenever parcel i improved dp[w].",
            "Walk backwards from (n, capacity): if keep[i][w] is set, take parcel i and reduce w by its weight.",
        ],
        "pseudocode": "KNAPSACK(weights, values, W):\n  dp[0..W] <- 0\n  for i in 0 .. n-1:\n    for w from W down to weights[i]:        # descending: 0/1, not unbounded\n      if dp[w - weights[i]] + values[i] > dp[w]:\n        dp[w] <- dp[w - weights[i]] + values[i]\n        keep[i][w] <- 1\n  w <- W; chosen <- empty\n  for i from n-1 down to 0:\n    if keep[i][w]: add i to chosen; w <- w - weights[i]\n  return dp[W], chosen",
        "recurrence": "dp[i][w] = dp[i-1][w]                                    if weight_i > w\ndp[i][w] = max( dp[i-1][w],  dp[i-1][w - weight_i] + value_i )   otherwise\ndp[0][w] = 0 for all w",
        "time": {"best": "O(n * W)", "average": "O(n * W)", "worst": "O(n * W)"},
        "space": "O(W) for values, O(n * W) bytes for the decision matrix used to reconstruct the answer",
        "notes": ["Pseudo-polynomial: W is a number, not an input length. This is why weights are whole kilograms.", "The full DP table is only displayed for small instances; large instances run the same code without storing the table."],
    },
    {
        "id": "dijkstra", "name": "Dijkstra's Shortest Path", "phase": "Phase 3",
        "role": "Computes shortest road distances between locations; used for every tour leg.",
        "concept": "A greedy algorithm for single-source shortest paths in graphs with non-negative edge weights. The unsettled node with the smallest known distance is settled next.",
        "principle": [
            "Set dist[source] = 0 and all other distances to infinity; push the source onto a min-heap.",
            "Pop the closest unsettled node u; its distance is final.",
            "Relax every edge (u, v): if dist[u] + w < dist[v], update dist[v], remember prev[v] = u and push v.",
            "Stale heap entries are skipped (lazy deletion). Follow prev[] backwards to rebuild the path.",
        ],
        "pseudocode": "DIJKSTRA(G, s):\n  dist[v] <- infinity for all v; dist[s] <- 0\n  heap <- {(0, s)}\n  while heap not empty:\n    (d, u) <- heap.pop_min()\n    if u already settled: continue\n    mark u settled\n    for each edge (u, v, w):\n      if d + w < dist[v]:\n        dist[v] <- d + w; prev[v] <- u; heap.push((dist[v], v))\n  return dist, prev",
        "recurrence": "dist[v] = min over edges (u,v) of ( dist[u] + w(u,v) ),  dist[s] = 0   (valid only if every w >= 0)",
        "time": {"best": "O(V + E) (target found early)", "average": "O((V + E) log V)", "worst": "O((V + E) log V)"},
        "space": "O(V + E) for the graph, O(V) for dist/prev/heap",
        "notes": ["Negative edge weights are rejected when a road is added, because they break correctness.", "Unreachable locations simply never receive a distance."],
    },
    {
        "id": "nearest-neighbour", "name": "Nearest Neighbour TSP", "phase": "Phase 3",
        "role": "Orders the delivery stops into a route starting and ending at the depot.",
        "concept": "A greedy heuristic for the Travelling Salesman Problem: always drive to the closest unvisited stop. Distances are shortest road distances from Dijkstra, not straight lines.",
        "principle": [
            "Start at the depot; the set of unvisited stops is the unique destinations of selected parcels.",
            "Run Dijkstra from the current location and move to the nearest unvisited, reachable stop.",
            "Repeat until no stop remains. Stops that cannot be reached are reported, never silently skipped.",
            "Return to the depot if a road path exists.",
        ],
        "pseudocode": "NEAREST-NEIGHBOUR(G, depot, stops):\n  current <- depot; route <- []\n  unvisited <- stops - {depot}\n  while unvisited not empty:\n    dist <- DIJKSTRA(G, current)\n    next <- linear scan: argmin over reachable s in unvisited of (dist[s], name)\n    if none reachable: report unreachable; break\n    route.append(leg(current -> next)); unvisited.remove(next); current <- next\n  if path(current -> depot) exists: route.append(return leg)\n  return route",
        "recurrence": "No recurrence: a greedy choice at each step.  Tour length is NOT guaranteed optimal.",
        "time": {"best": "O(k (V+E) log V + k^2)", "average": "O(k (V+E) log V + k^2)", "worst": "O(k (V+E) log V + k^2)"},
        "space": "O(V + k)",
        "notes": ["Approximation only: on general metrics the tour can be much longer than the optimal tour (the exact problem is NP-hard).", "Exact alternatives (Held-Karp, O(n^2 2^n)) are proposed future work, not implemented."],
    },
]


VIVA = {
    "merge-sort": [
        {"q": "Why is Merge Sort O(n log n) in every case?", "a": "The list is halved log2(n) times and each level of merging touches all n elements once, so the work is n per level times log n levels. The split is by position, not by value, so input order cannot change the shape of the recursion."},
        {"q": "Why Merge Sort here instead of Quick Sort?", "a": "It is stable and has a guaranteed O(n log n) worst case. Quick Sort degrades to O(n^2) on adversarial or already-sorted input without careful pivot choice."},
        {"q": "How are three sorting rules handled with one comparison?", "a": "The key is the tuple (-priority, deadline, id). Tuples compare element by element, so priority decides first, then deadline, then parcel ID, which makes the order fully deterministic."},
    ],
    "knapsack": [
        {"q": "Why must the inner loop run from high capacity to low?", "a": "dp[w - weight] must still hold the value from the previous item. Going upwards would reuse the same parcel several times, which solves the unbounded knapsack instead of 0/1."},
        {"q": "Is O(n * W) polynomial?", "a": "It is pseudo-polynomial: W is a numeric value, not the number of bits needed to write it. That is why weights are whole kilograms and why the decision matrix is size-limited."},
        {"q": "How do you recover which parcels were chosen?", "a": "A decision bit keep[i][w] is stored whenever parcel i improves dp[w]. Starting at (n, capacity), walk the parcels backwards; if the bit is set, take the parcel and subtract its weight."},
        {"q": "Why not a greedy value/weight ratio?", "a": "Greedy is optimal only for the fractional knapsack. For 0/1 it can be arbitrarily bad, for example one heavy valuable parcel against several light ones that leave capacity unused."},
    ],
    "dijkstra": [
        {"q": "Why can Dijkstra not handle negative edges?", "a": "It assumes a settled node's distance is final. A later negative edge could make a settled node cheaper, breaking that invariant. The system rejects negative roads when they are added."},
        {"q": "What is the complexity with a binary heap?", "a": "O((V + E) log V): each edge may push one heap entry (E log V) and each node is settled once. An array-based version without a heap would be O(V^2)."},
        {"q": "What is lazy deletion?", "a": "Instead of decreasing a key inside the heap, a new entry is pushed and stale entries are skipped when popped because the node is already settled."},
    ],
    "nearest-neighbour": [
        {"q": "Is Nearest Neighbour optimal?", "a": "No. It is a greedy approximation; the exact TSP is NP-hard. A greedy early choice can force a long return trip. The tests compare it with brute force and show cases where it is strictly worse."},
        {"q": "Why run Dijkstra between stops?", "a": "Stops are connected by roads, not straight lines. Dijkstra gives the true shortest road distance and the intermediate path between any two stops."},
        {"q": "What happens when a stop is unreachable?", "a": "Unreachable destinations are found before the knapsack runs, so their parcels are flagged undeliverable, are never loaded and no misleading leg is created (with one-way roads a stop unreachable from the previous stop is excluded and the selection recomputed). If the depot cannot be reached from the last stop the return leg is omitted and a warning is shown."},
    ],
}
for _a in CONTENT:
    _a["viva"] = VIVA[_a["id"]]


def content() -> list[dict]:
    return CONTENT


def demo_merge_sort(values: list[int]) -> dict:
    trace: list = []
    stats: dict = {}
    result = merge_sort(values, trace=trace, stats=stats)
    return {"input": values, "output": result, "steps": trace, "comparisons": stats["comparisons"]}


def demo_knapsack(weights: list[int], values: list[int], capacity: int) -> dict:
    from ..algorithms.errors import AlgorithmError
    if len(weights) != len(values):
        raise AlgorithmError("Provide the same number of weights and values")
    if any(w < 1 for w in weights) or any(v < 0 for v in values):
        raise AlgorithmError("Weights must be at least 1 and values must not be negative")
    res = knapsack_01(weights, values, capacity, record_table=True)
    return {"weights": weights, "values": values, "capacity": capacity, "best_value": res.best_value,
            "selected": res.selected, "total_weight": res.total_weight, "table": res.table, "keep": res.keep}


def _demo_graph() -> tuple[Graph, list[dict], list[dict]]:
    locs = [("A", 8, 50), ("B", 28, 18), ("C", 28, 82), ("D", 56, 50), ("E", 78, 20), ("F", 92, 70)]
    roads = [("A", "B", 4), ("A", "C", 2), ("B", "C", 5), ("B", "D", 10), ("C", "D", 3),
             ("D", "E", 4), ("D", "F", 11), ("E", "F", 3)]
    g = Graph()
    for n, _, _ in locs:
        g.add_node(n)
    for a, b, w in roads:
        g.add_edge(a, b, w)
    return (g, [{"name": n, "x": x, "y": y} for n, x, y in locs],
            [{"a": a, "b": b, "weight": w} for a, b, w in roads])


def demo_dijkstra(source: str, target: str) -> dict:
    g, locs, roads = _demo_graph()
    res = dijkstra(g, source, target=target, trace=True)
    return {"locations": locs, "roads": roads, "steps": res.steps, "path": res.path_to(target),
            "distance": res.dist.get(target)}


def demo_nn(source: str, stops: list[str]) -> dict:
    g, locs, roads = _demo_graph()
    r = nearest_neighbour_route(g, source, stops, trace=True)
    return {"locations": locs, "roads": roads, "steps": r.steps, "order": r.visit_order,
            "legs": [{"from": l.origin, "to": l.destination, "distance": l.distance, "path": l.path} for l in r.legs],
            "return_leg": ({"from": r.return_leg.origin, "to": r.return_leg.destination,
                            "distance": r.return_leg.distance, "path": r.return_leg.path} if r.return_leg else None),
            "total_distance": r.total_distance}
