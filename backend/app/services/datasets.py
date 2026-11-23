"""Reproducible dataset generation (fixed seeds) and the built-in sample city."""

from __future__ import annotations

import math
import random
from datetime import datetime, timedelta

BASE_DATE = datetime(2026, 12, 1, 9, 0)

# Hand-made sample road network (coordinates on a 0-100 canvas, distances in km).
SAMPLE_LOCATIONS = [
    ("Depot", 50, 52), ("Sohna Road", 52, 74), ("Sector 56", 70, 62), ("Golf Course Road", 80, 40),
    ("Cyber Hub", 62, 30), ("Udyog Vihar", 40, 24), ("MG Road", 74, 18), ("DLF Phase 3", 52, 8),
    ("Old Gurgaon", 24, 34), ("Palam Vihar", 14, 58), ("Sushant Lok", 30, 72), ("Badshahpur", 34, 90),
    ("Manesar", 14, 86),
]
SAMPLE_ROADS = [
    ("Depot", "Sohna Road", 4.2), ("Depot", "Sector 56", 5.1), ("Depot", "Cyber Hub", 4.6),
    ("Depot", "Old Gurgaon", 6.3), ("Depot", "Sushant Lok", 5.4), ("Sohna Road", "Sector 56", 4.9),
    ("Sohna Road", "Badshahpur", 5.2), ("Sector 56", "Golf Course Road", 3.8),
    ("Golf Course Road", "Cyber Hub", 4.4), ("Golf Course Road", "MG Road", 5.6),
    ("Cyber Hub", "Udyog Vihar", 4.7), ("Cyber Hub", "MG Road", 3.6), ("MG Road", "DLF Phase 3", 4.8),
    ("Udyog Vihar", "DLF Phase 3", 4.3), ("Udyog Vihar", "Old Gurgaon", 4.1),
    ("Old Gurgaon", "Palam Vihar", 5.3), ("Palam Vihar", "Sushant Lok", 4.5),
    ("Sushant Lok", "Badshahpur", 4.4), ("Palam Vihar", "Manesar", 6.0), ("Badshahpur", "Manesar", 5.5),
]


def sample_graph_data() -> dict:
    return {
        "locations": [{"name": n, "x": x, "y": y} for n, x, y in SAMPLE_LOCATIONS],
        "roads": [{"a": a, "b": b, "weight": w, "bidirectional": True} for a, b, w in SAMPLE_ROADS],
    }


def generate_graph_data(num_locations: int, seed: int) -> dict:
    """Connected random geometric road network; node 0 is named ``Depot``."""
    rng = random.Random(seed)
    num_locations = max(2, num_locations)
    pts = [(round(rng.uniform(2, 98), 1), round(rng.uniform(2, 98), 1)) for _ in range(num_locations)]
    names = ["Depot"] + [f"L{i:03d}" for i in range(1, num_locations)]
    dist = lambda i, j: max(0.5, round(math.dist(pts[i], pts[j]) * 0.5, 1))
    roads: dict[tuple[int, int], float] = {}
    for i in range(1, num_locations):          # spanning tree: guarantees connectivity
        j = min(range(i), key=lambda k: math.dist(pts[i], pts[k]))
        roads[(j, i)] = dist(j, i)
    for i in range(num_locations):             # extra local roads
        near = sorted((k for k in range(num_locations) if k != i), key=lambda k: math.dist(pts[i], pts[k]))[:2]
        for k in near:
            roads[(min(i, k), max(i, k))] = dist(i, k)
    return {
        "locations": [{"name": names[i], "x": pts[i][0], "y": pts[i][1]} for i in range(num_locations)],
        "roads": [{"a": names[a], "b": names[b], "weight": w, "bidirectional": True}
                  for (a, b), w in sorted(roads.items())],
    }


def generate_parcels(n: int, destinations: list[str], seed: int) -> list[dict]:
    """``n`` valid parcels with deterministic content for a given seed."""
    if not destinations:
        return []
    rng = random.Random(seed)
    out = []
    for i in range(1, n + 1):
        out.append({
            "id": f"PKG-{i:04d}",
            "destination": rng.choice(destinations),
            "weight": rng.randint(1, 30),
            "priority": rng.choices([1, 2, 3, 4, 5], weights=[15, 25, 30, 20, 10])[0],
            "deadline": (BASE_DATE + timedelta(hours=rng.randint(2, 72))).strftime("%Y-%m-%dT%H:%M"),
            "value": rng.randint(5, 80) * 10,
            "status": "pending",
        })
    return out
