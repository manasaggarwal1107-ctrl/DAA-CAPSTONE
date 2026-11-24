#!/usr/bin/env python3
"""Build Mini_Courier_Planner_Project_Screenshot_Portfolio.pdf

Run from the folder that contains `assets/` and `lib.py`:
    python3 build_portfolio.py
All benchmark/sample-data tables are generated directly from the supplied files.
Screenshot-derived values are transcribed from the screenshots and noted as such.
"""
import csv, json, os
from reportlab.lib.units import mm
from reportlab.platypus import (Spacer, PageBreak, NextPageTemplate, CondPageBreak,
                                Flowable, KeepTogether)
from lib import *

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, "assets")
SS = os.path.join(A, "screenshots")
BM = os.path.join(A, "benchmarks")
SD = os.path.join(A, "sample_data")
OUT = os.path.join(HERE, "out", "Mini_Courier_Planner_Project_Screenshot_Portfolio.pdf")

# ------------------------------------------------------------------ data
rows_csv = list(csv.DictReader(open(os.path.join(BM, "results.csv"))))
bj = json.load(open(os.path.join(BM, "results.json")))
for r, c in zip(bj["rows"], rows_csv):          # JSON must equal CSV
    for a in ("sorting", "knapsack", "dijkstra", "routing"):
        for k in ("median_ms", "min_ms", "mean_ms", "peak_kb", "repeats"):
            assert float(r[a][k]) == float(c[f"{a}_{k}"]), (r["n"], a, k)

def pcsv(name):
    return list(csv.DictReader(open(os.path.join(SD, name))))

def fmt_int(n):
    return f"{int(n):,}"

# figure numbers (single source of truth for cross-references)
F = dict(diagram=1, dash=2, parcels=3, sort=4, knap=5, net=6, route=7,
         l_merge=8, l_knap=9, l_dij=10, l_nn=11, rt=12, mem=13, bench=14,
         u_knap=15, u_route=16, reports=17, mobile=18)
def fr(k):  # figure reference text
    return f"Figure {F[k]}"

# ------------------------------------------------------------------ diagram
class DiagramBlock(Flowable):
    """Figure 1 \u2013 explanatory pipeline diagram (vector, no measurements)."""
    H = 78 * mm
    def __init__(self):
        super().__init__()
        self._lof = (0, f"Figure {F['diagram']}  \u2013  How the four algorithms are connected")
        self.cap = Paragraph(
            "Drawn for this document to explain the data flow; it is <b>not</b> a screenshot. "
            "Example values in the small grey captions are taken from the sample run in "
            f"{fr('dash')}, {fr('knap')} and {fr('route')}. The hand-off from sorting to the "
            f"knapsack is inferred from {fr('knap')}, whose dynamic-programming rows follow the "
            f"prioritised order of {fr('sort')}.", ST["cap"])

    def wrap(self, aw, ah):
        _, self.ch = self.cap.wrap(CONTENT_W, 1000)
        self.h = self.H + self.ch + 3 * mm
        return CONTENT_W, self.h

    def box(self, c, x, y, w, h, title, sub, fill, stroke, tcol=INK):
        c.setFillColor(fill); c.setStrokeColor(stroke); c.setLineWidth(0.9)
        c.roundRect(x, y, w, h, 2.2, stroke=1, fill=1)
        c.setFillColor(tcol); c.setFont("Body-B", 8.6)
        c.drawCentredString(x + w / 2, y + h - 5.2 * mm, title)
        c.setFillColor(MUTED); c.setFont("Body", 7.4)
        for i, line in enumerate(sub):
            c.drawCentredString(x + w / 2, y + h - 9.4 * mm - i * 3.3 * mm, line)

    def arrow(self, c, x1, y1, x2, y2, col=MUTED):
        import math
        c.setStrokeColor(col); c.setFillColor(col); c.setLineWidth(1)
        c.line(x1, y1, x2, y2)
        ang = math.atan2(y2 - y1, x2 - x1); L = 2.2 * mm
        p = c.beginPath()
        p.moveTo(x2, y2)
        p.lineTo(x2 - L * math.cos(ang - 0.45), y2 - L * math.sin(ang - 0.45))
        p.lineTo(x2 - L * math.cos(ang + 0.45), y2 - L * math.sin(ang + 0.45))
        p.close(); c.drawPath(p, stroke=0, fill=1)

    def draw(self):
        c = self.canv
        top = self.h
        tag = "EXPLANATORY DIAGRAM"
        c.setFont("Body-B", 6.8)
        tw = pdfmetrics.stringWidth(tag, "Body-B", 6.8) + 8
        c.setFillColor(KIND[tag]); c.roundRect(0, top - 5.6 * mm, tw, 4.4 * mm, 1.2, stroke=0, fill=1)
        c.setFillColor(colors.white); c.drawString(4, top - 4.15 * mm, tag)
        c.setFillColor(INK); c.setFont("Body-B", 10.6)
        c.drawString(tw + 8, top - 4.35 * mm, f"Figure {F['diagram']}  \u2014  How the four algorithms are connected")
        # frame
        fy = self.ch + 3 * mm
        c.setFillColor(PANEL2); c.setStrokeColor(RULE); c.setLineWidth(0.6)
        c.rect(0, fy, CONTENT_W, self.H - 8 * mm, stroke=1, fill=1)
        bw, bh, gap = 29 * mm, 19 * mm, 8.2 * mm
        x0 = 4 * mm
        ytop = fy + self.H - 8 * mm - 6 * mm - bh
        xs = [x0 + i * (bw + gap) for i in range(5)]
        W = HexColor("#FFFFFF")
        specs = [
            ("Pending parcels", ["queue of parcels", "ID \u00b7 weight \u00b7 priority", "deadline \u00b7 value"], W, RULE, INK),
            ("Merge Sort", ["priority \u2193, deadline \u2191,", "then ID", "O(n log n)"], ACCENT_L, ACCENT, INK),
            ("0/1 Knapsack (DP)", ["max weighted value", "within capacity W", "O(n\u00b7W)"], ACCENT_L, ACCENT, INK),
            ("Nearest Neighbour", ["visit nearest unvisited", "stop, return to depot", "heuristic"], ACCENT_L, ACCENT, INK),
            ("Route + ETA", ["ordered stops", "road paths, distance", "estimated arrival"], W, RULE, INK),
        ]
        for x, (t, sub, fill, stroke, tc) in zip(xs, specs):
            self.box(c, x, ytop, bw, bh, t, sub, fill, stroke, tc)
        for i in range(4):
            self.arrow(c, xs[i] + bw + 0.8 * mm, ytop + bh / 2, xs[i + 1] - 0.8 * mm, ytop + bh / 2)
        # example captions under row
        ex = ["e.g. 24 pending", "e.g. ordered queue,\nP5 first", "e.g. 7 selected,\n120 of 120 kg", "e.g. 5 stops,\n6 Dijkstra runs", "e.g. 57.8 km,\n7 parcels on time (est.)"]
        c.setFont("Body", 7); c.setFillColor(FAINT)
        for x, t in zip(xs, ex):
            for k, line in enumerate(t.split("\n")):
                c.drawCentredString(x + bw / 2, ytop - 4 * mm - k * 3 * mm, line)
        # bottom row: road network -> Dijkstra -> NN
        yb = fy + 4 * mm
        self.box(c, xs[2], yb, bw, 15 * mm, "Road network", ["13 locations", "20 roads (weighted)"], W, RULE)
        self.box(c, xs[3], yb, bw, 15 * mm, "Dijkstra", ["binary min-heap", "O((V+E) log V)"], ACCENT_L, ACCENT)
        self.arrow(c, xs[2] + bw + 0.8 * mm, yb + 7.5 * mm, xs[3] - 0.8 * mm, yb + 7.5 * mm)
        self.arrow(c, xs[3] + bw / 2, yb + 15 * mm + 0.8 * mm, xs[3] + bw / 2, ytop - 11.5 * mm)
        c.setFont("Body", 7); c.setFillColor(MUTED)
        c.drawString(xs[3] + bw / 2 + 2 * mm, yb + 17.5 * mm, "shortest road distances")
        # caption
        self.cap.drawOn(c, 0, 0)


# ------------------------------------------------------------------ helpers
story = []
def add(x):
    if isinstance(x, (list, tuple)):
        story.extend(x)
    else:
        story.append(x)

def fig(key, title, kind, img, caption, maxh, **kw):
    add(FigureBlock(F[key], title, kind, img, caption, maxh, **kw))

def sp(h=3):
    add(Spacer(1, h * mm))

def H1(num, title):
    add(PageBreak()); add(SectionHead(num, title))

def H2(text):
    add(SubHead(text, 1, "H2"))

def H3(text):
    add(Paragraph(text, ST["H3"]))

def ps(p):  # path to screenshot
    return os.path.join(SS, p)

