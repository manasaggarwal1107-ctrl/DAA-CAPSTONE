"""CSV/JSON export builders and the validating JSON/CSV parcel importer."""

from __future__ import annotations

import csv
import io
import json
import re
from typing import Optional

from pydantic import ValidationError

from ..errors import ApiError, friendly_validation_errors
from ..models import ParcelDraft

PARCEL_FIELDS = ["id", "destination", "weight", "priority", "deadline", "value", "status"]


def _csv(header: list[str], rows: list[list]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    w.writerows(rows)
    return buf.getvalue()


def parcels_csv(parcels: list[dict]) -> str:
    return _csv(PARCEL_FIELDS, [[p[f] for f in PARCEL_FIELDS] for p in parcels])


def parcels_json(parcels: list[dict]) -> str:
    return json.dumps({"parcels": parcels}, indent=2)


def packing_plan_csv(result: dict) -> str:
    rows = [[p["id"], "selected", p["destination"], p["weight"], p["priority"], p["value"],
             p["value"] * p["priority"], p["deadline"], ""] for p in result["selected"]]
    rows += [[p["id"], "rejected", p["destination"], p["weight"], p["priority"], p["value"],
              p["value"] * p["priority"], p["deadline"], p["reason"]] for p in result["rejected"]]
    rows += [[p["id"], "undeliverable", p["destination"], p["weight"], p["priority"], p["value"],
              p["value"] * p["priority"], p["deadline"], p["reason"]] for p in result.get("undeliverable", [])]
    return _csv(["parcel_id", "decision", "destination", "weight_kg", "priority", "value",
                 "priority_weighted_value", "deadline", "reason"], rows)


def route_csv(result: dict) -> str:
    route = result["route"]
    rows = [[i, l["from"], l["to"], l["distance"], l["cumulative"], " > ".join(l["path"])]
            for i, l in enumerate(route["legs"], start=1)]
    if route["return_leg"]:
        l = route["return_leg"]
        rows.append([len(rows) + 1, l["from"], l["to"], l["distance"], l["cumulative"], " > ".join(l["path"])])
    return _csv(["leg", "from", "to", "distance_km", "cumulative_km", "road_path"], rows)


def benchmark_csv(bench: dict) -> str:
    rows = []
    for r in bench["rows"]:
        row = [r["n"], r["locations"], r["roads"], r["capacity"], r["selected"], r["stops"], r["dp_cells"]]
        for stage in ("sorting", "knapsack", "dijkstra", "routing"):
            s = r[stage]
            row += [s["median_ms"], s["min_ms"], s["mean_ms"], s["repeats"], s["peak_kb"]]
        rows.append(row)
    header = ["parcels", "locations", "roads", "capacity_kg", "selected", "stops", "dp_cells"]
    for stage in ("sorting", "knapsack", "dijkstra", "routing"):
        header += [f"{stage}_median_ms", f"{stage}_min_ms", f"{stage}_mean_ms", f"{stage}_repeats", f"{stage}_peak_kb"]
    return _csv(header, rows)


def summary_csv(result: dict) -> str:
    r, rt = result, result["route"]
    rows = [["status", r["status"]], ["ran_at", r["ran_at"]], ["depot", r["depot"]],
            ["vehicle_capacity_kg", r["capacity"]], ["selected_parcels", len(r["selected"])],
            ["rejected_parcels", len(r["rejected"])],
            ["undeliverable_parcels", len(r.get("undeliverable", []))], ["used_weight_kg", r["used_weight"]],
            ["remaining_capacity_kg", r["remaining_capacity"]], ["utilisation_percent", r["utilisation"]],
            ["priority_weighted_value", r["total_value"]], ["delivery_stops", len(r["destinations"])],
            ["unreachable_destinations_excluded_from_selection", ";".join(r["unreachable"])],
            ["total_route_distance_km", rt["total_distance"]], ["returned_to_depot", rt["returned_to_depot"]],
            ["estimated_late_parcels", rt["late"]]]
    rows += [[f"time_{k}_ms", v] for k, v in r["timings_ms"].items()]
    return _csv(["metric", "value"], rows)


def parse_import(fmt: str, content: str, existing: list[dict], locations: set[str],
                 replace: bool) -> tuple[list[dict], list[dict]]:
    """Validate an import payload row by row.

    Returns ``(valid_parcels, errors)``; invalid rows never abort the import of
    valid ones, and each error names the row and field.
    """
    if not content.strip():
        raise ApiError(422, "empty_import", "The import file is empty")
    if fmt == "json":
        try:
            data = json.loads(content)
        except ValueError as exc:
            raise ApiError(422, "invalid_json", f"Not valid JSON: {exc}") from None
        rows = data.get("parcels") if isinstance(data, dict) else data
        if not isinstance(rows, list):
            raise ApiError(422, "invalid_json", "Expected a JSON array of parcels, or an object with a 'parcels' array")
    else:
        reader = csv.DictReader(io.StringIO(content.lstrip("﻿")))
        headers = [(h or "").strip().lower() for h in (reader.fieldnames or [])]
        missing = [f for f in ("destination", "weight", "priority", "deadline", "value") if f not in headers]
        if missing:
            raise ApiError(422, "invalid_csv", f"CSV is missing required column(s): {', '.join(missing)}")
        rows = [{(k or "").strip().lower(): (v if v != "" else None) for k, v in row.items()} for row in reader]

    taken = set() if replace else {p["id"] for p in existing}
    nums = [int(m.group(1)) for p in ([] if replace else existing) if (m := re.fullmatch(r"PKG-(\d+)", p["id"]))]
    counter = max(nums) if nums else 0
    valid: list[dict] = []
    errors: list[dict] = []
    for idx, raw in enumerate(rows, start=1):
        if not isinstance(raw, dict):
            errors.append({"row": idx, "field": "-", "message": "Row is not an object"})
            continue
        try:
            p = ParcelDraft.model_validate(raw).model_dump()
        except ValidationError as exc:
            errors += [{"row": idx, **e} for e in friendly_validation_errors(exc)]
            continue
        if p["destination"] not in locations:
            errors.append({"row": idx, "field": "destination",
                           "message": f"'{p['destination']}' is not a location in the road network"})
            continue
        if not p["id"]:                       # generated only for rows that are otherwise valid
            counter += 1
            p["id"] = f"PKG-{counter:04d}"
            while p["id"] in taken:
                counter += 1
                p["id"] = f"PKG-{counter:04d}"
        if p["id"] in taken:
            errors.append({"row": idx, "field": "id", "message": f"Duplicate parcel ID '{p['id']}'"})
            continue
        taken.add(p["id"])
        valid.append(p)
    return valid, errors
