"""0/1 Knapsack by dynamic programming (1-D array, capacities descending).

Recurrence (conceptual 2-D form):

    dp[i][w] = dp[i-1][w]                                   if wt[i] > w
    dp[i][w] = max(dp[i-1][w], dp[i-1][w-wt[i]] + val[i])   otherwise

The 1-D version keeps a single row and iterates ``w`` from capacity down to
``wt[i]`` so that ``dp[w-wt[i]]`` still holds the value from item ``i-1``;
this guarantees every item is used at most once.

Reconstruction: while filling, ``keep[i][w]`` records whether item ``i``
improved ``dp[w]``.  Walking items backwards from ``w = capacity`` recovers an
optimal subset.  ``keep`` is one ``bytearray`` of ``capacity+1`` bytes per
item, so memory is ``n * (capacity+1)`` bytes; ``MAX_DP_CELLS`` refuses
problems that would exceed a safe budget.

Time O(n*W), space O(W) for values + O(n*W) bytes for the decision matrix.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Sequence

from .errors import AlgorithmError, ResourceLimitError

MAX_DP_CELLS = 60_000_000      # decision-matrix safety limit (bytes)
MAX_TABLE_CELLS = 20_000       # largest full DP table returned for visualisation


@dataclass
class KnapsackResult:
    best_value: int
    selected: list[int]                 # indices into the input, ascending
    total_weight: int
    cells: int                          # n * (capacity + 1) decision cells
    table: Optional[list[list[int]]] = None   # table[i][w], i = items considered
    table_note: str = ""
    keep: list[list[int]] = field(default_factory=list)  # only when table recorded


def knapsack_01(weights: Sequence[int], values: Sequence[int], capacity: int, *,
                record_table: bool = False) -> KnapsackResult:
    """Solve 0/1 knapsack and return the optimal value and chosen item indices."""
    n = len(weights)
    if len(values) != n:
        raise AlgorithmError("weights and values must have the same length")
    if capacity < 0:
        raise AlgorithmError("capacity must be non-negative")
    if any(w < 0 for w in weights) or any(v < 0 for v in values):
        raise AlgorithmError("weights and values must be non-negative")
    cells = n * (capacity + 1)
    if cells > MAX_DP_CELLS:
        raise ResourceLimitError(
            f"Knapsack needs {cells:,} decision cells (items x capacity); the safety limit is "
            f"{MAX_DP_CELLS:,}. Reduce the vehicle capacity or the number of parcels.")

    dp = [0] * (capacity + 1)
    keep = [bytearray(capacity + 1) for _ in range(n)]
    want_table = record_table and (n + 1) * (capacity + 1) <= MAX_TABLE_CELLS
    table: Optional[list[list[int]]] = [list(dp)] if want_table else None

    for i in range(n):
        wt, val, row = weights[i], values[i], keep[i]
        # Descending capacities: dp[w - wt] still belongs to items 0..i-1.
        for w in range(capacity, wt - 1, -1):
            candidate = dp[w - wt] + val
            if candidate > dp[w]:
                dp[w] = candidate
                row[w] = 1
        if table is not None:
            table.append(list(dp))

    selected: list[int] = []
    w = capacity
    for i in range(n - 1, -1, -1):
        if keep[i][w]:
            selected.append(i)
            w -= weights[i]
    selected.reverse()

    note = ""
    if record_table and table is None:
        note = (f"DP table hidden: {(n + 1) * (capacity + 1):,} cells exceeds the display "
                f"limit of {MAX_TABLE_CELLS:,}. The algorithm still ran in full.")
    return KnapsackResult(
        best_value=dp[capacity] if capacity >= 0 else 0,
        selected=selected,
        total_weight=sum(weights[i] for i in selected),
        cells=cells,
        table=table,
        table_note=note,
        keep=[list(r) for r in keep] if table is not None else [],
    )
