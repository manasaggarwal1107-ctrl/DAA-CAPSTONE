# Test-Case Documentation

## Results (actually executed)

`cd backend && python3 -m pytest -q` on Linux, Python 3.13.18, pytest 9.1.1:

**128 tests collected, 128 passed** (111 original + 17 regression tests added in v1.0.1).

| File | Tests | Scope |
|---|---|---|
| `tests/test_algorithms.py` | 42 | Merge Sort, Knapsack, MinHeap, Dijkstra/Graph, Nearest Neighbour |
| `tests/test_pipeline.py` | 48 | Pipeline edge cases, models, store, import/export, benchmark, PDF |
| `tests/test_api.py` | 21 | HTTP-level integration (run through the Starlette app) |
| `tests/test_feasibility_regression.py` | 17 | Undeliverable parcels, selection/route consistency, exports/PDF agreement, Nearest Neighbour tie-breaking and trace |

Not executed: `run-tests.ps1` (no PowerShell in the build environment). Tests were run on Linux only. Oracles used inside tests: `sorted()` (for Merge Sort), brute-force subset enumeration (Knapsack, NN optimum), `heapq` (MinHeap), Bellman-Ford (Dijkstra) - the algorithms themselves use none of these.

## Edge cases required by the brief -> covering tests

| Required case | Test(s) |
|---|---|
| Empty parcel dataset | `TestPipelineEdgeCases::test_empty_dataset`; `TestMergeSort::test_empty_and_single` |
| One parcel | `test_single_parcel`; `test_empty_and_single` |
| Duplicate destinations / multiple parcels at one destination | `test_duplicate_destinations_one_stop` |
| Equal priorities / equal deadlines | `test_equal_priority_and_deadline_use_id_tiebreak`; `TestMergeSort::test_parcel_ordering_rules`, `test_stable` |
| Parcel heavier than capacity | `test_parcel_heavier_than_capacity`, `test_all_parcels_too_heavy`; `TestKnapsack::test_item_heavier_than_capacity` |
| Zero-capacity vehicle | `test_zero_capacity_selects_nothing`; `TestKnapsack::test_zero_capacity_and_empty`; API `test_zero_capacity_and_whatif_not_persisted` |
| Selected parcel whose destination is disconnected from the depot | `TestUnreachableDestinations::test_unreachable_parcel_is_never_selected_and_uses_no_capacity`, `test_one_way_road_reachable_from_depot_but_not_from_previous_stop` |
| Multiple parcels at one unreachable destination | `test_multiple_parcels_at_one_unreachable_destination` |
| All parcel destinations unreachable | `test_all_destinations_unreachable`; `TestExportsAndReportAgree::test_pdf_builds_when_everything_is_undeliverable` |
| Mix of reachable and unreachable destinations | `test_mixed_reachable_and_unreachable` |
| Deterministic Nearest Neighbour tie-breaking | `TestNearestNeighbourDeterminism` (3 tests + trace) |
| Selected weight = deliverable (routed) weight | `assert_consistent()` helper used by every pipeline regression test |
| Disconnected graph | `test_disconnected_graph_is_reported_not_routed`; `TestDijkstra::test_disconnected`; `TestNearestNeighbour::test_unreachable_reported_not_silent` |
| Invalid locations | `test_invalid_destination_flagged`, `test_unknown_depot_raises`; `TestDijkstra::test_unknown_nodes`; `TestNearestNeighbour::test_unknown_stop_reported`, `test_unknown_depot`; `TestStore::test_add_generates_id_and_rejects_duplicates_and_bad_destination` |
| Negative graph weights | `TestDijkstra::test_negative_weight_rejected`, `test_non_finite_weight_rejected`; `TestStore::test_negative_road_rejected`; API `test_graph_editing_and_shortest_path` |
| No selected parcels | `test_zero_capacity_selects_nothing`, `test_all_parcels_too_heavy` (status `nothing_selected`; `nothing_deliverable` when every destination is unreachable) |
| Missing JSON fields | `TestModels::test_missing_fields`; `TestImportExport::test_json_import_with_errors_per_row`, `test_csv_import_and_missing_column`; API `test_missing_fields_and_conflicts` |
| Large datasets | `test_large_dataset`; `TestKnapsack::test_table_skipped_when_large`, `test_resource_limit`; `TestBenchmark::test_run_benchmark_structure_and_csv` |
| No crash on ordinary invalid input | `TestImportExport::test_bad_files_raise_clean_errors`; API `test_validation_messages`, `test_settings_validation` |

## Algorithm correctness tests (`test_algorithms.py`)

* **Merge Sort:** matches `sorted()` on random data; input not mutated; stable; trace and comparison counter; registry lookup.
* **Knapsack:** optimal value equals brute force on random instances; classic textbook example; each item used at most once; DP table shape and final cell; table skipped for large instances; 60M-cell guard raises; invalid input rejected.
* **MinHeap:** pop order equals `heapq`; pop from empty raises.
* **Dijkstra:** distances equal Bellman-Ford on random graphs; path reconstruction; source == target; directed edges; edge/node removal; self-loop rejection; trace has steps.
* **Nearest Neighbour:** visits nearest first and returns; each stop once and no extra stops; depot in stops ignored; no return path on one-way roads; never better than the brute-force optimum.

## Integration and system tests

`test_pipeline.py` covers model validation, JSON-file store (seeding, persistence, corrupt-file recovery, ID generation, depot protection, cascade removal of roads), row-level import errors, CSV round trip, benchmark reproducibility (same seed, same datasets), generated graphs being connected, and PDF generation. `test_api.py` covers parcel CRUD, graph editing, the full workflow and dashboard, import/export and dataset loading, benchmark and report exports, learning centre endpoints, reset, and persistence on disk.

## Not tested automatically

The React UI has no unit tests. It was exercised manually by a scripted headless-Chromium walk through every page (no console errors or failed API calls) - a smoke test, not an assertion-based suite. PowerShell scripts untested.

## How to run

```powershell
.\run-tests.ps1                         # Windows (untested script)
cd backend; .\.venv\Scripts\python -m pytest     # after start.ps1 has created the venv
cd backend && python3 -m pytest -q      # Linux/macOS with dependencies installed
```