# ================================================================== COVER
add(Spacer(1, 52 * mm))
cover = [
    Paragraph('<font color="#0E7490">DESIGN AND ANALYSIS OF ALGORITHMS  \u00b7  ETCCDA302</font>',
              S("c1", fontName="Body-B", fontSize=10.5, leading=14, leftIndent=30 * mm)),
    Spacer(1, 7 * mm),
    Paragraph("MINI COURIER<br/>PLANNER", S("c2", fontName="Body-B", fontSize=44, leading=46,
                                              leftIndent=30 * mm, textColor=INK)),
    Spacer(1, 5 * mm),
    Paragraph("Project Screenshot Portfolio", S("c3", fontSize=22, leading=26,
                                                 leftIndent=30 * mm, textColor=ACCENT)),
    Spacer(1, 8 * mm),
    Paragraph("Visual evidence of the working implementation of four algorithms: "
              "Merge Sort, 0/1 Knapsack (dynamic programming), Dijkstra\u2019s algorithm with a "
              "binary min-heap, and Nearest Neighbour routing.",
              S("c4", fontSize=11.5, leading=17, leftIndent=30 * mm, rightIndent=34 * mm,
                textColor=MUTED)),
]
for f in cover:
    add(f)
add(Spacer(1, 34 * mm))
info = [
    ["Student", "Manas Aggarwal"],
    ["Programme", "B.Tech CSE (AI/ML)"],
    ["Subject", "Design and Analysis of Algorithms (DAA)"],
    ["Course code", "ETCCDA302"],
    ["University", "K.R. Mangalam University"],
    ["Document", "Companion evidence portfolio to the technical project report"],
]
t = Table([[Paragraph(f'<font color="#64748B">{a.upper()}</font>', S("ci1", fontName="Body-B", fontSize=7.6, leading=10)),
            Paragraph(b, S("ci2", fontSize=10.6, leading=14))] for a, b in info],
          colWidths=[30 * mm, 112 * mm])
t.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 3.2),
                       ("BOTTOMPADDING", (0, 0), (-1, -1), 3.2), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                       ("LINEBELOW", (0, 0), (-1, -2), 0.4, RULE)]))
t.hAlign = "LEFT"
wrap_t = Table([[t]], colWidths=[PAGE_W])
wrap_t.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 30 * mm), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                            ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
add(wrap_t)
add(Spacer(1, 22 * mm))
add(Paragraph("Evidence basis: 15 application screenshots \u00b7 2 benchmark charts \u00b7 measured benchmark data "
              "(CSV and JSON) \u00b7 synthetic sample datasets. Nothing in this document is invented or "
              "simulated; gaps in the supplied evidence are stated where they occur.",
              S("c5", fontSize=8.8, leading=12.6, leftIndent=30 * mm, rightIndent=34 * mm, textColor=MUTED)))
add(NextPageTemplate("body"))
add(PageBreak())

# ================================================================== CONTENTS
add(Paragraph("Contents", ST["H1"]))
toc = TableOfContents()
toc.levelStyles = [ST["toc1"], ST["toc2"]]
toc.dotsMinLevel = 0
add(toc)
add(Spacer(1, 8 * mm))
add(Paragraph("List of figures", ST["H2"]))
lof = ListOfFigures()
lof.levelStyles = [ST["lof"]]
lof.dotsMinLevel = 0
add(lof)

# ================================================================== 1 OVERVIEW
H1(1, "Project Overview")
add(P("Mini Courier Planner is a browser-based delivery-planning application built as a capstone for "
      "Design and Analysis of Algorithms (DAA). Given a queue of parcels, a vehicle capacity and a weighted "
      "road network, it decides which parcels to handle first, which to load, and in what order to deliver "
      "them.", "lead"))
H2("Purpose and problem addressed")
add(P("A courier vehicle faces three connected decisions. Parcels differ in urgency, so something must decide the "
      "order of handling. The vehicle has a weight limit, so not every pending parcel can be loaded. And the loaded "
      "parcels go to different places, so the drive has to be sequenced over a road network. The project maps each "
      "decision to a classical algorithm and exposes the result, the working and the cost of every step in one "
      "interface."))
H2("Application overview")
add(P("The application has nine pages in three navigation groups, visible in the sidebar of "
      f"{fr('dash')}: <b>Operations</b> (Dashboard, Parcels), <b>Optimisation</b> (Prioritisation, Load planning, "
      "Road network, Route planner) and <b>Analysis</b> (Benchmark lab, Learning centre, Reports &amp; export). "
      "A <i>Run optimisation</i> control in the top bar of every page executes the sorting, knapsack and routing "
      "stages in sequence, and the header shows when the last run took place."))
add(table_caption(1, "The four algorithms and their roles. Complexities are those stated in the application itself."))
sp(1.5)
add(data_table([
    ["Algorithm", "Role in the application", "Complexity as stated in the application", "Evidence"],
    ["Merge Sort", "Orders pending parcels: higher priority first, then earlier deadline, then parcel ID.",
     "Time O(n log n) in best, average and worst case; O(n) auxiliary space.", f"{fr('sort')}, {fr('l_merge')}"],
    ["0/1 Knapsack (dynamic programming)", "Selects the parcels that maximise priority-weighted value (delivery value \u00d7 priority) within vehicle capacity.",
     "Time O(n\u00b7W); O(W) values plus an O(n\u00b7W)-byte decision matrix to rebuild the chosen set.", f"{fr('knap')}, {fr('l_knap')}"],
    ["Dijkstra (binary min-heap)", "Single-source shortest road distances; used for every route leg and for path queries.",
     "Time O((V+E) log V); O(V+E) space.", f"{fr('net')}, {fr('l_dij')}"],
    ["Nearest Neighbour (TSP heuristic)", "Greedy delivery order from the depot using Dijkstra road distances; returns to the depot.",
     "O(k\u00b7(V+E) log V + k<super>2</super>) for k stops; a heuristic, not guaranteed optimal.", f"{fr('route')}, {fr('l_nn')}"],
], [33 * mm, 67 * mm, 52 * mm, 26 * mm], bold_first_col=True))
sp(4)
add(DiagramBlock())

H2("Evidence conventions and source material")
add(P("This portfolio uses only material supplied with the project: 15 screenshots captured from the running "
      "application, 2 benchmark charts with the measured data behind them, and the synthetic sample datasets. Every "
      "figure carries a tag stating what kind of evidence it is."))
add(table_caption(2, "Evidence tags used throughout this document."))
sp(1.5)
add(data_table([
    ["Tag", "Meaning", "Used for"],
    ["SCREENSHOT", "Unaltered capture of the running application.", f"Figures {F['dash']}\u2013{F['l_nn']}, {F['bench']}\u2013{F['reports']}"],
    ["UI SCREENSHOT, SEGMENTED", "As above, divided into consecutive segments for legibility; no content removed.", fr("mobile")],
    ["MEASURED DATA", "Chart produced from the supplied benchmark measurements (results.csv / results.json).", f"{fr('rt')}, {fr('mem')}"],
    ["EXPLANATORY DIAGRAM", "Drawn for this document; not a screenshot and contains no measurements.", fr("diagram")],
    ["SAMPLE INPUT", "Contents of a supplied synthetic sample data file, shown as a table.", "Tables 4, 12 and 14"],
], [44 * mm, 92 * mm, 42 * mm], bold_first_col=True))
sp(3)
add(info_box("Screenshots were captured from the real running application with headless Chromium (Playwright) on Linux, "
             "1440 px wide (full page), after one optimisation and one benchmark had been run; the mobile capture is 390 px wide. "
             f"In full-page captures the sticky header can appear part-way down the page (visible in {fr('sort')} and {fr('net')}); "
             "the capture README identifies this as a screenshot artefact. Short-lived toast notifications such as "
             "\u201cOptimisation complete\u201d are also visible in some captures. Screenshots are reproduced without cropping or editing.",
             "Capture conditions"))
sp(2)
add(info_box("All parcel and road data used for the demonstrations are synthetic sample data (generated parcel IDs PKG-xxxx; "
             "benchmark datasets generated from a fixed random seed). They are not real customer or courier records; place names "
             "are used only as labels. The 24-parcel dataset (parcels_24.csv) and the 13-location, 20-road network "
             f"(road_network.json) correspond to the application state in {fr('dash')} to {fr('route')}.",
             "Synthetic data"))

# ================================================================== 2 DASHBOARD
H1(2, "Application Dashboard")
add(P("The dashboard is the landing page. It summarises the parcel queue, the latest load plan and delivery route, "
      "and the timing of each algorithm stage after an optimisation run.", "lead"))
fig("dash", "Operations dashboard after one optimisation run", "SCREENSHOT", ps("01-dashboard.png"),
    "Full-page capture at 1440 px. Left: grouped navigation. Top bar: breadcrumb, last-run time (2026-11-23 02:56:24) with an "
    "\u201cup to date\u201d badge, and the Run optimisation button. Main area: eight indicator cards and four charts. "
    "A transient \u201cOptimisation complete\u201d notification is visible at the lower right.", 140 * mm)
