"""Regenerate the reproducible sample datasets in sample_data/ (fixed seeds)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.services import datasets, exports  # noqa: E402

out = ROOT / "sample_data"
out.mkdir(exist_ok=True)
graph = datasets.sample_graph_data()
dests = [l["name"] for l in graph["locations"] if l["name"] != "Depot"]
for n in (10, 24, 50, 100):
    parcels = datasets.generate_parcels(n, dests, 2026)
    (out / f"parcels_{n}.csv").write_text(exports.parcels_csv(parcels), encoding="utf-8", newline="")
    (out / f"parcels_{n}.json").write_text(json.dumps(parcels, indent=2), encoding="utf-8")
(out / "road_network.json").write_text(json.dumps(graph, indent=2), encoding="utf-8")
(out / "invalid_examples.csv").write_text(
    "id,destination,weight,priority,deadline,value,status\n"
    "BAD-1,Atlantis,5,3,2026-12-02T10:00,100,pending\n"
    "BAD-2,Old Gurgaon,-4,3,2026-12-02T10:00,100,pending\n"
    "BAD-3,Old Gurgaon,5,9,2026-12-02T10:00,100,pending\n"
    "BAD-4,Old Gurgaon,5,3,not-a-date,100,pending\n"
    "BAD-5,Old Gurgaon,5,3,2026-12-02T10:00,,pending\n", encoding="utf-8")
print("sample_data written:", sorted(p.name for p in out.iterdir()))
