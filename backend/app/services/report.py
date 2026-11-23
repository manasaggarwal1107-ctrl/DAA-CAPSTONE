"""PDF optimisation report (ReportLab) with matplotlib figures."""

from __future__ import annotations

import io
from datetime import datetime
from typing import Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # noqa: E402
from reportlab.lib.units import mm  # noqa: E402
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,  # noqa: E402
                                Spacer, Table, TableStyle)

from ..config import APP_NAME, APP_VERSION

NAVY = colors.HexColor("#0B1B33")
BLUE = colors.HexColor("#2563EB")
CYAN = "#0891B2"
GRID = colors.HexColor("#CBD5E1")
ZEBRA = colors.HexColor("#F1F5F9")


def _styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("t", parent=base["Title"], textColor=NAVY, fontSize=22, leading=26, alignment=0),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], textColor=NAVY, fontSize=13, spaceBefore=12, spaceAfter=6),
        "body": ParagraphStyle("b", parent=base["BodyText"], fontSize=9, leading=13),
        "small": ParagraphStyle("s", parent=base["BodyText"], fontSize=7.5, leading=10, textColor=colors.HexColor("#475569")),
        "cell": ParagraphStyle("c", parent=base["BodyText"], fontSize=7.5, leading=9),
    }


def _table(data: list[list], widths: list[float], header: bool = True) -> Table:
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [("FONTSIZE", (0, 0), (-1, -1), 7.5), ("GRID", (0, 0), (-1, -1), 0.3, GRID),
             ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 3),
             ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                  ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                  ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ZEBRA])]
    t.setStyle(TableStyle(style))
    return t


def _fig_to_image(fig, width_mm: float) -> Image:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=170, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    w, h = fig.get_size_inches()
    img = Image(buf)
    ratio = img.imageHeight / img.imageWidth
    img.drawWidth, img.drawHeight = width_mm * mm, width_mm * mm * ratio
    return img


def _route_figure(result: dict, graph_data: dict):
    pos = {l["name"]: (l["x"], l["y"]) for l in graph_data["locations"]}
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    for r in graph_data["roads"]:
        if r["a"] in pos and r["b"] in pos:
            ax.plot([pos[r["a"]][0], pos[r["b"]][0]], [pos[r["a"]][1], pos[r["b"]][1]], color="#CBD5E1", lw=1, zorder=1)
    legs = list(result["route"]["legs"]) + ([result["route"]["return_leg"]] if result["route"]["return_leg"] else [])
    for leg in legs:
        for a, b in zip(leg["path"], leg["path"][1:]):
            ax.annotate("", xy=pos[b], xytext=pos[a], zorder=3,
                        arrowprops=dict(arrowstyle="->", color=CYAN, lw=2, shrinkA=6, shrinkB=6))
    stops = set(result["route"]["order"])
    for name, (x, y) in pos.items():
        is_depot = name == result["depot"]
        ax.scatter([x], [y], s=150 if is_depot else 90, zorder=4,
                   color="#2563EB" if is_depot else ("#0891B2" if name in stops else "#94A3B8"))
        ax.annotate(name, (x, y), textcoords="offset points", xytext=(0, 9), ha="center", fontsize=6.5, color="#0B1B33")
    for i, name in enumerate(result["route"]["order"], start=1):
        ax.annotate(str(i), pos[name], ha="center", va="center", fontsize=6, color="white", zorder=5, weight="bold")
    ax.set_xlim(-4, 104); ax.set_ylim(104, -4); ax.axis("off")
    ax.set_title("Nearest Neighbour delivery route (depot = blue, numbered stops in visit order)", fontsize=8)
    return fig


def _benchmark_figure(bench: dict):
    rows = bench["rows"]
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    for stage, colour in (("sorting", "#2563EB"), ("knapsack", "#0891B2"), ("dijkstra", "#7C3AED"), ("routing", "#D97706")):
        ax.plot([r["n"] for r in rows], [r[stage]["median_ms"] for r in rows], marker="o", label=stage, color=colour)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("parcels (n)"); ax.set_ylabel("median runtime (ms)")
    ax.set_title("Measured runtimes (log-log)", fontsize=9)
    ax.grid(True, alpha=.3); ax.legend(fontsize=7)
    return fig


