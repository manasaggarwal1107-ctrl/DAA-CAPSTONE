"""Starlette application: JSON API plus the pre-built React frontend.

Run with:  uvicorn app.main:app --port 8000     (from the ``backend`` folder)
"""

from __future__ import annotations

import hashlib
import json
import statistics
import time
from pathlib import Path
from typing import Any, Callable, Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError
from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.middleware.gzip import GZipMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse, Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from . import config
from .algorithms.errors import AlgorithmError
from .algorithms.graph import dijkstra
from .errors import (ApiError, algorithm_handler, api_error_handler, unexpected_handler,
                     validation_handler)
from .models import (BenchmarkRequest, DatasetRequest, ImportRequest, LearnGraphRequest,
                     LearnKnapsackRequest, LearnSortRequest, Location, OptimiseRequest, Parcel,
                     ParcelDraft, PathRequest, Road, RoadRef, SettingsPatch)
from .services import benchmark, datasets, exports, learning, pipeline, report
from .services.store import Store

M = TypeVar("M", bound=BaseModel)


async def body(request: Request, model: Type[M]) -> M:
    """Parse and validate a JSON body (invalid JSON -> 400, bad fields -> 422)."""
    try:
        raw = await request.json()
    except ValueError:
        raise ApiError(400, "invalid_json", "Request body must be valid JSON") from None
    return model.model_validate(raw)


def ok(data: Any, status: int = 200) -> JSONResponse:
    return JSONResponse(data, status_code=status)


def download(content: str | bytes, filename: str, media: str) -> Response:
    return Response(content, media_type=media, headers={"Content-Disposition": f'attachment; filename="{filename}"'})


