# Algorithms, Recurrences and Complexity

All four algorithms are written by hand in `backend/app/algorithms/`. Results below are derived from that code.

## 1. Merge Sort (`sorting.py`)

**Purpose:** order parcels - higher priority first, then earlier deadline, then parcel ID. The single sort key is the tuple `(-priority, deadline, id)`; deadlines are `YYYY-MM-DDTHH:MM` strings, which compare chronologically.

**Principle:** split in halves recursively; a list of length <= 1 is sorted; merge two sorted lists by repeatedly taking the smaller front item. `<=` takes the left item on ties, so the sort is **stable**. The input is never modified (new lists are built).

```
MERGE-SORT(A):
  if len(A) <= 1: return copy(A)
  mid <- len(A) / 2
  L <- MERGE-SORT(A[:mid]);  R <- MERGE-SORT(A[mid:])
  return MERGE(L, R)

MERGE(L, R):
  i <- 0; j <- 0; out <- []
  while i < len(L) and j < len(R):
      if key(L[i]) <= key(R[j]): out.append(L[i]); i++
      else:                       out.append(R[j]); j++
  append the rest of L and R;  return out
```
**Recurrence:** `T(n) = 2T(n/2) + Theta(n)` -> `Theta(n log n)` (Master theorem, case 2).
**Extras:** optional `trace` (split/merge events for the step-by-step view) and `stats["comparisons"]`. A registry `SORTERS = {"merge": merge_sort}` with `get_sorter(name)` lets another lab algorithm be added with one entry; only Merge Sort is registered.

## 2. 0/1 Knapsack, dynamic programming (`knapsack.py`)

**Problem:** items = parcels with weight `wt` (whole kg) and value `val = delivery value x priority`; capacity `W` = vehicle capacity. Maximise total value, weight <= W, each parcel at most once.

**Recurrence (2-D form):**
```
dp[0][w] = 0
dp[i][w] = dp[i-1][w]                                  if wt_i > w
dp[i][w] = max( dp[i-1][w], dp[i-1][w - wt_i] + val_i ) otherwise
answer = dp[n][W]
```
**Implementation:** one 1-D array `dp[0..W]`; for each item, `w` runs from `W` **down to** `wt_i`. Going downward means `dp[w - wt_i]` still holds the value from items `0..i-1`, so no item can be used twice (an upward loop would give the unbounded knapsack). When `dp[w]` improves, `keep[i][w] = 1` is set (one `bytearray(W+1)` per item). **Reconstruction:** start at `w = W`, for `i = n-1 .. 0`: if `keep[i][w]` then take item `i` and `w -= wt_i`.

```
KNAPSACK(wt, val, W):
  dp[0..W] <- 0
  for i in 0..n-1:
    for w from W down to wt[i]:
      if dp[w - wt[i]] + val[i] > dp[w]: dp[w] <- that; keep[i][w] <- 1
  w <- W; for i from n-1 down to 0: if keep[i][w]: select i; w <- w - wt[i]
```
**Visualisation:** with `record_table=True` and `(n+1)(W+1) <= 20,000`, a snapshot of `dp` after each item gives row `i` of the 2-D table; the UI draws it and highlights the backtracking path. Larger instances still run in full; the table is simply not returned (a note says so).
**Guards:** zero capacity or no items -> empty selection; an item heavier than `W` is never taken; negative inputs rejected; `n x (W+1) > 60,000,000` -> `ResourceLimitError`.
**Pseudo-polynomial:** the cost depends on the *value* of `W`, not the number of bits to write it.

## 3. Dijkstra with a binary min-heap (`graph.py`)

**Graph:** adjacency list `dict[node, list[(neighbour, weight)]]`; two-way road = two arcs. Negative, NaN and infinite weights, self-loops and unknown nodes are rejected when an edge is added.
**MinHeap:** array-backed binary heap of `(priority, sequence, item)`; the sequence number makes ties FIFO and deterministic. `push` sifts up, `pop` sifts down, both `O(log n)`.

```
DIJKSTRA(G, s [, target]):
  dist[s] <- 0; heap <- {(0, s)}
  while heap not empty:
    (d, u) <- heap.pop()
    if u settled: continue                    # stale entry (lazy deletion)
    mark u settled
    if u == target: break                     # early exit
    for (v, w) in G[u]:
      if v not settled and d + w < dist[v]:   # relaxation
          dist[v] <- d + w; prev[v] <- u; heap.push((dist[v], v))
  return dist, prev                           # path: follow prev[] back from target
```
**Recurrence / invariant:** `dist[v] = min over arcs (u,v) of dist[u] + w(u,v)`, `dist[s] = 0`; valid only for `w >= 0` because a settled node's distance is final. Unreachable nodes never get a distance (`path_to` returns `None`). Optional `trace` records each settled node with its relaxations.

## 4. Nearest Neighbour TSP (`tsp.py`)

**Algorithm:** start at the depot; repeat: run Dijkstra from the current location, choose the unvisited stop with the smallest shortest-road distance by a **linear minimum scan** (ties: alphabetical name, via strict `<` on the pair `(distance, name)`), append that leg (with its intermediate road path), move there. Afterwards run Dijkstra to the depot for the return leg if a path exists. Stops equal to the depot are ignored; unknown/unreachable stops are reported in `unreachable` and the loop ends if nothing remaining is reachable. Locations without parcels are not visited as stops.

```
NN(G, depot, stops):
  cur <- depot; remaining <- stops \ {depot}
  while remaining:
     sp <- DIJKSTRA(G, cur)
     best <- none
     for s in remaining: if reachable and (sp.dist[s], s) < best: best <- (sp.dist[s], s)   # O(k) scan
     if best is none: report remaining unreachable; break
     (d, nxt) <- best; add leg cur -> nxt along sp.path; remaining -= nxt; cur <- nxt
  return leg to depot if reachable
```
**This is an approximation.** TSP is NP-hard; the greedy choice has no optimality guarantee. The test suite checks the tour is never shorter than the brute-force optimum on small graphs (`test_nn_is_an_approximation_never_better_than_optimal`).

## 5. Complexity summary

| Algorithm | Best | Average | Worst | Space |
|---|---|---|---|---|
| Merge Sort | O(n log n) | O(n log n) | O(n log n) | O(n) auxiliary |
| 0/1 Knapsack DP | O(nW) | O(nW) | O(nW) | O(W) values + O(nW) bytes decision matrix |
| Dijkstra (binary heap, lazy deletion) | O(V + E) if the target is found early | O((V+E) log V) | O((V+E) log V) | O(V + E) graph, O(V + E) heap entries |
| Nearest Neighbour (k stops) | O(k (V+E) log V + k²) | O(k (V+E) log V + k²) | O(k (V+E) log V + k²) | O(V + k) |

Nearest Neighbour also does O(k) work per step to pick the minimum, O(k^2) in total, with no sorting (the code only sorts a candidate list when `trace=True`, for display). The total is O(k (V+E) log V + k^2); for the sizes used here the k Dijkstra runs dominate. The k stops are the destinations of the *selected, deliverable* parcels: reachability from the depot is established before the knapsack runs (see ARCHITECTURE section 4). The Dijkstra best-case row is the early-exit case of `dijkstra(..., target=...)`; a full single-source run is always `O((V+E) log V)`.

**Theory vs. measurement:** this file is theory. Measured times are in [BENCHMARKS.md](BENCHMARKS.md).
