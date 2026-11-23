"""Thread-safe JSON persistence for parcels, the road network and settings."""

from __future__ import annotations

import copy
import json
import os
import re
import threading
from pathlib import Path
from typing import Any, Optional

from ..algorithms.graph import Graph
from ..config import DEFAULT_SETTINGS
from ..errors import ApiError
from ..models import Location, Parcel, ParcelDraft, Road
from . import datasets


def build_graph(graph_data: dict) -> Graph:
    """Construct the adjacency-list graph from stored locations/roads."""
    g = Graph()
    for loc in graph_data["locations"]:
        g.add_node(loc["name"])
    for r in graph_data["roads"]:
        g.add_edge(r["a"], r["b"], r["weight"], r.get("bidirectional", True))
    return g


class Store:
    """Holds the whole application state in ``state.json`` (atomic writes)."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.lock = threading.RLock()
        self.state: dict[str, Any] = {}
        self.load()

    # ---- persistence ----------------------------------------------------
    def _default_state(self) -> dict:
        graph = datasets.sample_graph_data()
        dests = [l["name"] for l in graph["locations"] if l["name"] != "Depot"]
        return {"parcels": datasets.generate_parcels(24, dests, 2026), "graph": graph,
                "settings": dict(DEFAULT_SETTINGS), "last_result": None, "last_benchmark": None}

    def load(self) -> None:
        with self.lock:
            try:
                self.state = json.loads(self.path.read_text(encoding="utf-8"))
                for key, default in self._default_state().items():
                    self.state.setdefault(key, default)
            except (OSError, ValueError):
                self.state = self._default_state()
                self.save()

    def save(self) -> None:
        with self.lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.state, indent=2), encoding="utf-8")
            os.replace(tmp, self.path)

    def reset_to_sample(self) -> None:
        with self.lock:
            self.state = self._default_state()
            self.save()

    # ---- parcels --------------------------------------------------------
    def parcels(self) -> list[dict]:
        with self.lock:
            return copy.deepcopy(self.state["parcels"])

    def location_names(self) -> set[str]:
        return {l["name"] for l in self.state["graph"]["locations"]}

    def _check_destination(self, destination: str) -> None:
        if destination not in self.location_names():
            raise ApiError(422, "unknown_destination",
                           f"Destination '{destination}' is not a location in the road network. "
                           f"Add it on the Network page first.", [{"field": "destination",
                           "message": f"'{destination}' is not a known location"}])

    def _next_id(self) -> str:
        nums = [int(m.group(1)) for p in self.state["parcels"] if (m := re.fullmatch(r"PKG-(\d+)", p["id"]))]
        return f"PKG-{(max(nums) + 1 if nums else 1):04d}"

    def add_parcel(self, draft: ParcelDraft) -> dict:
        with self.lock:
            data = draft.model_dump()
            data["id"] = data["id"] or self._next_id()
            if any(p["id"] == data["id"] for p in self.state["parcels"]):
                raise ApiError(409, "duplicate_id", f"Parcel ID '{data['id']}' already exists",
                               [{"field": "id", "message": "This ID is already in use"}])
            self._check_destination(data["destination"])
            self.state["parcels"].append(data)
            self.save()
            return data

    def update_parcel(self, parcel_id: str, parcel: Parcel) -> dict:
        with self.lock:
            idx = self._index(parcel_id)
            data = parcel.model_dump()
            data["id"] = parcel_id                       # IDs are immutable
            self._check_destination(data["destination"])
            self.state["parcels"][idx] = data
            self.save()
            return data

    def delete_parcel(self, parcel_id: str) -> None:
        with self.lock:
            del self.state["parcels"][self._index(parcel_id)]
            self.save()

    def _index(self, parcel_id: str) -> int:
        for i, p in enumerate(self.state["parcels"]):
            if p["id"] == parcel_id:
                return i
        raise ApiError(404, "parcel_not_found", f"Parcel '{parcel_id}' does not exist")

    def replace_parcels(self, parcels: list[dict]) -> None:
        with self.lock:
            self.state["parcels"] = parcels
            self.save()

    # ---- graph ----------------------------------------------------------
    def graph_data(self) -> dict:
        with self.lock:
            return copy.deepcopy(self.state["graph"])

    def graph(self) -> Graph:
        with self.lock:
            return build_graph(self.state["graph"])

    def add_location(self, loc: Location) -> None:
        with self.lock:
            if loc.name in self.location_names():
                raise ApiError(409, "duplicate_location", f"Location '{loc.name}' already exists")
            self.state["graph"]["locations"].append(loc.model_dump())
            self.save()

    def remove_location(self, name: str) -> int:
        """Remove a location and its roads; returns how many parcels now point nowhere."""
        with self.lock:
            if name not in self.location_names():
                raise ApiError(404, "unknown_location", f"Unknown location '{name}'")
            if name == self.state["settings"]["depot"]:
                raise ApiError(409, "depot_protected", "The depot cannot be removed. Choose another depot first.")
            g = self.state["graph"]
            g["locations"] = [l for l in g["locations"] if l["name"] != name]
            g["roads"] = [r for r in g["roads"] if name not in (r["a"], r["b"])]
            self.save()
            return sum(1 for p in self.state["parcels"] if p["destination"] == name)

    def add_road(self, road: Road) -> None:
        with self.lock:
            trial = self.graph()
            trial.add_edge(road.a, road.b, road.weight, road.bidirectional)   # validates everything
            roads = [r for r in self.state["graph"]["roads"]
                     if {r["a"], r["b"]} != {road.a, road.b}]
            roads.append(road.model_dump())
            self.state["graph"]["roads"] = roads
            self.save()

    def remove_road(self, a: str, b: str) -> None:
        with self.lock:
            before = self.state["graph"]["roads"]
            after = [r for r in before if {r["a"], r["b"]} != {a, b}]
            if len(after) == len(before):
                raise ApiError(404, "road_not_found", f"No road between '{a}' and '{b}'")
            self.state["graph"]["roads"] = after
            self.save()

    # ---- settings / cached results -------------------------------------
    def settings(self) -> dict:
        with self.lock:
            return dict(self.state["settings"])

    def update_settings(self, patch: dict) -> dict:
        with self.lock:
            if patch.get("depot") is not None and patch["depot"] not in self.location_names():
                raise ApiError(422, "unknown_location", f"Depot '{patch['depot']}' is not in the road network")
            self.state["settings"].update({k: v for k, v in patch.items() if v is not None})
            self.save()
            return dict(self.state["settings"])

    def set_result(self, key: str, value: Optional[dict]) -> None:
        with self.lock:
            self.state[key] = value
            self.save()

    def get_result(self, key: str) -> Optional[dict]:
        with self.lock:
            value = copy.deepcopy(self.state.get(key))
        # A result saved by an older version lacks the "undeliverable"/"counts" fields; treat it as absent
        # so the UI asks for a fresh optimisation instead of rendering an inconsistent plan.
        if key == "last_result" and isinstance(value, dict) and "counts" not in value:
            return None
        return value
