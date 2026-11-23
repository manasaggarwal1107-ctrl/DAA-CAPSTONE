"""Workflow, validation, import/export, benchmark and report tests (no HTTP)."""

import csv
import io
import json

import pytest
from pydantic import ValidationError

from app.errors import ApiError
from app.models import Parcel, ParcelDraft
from app.services import benchmark, datasets, exports, pipeline, report
from app.services.store import Store
from helpers import SETTINGS, graph_data, parcel


def run(parcels, gd=None, **kw):
    return pipeline.run_pipeline(parcels, gd or graph_data(), {**SETTINGS}, **kw)


class TestPipelineEdgeCases:
    def test_empty_dataset(self):
        r = run([])
        assert r["status"] == "no_parcels" and r["selected"] == [] and r["route"]["legs"] == []
        assert r["warnings"]

    def test_single_parcel(self):
        r = run([parcel(dest="B", weight=5)])
        assert r["status"] == "optimised"
        assert r["route"]["order"] == ["B"]
        assert r["route"]["total_distance"] == pytest.approx(2 + 3 + 3 + 2)   # Depot-A-B-A-Depot
        assert r["route"]["legs"][0]["path"] == ["Depot", "A", "B"]

    def test_duplicate_destinations_one_stop(self):
        r = run([parcel("PKG-0001", "B"), parcel("PKG-0002", "B"), parcel("PKG-0003", "B")])
        assert r["destinations"] == ["B"] and len(r["selected"]) == 3
        assert r["route"]["deliveries"][0]["parcels"] == ["PKG-0001", "PKG-0002", "PKG-0003"]

    def test_parcel_heavier_than_capacity(self):
        r = run([parcel("PKG-0001", "B", weight=500), parcel("PKG-0002", "A", weight=5)])
        assert [p["id"] for p in r["selected"]] == ["PKG-0002"]
        assert r["rejected"][0]["reason"] == "heavier than vehicle capacity"

    def test_zero_capacity_selects_nothing(self):
        r = run([parcel()], capacity=0)
        assert r["status"] == "nothing_selected" and r["selected"] == [] and r["route"]["order"] == []
        assert r["utilisation"] == 0.0

    def test_all_parcels_too_heavy(self):
        r = run([parcel(weight=99)], capacity=10)
        assert r["status"] == "nothing_selected" and r["warnings"]

    def test_equal_priority_and_deadline_use_id_tiebreak(self):
        ps = [parcel("PKG-0002"), parcel("PKG-0001"), parcel("PKG-0003")]
        assert [p["id"] for p in run(ps)["sorted_parcels"]] == ["PKG-0001", "PKG-0002", "PKG-0003"]

    def test_disconnected_graph_is_reported_not_routed(self):
        gd = graph_data(("Depot", "A", "Island"), (("Depot", "A", 2),))
        r = run([parcel("PKG-0001", "A"), parcel("PKG-0002", "Island")], gd)
        assert r["status"] == "partial_route"
        assert r["unreachable"] == ["Island"] and r["route"]["order"] == ["A"]
        assert any("Island" in w for w in r["warnings"])

    def test_invalid_destination_flagged(self):
        r = run([parcel(dest="Atlantis")])
        assert r["unreachable"] == ["Atlantis"] and r["route"]["legs"] == []

    def test_unknown_depot_raises(self):
        with pytest.raises(ValueError):
            run([parcel()], depot="Nowhere")

    def test_parcel_at_depot_needs_no_travel(self):
        r = run([parcel(dest="Depot")])
        assert r["route"]["legs"] == [] and r["route"]["total_distance"] == 0
        assert r["route"]["deliveries"][0]["destination"] == "Depot"

    def test_delivered_and_cancelled_excluded(self):
        r = run([parcel("PKG-0001"), parcel("PKG-0002", status="delivered"), parcel("PKG-0003", status="cancelled")])
        assert len(r["sorted_parcels"]) == 1

    def test_selection_respects_capacity_and_maximises_value(self):
        ps = [parcel("PKG-0001", "A", weight=10, priority=1, value=100),    # eff 100
              parcel("PKG-0002", "B", weight=10, priority=5, value=100),    # eff 500
              parcel("PKG-0003", "C", weight=10, priority=3, value=100)]    # eff 300
        r = run(ps, capacity=20)
        assert sorted(p["id"] for p in r["selected"]) == ["PKG-0002", "PKG-0003"]
        assert r["total_value"] == 800 and r["used_weight"] == 20 and r["remaining_capacity"] == 0
        assert r["utilisation"] == 100.0

    def test_late_estimation(self):
        r = run([parcel(deadline="2026-12-01T09:01")])           # impossible deadline
        assert r["route"]["late"] == 1 and any("deadline" in w for w in r["warnings"])

    def test_result_is_json_serialisable_and_timed(self):
        r = run(datasets.generate_parcels(30, ["A", "B", "C"], 1))
        json.dumps(r)
        assert set(r["timings_ms"]) >= {"validation", "sorting", "knapsack", "selection", "graph", "routing", "total"}

    def test_large_dataset(self):
        gd = datasets.generate_graph_data(60, 1)
        parcels = datasets.generate_parcels(2000, [l["name"] for l in gd["locations"][1:]], 1)
        r = pipeline.run_pipeline(parcels, gd, {**SETTINGS, "capacity": 300}, include_table=True)
        assert r["used_weight"] <= 300 and r["dp"]["table"] is None and r["dp"]["table_note"]


