# Evidence-Gap Report — Mini Courier Planner Screenshot Portfolio

Gaps, unclear points and inconsistencies found in the supplied material. Nothing below was filled in or invented in the PDF; each item is stated or avoided in the relevant section.

## A. Missing evidence
1. **Automated test evidence** — no unit-test output, logs or pass/fail counts were supplied. Section 7 reports none. The Learning centre says tests compare Nearest Neighbour with brute force; those tests were not provided.
2. **Invalid-record handling** — `invalid_examples.csv` (5 records) was supplied, but no screenshot/log of the import being rejected. Shown only as a sample input file.
3. **Parcel dialogs** — Add parcel, edit, delete, Import and Datasets dialogs are not captured (only the toolbar/icons).
4. **Dijkstra trace** — Learning-centre trace captured at step 0/6; the Road network query is a single direct road (Depot → Sohna Road, 4.2 km). Multi-road paths are evidenced only via route legs.
5. **Merge Sort trace** — only step 1/14 (first split) captured; Learning-centre example at step 0/12. Nearest Neighbour trace at step 0/3.
6. **Generated reports** — only the Reports page was supplied; no exported CSV/JSON/PDF produced by the app.
7. **Mobile coverage** — only the dashboard at 390 px; no opened menu, other pages or tablet widths.
8. **Negative-road rejection, 60-million-cell memory guard, whole-number validation** — stated in UI text only; not demonstrated.
9. **No optimal-tour comparison** for the Nearest Neighbour route.

## B. Inconsistencies / unclear points
1. **Dashboard timing** — "Algorithm time 2.18 ms" vs. listed stage timings (0.059 + 0.199 + 0.222 = 0.480 ms). The remainder is unexplained.
2. **Differing timings between pages** (sort 0.059 vs 0.073 ms; knapsack 0.199 / 0.286 / 0.315 ms; routing 0.222 / 0.154 ms) — separate runs; documented as such.
3. **Two benchmark runs** — screenshot: 2026-11-23 02:56:37, sizes 10–1,000, Python 3.13.18 (capture on Linux per README). Supplied data/charts: 2026-11-24 09:11:24, sizes 10–5,000, Python 3.13.7, Windows 11. Values differ (e.g. 1,000-parcel knapsack 36.91 vs 29.256 ms). Kept separate (Table 17).
4. **Chart titles vs data** — runtime.png / memory.png say repeats = 5; data files record 3 repeats for 1,000 and 5,000 parcels. Chart values match the data.
5. **Last dashboard chart differs** between desktop (stage timings) and mobile (benchmark medians) captures, although the README says all were captured after one optimisation and one benchmark.
6. **Screenshot artefacts** — sticky header mid-page (Figures 4, 6), toast overlays (Figures 2, 3, 8, 16), benchmark table's last column cut off (Figure 14), rejected-parcel list shows 6 of 17 rows and DP table capacities 0–15 of 0–120. All reproduced unaltered.
7. **Rejected-parcel reason** is the same generic text for every row ("lower priority-weighted value per kg than the chosen set").
8. **"Custom" min-heap** — the interface says "binary min-heap"; "custom" comes from your project brief and is used only in the brief-derived wording.

## C. Verification performed
- `results.json` vs `results.csv`: all values identical.
- Independent script on `parcels_24.csv` + `road_network.json` reproduced: sort order (ranks 1–10), 7 selected parcels / 120 kg / 18,590, route legs 6.3, 5.3, 8.9, 13.9, 10.4 km + 13.0 km return = 57.8 km. (Consistency check only, not application evidence.)

## D. Suggested additions if you want to close gaps
Test-runner output; a played-through Merge Sort/Dijkstra trace; an Add-parcel/Import dialog and the invalid-CSV import result; a multi-hop Dijkstra query; a downloaded PDF report; mobile views of other pages.
