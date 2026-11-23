"""Regression tests: reachability is computed BEFORE selection, so undeliverable parcels never consume
capacity, never count as selected and never appear in totals, exports or the PDF.

Graph used (Depot-A-B chain plus the disconnected Island/Isle pair):

    Depot --2-- A --3-- B          Island --1-- Isle        (Island/Isle cannot be reached from Depot)
"""
import csv
import io

import pytest

from app.algorithms.tsp import nearest_neighbour_route
from app.services import exports, pipeline, report
from helpers import SETTINGS, graph_data, make_graph, parcel

NODES = ("Depot", "A", "B", "Island", "Isle")
ROADS = (("Depot", "A", 2), ("A", "B", 3), ("Island", "Isle", 1))


def run(parcels, *, roads=ROADS, nodes=NODES, bidirectional=True, **kw):
    gd = graph_data(nodes, roads)
    for r in gd["roads"]:
        r["bidirectional"] = bidirectional
    return pipeline.run_pipeline(parcels, gd, {**SETTINGS}, **kw), gd


def ids(plist):
    return [p["id"] for p in plist]


def assert_consistent(r):
    """Every total describes exactly the selected parcels, and those are exactly the routed parcels."""
    selected_weight = sum(p["weight"] for p in r["selected"])
    delivered_weight = sum(d["weight"] for d in r["route"]["deliveries"])
    assert r["used_weight"] == selected_weight == delivered_weight
    assert r["remaining_capacity"] == r["capacity"] - selected_weight
    assert r["total_value"] == sum(p["value"] * p["priority"] for p in r["selected"])
    assert r["total_value"] == sum(d["value"] for d in r["route"]["deliveries"])
    delivered_ids = sorted(i for d in r["route"]["deliveries"] for i in d["parcels"])
    assert delivered_ids == sorted(ids(r["selected"]))
    assert not set(ids(r["selected"])) & set(ids(r["undeliverable"]))
    assert not set(ids(r["rejected"])) & set(ids(r["undeliverable"]))
    assert r["counts"]["selected"] == len(r["selected"])
    assert r["counts"]["undeliverable"] == len(r["undeliverable"])


class TestUnreachableDestinations:
    def test_unreachable_parcel_is_never_selected_and_uses_no_capacity(self):
        # The unreachable parcel is the most valuable and would win the knapsack if it were considered.
        big = parcel("PKG-0001", "Island", weight=15, priority=5, value=9000)
        ok = parcel("PKG-0002", "B", weight=15, priority=1, value=10)
        r, _ = run([big, ok])           # capacity 20: only one 15 kg parcel fits
        assert ids(r["selected"]) == ["PKG-0002"]          # old behaviour selected PKG-0001 and routed nothing
        assert ids(r["undeliverable"]) == ["PKG-0001"]
        assert r["undeliverable"][0]["category"] == pipeline.UNREACHABLE_DESTINATION
        assert r["used_weight"] == 15 and r["total_value"] == 10
        assert r["status"] == "partial_route"
        assert r["unreachable"] == ["Island"]
        assert_consistent(r)

    def test_multiple_parcels_at_one_unreachable_destination(self):
        ps = [parcel("PKG-0001", "Island", weight=2), parcel("PKG-0002", "Island", weight=3),
              parcel("PKG-0003", "Island", weight=4), parcel("PKG-0004", "A", weight=5)]
        r, _ = run(ps)
        assert ids(r["undeliverable"]) == ["PKG-0001", "PKG-0002", "PKG-0003"]
        assert ids(r["selected"]) == ["PKG-0004"] and r["used_weight"] == 5
        assert r["unreachable"] == ["Island"]
        assert any("Island" in w and "3 parcel(s)" in w for w in r["warnings"])
        assert_consistent(r)

    def test_all_destinations_unreachable(self):
        r, _ = run([parcel("PKG-0001", "Island"), parcel("PKG-0002", "Isle")])
        assert r["status"] == "nothing_deliverable"
        assert r["selected"] == [] and r["rejected"] == [] and len(r["undeliverable"]) == 2
        assert r["used_weight"] == 0 and r["total_value"] == 0 and r["utilisation"] == 0.0
        assert r["route"]["legs"] == [] and r["route"]["order"] == [] and r["route"]["total_distance"] == 0
        assert r["dp"]["order"] == []                         # nothing was fed to the DP
        assert_consistent(r)

    def test_mixed_reachable_and_unreachable(self):
        ps = [parcel("PKG-0001", "A", weight=4), parcel("PKG-0002", "Island", weight=4),
              parcel("PKG-0003", "B", weight=4), parcel("PKG-0004", "Nowhere", weight=4)]
        r, _ = run(ps)
        assert sorted(ids(r["selected"])) == ["PKG-0001", "PKG-0003"]
        cats = {p["id"]: p["category"] for p in r["undeliverable"]}
        assert cats == {"PKG-0002": pipeline.UNREACHABLE_DESTINATION, "PKG-0004": pipeline.UNKNOWN_DESTINATION}
        assert r["route"]["order"] == ["A", "B"]
        assert r["unreachable"] == ["Island", "Nowhere"]
        assert r["dp"]["order"] == ["PKG-0001", "PKG-0003"]    # DP saw deliverable parcels only
        assert r["counts"]["pending"] == 4 and r["counts"]["deliverable"] == 2
        assert_consistent(r)

    def test_sorted_list_still_contains_every_pending_parcel(self):
        r, _ = run([parcel("PKG-0001", "Island"), parcel("PKG-0002", "A")])
        assert ids(r["sorted_parcels"]) == ["PKG-0001", "PKG-0002"]

    def test_depot_destination_is_deliverable(self):
        r, _ = run([parcel("PKG-0001", "Depot", weight=3)])
        assert ids(r["selected"]) == ["PKG-0001"] and r["undeliverable"] == []
        assert_consistent(r)

    def test_one_way_road_reachable_from_depot_but_not_from_previous_stop(self):
        # Depot->A->B and Depot->C are one-way: from A (or B) the stop C cannot be reached.
        nodes, roads = ("Depot", "A", "C"), (("Depot", "A", 1), ("Depot", "C", 5))
        ps = [parcel("PKG-0001", "A", weight=5), parcel("PKG-0002", "C", weight=5)]
        r, _ = run(ps, nodes=nodes, roads=roads, bidirectional=False)
        # Nearest Neighbour goes A first and then cannot reach C: C's parcel must be reported undeliverable,
        # not left inside the selected weight/value.
        assert ids(r["selected"]) == ["PKG-0001"]
        assert r["undeliverable"][0]["category"] == pipeline.TOUR_UNREACHABLE
        assert r["counts"]["replans"] == 1 and r["used_weight"] == 5
        assert_consistent(r)

    def test_reachability_is_decided_before_knapsack_timings_present(self):
        r, _ = run([parcel("PKG-0001", "Island")])
        assert "reachability" in r["timings_ms"] and r["timings_ms"]["knapsack"] >= 0