class TestModels:
    def test_valid_parcel_normalises_deadline(self):
        p = Parcel(id="X1", destination="A", weight="12", priority=2, deadline="2026-12-03", value=100.0)
        assert p.weight == 12 and p.deadline == "2026-12-03T00:00" and p.status == "pending"

    @pytest.mark.parametrize("field,value", [("weight", 0), ("weight", -3), ("weight", 2.5), ("weight", "abc"),
                                             ("priority", 0), ("priority", 6), ("value", -1),
                                             ("deadline", "tomorrow"), ("destination", ""), ("status", "lost")])
    def test_invalid_fields_rejected(self, field, value):
        data = {"id": "X1", "destination": "A", "weight": 1, "priority": 1, "deadline": "2026-12-03", "value": 1}
        data[field] = value
        with pytest.raises(ValidationError):
            Parcel(**data)

    def test_missing_fields(self):
        with pytest.raises(ValidationError) as e:
            ParcelDraft.model_validate({"destination": "A"})
        assert {x["loc"][0] for x in e.value.errors()} == {"weight", "priority", "deadline", "value"}


class TestStore:
    def make(self, tmp_path):
        return Store(tmp_path / "state.json")

    def test_seeded_and_persistent(self, tmp_path):
        s = self.make(tmp_path)
        assert len(s.parcels()) == 24
        s.delete_parcel("PKG-0001")
        assert len(Store(tmp_path / "state.json").parcels()) == 23

    def test_corrupt_file_recovers(self, tmp_path):
        (tmp_path / "state.json").write_text("{not json")
        assert len(self.make(tmp_path).parcels()) == 24

    def test_add_generates_id_and_rejects_duplicates_and_bad_destination(self, tmp_path):
        s = self.make(tmp_path)
        draft = ParcelDraft(destination="Cyber Hub", weight=3, priority=2, deadline="2026-12-02", value=50)
        assert s.add_parcel(draft)["id"] == "PKG-0025"
        with pytest.raises(ApiError) as dup:
            s.add_parcel(draft.model_copy(update={"id": "PKG-0025"}))
        assert dup.value.status == 409
        with pytest.raises(ApiError) as bad:
            s.add_parcel(draft.model_copy(update={"destination": "Atlantis"}))
        assert bad.value.status == 422

    def test_update_and_missing(self, tmp_path):
        s = self.make(tmp_path)
        p = Parcel(id="ignored", destination="Cyber Hub", weight=9, priority=5, deadline="2026-12-02", value=70)
        assert s.update_parcel("PKG-0002", p)["id"] == "PKG-0002"
        with pytest.raises(ApiError):
            s.update_parcel("PKG-9999", p)

    def test_depot_cannot_be_removed(self, tmp_path):
        with pytest.raises(ApiError) as e:
            self.make(tmp_path).remove_location("Depot")
        assert e.value.status == 409

    def test_negative_road_rejected(self, tmp_path):
        from app.models import Road
        s = self.make(tmp_path)
        with pytest.raises(Exception):
            s.add_road(Road(a="Depot", b="Cyber Hub", weight=-4))

    def test_remove_location_removes_roads(self, tmp_path):
        s = self.make(tmp_path)
        s.remove_location("Manesar")
        assert all("Manesar" not in (r["a"], r["b"]) for r in s.graph_data()["roads"])


