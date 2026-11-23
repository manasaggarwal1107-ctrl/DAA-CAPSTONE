"""Correctness tests for merge sort, knapsack DP, heap/Dijkstra and Nearest Neighbour."""

import heapq
import itertools
import math
import random

import pytest

from app.algorithms.errors import AlgorithmError, NegativeWeightError, ResourceLimitError, UnknownNodeError
from app.algorithms.graph import Graph, MinHeap, dijkstra, shortest_path
from app.algorithms.knapsack import MAX_DP_CELLS, knapsack_01
from app.algorithms.sorting import SORTERS, get_sorter, merge_sort
from app.algorithms.tsp import nearest_neighbour_route
from app.services.pipeline import parcel_priority_key

from helpers import make_graph, parcel


# ------------------------------------------------------------------ sorting
class TestMergeSort:
    def test_empty_and_single(self):
        assert merge_sort([]) == []
        assert merge_sort([7]) == [7]

    def test_matches_reference_on_random_data(self):
        rng = random.Random(1)
        for n in (2, 3, 10, 57, 300):
            data = [rng.randint(-50, 50) for _ in range(n)]
            assert merge_sort(data) == sorted(data)      # sorted() used only as test oracle

    def test_input_not_mutated(self):
        data = [3, 1, 2]
        merge_sort(data)
        assert data == [3, 1, 2]

    def test_stable(self):
        items = [(1, "a"), (0, "b"), (1, "c"), (0, "d")]
        assert merge_sort(items, key=lambda t: t[0]) == [(0, "b"), (0, "d"), (1, "a"), (1, "c")]

    def test_trace_and_stats(self):
        trace, stats = [], {}
        assert merge_sort([5, 2, 4, 1], trace=trace, stats=stats) == [1, 2, 4, 5]
        assert {e["type"] for e in trace} == {"split", "merge"}
        assert stats["comparisons"] > 0

    def test_registry(self):
        assert get_sorter("merge") is SORTERS["merge"]
        with pytest.raises(ValueError):
            get_sorter("bogosort")

    def test_parcel_ordering_rules(self):
        ps = [parcel("PKG-0003", priority=2, deadline="2026-12-01T10:00"),
              parcel("PKG-0002", priority=5, deadline="2026-12-03T10:00"),
              parcel("PKG-0005", priority=5, deadline="2026-12-02T10:00"),   # same priority, earlier deadline
              parcel("PKG-0001", priority=2, deadline="2026-12-01T10:00"),   # equal priority+deadline -> id
              ]
        out = [p["id"] for p in merge_sort(ps, key=parcel_priority_key)]
        assert out == ["PKG-0005", "PKG-0002", "PKG-0001", "PKG-0003"]


# ----------------------------------------------------------------- knapsack
def brute_force(weights, values, cap):
    best = 0
    for mask in range(1 << len(weights)):
        w = sum(weights[i] for i in range(len(weights)) if mask >> i & 1)
        if w <= cap:
            best = max(best, sum(values[i] for i in range(len(weights)) if mask >> i & 1))
    return best


class TestKnapsack:
    def test_matches_brute_force(self):
        rng = random.Random(7)
        for _ in range(150):
            n = rng.randint(0, 9)
            wts = [rng.randint(1, 12) for _ in range(n)]
            vals = [rng.randint(0, 60) for _ in range(n)]
            cap = rng.randint(0, 30)
            res = knapsack_01(wts, vals, cap)
            assert res.best_value == brute_force(wts, vals, cap)
            # reconstruction is consistent with the reported optimum
            assert sum(vals[i] for i in res.selected) == res.best_value
            assert sum(wts[i] for i in res.selected) == res.total_weight <= cap
            assert len(set(res.selected)) == len(res.selected)         # each item at most once

    def test_classic_example(self):
        res = knapsack_01([1, 3, 4, 5], [1, 4, 5, 7], 7)
        assert res.best_value == 9 and res.selected == [1, 2]

    def test_zero_capacity_and_empty(self):
        assert knapsack_01([1, 2], [5, 6], 0).selected == []
        res = knapsack_01([], [], 10)
        assert res.best_value == 0 and res.selected == []

    def test_item_heavier_than_capacity(self):
        res = knapsack_01([50, 2], [999, 3], 10)
        assert res.selected == [1] and res.best_value == 3

    def test_single_item_not_reused(self):
        # Ascending capacity order (unbounded knapsack bug) would give 30 here.
        assert knapsack_01([2], [10], 6).best_value == 10

    def test_table_shape_and_final_cell(self):
        res = knapsack_01([2, 3], [3, 4], 5, record_table=True)
        assert len(res.table) == 3 and len(res.table[0]) == 6
        assert res.table[-1][-1] == res.best_value == 7

    def test_table_skipped_when_large(self):
        res = knapsack_01([1] * 200, [1] * 200, 200, record_table=True)
        assert res.table is None and "hidden" in res.table_note

    def test_resource_limit(self):
        with pytest.raises(ResourceLimitError):
            knapsack_01([1] * 1000, [1] * 1000, MAX_DP_CELLS)

    def test_invalid_input(self):
        with pytest.raises(AlgorithmError):
            knapsack_01([1], [1, 2], 5)
        with pytest.raises(AlgorithmError):
            knapsack_01([1], [1], -1)