sp(3)
H2("Navigation and layout")
add(bullets([
    "<b>Sidebar:</b> Operations, Optimisation and Analysis groups with nine pages; the current page is highlighted.",
    "<b>Top bar:</b> breadcrumb (Operations / Dashboard), last-run timestamp with status badge, and the primary Run optimisation action.",
    "<b>Content:</b> two rows of four indicator cards followed by a 2 \u00d7 2 grid of charts; dark theme throughout.",
]))
add(table_caption(3, f"Indicators shown on the dashboard ({fr('dash')}), transcribed from the screenshot."))
sp(1.5)
add(data_table([
    ["Indicator", "Value shown", "Supporting text shown"],
    ["Total parcels", "24", "24 pending dispatch"],
    ["Pending parcels", "24", "status = pending"],
    ["Selected for load", "7", "of 24 pending \u00b7 value 18,590"],
    ["Vehicle utilisation", "100%", "120 of 120 kg"],
    ["Route distance", "57.8 km", "5 delivery stops"],
    ["Delivery locations", "13", "20 road connections"],
    ["Optimisation status", "Optimised", "Ran 2026-11-23 02:56:24"],
    ["Algorithm time", "2.18 ms", "sort 0.059 ms \u00b7 knapsack 0.199 ms \u00b7 route 0.222 ms"],
], [44 * mm, 36 * mm, 98 * mm], bold_first_col=True))
sp(3)
H2("Charts")
add(bullets([
    "<b>Parcel priority distribution:</b> number of parcels at each priority level P1\u2013P5 (5 = most urgent). Bar heights read as 5, 3, 8, 6 and 2 parcels, which total the 24 pending parcels.",
    "<b>Parcel weight distribution:</b> parcels per weight band (1\u20135 kg up to 26\u201330 kg, plus &gt;30 kg). Bars read as 1, 3, 6, 4, 4 and 6 parcels, none above 30 kg; they also total 24.",
    f"<b>Delivery performance:</b> cumulative distance at each of the five stops, headed \u201c7 on time \u00b7 0 late (estimate)\u201d. The bar heights are consistent with the cumulative distances in {fr('route')}.",
    "<b>Algorithm runtime comparison:</b> one bar each for sorting, knapsack and routing from the latest optimisation run.",
], ))
add(P("Chart values above are read from bar heights because the charts carry no data labels.", "small"))
sp(2)
add(note_box("The headline \u201cAlgorithm time 2.18 ms\u201d is reproduced as displayed. The three stage timings listed beneath it "
             "add up to less than this total, and the supplied evidence does not itemise the remainder. "
             f"Stage timings also differ between pages ({fr('sort')} and {fr('knap')} show 0.073 ms and 0.286 ms) because each page reports its own "
             "measured run."))

# ================================================================== 3 PARCELS
H1(3, "Parcel Management")
add(P("The Parcels page is where delivery parcels are listed, filtered, edited and imported. Every optimisation stage "
      "starts from this data.", "lead"))
fig("parcels", "Parcel management \u2013 listing, filters and actions", "SCREENSHOT", ps("02-parcels.png"),
    "First page of the parcel table (20 of 24 parcels; footer reads \u201c24 of 24 parcels \u00b7 Page 1 / 2\u201d), sorted by earliest deadline. "
    "The toolbar offers Datasets, Import, CSV, JSON and Add parcel; the filter row offers search by parcel ID or destination, "
    "priority, destination, status and sort order. A toast overlaps one status cell (PKG-0018).", 150 * mm)
sp(3)
H2("Parcel information and input")
add(P("The page description states that weights and values are whole numbers because the knapsack dynamic program is indexed by "
      "integer capacity. The \u201cWeighted\u201d column is value \u00d7 priority, the quantity the knapsack maximises "
      f"(for example PKG-0020: 90 \u00d7 4 = 360; PKG-0022: 670 \u00d7 5 = 3,350 in {fr('knap')})."))
add(table_caption(4, "Fields of a parcel record, shown for PKG-0005 in the screenshot."))
sp(1.5)
add(data_table([
    ["Field", "Example", "Notes"],
    ["Parcel ID", "PKG-0005", "Unique identifier; also the final tie-breaker when sorting."],
    ["Destination", "Udyog Vihar", "Must be a location on the road network (see Section 7)."],
    ["Weight (kg)", "27", "Whole number; consumes vehicle capacity."],
    ["Priority", "P1", "P1\u2013P5, where 5 is most urgent."],
    ["Deadline", "01 Dec, 12:00", "Used by the sort and for the estimated on-time check."],
    ["Value", "670", "Delivery value; whole number."],
    ["Weighted", "670", "Value \u00d7 priority (here 670 \u00d7 1)."],
    ["Status", "pending", "All 24 parcels in the capture are pending."],
], [32 * mm, 34 * mm, 112 * mm], bold_first_col=True))
sp(3)
add(table_caption(5, "Supplied synthetic sample datasets (computed from the CSV files in sample_data)."))
sp(1.5)
ds = []
for n in (10, 24, 50, 100):
    rr = pcsv(f"parcels_{n}.csv")
    ds.append([f"parcels_{n}.csv / .json", len(rr), fmt_int(sum(int(x['weight']) for x in rr)),
               len({x['destination'] for x in rr}), ", ".join(sorted({x['status'] for x in rr})),
               "Used in Figures 2\u20137" if n == 24 else "Sample dataset"])
add(data_table([["File", "Parcels", "Total weight (kg)", "Distinct destinations", "Status values", "Note"]] + ds,
               [38 * mm, 18 * mm, 30 * mm, 33 * mm, 24 * mm, 35 * mm], align_right=(1, 2, 3)))
sp(3)
r24 = pcsv("parcels_24.csv")[:4]
add(table_caption(6, "First four records of parcels_24.csv (SAMPLE INPUT, synthetic)."))
sp(1.5)
add(data_table([["id", "destination", "weight", "priority", "deadline", "value", "status"]] +
               [[x["id"], x["destination"], x["weight"], x["priority"], x["deadline"], x["value"], x["status"]] for x in r24],
               [26 * mm, 32 * mm, 18 * mm, 18 * mm, 40 * mm, 18 * mm, 26 * mm], align_right=(2, 3, 5)))
sp(3)
add(note_box("The toolbar buttons (Datasets, Import, CSV, JSON, Add parcel) and the edit and delete icons are visible, but the dialogs "
             "behind them were not part of the supplied screenshots, so parcel creation, editing and import are not shown in action."))

# ================================================================== 4 ALGORITHMS
H1(4, "Algorithm Implementation Evidence")
add(P("Each subsection pairs the interface screenshot with the numeric output it displays and a pointer to the relevant "
      "execution trace. Values in tables are transcribed from the screenshots.", "lead"))
# ---- 4.1 Merge sort
add(SubHead("4.1  Merge Sort \u2013 parcel prioritisation", 1, "H2"))
add(P("The Prioritisation page orders the pending parcels with a hand-written Merge Sort. The comparison key is "
      "(\u2212priority, deadline, ID): higher priority first, then earlier deadline, then parcel ID as a deterministic tie-breaker."))
fig("sort", "Prioritisation engine \u2013 original versus prioritised order", "SCREENSHOT", ps("03-sorting.png"),
    "Summary cards (24 pending parcels, median sort time of 5 runs 0.073 ms, 78 key comparisons, O(n log n) time, O(n) extra space); "
    "original (insertion) order beside prioritised order, ten rows each; and a step-by-step trace panel. "
    "The sticky header overlaps the first table row in this full-page capture.", 168 * mm)
sp(3)
H3("Actual sorting output")
add(table_caption(7, f"Prioritised order, ranks 1\u201310, transcribed from {fr('sort')}."))
sp(1.5)
add(data_table([
    ["Rank", "Parcel", "Priority", "Deadline", "Destination"],
    ["1", "PKG-0022", "P5", "02 Dec, 20:00", "Old Gurgaon"],
    ["2", "PKG-0024", "P5", "03 Dec, 00:00", "Palam Vihar"],
    ["3", "PKG-0020", "P4", "01 Dec, 12:00", "Cyber Hub"],
    ["4", "PKG-0021", "P4", "03 Dec, 21:00", "Golf Course Road"],
    ["5", "PKG-0013", "P4", "04 Dec, 00:00", "Palam Vihar"],
    ["6", "PKG-0003", "P4", "04 Dec, 01:00", "Palam Vihar"],
    ["7", "PKG-0012", "P4", "04 Dec, 01:00", "DLF Phase 3"],
    ["8", "PKG-0023", "P4", "04 Dec, 02:00", "Old Gurgaon"],
    ["9", "PKG-0015", "P3", "02 Dec, 00:00", "Sohna Road"],
    ["10", "PKG-0016", "P3", "02 Dec, 16:00", "Old Gurgaon"],
], [16 * mm, 32 * mm, 22 * mm, 40 * mm, 68 * mm], align_right=(0,)))
add(P(f"Rank 1 is partly covered by the sticky header in {fr('sort')}; its values are confirmed by the parcel table in {fr('parcels')}.", "small"))
sp(2)
H3("How the output demonstrates prioritisation")
add(bullets([
    "The two priority-5 parcels (PKG-0022, PKG-0024) come first; the priority-4 group follows, then priority 3.",
    "Within priority 4 the order follows the deadline, from PKG-0020 (01 Dec, 12:00) to PKG-0023 (04 Dec, 02:00).",
    "PKG-0003 and PKG-0012 share the deadline 04 Dec, 01:00 and are ordered by ID, which is the tie-breaker rule at work.",
    "The explanatory panel notes that equal keys keep their input order, so Merge Sort is stable.",
]))
H3("Execution trace")
add(P("The trace panel reads \u201cTrace of the real implementation on the first 8 parcels of the queue\u201d, with 14 steps. "
      "The capture shows step 1 of 14: the first split at depth 0 divides PKG-0001\u2013PKG-0004 from PKG-0005\u2013PKG-0008 (\u201c4 + 4 items\u201d). "
      f"A second, number-based example is in the Learning centre ({fr('l_merge')})."))
