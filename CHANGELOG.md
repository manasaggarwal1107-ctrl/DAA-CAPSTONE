# Changelog

## 1.0.1 - route feasibility, TSP selection and documentation fixes

### Fixed: knapsack ran before reachability (`backend/app/services/pipeline.py`)
* **Problem.** The 0/1 Knapsack ran on every pending parcel; unreachable destinations were only discovered afterwards by the route builder. An undeliverable parcel could therefore win a place in the knapsack, consume capacity and be counted in `selected`, `used_weight` and `total_value` although no leg was ever drawn to it. Some user-facing text also said such parcels were "not loaded" while they were still included in those totals.
* **New order.** validate -> build graph -> **depot reachability (one Dijkstra run)** -> Merge Sort of all pending parcels -> Knapsack on **deliverable** parcels only -> destination extraction -> Dijkstra + Nearest Neighbour -> ETA model -> timings.
* **Classification.** Undeliverable parcels get a `category` and `reason`: `unknown_destination`, `unreachable_destination`, or `tour_unreachable` (one-way roads: reachable from the depot but not from the previous stop; the selection is then recomputed, `counts.replans`). They are excluded from the knapsack, so they use no capacity and add no value.
* **One result everywhere.** New result fields `undeliverable` and `counts`; new statuses `nothing_deliverable`; `unreachable` now lists the destinations of undeliverable parcels; the `dp` section describes the parcels the knapsack really received; new timing key `reachability`.
* **UI** (design unchanged): Load planning page shows an *Undeliverable parcels* table and "Selected / deliverable"; Route planner notice reworded; Dashboard knows the new status.
* **Exports / PDF.** `packing-plan.csv` has `undeliverable` rows; `summary.csv` has `undeliverable_parcels`; the PDF summary and a new *Undeliverable parcels* table agree with the UI.
* **Stored results.** A `last_result` saved by 1.0.0 (no `counts`) is ignored on load, so the UI asks for a fresh optimisation instead of rendering an inconsistent plan.

### Fixed: Nearest Neighbour sorted candidates to find a minimum (`backend/app/algorithms/tsp.py`)
* The next stop is now chosen with a **linear scan** (strict `<` on `(distance, name)`), O(k) per step instead of O(k log k). Ties go to the alphabetically smaller location. The optional `trace` output is preserved (its display list is sorted only when `trace=True`).
* Complexity statement made exact: **O(k (V+E) log V + k²)** (k Dijkstra runs plus k linear scans). Docstring, Learning Centre content and docs updated.

### Documentation audited and corrected
README, ARCHITECTURE, PROJECT_REPORT, ALGORITHMS, BENCHMARKS, VIVA, TESTING and INSTALL_AND_RUN now describe the real pipeline order, undeliverable-parcel behaviour, selection rule and complexity. **Correction:** the 1.0.0 README/report/viva said unroutable parcels were filtered before the knapsack; the 1.0.0 code did not do that. BENCHMARKS tables were regenerated from a fresh benchmark run (`docs/benchmarks/`), and the in-app Learning Centre text was updated to match. `react-icons` (unused) was removed from `package.json`.

### Tests: 111 -> 128 (`backend/tests/test_feasibility_regression.py`, 17 new)
Selected parcel with a disconnected destination; several parcels at one unreachable destination; all destinations unreachable; reachable/unreachable mix; unknown destination; one-way-road re-plan; depot destination; selected weight = routed weight = `used_weight` (and value); packing-plan CSV, summary CSV, route CSV and PDF agree; deterministic Nearest Neighbour tie-breaking independent of input order; trace preserved.

### Verification (what was and was not run)
* Run (Linux, Python 3.13): all 128 tests pass; server started; every UI page loaded in headless Chromium with no console errors or failed API calls, including a scenario with a disconnected location and undeliverable parcels; PDF and CSV exports downloaded and inspected.
* **Not run: anything on Windows.** `start.ps1`, `start.bat`, `run-tests.ps1` and Windows 10/11 compatibility remain unverified.