def create_app(data_dir: Optional[Path] = None, frontend_dist: Optional[Path] = None) -> Starlette:
    store = Store((Path(data_dir) if data_dir else config.DATA_DIR) / "state.json")

    def signature() -> str:
        blob = json.dumps([store.state["parcels"], store.state["graph"], store.state["settings"]], sort_keys=True)
        return hashlib.sha1(blob.encode()).hexdigest()

    def optimise(capacity: Optional[int] = None, depot: Optional[str] = None, sorter: str = "merge",
                 persist: bool = True) -> dict:
        try:
            result = pipeline.run_pipeline(store.parcels(), store.graph_data(), store.settings(),
                                           capacity=capacity, depot=depot, sorter=sorter)
        except ValueError as exc:
            if isinstance(exc, AlgorithmError):
                raise
            raise ApiError(422, "invalid_input", str(exc)) from None
        if persist:
            result["signature"] = signature()
            store.set_result("last_result", result)
        return result

    def latest_result() -> dict:
        res = store.get_result("last_result")
        return res if res else optimise()

    # ------------------------------------------------------------- state
    async def get_state(_: Request) -> Response:
        return ok({"parcels": store.parcels(), "graph": store.graph_data(), "settings": store.settings()})

    async def get_result(_: Request) -> Response:
        res = store.get_result("last_result")
        if res:
            res["stale"] = res.get("signature") != signature()
        return ok({"result": res})

    async def reset(_: Request) -> Response:
        store.reset_to_sample()
        return ok({"ok": True})

    async def dashboard(_: Request) -> Response:
        parcels, res, bench = store.parcels(), store.get_result("last_result"), store.get_result("last_benchmark")
        prio = {str(k): 0 for k in range(1, 6)}
        for p in parcels:
            prio[str(p["priority"])] += 1
        edges = [0, 5, 10, 15, 20, 25, 30]
        weight_bins = [{"label": f"{lo + 1}-{hi}", "count": sum(1 for p in parcels if lo < p["weight"] <= hi)}
                       for lo, hi in zip(edges, edges[1:])]
        weight_bins.append({"label": f">{edges[-1]}", "count": sum(1 for p in parcels if p["weight"] > edges[-1])})
        return ok({
            "total_parcels": len(parcels),
            "pending_parcels": sum(1 for p in parcels if p["status"] == "pending"),
            "locations": len(store.state["graph"]["locations"]),
            "roads": len(store.state["graph"]["roads"]),
            "priority_distribution": [{"priority": k, "count": v} for k, v in prio.items()],
            "weight_distribution": weight_bins,
            "result": None if not res else {
                "status": res["status"], "ran_at": res["ran_at"], "stale": res.get("signature") != signature(),
                "selected": len(res["selected"]), "utilisation": res["utilisation"], "capacity": res["capacity"],
                "used_weight": res["used_weight"], "total_value": res["total_value"],
                "route_distance": res["route"]["total_distance"], "timings_ms": res["timings_ms"],
                "deliveries": res["route"]["deliveries"], "on_time": res["route"]["on_time"],
                "late": res["route"]["late"], "warnings": res["warnings"]},
            "benchmark": None if not bench else {"generated_at": bench["generated_at"], "rows": bench["rows"]},
        })

    # ----------------------------------------------------------- parcels
    async def list_parcels(_: Request) -> Response:
        return ok({"parcels": store.parcels()})

    async def create_parcel(request: Request) -> Response:
        return ok(store.add_parcel(await body(request, ParcelDraft)), 201)

    async def edit_parcel(request: Request) -> Response:
        try:
            raw = await request.json()
        except ValueError:
            raise ApiError(400, "invalid_json", "Request body must be valid JSON") from None
        if isinstance(raw, dict):
            raw = {**raw, "id": request.path_params["pid"]}      # the ID in the URL is authoritative
        return ok(store.update_parcel(request.path_params["pid"], Parcel.model_validate(raw)))

    async def remove_parcel(request: Request) -> Response:
        store.delete_parcel(request.path_params["pid"])
        return ok({"ok": True})

    async def import_parcels(request: Request) -> Response:
        req = await body(request, ImportRequest)
        replace = req.mode == "replace"
        valid, errors = exports.parse_import(req.format, req.content, store.parcels(),
                                             store.location_names(), replace)
        if valid or replace:
            store.replace_parcels(valid if replace else store.parcels() + valid)
        return ok({"added": len(valid), "errors": errors, "total": len(store.parcels())})

    async def load_dataset(request: Request) -> Response:
        req = await body(request, DatasetRequest)
        dests = [l["name"] for l in store.graph_data()["locations"] if l["name"] != store.settings()["depot"]]
        store.replace_parcels(datasets.generate_parcels(req.size, dests, req.seed))
        return ok({"generated": req.size, "seed": req.seed})

    # ---------------------------------------------------------- settings
    async def get_settings(_: Request) -> Response:
        return ok(store.settings())

    async def put_settings(request: Request) -> Response:
        patch = await body(request, SettingsPatch)
        data = patch.model_dump()
        if data.get("dispatch_time"):
            from .models import normalise_deadline
            try:
                data["dispatch_time"] = normalise_deadline(data["dispatch_time"])
            except ValueError as exc:
                raise ApiError(422, "validation_error", str(exc), [{"field": "dispatch_time", "message": str(exc)}])
        return ok(store.update_settings(data))

    # ------------------------------------------------------------- graph
    async def get_graph(_: Request) -> Response:
        g = store.graph()
        return ok({**store.graph_data(), "adjacency": {n: [{"to": d, "weight": w} for d, w in g.neighbours(n)]
                                                       for n in g.nodes()}})

    async def add_location(request: Request) -> Response:
        store.add_location(await body(request, Location))
        return ok({"ok": True}, 201)

    async def del_location(request: Request) -> Response:
        return ok({"ok": True, "affected_parcels": store.remove_location(request.path_params["name"])})

    async def add_road(request: Request) -> Response:
        store.add_road(await body(request, Road))
        return ok({"ok": True}, 201)

    async def del_road(request: Request) -> Response:
        ref = await body(request, RoadRef)
        store.remove_road(ref.a, ref.b)
        return ok({"ok": True})

    async def path(request: Request) -> Response:
        req = await body(request, PathRequest)
        res = dijkstra(store.graph(), req.source, target=req.target)
        nodes = res.path_to(req.target)
        if nodes is None:
            return ok({"reachable": False, "path": [], "distance": None,
                       "message": f"No road path exists from '{req.source}' to '{req.target}'."})
        g = store.graph()
        hops = [{"from": a, "to": b, "distance": next(w for d, w in g.neighbours(a) if d == b)}
                for a, b in zip(nodes, nodes[1:])]
        return ok({"reachable": True, "path": nodes, "distance": round(res.dist[req.target], 3), "hops": hops})

    # -------------------------------------------------------- algorithms
    async def sort_endpoint(request: Request) -> Response:
        raw = await request.json() if (await request.body()) else {}
        sorter = raw.get("sorter", "merge") if isinstance(raw, dict) else "merge"
        active = [p for p in store.parcels() if p["status"] == "pending"]
        stats: dict = {}
        samples = []
        for _ in range(5):                       # repeated measurement; the median is reported
            t0 = time.perf_counter()
            ordered = pipeline.sort_parcels(active, sorter, stats={"comparisons": 0})
            samples.append((time.perf_counter() - t0) * 1000)
        pipeline.sort_parcels(active, sorter, stats=stats)
        trace: list = []
        pipeline.sort_parcels(active[:8], sorter, trace=trace)
        return ok({"sorter": sorter, "original": active, "sorted": ordered, "n": len(active),
                   "time_ms": round(statistics.median(samples), 4), "repeats": 5,
                   "comparisons": stats["comparisons"],
                   "trace": trace, "trace_parcels": [p["id"] for p in active[:8]],
                   "complexity": {"time": "O(n log n) best / average / worst", "space": "O(n)"}})

    async def knapsack_endpoint(request: Request) -> Response:
        raw = await request.json() if (await request.body()) else {}
        req = OptimiseRequest.model_validate(raw)
        return ok(await run_in_threadpool(optimise, req.capacity, req.depot, req.sorter, False))

    async def optimise_endpoint(request: Request) -> Response:
        raw = await request.json() if (await request.body()) else {}
        req = OptimiseRequest.model_validate(raw)
        if req.capacity is not None:
            store.update_settings({"capacity": req.capacity})
        if req.depot is not None:
            store.update_settings({"depot": req.depot})
        return ok(await run_in_threadpool(optimise, None, None, req.sorter, True))

    # --------------------------------------------------------- benchmark
    async def run_bench(request: Request) -> Response:
        req = await body(request, BenchmarkRequest)
        result = await run_in_threadpool(benchmark.run_benchmark, req.sizes, req.repeats, req.seed)
        store.set_result("last_benchmark", result)
        return ok(result)

    async def latest_bench(_: Request) -> Response:
        return ok({"benchmark": store.get_result("last_benchmark")})

    # ---------------------------------------------------------- learning
    async def learn_content(_: Request) -> Response:
        return ok({"algorithms": learning.content()})

    async def learn_sort(request: Request) -> Response:
        return ok(learning.demo_merge_sort((await body(request, LearnSortRequest)).values))

    async def learn_knapsack(request: Request) -> Response:
        r = await body(request, LearnKnapsackRequest)
        return ok(learning.demo_knapsack(r.weights, r.values, r.capacity))

    async def learn_dijkstra(request: Request) -> Response:
        r = await body(request, LearnGraphRequest)
        return ok(learning.demo_dijkstra(r.source, r.target))

    async def learn_nn(request: Request) -> Response:
        r = await body(request, LearnGraphRequest)
        return ok(learning.demo_nn(r.source, r.stops))

    # ----------------------------------------------------------- exports
    async def export(request: Request) -> Response:
        kind = request.path_params["kind"]
        csv_t, json_t = "text/csv; charset=utf-8", "application/json"
        if kind == "parcels.csv":
            return download(exports.parcels_csv(store.parcels()), kind, csv_t)
        if kind == "parcels.json":
            return download(exports.parcels_json(store.parcels()), kind, json_t)
        if kind in ("packing-plan.csv", "route.csv", "summary.csv", "report.pdf"):
            res = await run_in_threadpool(latest_result)
            if kind == "packing-plan.csv":
                return download(exports.packing_plan_csv(res), kind, csv_t)
            if kind == "route.csv":
                return download(exports.route_csv(res), kind, csv_t)
            if kind == "summary.csv":
                return download(exports.summary_csv(res), kind, csv_t)
            pdf = await run_in_threadpool(report.build_report, res, store.graph_data(), store.get_result("last_benchmark"))
            return download(pdf, "mini-courier-report.pdf", "application/pdf")
        if kind == "benchmark.csv":
            bench = store.get_result("last_benchmark")
            if not bench:
                raise ApiError(404, "no_benchmark", "Run the benchmark first; there are no measurements to export yet.")
            return download(exports.benchmark_csv(bench), kind, csv_t)
        raise ApiError(404, "unknown_export", f"Unknown export '{kind}'")

    async def api_not_found(request: Request) -> Response:
        raise ApiError(404, "not_found", f"No API endpoint at {request.url.path}")

    routes = [
        Route("/api/state", get_state), Route("/api/result", get_result), Route("/api/dashboard", dashboard),
        Route("/api/reset", reset, methods=["POST"]),
        Route("/api/parcels", list_parcels, methods=["GET"]), Route("/api/parcels", create_parcel, methods=["POST"]),
        Route("/api/parcels/import", import_parcels, methods=["POST"]),
        Route("/api/parcels/{pid}", edit_parcel, methods=["PUT"]),
        Route("/api/parcels/{pid}", remove_parcel, methods=["DELETE"]),
        Route("/api/datasets/load", load_dataset, methods=["POST"]),
        Route("/api/settings", get_settings, methods=["GET"]), Route("/api/settings", put_settings, methods=["PUT"]),
        Route("/api/graph", get_graph, methods=["GET"]),
        Route("/api/graph/locations", add_location, methods=["POST"]),
        Route("/api/graph/locations/{name}", del_location, methods=["DELETE"]),
        Route("/api/graph/roads", add_road, methods=["POST"]),
        Route("/api/graph/roads", del_road, methods=["DELETE"]),
        Route("/api/graph/shortest-path", path, methods=["POST"]),
        Route("/api/sort", sort_endpoint, methods=["POST"]),
        Route("/api/knapsack", knapsack_endpoint, methods=["POST"]),
        Route("/api/optimise", optimise_endpoint, methods=["POST"]),
        Route("/api/benchmark/run", run_bench, methods=["POST"]),
        Route("/api/benchmark/latest", latest_bench, methods=["GET"]),
        Route("/api/learn/content", learn_content), Route("/api/learn/merge-sort", learn_sort, methods=["POST"]),
        Route("/api/learn/knapsack", learn_knapsack, methods=["POST"]),
        Route("/api/learn/dijkstra", learn_dijkstra, methods=["POST"]),
        Route("/api/learn/nearest-neighbour", learn_nn, methods=["POST"]),
        Route("/api/export/{kind}", export),
        Route("/api/{rest:path}", api_not_found, methods=["GET", "POST", "PUT", "DELETE"]),
    ]
    dist = Path(frontend_dist) if frontend_dist else config.FRONTEND_DIST
    if (dist / "index.html").exists():
        routes.append(Mount("/", StaticFiles(directory=dist, html=True), name="ui"))
    else:
        async def no_ui(_: Request) -> Response:
            return PlainTextResponse("Frontend build not found. Run scripts\\build-frontend.ps1 (needs Node.js) "
                                     "or use the API under /api.", status_code=200)
        routes.append(Route("/", no_ui))

    app = Starlette(routes=routes, exception_handlers={
        ApiError: api_error_handler, ValidationError: validation_handler,
        AlgorithmError: algorithm_handler, Exception: unexpected_handler})
    app.add_middleware(GZipMiddleware, minimum_size=1024)
    app.state.store = store
    return app


app = create_app()