add(note_box("Only the first trace step was captured, so the merge steps themselves are not shown for the parcel data."))

# ---- 4.2 Knapsack
add(PageBreak())
add(SubHead("4.2  0/1 Knapsack (dynamic programming) \u2013 parcel selection", 1, "H2"))
add(P("The Load planning page chooses the set of parcels that maximises total priority-weighted value without exceeding "
      "the vehicle\u2019s weight capacity; each parcel is loaded at most once."))
fig("knap", "Load planning \u2013 selected and rejected parcels with the DP table", "SCREENSHOT", ps("04-knapsack.png"),
    "Capacity input (120 kg, \u201cwhat-if only until saved\u201d), result cards, selected parcels (7), rejected parcels (17; the first six rows are visible), "
    "the dynamic-programming table (2,904 cells; capacities 0\u201315 visible) and the recurrence panel.", 172 * mm)
sp(3)
H3("Actual parcel selection output")
add(table_caption(8, f"Selected parcels, transcribed from {fr('knap')}."))
sp(1.5)
add(data_table([
    ["Parcel", "Destination", "kg", "Priority", "Value", "Weighted"],
    ["PKG-0022", "Old Gurgaon", "12", "P5", "670", "3,350"],
    ["PKG-0021", "Golf Course Road", "21", "P4", "710", "2,840"],
    ["PKG-0013", "Palam Vihar", "9", "P4", "700", "2,800"],
    ["PKG-0003", "Palam Vihar", "27", "P4", "800", "3,200"],
    ["PKG-0012", "DLF Phase 3", "17", "P4", "550", "2,200"],
    ["PKG-0023", "Old Gurgaon", "17", "P4", "600", "2,400"],
    ["PKG-0019", "Badshahpur", "17", "P3", "600", "1,800"],
    ["Total (7 parcels)", "", "120", "", "", "18,590"],
], [34 * mm, 44 * mm, 18 * mm, 24 * mm, 24 * mm, 34 * mm], align_right=(2, 4, 5), total_row=True))
add(P("The totals row is the sum of the rows above and matches the result cards in the screenshot (120 kg, 18,590).", "small"))
sp(2)
H3("Capacity constraint demonstration")
add(bullets([
    "<b>Capacity binds exactly:</b> total weight 120 kg against a 120 kg capacity, remaining capacity 0 kg, \u201c100% of capacity used\u201d.",
    "<b>Selected / deliverable:</b> 7 of 24 parcels; the other 17 are listed as rejected, left for a later trip. The six visible rejected rows are PKG-0024 (22 kg), PKG-0020 (10 kg), PKG-0015 (23 kg), PKG-0016 (5 kg), PKG-0018 (18 kg) and PKG-0002 (29 kg); each shows the reason \u201clower priority-weighted value per kg than the chosen set\u201d.",
    "<b>Selection by combination:</b> PKG-0016 (5 kg, weighted value 600, 120 per kg) is rejected while PKG-0019 (17 kg, 1,800, about 106 per kg) is chosen. The dynamic program compares whole combinations, so a parcel with a better individual ratio can still be left out.",
    "<b>What-if versus saved:</b> <i>Solve</i> explores a capacity without saving it; <i>Save capacity &amp; run full optimisation</i> stores it for the other stages.",
]))
H3("Execution trace")
add(P("The dynamic-programming table is the trace. Its rows follow the prioritised order of Section 4.1 (PKG-0022, PKG-0024, PKG-0020, PKG-0021, \u2026), "
      "rows of selected parcels are marked green with a check, and the outlined cells mark the backtracking path. "
      "The table has 2,904 cells, which equals 24 parcels \u00d7 121 capacities (0\u2013120); the capture shows capacities 0\u201315 only. "
      f"A small worked example with the full table is in the Learning centre ({fr('l_knap')})."))

# ---- 4.3 Dijkstra
add(PageBreak())
add(SubHead("4.3  Dijkstra\u2019s algorithm \u2013 shortest road paths", 1, "H2"))
add(P("The Road network page stores roads as a weighted adjacency list. Dijkstra\u2019s algorithm with a binary min-heap finds the "
      "shortest path between any two locations; negative road lengths are rejected when a road is added."))
fig("net", "Road network \u2013 map, path query, locations and adjacency list", "SCREENSHOT", ps("05-network.png"),
    "Network map (13 locations, 20 roads, lengths in km) with the Depot\u2013Sohna Road path highlighted; forms for adding a location (name, X and Y 0\u2013100) "
    "and a road (from, to, length, two-way); the shortest-path panel; the location table with Make depot / Remove actions; and the adjacency list. "
    "The sticky header overlaps part of the map in this full-page capture.", 176 * mm)
sp(3)
H3("Shortest-path output")
add(P("The query in the capture is Depot to Sohna Road: total distance 4.2 km, 1 road used, path Depot \u2192 Sohna Road. "
      "The adjacency list gives the Depot\u2019s neighbours as Sohna Road (4.2), Sector 56 (5.1), Cyber Hub (4.6), Old Gurgaon (6.3) and Sushant Lok (5.4). "
      "Because this query is a single direct road, multi-road paths are evidenced by the route legs in the Route planner:"))
add(table_caption(9, f"Shortest-path outputs visible in {fr('net')} and {fr('route')}."))
sp(1.5)
add(data_table([
    ["Query", "Road path returned", "Distance (km)", "Seen in"],
    ["Depot \u2192 Sohna Road", "Depot \u2192 Sohna Road", "4.2", fr("net")],
    ["Palam Vihar \u2192 Badshahpur", "Palam Vihar \u2192 Sushant Lok \u2192 Badshahpur", "8.9", f"{fr('route')}, leg 3"],
    ["Badshahpur \u2192 Golf Course Road", "Badshahpur \u2192 Sohna Road \u2192 Sector 56 \u2192 Golf Course Road", "13.9", f"{fr('route')}, leg 4"],
    ["Golf Course Road \u2192 DLF Phase 3", "Golf Course Road \u2192 MG Road \u2192 DLF Phase 3", "10.4", f"{fr('route')}, leg 5"],
], [50 * mm, 74 * mm, 24 * mm, 30 * mm], align_right=(2,)))
add(P(f"The map edge labels in {fr('route')} are consistent with these sums, for example 4.5 + 4.4 = 8.9 km via Sushant Lok.", "small"))
sp(2)
H3("Implementation points stated in the interface")
add(bullets([
    "Binary min-heap as the priority queue; stale heap entries are skipped (lazy deletion), and the search can exit early once the target is settled.",
    "Negative road lengths are rejected, because they would break the algorithm\u2019s correctness; unreachable locations never receive a distance.",
    "Locations can be added or removed and any location can be made the depot, so the network is editable.",
]))
add(note_box(f"The Dijkstra step-through in the Learning centre ({fr('l_dij')}) was captured at step 0 of 6, so no step-by-step Dijkstra trace is shown. "
             "The path query in the capture is the simplest case (one road); longer paths appear only as route legs."))

# ---- 4.4 NN
add(PageBreak())
add(SubHead("4.4  Nearest Neighbour \u2013 delivery route planning", 1, "H2"))
add(P("Starting at the depot, the vehicle repeatedly drives to the nearest unvisited delivery location, measured by Dijkstra road distance, "
      "and returns to the depot when a road back exists."))
fig("route", "Route planner \u2013 dispatch settings, route map, legs and arrival estimates", "SCREENSHOT", ps("06-route.png"),
    "Dispatch settings (capacity 120 kg, depot, dispatch time 12/01/2026 09:00, 30 km/h, 5 minutes per stop), five result cards, the route map "
    "(cyan outbound legs, violet return, numbered stops), the \u201cApproximation, not the optimum\u201d panel, route legs and estimated arrivals.", 176 * mm)