class TestExportsAndReportAgree:
    @pytest.fixture()
    def result(self):
        ps = [parcel("PKG-0001", "A", weight=4), parcel("PKG-0002", "Island", weight=4),
              parcel("PKG-0003", "B", weight=30)]
        return run(ps)

    def test_packing_plan_csv_lists_all_three_decisions(self, result):
        r, _ = result
        rows = list(csv.DictReader(io.StringIO(exports.packing_plan_csv(r))))
        by_decision = {d: [x["parcel_id"] for x in rows if x["decision"] == d] for d in ("selected", "rejected", "undeliverable")}
        assert by_decision == {"selected": ["PKG-0001"], "rejected": ["PKG-0003"], "undeliverable": ["PKG-0002"]}
        assert "road path" in [x for x in rows if x["decision"] == "undeliverable"][0]["reason"]

    def test_summary_csv_matches_result(self, result):
        r, _ = result
        s = dict(csv.reader(io.StringIO(exports.summary_csv(r))))
        assert s["selected_parcels"] == "1" and s["rejected_parcels"] == "1" and s["undeliverable_parcels"] == "1"
        assert s["used_weight_kg"] == str(r["used_weight"]) == "4"

    def test_route_csv_never_visits_unreachable_destination(self, result):
        r, _ = result
        assert "Island" not in exports.route_csv(r)

    def test_pdf_builds_with_undeliverable_parcels(self, result):
        r, gd = result
        pdf = report.build_report(r, gd, None)
        assert pdf.startswith(b"%PDF") and len(pdf) > 2000

    def test_pdf_builds_when_everything_is_undeliverable(self):
        r, gd = run([parcel("PKG-0001", "Island")])
        assert report.build_report(r, gd, None).startswith(b"%PDF")


class TestNearestNeighbourDeterminism:
    def make(self):
        #  Depot is 5 from each of B, C, D (equal); A is 5 from Depot as well.
        return make_graph(["Depot", "A", "B", "C", "D"],
                          [("Depot", "A", 5), ("Depot", "B", 5), ("Depot", "C", 5), ("Depot", "D", 5)])

    def test_equal_distances_choose_smallest_name(self):
        r = nearest_neighbour_route(self.make(), "Depot", ["D", "B", "C", "A"])
        assert r.visit_order[0] == "A"

    def test_result_independent_of_stop_input_order(self):
        g = self.make()
        orders = [["A", "B", "C", "D"], ["D", "C", "B", "A"], ["C", "A", "D", "B"], ["B", "D", "A", "C"]]
        results = [nearest_neighbour_route(g, "Depot", o).visit_order for o in orders]
        assert all(v == results[0] for v in results)
        assert results[0] == ["A", "B", "C", "D"]

    def test_trace_is_preserved_and_matches_selection(self):
        g = self.make()
        r = nearest_neighbour_route(g, "Depot", ["C", "A", "B"], trace=True)
        assert len(r.steps) == 3
        first = r.steps[0]
        assert first["from"] == "Depot" and first["chosen"] == "A"
        assert [c["stop"] for c in first["candidates"]] == ["A", "B", "C"]      # display order: distance, name
        assert [s["chosen"] for s in r.steps] == r.visit_order
        assert nearest_neighbour_route(g, "Depot", ["C", "A", "B"]).visit_order == r.visit_order  # trace is optional

    def test_trace_lists_unreachable_stops(self):
        g = make_graph(["Depot", "A", "Z"], [("Depot", "A", 1)])
        r = nearest_neighbour_route(g, "Depot", ["A", "Z"], trace=True)
        assert r.steps[0]["unreachable"] == ["Z"] and r.steps[0]["chosen"] == "A"