# ------------------------------------------------------------ heap / graph
class TestHeap:
    def test_matches_heapq(self):
        rng = random.Random(3)
        h, ref = MinHeap(), []
        for i in range(500):
            v = rng.random()
            h.push(v, i)
            heapq.heappush(ref, v)
        assert [h.pop()[0] for _ in range(500)] == [heapq.heappop(ref) for _ in range(500)]

    def test_empty_pop(self):
        with pytest.raises(IndexError):
            MinHeap().pop()


def bellman_ford(nodes, arcs, src):
    dist = {n: math.inf for n in nodes}
    dist[src] = 0
    for _ in nodes:
        for a, b, w in arcs:
            if dist[a] + w < dist[b]:
                dist[b] = dist[a] + w
    return dist


class TestDijkstra:
    def test_matches_bellman_ford_on_random_graphs(self):
        rng = random.Random(11)
        for trial in range(40):
            n = rng.randint(2, 14)
            nodes = [f"N{i}" for i in range(n)]
            g, arcs = Graph(), []
            for x in nodes:
                g.add_node(x)
            for _ in range(rng.randint(0, 3 * n)):
                a, b = rng.sample(nodes, 2)
                w = rng.randint(0, 20)
                both = rng.random() < 0.5
                g.add_edge(a, b, w, both)
                arcs.append((a, b, w))
                if both:
                    arcs.append((b, a, w))
            # reconcile duplicate overwrites: rebuild arcs from the graph itself
            arcs = [(a, d, w) for a in g.nodes() for d, w in g.neighbours(a)]
            res = dijkstra(g, "N0")
            ref = bellman_ford(nodes, arcs, "N0")
            for node in nodes:
                if math.isinf(ref[node]):
                    assert node not in res.dist
                else:
                    assert res.dist[node] == pytest.approx(ref[node])

    def test_path_reconstruction(self):
        g = make_graph("ABCD", [("A", "B", 1), ("B", "C", 1), ("A", "C", 5), ("C", "D", 1)])
        assert shortest_path(g, "A", "D") == (["A", "B", "C", "D"], 3.0)

    def test_same_source_and_target(self):
        g = make_graph("AB", [("A", "B", 1)])
        assert shortest_path(g, "A", "A") == (["A"], 0.0)

    def test_disconnected(self):
        g = make_graph("ABC", [("A", "B", 1)])
        assert shortest_path(g, "A", "C") == (None, None)

    def test_negative_weight_rejected(self):
        g = make_graph("AB", [])
        with pytest.raises(NegativeWeightError):
            g.add_edge("A", "B", -1)

    @pytest.mark.parametrize("bad", [float("nan"), float("inf"), "5", None])
    def test_non_finite_weight_rejected(self, bad):
        g = make_graph("AB", [])
        with pytest.raises(AlgorithmError):
            g.add_edge("A", "B", bad)

    def test_unknown_nodes(self):
        g = make_graph("AB", [("A", "B", 1)])
        with pytest.raises(UnknownNodeError):
            dijkstra(g, "Z")
        with pytest.raises(UnknownNodeError):
            dijkstra(g, "A", target="Z")
        with pytest.raises(UnknownNodeError):
            g.add_edge("A", "Z", 1)

    def test_self_loop_rejected(self):
        with pytest.raises(AlgorithmError):
            make_graph("A", []).add_edge("A", "A", 1)

    def test_directed_edges(self):
        g = make_graph("AB", [("A", "B", 2)], bidirectional=False)
        assert shortest_path(g, "A", "B")[1] == 2
        assert shortest_path(g, "B", "A") == (None, None)

    def test_remove_edge_and_node(self):
        g = make_graph("ABC", [("A", "B", 1), ("B", "C", 1)])
        g.remove_edge("A", "B")
        assert shortest_path(g, "A", "C") == (None, None)
        with pytest.raises(AlgorithmError):
            g.remove_edge("A", "B")
        g.remove_node("C")
        assert not g.has_node("C") and g.neighbours("B") == []

    def test_edges_listing(self):
        g = make_graph("ABC", [("A", "B", 1)])
        g.add_edge("B", "C", 2, bidirectional=False)
        edges = {(e["a"], e["b"], e["bidirectional"]) for e in g.edges()}
        assert edges == {("A", "B", True), ("B", "C", False)}

    def test_trace_has_steps(self):
        g = make_graph("AB", [("A", "B", 4)])
        res = dijkstra(g, "A", trace=True)
        assert res.steps[0]["visit"] == "A" and res.steps[0]["relaxed"][0]["to"] == "B"