sp(3)
H3("Route output and distance information")
add(table_caption(10, f"Route legs, transcribed from {fr('route')}."))
sp(1.5)
add(data_table([
    ["#", "From \u2192 To", "Road path", "Leg (km)", "Total (km)"],
    ["1", "Depot \u2192 Old Gurgaon", "Depot \u2192 Old Gurgaon", "6.3", "6.3"],
    ["2", "Old Gurgaon \u2192 Palam Vihar", "Old Gurgaon \u2192 Palam Vihar", "5.3", "11.6"],
    ["3", "Palam Vihar \u2192 Badshahpur", "Palam Vihar \u2192 Sushant Lok \u2192 Badshahpur", "8.9", "20.5"],
    ["4", "Badshahpur \u2192 Golf Course Road", "Badshahpur \u2192 Sohna Road \u2192 Sector 56 \u2192 Golf Course Road", "13.9", "34.4"],
    ["5", "Golf Course Road \u2192 DLF Phase 3", "Golf Course Road \u2192 MG Road \u2192 DLF Phase 3", "10.4", "44.8"],
    ["\u2013", "DLF Phase 3 \u2192 Depot (return)", "Violet path on the map", "13.0*", "57.8"],
], [8 * mm, 54 * mm, 72 * mm, 20 * mm, 24 * mm], align_right=(3, 4)))
add(P("* Derived: the headline total (57.8 km) minus the five outbound legs (44.8 km). The captured legs table lists the outbound legs only.", "small"))
sp(2)
add(table_caption(11, f"Deliveries and estimated arrival, transcribed from {fr('route')} (estimates, not measurements)."))
sp(1.5)
add(data_table([
    ["Stop", "Parcels", "Estimated arrival", "Deadline check"],
    ["1. Old Gurgaon", "PKG-0022, PKG-0023", "01 Dec, 09:17", "on time"],
    ["2. Palam Vihar", "PKG-0013, PKG-0003", "01 Dec, 09:33", "on time"],
    ["3. Badshahpur", "PKG-0019", "01 Dec, 09:56", "on time"],
    ["4. Golf Course Road", "PKG-0021", "01 Dec, 10:28", "on time"],
    ["5. DLF Phase 3", "PKG-0012", "01 Dec, 10:54", "on time"],
], [46 * mm, 52 * mm, 44 * mm, 36 * mm]))
add(P(f"The seven parcels on the route are exactly the seven selected in {fr('knap')}. The result cards read: total route distance 57.8 km, "
      "5 delivery stops, 6 Dijkstra runs, routing time 0.222 ms, estimated on time / late 7 / 0. Six runs is consistent with one run from the depot and from each "
      "subsequent stop, including the last stop for the return leg. The interface defines ETA as dispatch time + distance \u00f7 speed + stop time.", "small"))
sp(2)
H3("The heuristic and its limitations")
add(bullets([
    "Nearest Neighbour is greedy: it needs one Dijkstra run per stop, about O(k\u00b7(V+E) log V) for k stops.",
    "The Travelling Salesman Problem is NP-hard, so exact tours need exponential time as stops grow; a greedy early choice can force a long detour later, and the tour is not guaranteed to be the shortest possible (stated in the \u201cApproximation, not the optimum\u201d panel).",
    "Locations without selected parcels are not visited unless a road passes through them; stops that cannot be reached are reported, not silently skipped (Learning centre).",
    "In this run the return leg accounts for 13.0 of the 57.8 km. The supplied evidence contains no optimal tour for comparison, so the quality of this route relative to the optimum is not established.",
]))
add(note_box("The Learning centre states that the project\u2019s tests compare Nearest Neighbour with brute force and show cases where it is strictly worse. "
             "Those tests and their results were not supplied, so this portfolio reports no such comparison."))

# ================================================================== 5 LEARNING
H1(5, "Learning and Algorithm Explanation Modules")
add(P("The Learning centre contains one tab per algorithm. Each tab gives a concept summary, working principle, pseudocode, recurrence, "
      "complexity table, notes, an interactive example and viva questions. The interface states that each interactive example runs the same "
      "implementation the planner uses.", "lead"))
add(table_caption(12, "Learning-centre content and the state in which each tab was captured."))
sp(1.5)
add(data_table([
    ["Tab", "Interactive example (as captured)", "Trace state", "Viva questions"],
    ["Merge Sort", "Input 38, 27, 43, 3, 9, 82, 10 (max 16 numbers) \u2192 sorted 3, 9, 10, 27, 38, 43, 82 with 13 comparisons", "Step 0 / 12", "3"],
    ["0/1 Knapsack", "Weights 1, 3, 4, 5; values 1, 4, 5, 7; capacity 7 \u2192 best value 9 using items 2 and 3 (weight 7 of 7)", "DP table filled", "4"],
    ["Dijkstra\u2019s Shortest Path", "Six-node graph A\u2013F, source A, target F", "Step 0 / 6", "3"],
    ["Nearest Neighbour TSP", "Depot A with stops B, C, D, E, F; B, D and F selected", "Step 0 / 3", "3"],
], [34 * mm, 88 * mm, 30 * mm, 26 * mm], bold_first_col=True))
sp(2)
add(info_box("In all four tabs the pseudocode, recurrence and complexity panels are fully visible. The Merge Sort, Dijkstra and Nearest Neighbour "
             "step-through controls were captured before pressing Play, so those animations are not shown in progress. "
             "The first viva answer is expanded in each tab.", "Reading the captures"))

def learn(key, sub, title, img, cap, bullets_):
    add(PageBreak())
    add(SubHead(sub, 1, "H2"))
    fig(key, title, "SCREENSHOT", img, cap, 150 * mm)
    sp(2)
    add(bullets(bullets_))

learn("l_merge", "5.1  Merge Sort module", "Learning centre \u2013 Merge Sort tab", ps("08-learn-merge.png"),
      "Concept and four-step working principle; recurrence and complexity cards; interactive example with Trace Merge Sort; pseudocode for MERGE-SORT and MERGE; "
      "viva questions. A \u201cBenchmark finished\u201d notification overlaps part of the first viva answer.",
      ["<b>Divide and conquer:</b> split into halves, treat one-element lists as sorted, merge by repeatedly taking the smaller front element; ties take the left element, which makes the sort stable.",
       "<b>Recurrence:</b> T(n) = 2T(n/2) + \u0398(n), giving \u0398(n log n) by the Master theorem, case 2; best, average and worst case are all O(n log n) with O(n) auxiliary space.",
       "<b>Link to the planner:</b> the sort key is the tuple (\u2212priority, deadline, ID), so one comparison handles all three prioritisation rules.",
       "<b>Interactive example:</b> the entered numbers are sorted to 3, 9, 10, 27, 38, 43, 82 using 13 comparisons; Play, Next and a slider step through the 12-step trace."])
learn("l_knap", "5.2  0/1 Knapsack module", "Learning centre \u2013 0/1 Knapsack tab", ps("08-learn-knapsack.png"),
      "Concept and working principle; recurrence and complexity cards; interactive example with the filled DP table and highlighted backtracking cells; pseudocode; viva questions.",
      ["<b>Recurrence:</b> dp[i][w] = dp[i\u22121][w] if weight<sub>i</sub> &gt; w, otherwise max(dp[i\u22121][w], dp[i\u22121][w \u2212 weight<sub>i</sub>] + value<sub>i</sub>), with dp[0][w] = 0.",
       "<b>Worked example:</b> for weights 1, 3, 4, 5, values 1, 4, 5, 7 and capacity 7 the best value is 9, obtained from items 2 and 3 (weight 7 of 7); the highlighted cells trace the choice backwards.",
       "<b>Why capacities descend:</b> the one-dimensional array is updated from high to low capacity so a parcel is never counted twice, which keeps the problem 0/1 rather than unbounded.",
       "<b>Pseudo-polynomial:</b> O(n\u00b7W) depends on the numeric capacity W, which is why weights are whole kilograms; the full table is displayed only for small instances."])
learn("l_dij", "5.3  Dijkstra module", "Learning centre \u2013 Dijkstra\u2019s Shortest Path tab", ps("08-learn-dijkstra.png"),
      "Concept and working principle; recurrence and complexity cards; interactive six-node graph (source A, target F) with step controls at step 0 of 6; pseudocode; viva questions.",
      ["<b>Working principle:</b> set dist[source] = 0 and everything else to infinity, repeatedly settle the closest unsettled node, relax its edges, and rebuild the path from prev[] at the end.",
       "<b>Recurrence:</b> dist[v] = min over edges (u, v) of dist[u] + w(u, v), valid only if every w \u2265 0.",
       "<b>Complexity:</b> best case O(V+E) when the target is found early; average and worst case O((V+E) log V); space O(V+E) for the graph and O(V) for dist, prev and the heap.",
       "<b>Viva topics:</b> why negative edges are not allowed, complexity with a binary heap, and lazy deletion."])