def build_report(result: dict, graph_data: dict, bench: Optional[dict]) -> bytes:
    s = _styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm, topMargin=16 * mm,
                            bottomMargin=16 * mm, title=f"{APP_NAME} - Optimisation Report", author=APP_NAME)
    story: list = []
    r, rt = result, result["route"]

    def footer(canvas, d):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#64748B"))
        canvas.drawString(16 * mm, 9 * mm, f"{APP_NAME} v{APP_VERSION} - DAA (ETCCDA302), K.R. Mangalam University")
        canvas.drawRightString(A4[0] - 16 * mm, 9 * mm, f"Page {d.page}")
        canvas.restoreState()

    story += [Paragraph("Delivery Optimisation Report", s["title"]),
              Paragraph(f"{APP_NAME} &middot; generated {datetime.now():%Y-%m-%d %H:%M} &middot; "
                        f"optimisation run {r['ran_at']}", s["small"]), Spacer(1, 8)]

    kpi = [["Metric", "Value"],
           ["Status", r["status"].replace("_", " ")], ["Depot", r["depot"]],
           ["Vehicle capacity", f"{r['capacity']} kg"],
           ["Selected / rejected (capacity) / undeliverable",
            f"{len(r['selected'])} / {len(r['rejected'])} / {len(r.get('undeliverable', []))}"],
           ["Load", f"{r['used_weight']} kg ({r['utilisation']}% utilised, {r['remaining_capacity']} kg free)"],
           ["Priority-weighted value", f"{r['total_value']:,}"],
           ["Delivery stops", str(len(r["destinations"]))],
           ["Total route distance", f"{rt['total_distance']} km" + ("" if rt["returned_to_depot"] else " (no return leg)")],
           ["Estimated late parcels", str(rt["late"])],
           ["Pipeline time", f"{r['timings_ms']['total']} ms"]]
    story += [Paragraph("1. Summary", s["h2"]), _table(kpi, [60 * mm, 114 * mm])]
    if r["warnings"]:
        story += [Spacer(1, 6)] + [Paragraph(f"Warning: {w}", s["body"]) for w in r["warnings"]]

    plan = [["Parcel", "Destination", "kg", "Pri", "Value", "Weighted", "Deadline"]]
    plan += [[p["id"], p["destination"], p["weight"], p["priority"], p["value"], p["value"] * p["priority"], p["deadline"]]
             for p in r["selected"]]
    story += [Paragraph("2. Packing plan - selected parcels (0/1 Knapsack DP)", s["h2"]),
              _table(plan, [24 * mm, 46 * mm, 12 * mm, 10 * mm, 18 * mm, 22 * mm, 42 * mm])]
    if r["rejected"]:
        rej = [["Parcel", "Destination", "kg", "Pri", "Reason"]]
        rej += [[p["id"], p["destination"], p["weight"], p["priority"], Paragraph(p["reason"], s["cell"])] for p in r["rejected"]]
        story += [Paragraph("Rejected parcels", s["h2"]), _table(rej, [24 * mm, 46 * mm, 12 * mm, 10 * mm, 82 * mm])]

    if r.get("undeliverable"):
        und = [["Parcel", "Destination", "kg", "Pri", "Reason"]]
        und += [[p["id"], p["destination"], p["weight"], p["priority"], Paragraph(p["reason"], s["cell"])] for p in r["undeliverable"]]
        story += [Paragraph("Undeliverable parcels (excluded before the knapsack: no load, no value, no route)", s["h2"]),
                  _table(und, [24 * mm, 46 * mm, 12 * mm, 10 * mm, 82 * mm])]

    story += [PageBreak(), Paragraph("3. Delivery route (Dijkstra + Nearest Neighbour)", s["h2"])]
    if rt["legs"]:
        story.append(_fig_to_image(_route_figure(r, graph_data), 170))
    legs = [["#", "From", "To", "km", "Cumulative km", "Road path"]]
    all_legs = list(rt["legs"]) + ([rt["return_leg"]] if rt["return_leg"] else [])
    legs += [[i, l["from"], l["to"], l["distance"], l["cumulative"], Paragraph(" &gt; ".join(l["path"]), s["cell"])]
             for i, l in enumerate(all_legs, start=1)]
    if len(legs) > 1:
        story += [Spacer(1, 6), _table(legs, [8 * mm, 32 * mm, 32 * mm, 14 * mm, 24 * mm, 64 * mm])]
    story.append(Paragraph("Nearest Neighbour is a greedy approximation of the Travelling Salesman Problem. "
                           "It does not guarantee the globally shortest tour.", s["small"]))
    if r["unreachable"]:
        story.append(Paragraph(f"Unreachable destinations (their parcels are undeliverable and were not loaded): {', '.join(r['unreachable'])}", s["body"]))

    t = r["timings_ms"]
    story += [Paragraph("4. Measured execution time of this run", s["h2"]),
              _table([["Stage", "Time (ms)"]] + [[k, v] for k, v in t.items()], [60 * mm, 40 * mm]),
              Paragraph(f"Merge sort performed {r['sort_comparisons']:,} comparisons; the knapsack evaluated "
                        f"{r['dp']['cells']:,} decision cells.", s["small"])]

    if bench:
        rows = [["n", "Sort ms", "Knapsack ms", "Dijkstra ms", "Route ms", "DP cells", "Peak KB (knap.)"]]
        rows += [[b["n"], b["sorting"]["median_ms"], b["knapsack"]["median_ms"], b["dijkstra"]["median_ms"],
                  b["routing"]["median_ms"], f"{b['dp_cells']:,}", b["knapsack"]["peak_kb"]] for b in bench["rows"]]
        story += [PageBreak(), Paragraph("5. Benchmark results (measured medians)", s["h2"]),
                  Paragraph(f"Measured {bench['generated_at']} on Python {bench['environment']['python']}, "
                            f"seed {bench['parameters']['seed']}, {bench['parameters']['repeats']} repeats "
                            f"(max 3 for n &gt; 500). Theoretical complexity is not a measurement.", s["small"]),
                  Spacer(1, 4), _table(rows, [14 * mm, 24 * mm, 28 * mm, 28 * mm, 26 * mm, 28 * mm, 26 * mm]),
                  Spacer(1, 6), _fig_to_image(_benchmark_figure(bench), 165)]
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()
