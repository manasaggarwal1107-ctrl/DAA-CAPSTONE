# Benchmark results

All numbers below are **measured**, produced by `python scripts/run_benchmark.py` (also available in the app under *Benchmark lab*). Theoretical complexity is stated separately and is never presented as a measurement.

* Machine: Linux x86_64, Python 3.13.18 (see `docs/benchmarks/results.json` → `environment`). Your machine will give different absolute values; the *growth shape* is what matters.
* Method: `time.perf_counter()`, **5 repeats** per stage, median reported (minimum, mean in the CSV). Datasets come from a fixed seed (**42**), so inputs are identical on every run.
* Memory: `tracemalloc` peak of one *separate* extra run per stage (timing runs are never traced).
* Raw data: `docs/benchmarks/results.csv`, `results.json`. Graphs: `docs/benchmarks/runtime.png`, `docs/benchmarks/memory.png`.

## Dataset rules

| Rule | Value |
|---|---|
| Parcel counts | 10, 50, 100, 500, 1,000, 5,000 |
| Locations | `min(max(8, n/10), 150)`; connected graph from the same seed |
| Vehicle capacity | 25 % of total parcel weight, **capped at 600 kg** |
| Stops | distinct destinations of the parcels the knapsack selected |

## Median runtime (ms)

| Parcels | Locations | Capacity kg | Selected | Stops | DP cells | Merge Sort | Knapsack DP | Dijkstra (1 source) | Nearest Neighbour route |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | 8 | 27 | 5 | 4 | 280 | 0.0104 | 0.0155 | 0.0108 | 0.0615 |
| 50 | 8 | 178 | 19 | 7 | 8,950 | 0.0680 | 0.4163 | 0.0124 | 0.0872 |
| 100 | 10 | 368 | 42 | 9 | 36,900 | 0.1749 | 2.0311 | 0.0121 | 0.1541 |
| 500 | 50 | 600 | 104 | 43 | 300,500 | 1.1315 | 17.3871 | 0.0808 | 3.7758 |
| 1,000 | 100 | 600 | 146 | 79 | 601,000 | 2.3935 | 31.7173 | 0.1842 | 14.4797 |
| 5,000 | 150 | 600 | 281 | 120 | 3,005,000 | 15.6397 | 189.5709 | 0.3157 | 36.6915 |

## Peak memory (KiB, tracemalloc)

| Parcels | Sort | Knapsack | Dijkstra | Route |
|---:|---:|---:|---:|---:|
| 10 | 1.1 | 2.7 | 1.7 | 3.4 |
| 50 | 2.4 | 19.7 | 1.3 | 4.2 |
| 100 | 3.6 | 57.8 | 1.3 | 4.4 |
| 500 | 13.4 | 351.1 | 6.2 | 20.5 |
| 1,000 | 25.5 | 679.0 | 16.8 | 50.9 |
| 5,000 | 122.2 | 3,288.1 | 16.8 | 63.8 |

## Theory versus measurement

| Stage | Theory | What the measurements show |
|---|---|---|
| Merge Sort | O(n log n) | 10× more parcels (500→5,000) costs ≈ 14× more time (1.13→15.64 ms): slightly super-linear, as n log n predicts. |
| Knapsack | O(n·W) time, O(n·W) decision bytes | Time follows the DP cell count (100→5,000 parcels: 36,900 → 3,005,000 cells, ≈ 81×; time 2.03 → 189.6 ms, ≈ 93×). Memory grows with the cells too. |
| Dijkstra | O((V+E) log V) | Depends on graph size, not parcel count; grows from 0.01 ms (8 nodes) to 0.31 ms (150 nodes). |
| Route | k Dijkstra runs, O(k·(V+E) log V), plus an O(k²) linear minimum scan | Grows with both stops and graph size (k = 4 → 120). The O(k²) scan is not measured separately. |

Caveat: the graph size grows with n only because of the generator rule, so Dijkstra/route growth reflects that rule, not a property of parcels.

## Resource limits

* The decision matrix stores one byte per (parcel, capacity) cell. The capacity cap (600 kg) keeps 5,000 parcels at 3 million cells (~3 MB).
* The application refuses any knapsack above **60,000,000** decision cells with a message telling the user to reduce capacity or parcel count (`MAX_DP_CELLS` in `backend/app/algorithms/knapsack.py`).
* The DP *table* sent to the browser is drawn only for small instances; otherwise the UI says why it is not shown.
* Timings vary between runs with CPU load. Rerun with more repeats for tighter results.