learn("l_nn", "5.4  Nearest Neighbour module", "Learning centre \u2013 Nearest Neighbour TSP tab", ps("08-learn-nearest.png"),
      "Concept and working principle; \u201cno recurrence\u201d card and complexity table; interactive graph with selectable stops and step controls at step 0 of 3; pseudocode; viva questions.",
      ["<b>Working principle:</b> from the current location run Dijkstra, move to the nearest unvisited reachable stop, repeat, and return to the depot if a path exists.",
       "<b>Honest framing:</b> the recurrence card states there is no recurrence, only a greedy choice at each step, and that tour length is not guaranteed optimal.",
       "<b>Complexity shown:</b> O(k(V+E) log V + k<super>2</super>) in best, average and worst case; space O(V + k).",
       "<b>Future work:</b> the Notes card names the exact Held\u2013Karp alternative, O(n<super>2</super>2<super>n</super>), as proposed future work that is not implemented."])

# ================================================================== 6 BENCHMARKS
H1(6, "Benchmarking and Performance Analysis")
add(P("The measurements in this section come from the supplied benchmark files (results.csv and results.json, which were compared field by field and match) and the two charts drawn from them. "
      "The benchmark-lab screenshot in Section 6.5 is from a separate, earlier run and is kept apart.", "lead"))
H2("6.1  Benchmark design and input sizes")
p_ = bj["parameters"]; env = bj["environment"]
add(bullets([
    f"<b>Dataset sizes (parcels):</b> {', '.join(str(s) for s in p_['sizes'])}, generated from a fixed random seed ({p_['seed']}) so the same inputs are reproduced on every run.",
    f"<b>Repeats:</b> {p_['repeats']} requested; the data record 5 repeats for 10\u2013500 parcels and 3 repeats for 1,000 and 5,000 parcels. Medians are reported with minimum and mean values in the data files.",
    f"<b>Vehicle capacity rule:</b> {p_['capacity_rule']}; the cap keeps the knapsack decision matrix near 3 million cells at 5,000 parcels instead of growing without bound.",
    f"<b>Road-network size rule:</b> locations = {p_['locations_rule']}, so the graph grows with the dataset size but is capped at 150 locations.",
    f"<b>Measurement method (from the Benchmark lab page):</b> times use time.perf_counter(); peak memory is the tracemalloc peak of a separate run, and timing runs are never traced.",
    f"<b>Environment recorded in results.json:</b> Python {env['python']}, {env['platform']}, {env['processor']}; generated {bj['generated_at']}.",
]))
add(table_caption(13, "Benchmark inputs for each dataset size (from results.csv)."))
sp(1.5)
t_in = [["Parcels", "Locations", "Roads", "Capacity (kg)", "Selected", "Stops", "DP cells", "Repeats"]]
for c in rows_csv:
    t_in.append([fmt_int(c["parcels"]), c["locations"], c["roads"], c["capacity_kg"], c["selected"], c["stops"],
                 fmt_int(c["dp_cells"]), f"{c['sorting_repeats']}"])
add(data_table(t_in, [22 * mm, 22 * mm, 20 * mm, 26 * mm, 22 * mm, 18 * mm, 28 * mm, 20 * mm], align_right=tuple(range(8))))
add(P("DP cells = parcels \u00d7 (capacity + 1), for example 5,000 \u00d7 601 = 3,005,000. Theoretical complexities appear in the application separately and are not measurements.", "small"))

add(PageBreak())
H2("6.2  Runtime")
fig("rt", "Median runtime per stage (supplied chart)", "MEASURED DATA", os.path.join(BM, "runtime.png"),
    "Log\u2013log chart of median runtime in milliseconds against parcel count for Merge Sort, 0/1 Knapsack DP, Dijkstra (one source) and the Nearest Neighbour route. "
    "The chart title says repeats = 5 and seed = 42; the data files record 3 repeats for the two largest sizes.", 108 * mm)
sp(3)
add(table_caption(14, "Median runtime in milliseconds, with the minimum in parentheses (from results.csv)."))
sp(1.5)
t_rt = [["Parcels", "Merge Sort", "0/1 Knapsack DP", "Dijkstra (one source)", "Nearest Neighbour route"]]
for c in rows_csv:
    t_rt.append([fmt_int(c["parcels"])] + [f"{c[f'{a}_median_ms']} ({c[f'{a}_min_ms']})" for a in ("sorting", "knapsack", "dijkstra", "routing")])
add(data_table(t_rt, [24 * mm, 36 * mm, 38 * mm, 40 * mm, 40 * mm], align_right=tuple(range(5))))

add(PageBreak())
H2("6.3  Peak memory")
fig("mem", "Peak memory per stage (supplied chart)", "MEASURED DATA", os.path.join(BM, "memory.png"),
    "Log\u2013log chart of tracemalloc peak memory in KiB against parcel count for the same four stages. The chart title again says repeats = 5.", 108 * mm)
sp(3)
add(table_caption(15, "Peak memory in KiB (from results.csv)."))
sp(1.5)
t_mem = [["Parcels", "Merge Sort", "0/1 Knapsack DP", "Dijkstra (one source)", "Nearest Neighbour route"]]
for c in rows_csv:
    t_mem.append([fmt_int(c["parcels"])] + [f"{c[f'{a}_peak_kb']}" for a in ("sorting", "knapsack", "dijkstra", "routing")])
add(data_table(t_mem, [24 * mm, 36 * mm, 38 * mm, 40 * mm, 40 * mm], align_right=tuple(range(5))))

H2("6.4  Reading the trends")
kn = {int(c["parcels"]): c for c in rows_csv}
ns = {n: float(kn[n]["knapsack_median_ms"]) * 1e6 / float(kn[n]["dp_cells"]) for n in kn}
ratio_ms = float(kn[5000]["sorting_median_ms"]) / float(kn[10]["sorting_median_ms"])
add(bullets([
    f"<b>Knapsack tracks n \u00d7 W.</b> Its median time divided by the number of DP cells is about {ns[50]:.0f}\u2013{ns[1000]:.0f} ns per cell from 50 to 5,000 parcels (Table 16), so the runtime grows in step with the table size, as O(n\u00b7W) predicts. "
    f"Because capacity is capped at 600 kg from 500 parcels upward, growth from 500 to 5,000 parcels is close to linear in n ({float(kn[5000]['knapsack_median_ms'])/float(kn[500]['knapsack_median_ms']):.1f}\u00d7 for 10\u00d7 the parcels).",
    f"<b>Knapsack dominates cost from 50 parcels upward,</b> in both time (138.9 ms at 5,000 parcels) and memory (3,288.1 KiB, about 3.2 MiB). That is the order of magnitude of the roughly 3 million decision cells the application describes for 5,000 parcels.",
    f"<b>Merge Sort</b> grows from {kn[10]['sorting_median_ms']} ms to {kn[5000]['sorting_median_ms']} ms (about {ratio_ms:,.0f}\u00d7) while the input grows 500\u00d7. That is faster than linear and below the roughly 1,850\u00d7 that n log n predicts over this range (n log<sub>2</sub> n for 5,000 versus 10), so it is consistent with n log n; small-size timings are noisy.",
    f"<b>Dijkstra</b> stays small ({kn[10]['dijkstra_median_ms']} to {kn[5000]['dijkstra_median_ms']} ms) because its cost depends on the graph, not the parcel count. The graphs for 10, 50 and 100 parcels have only 8\u201310 locations, which is why that part of the curve is almost flat; its memory peak is identical (16.8 KiB) at 1,000 and 5,000 parcels.",
    f"<b>Nearest Neighbour routing</b> rises from {kn[10]['routing_median_ms']} ms to {kn[5000]['routing_median_ms']} ms as the number of stops grows from 4 to 120 and the graph from 8 to 150 locations, since it runs a Dijkstra search for every stop.",
    "<b>At the smallest sizes</b> (10 parcels) all stages take about 0.01\u20130.06 ms, close to timer resolution, so differences between stages there should not be over-interpreted.",
]))
add(note_box("These figures describe this implementation on one machine, with one seed and 3\u20135 repeats. They are consistent with the stated complexities "
             "but do not prove them, and they should not be read as a general speed claim."))
sp(3)
add(table_caption(16, "Derived from Tables 13 and 14: knapsack median time per DP cell."))
sp(1.5)
t_ns = [["Parcels", "DP cells", "Knapsack median (ms)", "Time per DP cell (ns)"]]
for c in rows_csv:
    n = int(c["parcels"])
    t_ns.append([fmt_int(n), fmt_int(c["dp_cells"]), c["knapsack_median_ms"], f"{ns[n]:.1f}"])
add(data_table(t_ns, [30 * mm, 40 * mm, 50 * mm, 50 * mm], align_right=(0, 1, 2, 3)))

