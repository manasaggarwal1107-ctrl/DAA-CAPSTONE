# Viva preparation: questions and answers

Answers describe what this implementation actually does (code references in brackets).

## Merge Sort  (`algorithms/sorting.py`)
1. **Why is Merge Sort O(n log n) in every case?** The list is halved log₂n times and each level merges n elements once. The split is by position, so input order cannot change the recursion shape.
2. **Why Merge Sort rather than Quick Sort?** It is stable and has a guaranteed O(n log n) worst case; Quick Sort can degrade to O(n²) on bad pivots.
3. **How do three sorting rules fit one comparison?** The key is the tuple `(-priority, deadline, id)`; tuples compare element by element.
4. **What is the space complexity?** O(n) auxiliary space for the merged lists, plus O(log n) recursion depth.
5. **What does stable mean and does it matter here?** Equal keys keep input order. The ID tie-breaker already makes keys unique, so the order is deterministic regardless.
6. **How could another sorting algorithm be added?** Sorters are registered by name in the sorter registry with the same call signature, so one entry adds a new algorithm.
7. **Did you use `sorted()`?** Not in the sorting stage. Tests use it as an oracle. (`tsp.py` uses it only to order the display list of the optional trace; the next stop is chosen by a linear scan.)

## 0/1 Knapsack  (`algorithms/knapsack.py`)
8. **State the recurrence.** `dp[i][w] = dp[i-1][w]` if `wt_i > w`, else `max(dp[i-1][w], dp[i-1][w-wt_i] + val_i)`; `dp[0][w] = 0`. Value = delivery value × priority.
9. **Why does the inner loop run from high capacity to low?** `dp[w-wt]` must still hold the previous item's value; going upwards would reuse one parcel several times (unbounded knapsack).
10. **Is O(nW) polynomial?** Pseudo-polynomial: W is a numeric value, not an input length. Hence whole-kg weights and the decision-matrix guard.
11. **How do you recover the chosen parcels?** A decision byte `keep[i][w]` is set whenever item i improves `dp[w]`; walk back from `(n, capacity)` subtracting weights for set bytes.
12. **Why not a greedy value/weight ratio?** Greedy is optimal only for the fractional knapsack; for 0/1 it can be arbitrarily bad.
13. **What is the space usage?** O(W) for the values plus n·(W+1) bytes of decisions (the 1-D array is why values need only O(W)).
14. **What if a parcel is heavier than the vehicle or capacity is 0?** It is never selected and appears in the rejected list with a reason; capacity 0 selects nothing (covered by tests).
15. **How is correctness checked?** Tests compare the DP with brute force over all subsets on random small instances.
16. **Why are deadlines ignored by the knapsack?** The brief's objective is priority-weighted value under a weight limit; deadlines are used for sorting and for the (modelled) on-time check. Time-window-aware selection is future work.

## Dijkstra  (`algorithms/graph.py`)
17. **Why no negative edges?** A settled node's distance is assumed final; a later negative edge could invalidate it. Negative roads are rejected on entry.
18. **Complexity with a binary heap?** O((V+E) log V). An array-scan version is O(V²).
19. **What is lazy deletion?** Instead of decrease-key, push a new heap entry and skip stale ones when popped.
20. **Which heap did you use?** A hand-written array-based binary min-heap, not `heapq`.
21. **How is the actual path obtained?** A `prev` map records the predecessor on each improvement; follow it back from the target.
22. **How are unreachable nodes handled?** They never get a distance; callers report "no route" rather than inventing a path.
23. **Why an adjacency list?** O(V+E) space and fast neighbour iteration for sparse road networks.

## Nearest Neighbour TSP  (`algorithms/tsp.py`)
24. **Is it optimal?** No. TSP is NP-hard; the greedy choice can force a long detour. Tests compare it with brute force on small cases.
25. **Why Dijkstra between stops?** Stops are joined by roads, so true distances and intermediate paths come from shortest paths.
26. **What is its complexity?** About k Dijkstra runs for k stops: O(k·(V+E) log V), plus an O(k) linear minimum scan per step (O(k²) in total, no sorting). Ties on distance go to the alphabetically smaller location.
27. **What if a stop is unreachable or there is no road back?** Reachability from the depot is computed *before* the knapsack, so parcels for unreachable destinations are classified undeliverable and never loaded. With one-way roads a stop may be reachable from the depot but not from the previous stop; those parcels are then excluded and the selection is recomputed. A missing return path is reported and the tour ends at the last stop.
28. **Which locations are visited?** Only destinations of selected parcels (plus roads passed through).
29. **How could the route be improved?** 2-opt or Christofides, or exact DP (Held–Karp) for few stops. Not implemented.

## Design and process
30. **Why Starlette instead of FastAPI?** FastAPI could not be installed in the build environment (no network). Starlette is FastAPI's base; handlers are plain async functions.
31. **How do you avoid misleading results?** Benchmarks show only measured values; ETAs are labelled as a model; undeliverable parcels are excluded before selection and listed separately, so selected weight/value always equal what the route delivers.
32. **How does the pipeline fit together?** Validate → build graph → depot reachability (Dijkstra) → Merge Sort of all pending parcels → Knapsack on deliverable parcels only → unique destinations → Dijkstra/NN route (re-plan if a stop is unreachable from the previous stop) → ETA check → timings → results/exports (`services/pipeline.py`).
33. **Why is reachability checked before the knapsack?** Otherwise a valuable but undeliverable parcel could win a place in the knapsack, consume capacity and inflate the reported weight and value while the route could never deliver it. Checking first keeps the packing plan and the route consistent.