# ---------------------------------------------------------------------- TSP
class TestNearestNeighbour:
    def setup_method(self):
        # Depot - A(1) - B(2 from A) ; Depot - C(10)
        self.g = make_graph(["Depot", "A", "B", "C"], [("Depot", "A", 1), ("A", "B", 2), ("Depot", "C", 10)])

    def test_visits_nearest_first_and_returns(self):
        r = nearest_neighbour_route(self.g, "Depot", ["C", "B", "A"])
        assert r.visit_order == ["A", "B", "C"]
        assert r.total_distance == pytest.approx(1 + 2 + 13 + 10)
        assert r.returned_to_depot and r.return_leg.destination == "Depot"

    def test_each_stop_once_and_no_extra_stops(self):
        r = nearest_neighbour_route(self.g, "Depot", ["B", "B", "B"])
        assert r.visit_order == ["B"]               # duplicates collapse; A is only passed through

    def test_depot_in_stops_ignored(self):
        assert nearest_neighbour_route(self.g, "Depot", ["Depot"]).legs == []

    def test_no_stops(self):
        r = nearest_neighbour_route(self.g, "Depot", [])
        assert r.legs == [] and r.total_distance == 0 and not r.returned_to_depot

    def test_unreachable_reported_not_silent(self):
        g = make_graph(["Depot", "A", "Z"], [("Depot", "A", 1)])
        r = nearest_neighbour_route(g, "Depot", ["A", "Z"])
        assert r.visit_order == ["A"] and r.unreachable == ["Z"]

    def test_unknown_stop_reported(self):
        r = nearest_neighbour_route(self.g, "Depot", ["A", "Nowhere"])
        assert r.unreachable == ["Nowhere"]

    def test_unknown_depot(self):
        with pytest.raises(UnknownNodeError):
            nearest_neighbour_route(self.g, "X", ["A"])

    def test_no_return_path_on_one_way_roads(self):
        g = make_graph(["Depot", "A"], [("Depot", "A", 3)], bidirectional=False)
        r = nearest_neighbour_route(g, "Depot", ["A"])
        assert r.returned_to_depot is False and r.total_distance == 3

    def test_nn_is_an_approximation_never_better_than_optimal(self):
        """Brute-force the optimal tour on random graphs: NN >= optimal, and sometimes strictly worse."""
        rng = random.Random(5)
        strictly_worse = 0
        for _ in range(60):
            nodes = ["D"] + [f"S{i}" for i in range(5)]
            g = Graph()
            for n in nodes:
                g.add_node(n)
            for a, b in itertools.combinations(nodes, 2):
                g.add_edge(a, b, rng.randint(1, 30))
            stops = nodes[1:]
            nn = nearest_neighbour_route(g, "D", stops).total_distance
            dist = {n: dijkstra(g, n).dist for n in nodes}
            best = min(dist["D"][p[0]] + sum(dist[a][b] for a, b in zip(p, p[1:])) + dist[p[-1]]["D"]
                       for p in itertools.permutations(stops))
            assert nn >= best - 1e-9
            strictly_worse += nn > best + 1e-9
        assert strictly_worse > 0