add(PageBreak())
H2("6.5  Benchmark lab interface")
fig("bench", "Benchmark lab \u2013 run controls, charts, table and theory panel", "SCREENSHOT", ps("07-benchmarks.png"),
    "Run controls (dataset sizes 10\u20135,000 with 10\u20131,000 selected, repeats 5, seed 42), run metadata, two charts, the benchmark table (median with minimum in parentheses) and the "
    "theory-versus-measurement panel. This is a separate run from the supplied data files: measured 2026-11-23 02:56:37, datasets 10\u20131,000, Python 3.13.18. "
    "The table\u2019s last column is cut off by the page width in the capture.", 150 * mm)
sp(3)
add(table_caption(17, "Two separate benchmark runs: median ms from the screenshot table versus the supplied results.csv."))
sp(1.5)
def g(n, a): return kn[n][f"{a}_median_ms"]
add(data_table([
    ["Parcels", "Stage", "Screenshot run (2026-11-23, Python 3.13.18)", "Supplied results (2026-11-24, Python 3.13.7)"],
    ["100", "Merge Sort", "0.179", g(100, "sorting")],
    ["100", "0/1 Knapsack DP", "2.21", g(100, "knapsack")],
    ["1,000", "Merge Sort", "2.54", g(1000, "sorting")],
    ["1,000", "0/1 Knapsack DP", "36.91", g(1000, "knapsack")],
    ["1,000", "Dijkstra (one source)", "0.190", g(1000, "dijkstra")],
    ["1,000", "Nearest Neighbour", "15.91", g(1000, "routing")],
], [22 * mm, 46 * mm, 55 * mm, 55 * mm], align_right=(0, 2, 3)))
add(P("Screenshot values were read from the benchmark table in the capture; the Dijkstra and Nearest Neighbour columns show 0.013 / 0.119 ms at 100 parcels in the screenshot versus "
      f"{g(100,'dijkstra')} / {g(100,'routing')} ms in the file. The two runs use the same seed and sizes but different hardware and software, and wall-clock timings vary with CPU load, as the page itself notes. "
      "The supplied charts and tables in 6.2\u20136.4 use the data-file run only.", "small"))

# ================================================================== 7 TESTING
H1(7, "Testing and Edge Cases")
add(P("This section separates three kinds of evidence: demonstrations captured in the user interface, behaviour that the interface merely states, and automated test evidence.", "lead"))
add(info_box("No automated test output (unit tests, test logs or pass/fail counts) was supplied. This portfolio therefore reports <b>no</b> automated-test results. "
             "The edge-case evidence below consists of two UI screenshots and one sample input file.", "Evidence basis"))
sp(3)
add(table_caption(18, "Edge cases and the evidence available for each."))
sp(1.5)
add(data_table([
    ["Edge case", "What the supplied evidence shows", "Evidence type"],
    ["Parcel to an unreachable destination", f"PKG-0025 and PKG-0026 (Island) are flagged undeliverable and excluded before the knapsack ({fr('u_knap')}, {fr('u_route')}).", "UI screenshot (demonstrated)"],
    ["Warnings surfaced to the user", "Notes banner on Load planning; Warnings and red Undeliverable parcels panels on Route planner; toast \u201cOptimisation finished with warnings\u201d.", "UI screenshot (demonstrated)"],
    ["Capacity exactly filled", f"7 parcels, 120 of 120 kg, 0 kg remaining ({fr('knap')}).", "UI screenshot (demonstrated)"],
    ["Invalid parcel records", "invalid_examples.csv holds five records, each differing from a valid record in one field. The application\u2019s response to importing them was not captured.", "Sample input file only"],
    ["Negative road length", f"Stated as rejected in the Road network page text and Learning centre ({fr('net')}, {fr('l_dij')}); no rejection was captured.", "Stated in UI text"],
    ["Knapsack memory guard", f"Stated: requests above 60 million decision cells are refused ({fr('knap')}, {fr('bench')}); not demonstrated.", "Stated in UI text"],
    ["Non-integer weights or values", f"Stated: whole numbers are required because the DP is indexed by integer capacity ({fr('parcels')}); not demonstrated.", "Stated in UI text"],
    ["Automated tests (including brute-force comparison)", "Referred to in the Learning centre; the tests and results were not supplied.", "No evidence supplied"],
], [42 * mm, 100 * mm, 36 * mm], bold_first_col=True))

add(PageBreak())
H2("7.1  Undeliverable parcels \u2013 load planning")
fig("u_knap", "Load planning with two undeliverable parcels", "SCREENSHOT", ps("11-undeliverable-knapsack.png"),
    "Same data as Figure 5 plus two parcels whose destination, \u201cIsland\u201d, has no road from the depot. An amber Notes banner and a new Undeliverable parcels (2) table appear above the DP table.", 188 * mm)
sp(2)
add(bullets([
    "The banner reads that destination \u2018Island\u2019 cannot be reached from depot \u2018Depot\u2019 and that PKG-0025 and PKG-0026 are undeliverable; they were excluded before the knapsack, so they use no capacity, add no value and are not on the route.",
    f"The undeliverable table lists both parcels (20 kg each, priority P5) with the reason \u201cno road path from depot \u2018Depot\u2019 to \u2018Island\u2019\u201d.",
    f"The knapsack result is unchanged from {fr('knap')}: 7 of 24 deliverable parcels, 120 kg, 0 kg remaining, weighted value 18,590. The knapsack time reads 0.315 ms in this run (0.286 ms in {fr('knap')}).",
]))

add(PageBreak())
H2("7.2  Undeliverable parcels \u2013 route planning")
fig("u_route", "Route planner with the same undeliverable parcels", "SCREENSHOT", ps("12-undeliverable-route.png"),
    "Two notices appear above the result cards (amber Warnings and red Undeliverable parcels). The route map shows \u201cIsland\u201d as an isolated, unvisited node at the lower right. A toast reads \u201cOptimisation finished with warnings\u201d.", 188 * mm)
sp(2)
add(bullets([
    "The red panel states that no road path connects the depot to Island and that the 2 parcels were excluded, so they are not loaded, not counted in the selected weight or value, and not on the route.",
    f"The route itself is unchanged from {fr('route')}: the same five legs, 57.8 km, 5 stops, 6 Dijkstra runs and 7 / 0 on time. Routing time reads 0.154 ms in this run (0.222 ms earlier).",
    "Taken together, Figures 15 and 16 show the application detecting an unreachable destination, reporting it in two places, and continuing to produce a valid plan for the remaining parcels.",
]))

add(PageBreak())
H2("7.3  Invalid sample records")
add(P("The supplied invalid_examples.csv is a synthetic sample input file. It is reproduced as a table; the third column is an annotation added for this document, based on comparing each record with a valid record."))
inv = pcsv("invalid_examples.csv")
ann = {"BAD-1": "destination \u201cAtlantis\u201d is not a location in road_network.json",
       "BAD-2": "negative weight (\u22124)",
       "BAD-3": "priority 9 is outside P1\u2013P5",
       "BAD-4": "deadline \u201cnot-a-date\u201d is not a valid date-time",
       "BAD-5": "value is empty"}
add(table_caption(19, "invalid_examples.csv (SAMPLE INPUT, synthetic)."))
sp(1.5)
add(data_table([["id", "destination", "weight", "priority", "deadline", "value", "status", "Differs from a valid record (annotation)"]] +
               [[x["id"], x["destination"], x["weight"], x["priority"], x["deadline"], x["value"] or "(empty)", x["status"], ann[x["id"]]] for x in inv],
               [15 * mm, 24 * mm, 14 * mm, 14 * mm, 28 * mm, 14 * mm, 15 * mm, 54 * mm], align_right=(2, 3)))
sp(3)
add(note_box("No screenshot or log of these records being imported or rejected was supplied, so this portfolio does not claim how the application handles them."))

# ================================================================== 8 REPORTS
H1(8, "Reports and Outputs")
add(P("The Reports and export page offers downloads of the data behind each stage. Plan and route exports use the latest optimisation; the page states that a fresh one is run automatically if none exists.", "lead"))
fig("reports", "Reports and export page", "SCREENSHOT", ps("09-reports.png"),
    "Seven download cards: Parcel list (CSV), Parcel list (JSON), Packing plan (CSV), Delivery route (CSV), Optimisation summary (CSV), Benchmark results (CSV, flagged \u201cneeds a benchmark run\u201d) and PDF report.", 92 * mm)
sp(3)
add(table_caption(20, f"Exports offered, as described on the page ({fr('reports')})."))
sp(1.5)
add(data_table([
    ["Export", "Content as described on the page"],
    ["Parcel list (CSV)", "Every parcel with destination, weight, priority, deadline, value and status."],
    ["Parcel list (JSON)", "The same data in the format accepted by the importer."],
    ["Packing plan (CSV)", "Selected, rejected and undeliverable parcels with weights, weighted values and reasons."],
    ["Delivery route (CSV)", "Route legs with road paths, distances and the estimated arrival at each stop."],
    ["Optimisation summary (CSV)", "Capacity, utilisation, value, distance and stage timings of the latest run."],
    ["Benchmark results (CSV)", "All measured medians, minima, means and peak memory per dataset size; needs a benchmark run first."],
    ["PDF report", "Formatted report: summary, packing plan, route, timings and benchmark charts (when available)."],
], [48 * mm, 130 * mm], bold_first_col=True))
sp(3)
add(bullets([
    "The field list of the parcel exports matches the columns of the supplied parcels_24.csv (id, destination, weight, priority, deadline, value, status).",
    "The supplied results.csv has the content the Benchmark results export describes (medians, minima, means and peak memory per dataset size); the supplied materials do not state that it was produced with that button.",
]))
add(note_box("Only the export page itself was supplied. No generated PDF report or other exported file from the application was provided, so report contents are not shown."))

