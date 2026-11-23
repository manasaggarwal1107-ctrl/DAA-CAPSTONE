# Mini-Courier Planner

**Intelligent Delivery & Package Optimisation System** - capstone project for *Design & Analysis of Algorithms (ETCCDA302)*, K.R. Mangalam University.

A courier-planning web application that takes delivery parcels and a road network and produces a load plan and a delivery route using four hand-written algorithms:

| Stage | Algorithm | Where |
|---|---|---|
| Prioritise parcels | Merge Sort (stable, manual) | `backend/app/algorithms/sorting.py` |
| Choose what fits in the vehicle | 0/1 Knapsack, dynamic programming (1-D, capacities descending) | `backend/app/algorithms/knapsack.py` |
| Shortest road distances | Dijkstra with a hand-written binary min-heap | `backend/app/algorithms/graph.py` |
| Delivery tour | Nearest Neighbour TSP heuristic on Dijkstra distances | `backend/app/algorithms/tsp.py` |

Merge Sort, Knapsack and Dijkstra use no `sorted()`, `heapq`, NetworkX, SciPy or optimisation library (tests use `sorted()`, `heapq` and brute force only as *oracles*). The Nearest Neighbour code picks the next stop with a linear minimum scan; it calls `sorted()` only to order candidate and error lists for the optional trace/reporting, never to select a stop.

## Quick start (Windows 10/11)

```powershell
.\start.ps1        # or double-click start.bat
```
Opens http://127.0.0.1:8000. No login. Full instructions: [docs/INSTALL_AND_RUN.md](docs/INSTALL_AND_RUN.md).

## What is implemented

Dashboard (KPIs and 4 charts) - Parcel management (add/edit/delete/search/filter/sort, CSV/JSON import and export, row-level validation messages) - Prioritisation page with Merge Sort trace - Load planning page with DP table and reconstruction path - Road network editor with Dijkstra path finder - Route planner with ETA model - Benchmark lab (6 dataset sizes, real `perf_counter` timings, tracemalloc peaks, CSV export) - Learning centre (concept, pseudocode, recurrence, complexity, live traces, viva questions) - Reports (CSV exports and a PDF report).

## IMPORTANT: deviations from the original brief

The original brief asked for FastAPI, Vite and Recharts/Lucide. The build environment had **no network access**, so those packages could not be installed or tested. The delivered stack is what was actually built and run:

| Brief | Delivered | Note |
|---|---|---|
| FastAPI | **Starlette** + Pydantic v2 + uvicorn | FastAPI is itself built on Starlette; the route handlers are plain async functions and port over easily |
| Vite | **esbuild** bundler + Tailwind CSS 4 compiler (`frontend/scripts/build.mjs`) | React 19 + TypeScript, as requested |
| Recharts | Small dependency-free **SVG charts** (`frontend/src/components/charts.tsx`) | |
| Lucide icons | **Inline Lucide-style SVG icon set** (`frontend/src/icons.tsx`) | |
| JSON or SQLite | **One JSON file**, `backend/data/state.json` (atomic writes) | |
| Matplotlib/Plotly | Matplotlib (PDF report figures, benchmark PNGs) | |

All of these are replaceable; they were *not* silently swapped, and this table is the full list.

## What was and was not verified

* **Run and verified (Linux, Python 3.13, headless Chromium via Playwright):** 128 automated tests pass; the server started; every UI page loaded with no console errors or failed API calls; benchmark and screenshots produced from the running app.
* **NOT executed:** `start.ps1`, `start.bat`, `run-tests.ps1` (no PowerShell in the build environment). They were written carefully but have never been run - if one fails on your machine, the manual commands in INSTALL_AND_RUN.md do the same thing. The code was never run on Windows.
* **Not possible to type-check:** `@types/react` was unavailable, so `npm run typecheck` was not run; the frontend is verified by building and running it in a browser.
* Benchmark numbers are real measurements from one Linux machine; yours will differ.

## Design decisions worth knowing

* **Weights and values are whole numbers** (kg and currency units). The knapsack table is indexed by integer capacity, so fractional weights are rejected with a clear message.
* Effective value = `value x priority`; knapsack maximises the sum of effective values.
* The **ETA / "on time or late" figures are a model** (`distance / speed + minutes per stop`), not measurements.
* Nearest Neighbour is an **approximation**; the UI and docs say so.
* **Reachability is checked before selection.** Parcels whose destination is unknown or unreachable from the depot are classified *undeliverable*, excluded before the knapsack (so they use no capacity and add no value), listed separately in the UI, exports and PDF, and never routed. Selected weight, selected value and the route always describe the same parcels.

## Documentation

| File | Content |
|---|---|
| [CHANGELOG.md](CHANGELOG.md) | What changed in v1.0.1 and why |
| [docs/PROJECT_REPORT.md](docs/PROJECT_REPORT.md) | Report mapped to the five assignment phases |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture, API, data model |
| [docs/ALGORITHMS.md](docs/ALGORITHMS.md) | Algorithms, pseudocode, recurrences, complexity |
| [docs/TESTING.md](docs/TESTING.md) | Test-case documentation and results |
| [docs/BENCHMARKS.md](docs/BENCHMARKS.md) | Measured benchmark results vs theory |
| [docs/VIVA.md](docs/VIVA.md) | Viva questions and answers |
| [docs/INSTALL_AND_RUN.md](docs/INSTALL_AND_RUN.md) | Install, run, test, demo workflow |
| [docs/screenshots/](docs/screenshots/README.md) | Screenshots of the running application |
| `sample_data/` | Sample parcel CSV/JSON (10/24/50/100), road network, invalid-import examples |

## Folder structure

```
backend/app/algorithms   sorting, knapsack, graph (+heap, Dijkstra), tsp   (pure Python)
backend/app/services     pipeline, store, datasets, benchmark, exports, report, learning
backend/app/main.py      Starlette routes, error handling, static file serving
backend/tests            pytest suite (128 tests)
frontend/src             React + TypeScript UI;  frontend/dist = prebuilt bundle
sample_data  scripts  docs  start.ps1  start.bat  run-tests.ps1
```

## Future improvements (not implemented)

2-opt / Christofides tour improvement, multiple vehicles, time-window-aware routing (the knapsack ignores deadlines), real map data, SQLite storage, authentication, a FastAPI/Vite/Recharts port, a user-selectable second sorting algorithm in the UI (the registry supports it; only Merge Sort is registered).
