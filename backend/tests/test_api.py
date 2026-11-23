"""Integration tests: a real uvicorn server on a free port, real HTTP, a temp JSON store."""

import csv
import io
import json
import socket
import threading
import time
import urllib.error
import urllib.request

import pytest
import uvicorn

from app.main import create_app

NEW = {"destination": "Cyber Hub", "weight": 7, "priority": 4, "deadline": "2026-12-02T10:00", "value": 800}


class Client:
    def __init__(self, base):
        self.base = base

    def call(self, method, path, body=None, raw=False):
        data = None
        if body is not None:
            data = body.encode() if isinstance(body, str) else json.dumps(body).encode()
        req = urllib.request.Request(self.base + path, data=data, method=method,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                payload = r.read()
                return r.status, (payload if raw else json.loads(payload)), r.headers
        except urllib.error.HTTPError as e:
            payload = e.read()
            return e.code, (payload if raw else json.loads(payload)), e.headers

    def get(self, p, **k): return self.call("GET", p, **k)
    def post(self, p, b=None, **k): return self.call("POST", p, b, **k)
    def put(self, p, b=None): return self.call("PUT", p, b)
    def delete(self, p, b=None): return self.call("DELETE", p, b)


@pytest.fixture
def api(tmp_path):
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(create_app(tmp_path), host="127.0.0.1", port=port, log_level="error"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.05)
    yield Client(f"http://127.0.0.1:{port}")
    server.should_exit = True
    thread.join(timeout=5)


def test_state_and_unknown_routes(api):
    status, state, _ = api.get("/api/state")
    assert status == 200 and len(state["parcels"]) == 24 and state["settings"]["depot"] == "Depot"
    status, body, _ = api.get("/api/nope")
    assert status == 404 and body["error"]["code"] == "not_found"
    status, body, _ = api.post("/api/parcels", "{not json")
    assert status == 400 and body["error"]["code"] == "invalid_json"


def test_parcel_crud_roundtrip(api):
    status, created, _ = api.post("/api/parcels", {**NEW, "id": "T-1"})
    assert status == 201 and created["id"] == "T-1" and created["status"] == "pending"
    status, auto, _ = api.post("/api/parcels", NEW)
    assert status == 201 and auto["id"] == "PKG-0025"
    status, upd, _ = api.put("/api/parcels/T-1", {**NEW, "weight": 9, "id": "IGNORED"})
    assert status == 200 and upd["weight"] == 9 and upd["id"] == "T-1"
    assert api.delete("/api/parcels/T-1")[0] == 200
    status, body, _ = api.delete("/api/parcels/T-1")
    assert status == 404 and body["error"]["code"] == "parcel_not_found"
    assert api.put("/api/parcels/NOPE", NEW)[0] == 404


@pytest.mark.parametrize("patch,field,fragment", [
    ({"weight": 0}, "weight", "greater than or equal to 1"),
    ({"weight": 2.5}, "weight", "whole number"),
    ({"weight": "abc"}, "weight", "whole number"),
    ({"priority": 9}, "priority", "less than or equal to 5"),
    ({"deadline": "tomorrow"}, "deadline", "not a valid date"),
    ({"value": -5}, "value", "greater than or equal to 0"),
    ({"destination": ""}, "destination", "at least 1"),
    ({"status": "lost"}, "status", "pending"),
])
def test_validation_messages(api, patch, field, fragment):
    status, body, _ = api.post("/api/parcels", {**NEW, **patch})
    assert status == 422 and body["error"]["code"] == "validation_error"
    fields = {d["field"]: d["message"] for d in body["error"]["details"]}
    assert fragment in fields[field], fields


def test_missing_fields_and_conflicts(api):
    status, body, _ = api.post("/api/parcels", {"destination": "Cyber Hub"})
    assert status == 422
    assert {d["field"] for d in body["error"]["details"]} == {"weight", "priority", "deadline", "value"}
    status, body, _ = api.post("/api/parcels", {**NEW, "destination": "Atlantis"})
    assert status == 422 and body["error"]["code"] == "unknown_destination"
    api.post("/api/parcels", {**NEW, "id": "DUP"})
    status, body, _ = api.post("/api/parcels", {**NEW, "id": "DUP"})
    assert status == 409 and body["error"]["code"] == "duplicate_id"


def test_graph_editing_and_shortest_path(api):
    status, p, _ = api.post("/api/graph/shortest-path", {"source": "Depot", "target": "Manesar"})
    assert status == 200 and p["reachable"] and p["path"][0] == "Depot" and p["path"][-1] == "Manesar"
    assert p["distance"] == pytest.approx(sum(h["distance"] for h in p["hops"]))
    # new isolated location -> clear "unreachable" answer, never a fake route
    assert api.post("/api/graph/locations", {"name": "Island", "x": 5, "y": 5})[0] == 201
    assert api.post("/api/graph/locations", {"name": "Island", "x": 5, "y": 5})[0] == 409
    status, p, _ = api.post("/api/graph/shortest-path", {"source": "Depot", "target": "Island"})
    assert status == 200 and p["reachable"] is False and "No road path" in p["message"]
    assert api.post("/api/graph/roads", {"a": "Island", "b": "Depot", "weight": 3.5})[0] == 201
    assert api.post("/api/graph/shortest-path", {"source": "Island", "target": "Depot"})[1]["distance"] == 3.5
    status, body, _ = api.post("/api/graph/roads", {"a": "Island", "b": "Depot", "weight": -2})
    assert status == 422 and "negative" in body["error"]["message"].lower()
    assert api.post("/api/graph/roads", {"a": "Island", "b": "Nowhere", "weight": 1})[0] == 404
    assert api.post("/api/graph/shortest-path", {"source": "Depot", "target": "Nowhere"})[0] == 404
    assert api.delete("/api/graph/roads", {"a": "Island", "b": "Depot"})[0] == 200
    assert api.delete("/api/graph/roads", {"a": "Island", "b": "Depot"})[0] == 404
    status, body, _ = api.delete("/api/graph/locations/Island")
    assert status == 200 and body["affected_parcels"] == 0
    assert api.delete("/api/graph/locations/Depot")[0] == 409
    adj = api.get("/api/graph")[1]["adjacency"]
    assert "Island" not in adj and adj["Depot"]


def test_full_workflow_and_dashboard(api):
    assert api.get("/api/result")[1]["result"] is None
    status, res, _ = api.post("/api/optimise", {"capacity": 60})
    assert status == 200 and res["status"] == "optimised" and res["capacity"] == 60
    assert res["used_weight"] <= 60 and res["route"]["total_distance"] > 0 and res["route"]["returned_to_depot"]
    assert set(res["timings_ms"]) >= {"sorting", "knapsack", "routing", "total"}
    assert api.get("/api/settings")[1]["capacity"] == 60           # capacity persisted
    dash = api.get("/api/dashboard")[1]
    assert dash["total_parcels"] == 24 and dash["result"]["selected"] == len(res["selected"])
    assert dash["result"]["stale"] is False
    api.post("/api/parcels", NEW)                                  # data changed -> result is stale
    assert api.get("/api/result")[1]["result"]["stale"] is True
    assert api.post("/api/optimise", {"depot": "Nowhere"})[0] == 422
    assert api.post("/api/optimise", {"capacity": -5})[0] == 422


def test_zero_capacity_and_whatif_not_persisted(api):
    status, res, _ = api.post("/api/knapsack", {"capacity": 0})
    assert status == 200 and res["status"] == "nothing_selected" and res["selected"] == []
    assert api.get("/api/result")[1]["result"] is None            # what-if runs are not stored
    status, res, _ = api.post("/api/knapsack", {"capacity": 40})
    assert res["dp"]["table"] is not None and len(res["dp"]["table"]) == 25


def test_sorting_endpoint(api):
    status, s, _ = api.post("/api/sort", {})
    assert status == 200 and s["n"] == 24 and len(s["original"]) == len(s["sorted"]) == 24
    keys = [(-p["priority"], p["deadline"], p["id"]) for p in s["sorted"]]
    assert keys == sorted(keys) and s["comparisons"] > 0 and s["time_ms"] >= 0 and s["trace"]
    assert api.post("/api/sort", {"sorter": "bogus"})[0] == 422


def test_settings_validation(api):
    assert api.put("/api/settings", {"speed_kmph": 0})[0] == 422
    assert api.put("/api/settings", {"depot": "Nowhere"})[0] == 422
    assert api.put("/api/settings", {"dispatch_time": "never"})[0] == 422
    status, s, _ = api.put("/api/settings", {"capacity": 77, "depot": "Cyber Hub"})
    assert status == 200 and s["capacity"] == 77 and s["depot"] == "Cyber Hub"


def test_import_export_and_dataset_loading(api):
    csv_text = api.get("/api/export/parcels.csv", raw=True)[1].decode()
    assert len(list(csv.DictReader(io.StringIO(csv_text)))) == 24
    status, out, _ = api.post("/api/parcels/import", {"format": "csv", "mode": "replace", "content": csv_text})
    assert status == 200 and out["added"] == 24 and out["errors"] == []
    bad = json.dumps([{"destination": "Cyber Hub"}, {**NEW, "id": "OK-1"}])
    status, out, _ = api.post("/api/parcels/import", {"format": "json", "content": bad})
    assert status == 200 and out["added"] == 1 and out["errors"][0]["row"] == 1 and out["total"] == 25
    assert api.post("/api/parcels/import", {"format": "json", "content": "{oops"})[0] == 422
    assert api.post("/api/parcels/import", {"format": "xml", "content": "x"})[0] == 422
    assert api.get("/api/export/parcels.json", raw=True)[1].startswith(b"{")
    assert api.post("/api/datasets/load", {"size": 200, "seed": 5})[0] == 200
    assert len(api.get("/api/parcels")[1]["parcels"]) == 200
    assert api.post("/api/datasets/load", {"size": 0})[0] == 200          # empty dataset
    res = api.post("/api/optimise", {})[1]
    assert res["status"] == "no_parcels" and res["warnings"]


def test_benchmark_and_report_exports(api):
    assert api.get("/api/export/benchmark.csv")[0] == 404
    status, b, _ = api.post("/api/benchmark/run", {"sizes": [10, 50], "repeats": 2})
    assert status == 200 and [r["n"] for r in b["rows"]] == [10, 50]
    assert api.get("/api/benchmark/latest")[1]["benchmark"]["rows"][0]["n"] == 10
    assert api.post("/api/benchmark/run", {"sizes": []})[0] == 422
    assert api.post("/api/benchmark/run", {"sizes": [50000]})[0] == 422
    status, text, hdr = api.get("/api/export/benchmark.csv", raw=True)
    assert status == 200 and "attachment" in hdr["Content-Disposition"] and text.count(b"\n") == 3
    for kind in ("packing-plan.csv", "route.csv", "summary.csv"):
        status, text, _ = api.get(f"/api/export/{kind}", raw=True)
        assert status == 200 and len(text) > 20, kind
    status, pdf, hdr = api.get("/api/export/report.pdf", raw=True)
    assert status == 200 and pdf[:5] == b"%PDF-" and hdr["Content-Type"] == "application/pdf"
    assert api.get("/api/export/nothing.zip")[0] == 404


def test_learning_centre(api):
    content = api.get("/api/learn/content")[1]["algorithms"]
    assert [a["id"] for a in content] == ["merge-sort", "knapsack", "dijkstra", "nearest-neighbour"]
    assert all(a["pseudocode"] and a["time"] and a["space"] for a in content)
    s = api.post("/api/learn/merge-sort", {"values": [5, 2, 9, 1]})[1]
    assert s["output"] == [1, 2, 5, 9] and s["steps"]
    assert api.post("/api/learn/merge-sort", {"values": []})[0] == 422
    k = api.post("/api/learn/knapsack", {"weights": [1, 3, 4, 5], "values": [1, 4, 5, 7], "capacity": 7})[1]
    assert k["best_value"] == 9 and k["selected"] == [1, 2] and len(k["table"]) == 5
    assert api.post("/api/learn/knapsack", {"weights": [1], "values": [1, 2], "capacity": 7})[0] == 422
    d = api.post("/api/learn/dijkstra", {"source": "A", "target": "F"})[1]
    assert d["path"][0] == "A" and d["path"][-1] == "F" and d["steps"]
    assert api.post("/api/learn/dijkstra", {"source": "Z", "target": "F"})[0] == 404
    n = api.post("/api/learn/nearest-neighbour", {"source": "A", "stops": ["B", "D", "F"]})[1]
    assert sorted(n["order"]) == ["B", "D", "F"] and n["return_leg"]


def test_reset_restores_sample_data(api):
    api.post("/api/datasets/load", {"size": 3})
    assert api.post("/api/reset", {})[0] == 200
    assert len(api.get("/api/parcels")[1]["parcels"]) == 24


def test_state_persists_on_disk(api, tmp_path):
    api.post("/api/parcels", {**NEW, "id": "DISK-1"})
    saved = json.loads((tmp_path / "state.json").read_text())
    assert any(p["id"] == "DISK-1" for p in saved["parcels"])