# ================================================================== 9 RESPONSIVE
H1(9, "Responsive Design")
add(P("The dashboard was also captured at 390 px width, shown as three consecutive segments cut only at the gaps between cards.", "lead"))
segs = [os.path.join(SS, f"10-mobile-seg{s}.png") for s in "ABC"]
fig("mobile", "Dashboard at 390 px width", "UI SCREENSHOT, SEGMENTED", segs,
    "Segment A: header, page title and the first five indicator cards. Segment B: the remaining three indicator cards and the first two charts. Segment C: delivery performance and runtime charts.",
    126 * mm, seg_labels=["A  \u2013  top", "B  \u2013  middle", "C  \u2013  bottom"])
sp(3)
add(table_caption(21, f"Layout differences between the desktop capture ({fr('dash')}) and the mobile capture ({fr('mobile')})."))
sp(1.5)
add(data_table([
    ["Element", "Desktop (1440 px)", "Mobile (390 px)"],
    ["Navigation", "Persistent sidebar with three labelled groups.", "Sidebar replaced by a menu icon at the top left (menu closed in the capture)."],
    ["Indicator cards", "Four per row, two rows.", "One per row, stacked vertically; all eight keep the same values."],
    ["Charts", "2 \u00d7 2 grid.", "Stacked, each at full width; axes and labels stay legible."],
], [30 * mm, 70 * mm, 78 * mm], bold_first_col=True))
sp(3)
add(note_box("Only the Dashboard was captured at mobile width; the opened menu, other pages and tablet widths are not evidenced. "
             f"The last chart differs between captures: stage timings of the latest run in {fr('dash')}, benchmark medians in {fr('mobile')}; the supplied materials do not explain why."))

# ================================================================== 10 CONCLUSION
H1(10, "Conclusion")
add(P("The supplied evidence shows a working, multi-page planning application in which four classical algorithms form one pipeline: a queue of parcels is ordered, "
      "a subset is chosen to fit the vehicle, and the chosen destinations are sequenced over a road network.", "lead"))
add(table_caption(22, "The sample run end to end (values from the screenshots)."))
sp(1.5)
add(data_table([
    ["Stage", "Algorithm", "Input", "Output shown", "Evidence"],
    ["Prioritise", "Merge Sort", "24 pending parcels", "Ordered queue, priority 5 first; 78 key comparisons", fr("sort")],
    ["Select", "0/1 Knapsack DP", "24 deliverable parcels, 120 kg", "7 parcels, 120 kg, weighted value 18,590", fr("knap")],
    ["Measure paths", "Dijkstra, binary min-heap", "13 locations, 20 roads", "Shortest road paths between stops (e.g. 8.9, 13.9, 10.4 km legs)", f"{fr('net')}, {fr('route')}"],
    ["Route", "Nearest Neighbour", "5 destinations of selected parcels", "57.8 km, 5 stops, all 7 parcels on time (estimate)", fr("route")],
], [24 * mm, 34 * mm, 38 * mm, 58 * mm, 24 * mm], bold_first_col=True))
sp(3)
H2("Practical roles of the four algorithms")
add(bullets([
    "<b>Merge Sort</b> gives a stable, deterministic ordering of parcels by urgency, using one combined comparison key.",
    "<b>0/1 Knapsack dynamic programming</b> finds the best-value load for a hard weight limit, evaluating combinations rather than ranking parcels one by one.",
    "<b>Dijkstra with a binary min-heap</b> supplies the shortest road distances that both the path queries and the routing stage depend on.",
    "<b>Nearest Neighbour</b> turns those distances into a practical delivery order quickly, with its approximation limits stated openly in the interface.",
]))
H2("Value of the project")
add(P("Beyond producing a plan, the application makes each algorithm inspectable: it shows the DP table behind the load plan, reports undeliverable parcels instead of hiding them, "
      "separates measured timings from theoretical complexity, and includes a learning centre with pseudocode, recurrences and viva questions. "
      "The benchmarks show the knapsack stage dominating time and memory as the dataset grows, which matches its O(n\u00b7W) nature, while sorting and path search remain small."))
add(P("This portfolio is a visual evidence companion. Where the supplied material did not contain evidence (automated test results, parcel-form and import dialogs, step-by-step "
      "Dijkstra and Merge Sort traces, generated report files, and mobile views beyond the dashboard), the gap is stated in the relevant section rather than filled in."))

# ================================================================== APPENDIX
add(PageBreak())
add(SectionHead("A", "Appendix: Source-Material Inventory"))
add(P("Every supplied screenshot and chart appears exactly once as a figure. The table maps each supplied file to its place in this document.", "lead"))
add(table_caption(23, "Supplied files and where they are used."))
sp(1.5)
add(data_table([
    ["Supplied file", "Used as", "Section"],
    ["screenshots/01-dashboard.png", fr("dash"), "2"],
    ["screenshots/02-parcels.png", fr("parcels"), "3"],
    ["screenshots/03-sorting.png", fr("sort"), "4.1"],
    ["screenshots/04-knapsack.png", fr("knap"), "4.2"],
    ["screenshots/05-network.png", fr("net"), "4.3"],
    ["screenshots/06-route.png", fr("route"), "4.4"],
    ["screenshots/08-learn-merge / -knapsack / -dijkstra / -nearest.png", f"{fr('l_merge')} to {F['l_nn']}", "5"],
    ["benchmarks/runtime.png, memory.png", f"{fr('rt')}, {fr('mem')}", "6.2, 6.3"],
    ["screenshots/07-benchmarks.png", fr("bench"), "6.5"],
    ["screenshots/11-undeliverable-knapsack.png, 12-undeliverable-route.png", f"{fr('u_knap')}, {fr('u_route')}", "7.1, 7.2"],
    ["screenshots/09-reports.png", fr("reports"), "8"],
    ["screenshots/10-mobile-dashboard.png", f"{fr('mobile')} (3 segments)", "9"],
    ["benchmarks/results.csv, results.json", "Tables 13\u201316 and the 6.1 parameters", "6"],
    ["sample_data/parcels_10, 24, 50, 100 (.csv / .json)", "Tables 5, 6", "3"],
    ["sample_data/road_network.json", "Network size and consistency check", "1, 4.3"],
    ["sample_data/invalid_examples.csv", "Table 19", "7.3"],
    ["screenshots/README.md", "Capture conditions", "1"],
], [100 * mm, 52 * mm, 26 * mm]))
sp(3)
H3("Consistency checks performed while preparing this document")
add(bullets([
    "results.json and results.csv were compared field by field (medians, minima, means, peak memory, repeats for all four stages and six sizes); all values match.",
    "As a cross-check, the 24-parcel sample file and the road network were processed with an independent script. It reproduced the prioritised order (ranks 1\u201310), the 7 selected parcels, 120 kg and 18,590 weighted value, and the five route legs (6.3, 5.3, 8.9, 13.9, 10.4 km) plus a 13.0 km return, 57.8 km in total. These checks confirm the screenshots are consistent with the sample data; they are not additional application evidence.",
    "Chart titles in runtime.png and memory.png say repeats = 5, while the data files record 3 repeats for 1,000 and 5,000 parcels. The chart values themselves match the data files.",
]))


# ------------------------------------------------------------------ build
def main():
    doc = Portfolio(OUT, title="Mini Courier Planner \u2013 Project Screenshot Portfolio",
                    author="Manas Aggarwal",
                    subject="Design and Analysis of Algorithms (ETCCDA302) \u2013 B.Tech CSE (AI/ML), K.R. Mangalam University",
                    keywords="DAA, Merge Sort, 0/1 Knapsack, Dijkstra, Nearest Neighbour, screenshot portfolio")
    # keep each table caption together with its (short) table
    out, i = [], 0
    while i < len(story):
        f = story[i]
        if isinstance(f, Paragraph) and getattr(f, "text", "").startswith('<font name="Body-B" color="#0E7490">Table'):
            grp = [f]; j = i + 1
            while j < len(story) and isinstance(story[j], Spacer):
                grp.append(story[j]); j += 1
            if j < len(story) and isinstance(story[j], Table) and len(story[j]._cellvalues) <= 16:
                grp.append(story[j]); out.append(KeepTogether(grp)); i = j + 1; continue
        out.append(f); i += 1
    story[:] = out
    doc.multiBuild(story)
    print("built", OUT)

if __name__ == "__main__":
    main()
