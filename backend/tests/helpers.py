"""Shared test helpers."""
from app.algorithms.graph import Graph


def make_graph(nodes, roads, bidirectional=True):
    g = Graph()
    for n in nodes:
        g.add_node(n)
    for a, b, w in roads:
        g.add_edge(a, b, w, bidirectional)
    return g


def parcel(pid="PKG-0001", dest="B", weight=5, priority=3, deadline="2026-12-02T10:00", value=100, status="pending"):
    return {"id": pid, "destination": dest, "weight": weight, "priority": priority,
            "deadline": deadline, "value": value, "status": status}


def graph_data(nodes=("Depot", "A", "B", "C"), roads=(("Depot", "A", 2), ("A", "B", 3), ("Depot", "C", 7))):
    return {"locations": [{"name": n, "x": 10 * i, "y": 10 * i} for i, n in enumerate(nodes)],
            "roads": [{"a": a, "b": b, "weight": w, "bidirectional": True} for a, b, w in roads]}


SETTINGS = {"capacity": 20, "depot": "Depot", "dispatch_time": "2026-12-01T09:00",
            "speed_kmph": 30.0, "service_minutes": 5}
