# Project Report: Mini-Courier Planner

*Design & Analysis of Algorithms (ETCCDA302), K.R. Mangalam University*

## 1. Problem statement
A courier has a vehicle with limited weight capacity, a queue of parcels (each with destination, weight, priority, deadline and value) and a road network. The system must decide **which parcels to load**, **in what order of priority they are considered**, and **which route to drive**, and must show how fast each algorithm runs.

## 2. Solution overview
```
Parcel input → validation → graph construction → depot reachability (one Dijkstra run; parcels with unknown or
unreachable destinations are classified *undeliverable*) → Merge Sort of all pending parcels (priority, deadline, ID)
→ 0/1 Knapsack DP on the deliverable parcels only (value × priority, capacity in kg)
→ unique destinations of selected parcels → Dijkstra (binary min-heap) + Nearest Neighbour tour (+ return to depot if a road exists)
→ ETA model → stage timings → dashboard, exports and PDF report
```
All stages share one parcel structure and one graph model (`backend/app/services/pipeline.py`).

## 3. Stack actually delivered (deviations from the brief)
Starlette + Pydantic v2 + uvicorn instead of FastAPI; React 19 + TypeScript + Tailwind CSS 4 bundled with esbuild instead of Vite; dependency-free SVG charts and an inline SVG icon set instead of Recharts/Lucide; a single JSON file instead of SQLite. Reason: no network access in the build environment, so the requested packages could not be installed or tested. See README for the full table.

## 4. Mapping to the five assignment phases

### Phase 1: Courier problem design and planning
* Problem model, data structures and pipeline: sections 1-2, `docs/ARCHITECTURE.md`.
* Parcel fields: ID, destination, weight (kg, whole), priority 1-5, deadline, value, status; validation messages in the form and in imports.
* Evidence: Parcels page, `sample_data/`, `backend/app/models.py`.

### Phase 2: Package prioritisation and box filling
* **Merge Sort** (manual, stable, tuple key `(-priority, deadline, id)`), step-by-step trace, comparison count, timing: *Prioritisation* page, `algorithms/sorting.py`.
* **0/1 Knapsack DP** (1-D array, capacities descending, decision bytes for reconstruction), selected/rejected lists, remaining capacity, DP table with backtracking path: *Load planning* page, `algorithms/knapsack.py`.
* Evidence: screenshots 03, 04; tests against brute force (`docs/TESTING.md`).

### Phase 3: Route maker and graph processing
* Weighted adjacency-list graph with add/remove location and road, negative-weight rejection: *Road network* page, `algorithms/graph.py`.
* **Dijkstra** with a hand-written binary min-heap; path and distance display.
* **Nearest Neighbour TSP** over Dijkstra distances, legs, return leg, undeliverable-parcel handling (excluded before the knapsack, never counted as loaded), and a clear statement that it is an approximation: *Route planner* page, `algorithms/tsp.py`.
* Evidence: screenshots 05, 06.

### Phase 4: Performance testing and optimisation
* Reproducible datasets (10 to 5,000 parcels, fixed seed), `perf_counter` with repeats, tracemalloc memory, CSV export: *Benchmark lab*, `services/benchmark.py`.
* Optimisation work: 1-D DP array (O(W) values), decision-matrix guard, capacity cap in benchmarks, early exit in Dijkstra, one Dijkstra per stop in the tour.
* Evidence: `docs/BENCHMARKS.md`, `docs/benchmarks/*`, screenshot 07.

### Phase 5: Final report and demonstration
* This report, README, architecture, algorithm, testing, benchmark, viva and install documents; PDF report and CSV exports (*Reports & export*); *Learning centre*; demonstration workflow in `docs/INSTALL_AND_RUN.md`.

## 5. Results
* **128 automated tests passed** (Linux, Python 3.13), including regression tests for undeliverable parcels and deterministic Nearest Neighbour tie-breaking.
* Full workflow exercised in headless Chromium: every page loaded with no console errors or failed API calls.
* Measured medians for 5,000 parcels on the build machine: sort 15.6 ms, knapsack 190 ms, Dijkstra 0.32 ms, route 36.7 ms (details and caveats in `docs/BENCHMARKS.md`).

## 6. Limitations (honest list)
* Weights and values are whole numbers by design (knapsack table indexed by integer capacity).
* Knapsack ignores deadlines; the on-time/late figure is a **model** (distance ÷ speed + minutes per stop), not a measurement.
* Nearest Neighbour is a heuristic and can be well above the optimal tour.
* Single vehicle, single depot, static road weights.
* PowerShell scripts were not executed; type-checking (`tsc`) was not run because `@types/react` was unavailable; verification of the frontend was by building and running it in a browser.
* Benchmark values come from one Linux machine.

## 7. Future improvements (not implemented)
2-opt / Christofides or Held-Karp for small tours; multiple vehicles; time-window-aware selection and routing; real map data; SQLite storage; authentication; port to FastAPI, Vite and Recharts; a second sorting algorithm selectable in the UI (the registry already supports it).
