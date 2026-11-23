# System Architecture

## 1. Overview

```
Browser (React 19 + TypeScript, Tailwind CSS 4, SVG charts)
        |  JSON over HTTP  (/api/...)
Starlette app  (backend/app/main.py)  -- central error handlers (errors.py)
        |
services/   pipeline.py  store.py  datasets.py  benchmark.py  exports.py  report.py  learning.py
        |
algorithms/ sorting.py  knapsack.py  graph.py (MinHeap, Graph, Dijkstra)  tsp.py     <- pure Python, no web imports
        |
backend/data/state.json   (single JSON file, atomic write, process-wide lock)
```
`main.py` also serves the prebuilt frontend (`frontend/dist`) with `StaticFiles`, so one process and one port run the whole product. If `dist` is missing it returns a plain-text hint.

## 2. Stack actually used (and why it differs from the brief)

Starlette + Pydantic v2 + uvicorn (not FastAPI); esbuild + Tailwind 4 compiler (not Vite); dependency-free SVG charts (not Recharts); inline SVG icon set (not Lucide); JSON file storage; ReportLab + Matplotlib for the PDF. FastAPI/Vite/Recharts/Lucide could not be installed in the build environment (no network). Handlers are plain `async def` functions registered as Starlette `Route`s, so a FastAPI port is mechanical.

## 3. Shared data structures

* **Parcel** (`models.py`, Pydantic): `id`, `destination`, `weight` (int kg 1-10000), `priority` (int 1-5, 5 = most urgent), `deadline` (`YYYY-MM-DDTHH:MM`), `value` (int >= 0), `status` (`pending | delivered | cancelled`). Weights/values must be whole numbers because the DP is indexed by integer capacity.
* **Graph**: `Location{name,x,y}`, `Road{a,b,weight,bidirectional}`; at run time `store.build_graph` creates the adjacency-list `Graph` (`dict[str, list[(neighbour, weight)]]`; a two-way road is two arcs).
* **Settings**: `capacity`, `depot`, `dispatch_time`, `speed_kmph`, `service_minutes`.
* Algorithms work on plain lists/dicts, so the same parcel dicts flow through every stage.

## 4. The integrated workflow (`services/pipeline.py: run_pipeline`)

1. **Validation** - depot must exist; only `pending` parcels take part (delivered/cancelled are excluded with a warning).
2. **Graph construction** - the stored locations and roads are loaded into the adjacency-list graph.
3. **Depot reachability (before any selection)** - one Dijkstra run from the depot classifies every pending parcel: *deliverable*, or *undeliverable* with category `unknown_destination` (not a location of the network) or `unreachable_destination` (no road path from the depot).
4. **Sorting** - Merge Sort of **all** pending parcels with key `(-priority, deadline, id)` (so the prioritised list is complete).
5. **Knapsack** - runs on the **deliverable** parcels only, in sorted order: weights = parcel kg, values = `value x priority`, capacity = vehicle capacity. Undeliverable parcels therefore use no capacity and add no value; the decision matrix reconstructs selected / rejected parcels.
6. **Selected destination extraction** - unique destinations of selected parcels (the depot itself needs no travel).
7. **Dijkstra + Nearest Neighbour** - tour from the depot over those destinations; return leg if a road back exists. With *one-way* roads a destination can be reachable from the depot yet unreachable from the previous stop; its parcels are then moved to `undeliverable` (category `tour_unreachable`) and steps 5-7 are repeated, so the plan never contains parcels the route cannot deliver (`counts.replans` records this).
8. **Delivery model** - cumulative distance -> ETA = dispatch + distance / speed + stop minutes; compared with each deadline (an estimate, not a measurement).
9. **Timing** - each stage timed with `time.perf_counter()` (`timings_ms`: validation, graph, reachability, sorting, knapsack, selection, routing, total; knapsack/selection/routing accumulate over re-plans).

The result (status `optimised | partial_route | nothing_selected | nothing_deliverable | no_parcels`, `selected`, `rejected` (capacity only, with reason), `undeliverable` (with `category` and reason), `counts`, DP info for the deliverable parcels, route legs, warnings, timings) is one JSON object, stored as `last_result`. A result saved by an older version (no `counts`) is discarded on load. The dashboard marks a result **stale** when parcels, graph or settings change (hash of the stored state).

**Consistency invariants** (checked by `tests/test_feasibility_regression.py`): `used_weight` = sum of selected weights = sum of the weights of the parcels in `route.deliveries`; `total_value` likewise; `selected`, `rejected` and `undeliverable` are disjoint; `unreachable` lists the destinations of the undeliverable parcels, and no leg is drawn to them. The packing-plan CSV, summary CSV, route CSV, PDF report and the Load planning / Route planner pages are all generated from this one result object.

## 5. HTTP API (all under `/api`)

| Group | Endpoints |
|---|---|
| State | `GET /state`, `GET /result`, `GET /dashboard`, `POST /reset` |
| Parcels | `GET/POST /parcels`, `PUT/DELETE /parcels/{id}`, `POST /parcels/import` (JSON body `{format, content, mode}`), `POST /datasets/load` |
| Settings | `GET/PUT /settings` |
| Graph | `GET /graph`, `POST /graph/locations`, `DELETE /graph/locations/{name}`, `POST/DELETE /graph/roads`, `POST /graph/shortest-path` |
| Algorithms | `POST /sort`, `POST /knapsack` (what-if, not saved), `POST /optimise` (saves capacity/depot and result) |
| Benchmark | `POST /benchmark/run`, `GET /benchmark/latest` |
| Learning | `GET /learn/content`, `POST /learn/merge-sort`, `/learn/knapsack`, `/learn/dijkstra`, `/learn/nearest-neighbour` |
| Export | `GET /export/{parcels.csv, parcels.json, packing-plan.csv, route.csv, summary.csv, benchmark.csv, report.pdf}` |

Errors always have the shape `{"error": {"code", "message", "details"}}` (`errors.py`): `ApiError` (client mistakes), Pydantic `ValidationError` (422 with per-field messages), `AlgorithmError` subclasses (unknown location 404, resource limit 413, invalid input 422) and a last-resort 500 handler that logs and returns a safe message.

## 6. Persistence

`store.py` keeps the whole state in memory behind an `RLock` and writes `state.json` atomically (temp file + `os.replace`). A missing or corrupt file is replaced by the seeded sample state (24 parcels, 13 locations, 20 roads). The location is `backend/data/` or `COURIER_DATA_DIR`; there are no absolute paths in the code.

## 7. Frontend

`frontend/src`: `App.tsx` (sidebar + hash router), `store.tsx` (global state, toasts), `api.ts` (fetch wrapper that understands the error shape), `components/` (`ui.tsx` primitives, `charts.tsx` bar/line charts, `GraphCanvas.tsx` interactive SVG network, `viz.tsx` merge-trace and DP-table players), `pages/` (Dashboard, Parcels, Sorting, Knapsack, Network, Route, Benchmarks, Learn, Reports). Form checks mirror the server rules for instant feedback; the server stays authoritative. The parcel list sorts with the browser sort for display only - the algorithmic Merge Sort runs on the backend.

## 8. Resource limits

Knapsack decision matrix refused above 60,000,000 cells (`MAX_DP_CELLS`); the DP table is sent to the browser only when it has <= 20,000 cells; benchmark sizes are limited to 1-10,000 parcels per dataset by the request model; vehicle capacity <= 100,000 kg.

## 9. Not implemented

Authentication, multi-vehicle routing, deadline-aware optimisation, real maps, SQLite, concurrent multi-user editing (single in-process lock only).