class TestImportExport:
    LOCS = {"A", "B"}

    def test_json_import_with_errors_per_row(self):
        content = json.dumps({"parcels": [
            {"id": "P1", "destination": "A", "weight": 3, "priority": 2, "deadline": "2026-12-02", "value": 10},
            {"id": "P2", "destination": "A", "priority": 2, "deadline": "2026-12-02", "value": 10},   # missing weight
            {"id": "P1", "destination": "B", "weight": 1, "priority": 1, "deadline": "2026-12-02", "value": 1},  # dup
            {"destination": "Z", "weight": 1, "priority": 1, "deadline": "2026-12-02", "value": 1},   # bad dest
            {"destination": "B", "weight": 1, "priority": 1, "deadline": "2026-12-02", "value": 1},   # auto id
        ]})
        valid, errors = exports.parse_import("json", content, [], self.LOCS, replace=False)
        assert [p["id"] for p in valid] == ["P1", "PKG-0001"]
        assert {(e["row"], e["field"]) for e in errors} == {(2, "weight"), (3, "id"), (4, "destination")}

    def test_csv_import_and_missing_column(self):
        good = "id,destination,weight,priority,deadline,value\nP1,A,4,3,2026-12-02,200\n"
        valid, errors = exports.parse_import("csv", good, [], self.LOCS, True)
        assert len(valid) == 1 and not errors
        with pytest.raises(ApiError) as e:
            exports.parse_import("csv", "id,destination\nP1,A\n", [], self.LOCS, True)
        assert "weight" in e.value.message

    @pytest.mark.parametrize("fmt,content", [("json", ""), ("json", "{oops"), ("json", '{"a": 1}'), ("csv", "   ")])
    def test_bad_files_raise_clean_errors(self, fmt, content):
        with pytest.raises(ApiError):
            exports.parse_import(fmt, content, [], self.LOCS, False)

    def test_append_detects_existing_ids(self):
        existing = [parcel("PKG-0001", "A")]
        content = json.dumps([{"id": "PKG-0001", "destination": "A", "weight": 1, "priority": 1,
                               "deadline": "2026-12-02", "value": 1}])
        valid, errors = exports.parse_import("json", content, existing, self.LOCS, replace=False)
        assert not valid and errors[0]["field"] == "id"

    def test_csv_exports_roundtrip(self):
        ps = [parcel("PKG-0001", "A"), parcel("PKG-0002", "B")]
        text = exports.parcels_csv(ps)
        rows = list(csv.DictReader(io.StringIO(text)))
        assert [r["id"] for r in rows] == ["PKG-0001", "PKG-0002"]
        valid, errors = exports.parse_import("csv", text, [], {"A", "B"}, True)
        assert valid == ps and not errors

    def test_result_exports(self):
        r = run([parcel("PKG-0001", "B"), parcel("PKG-0002", "C", weight=500)])
        assert "PKG-0002,rejected" in exports.packing_plan_csv(r)
        assert "Depot > A > B" in exports.route_csv(r)
        assert "total_route_distance_km" in exports.summary_csv(r)


class TestBenchmark:
    def test_datasets_reproducible(self):
        a = datasets.generate_parcels(50, ["A", "B", "C"], 42)
        assert a == datasets.generate_parcels(50, ["A", "B", "C"], 42)
        assert a != datasets.generate_parcels(50, ["A", "B", "C"], 43)

    def test_generated_graph_connected(self):
        from app.algorithms.graph import dijkstra
        from app.services.store import build_graph
        gd = datasets.generate_graph_data(80, 9)
        assert len(dijkstra(build_graph(gd), "Depot").dist) == 80

    def test_run_benchmark_structure_and_csv(self):
        b = benchmark.run_benchmark([10, 50], repeats=2, seed=1)
        assert [r["n"] for r in b["rows"]] == [10, 50]
        for row in b["rows"]:
            for stage in benchmark.STAGES:
                s = row[stage]
                assert s["repeats"] == 2 and s["min_ms"] <= s["median_ms"] and s["peak_kb"] >= 0
        assert exports.benchmark_csv(b).splitlines()[0].startswith("parcels,locations")
        assert len(exports.benchmark_csv(b).splitlines()) == 3


class TestReport:
    def test_pdf_generated(self):
        r = run([parcel("PKG-0001", "B"), parcel("PKG-0002", "C")])
        bench = benchmark.run_benchmark([10], repeats=1)
        pdf = report.build_report(r, graph_data(), bench)
        assert pdf[:5] == b"%PDF-" and len(pdf) > 5000
        assert report.build_report(run([]), graph_data(), None)[:5] == b"%PDF-"
