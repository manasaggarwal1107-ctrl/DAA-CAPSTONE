"""Manual Merge Sort (stable, top-down) and a small sorter registry.

Time  : O(n log n) in best, average and worst case.
Space : O(n) auxiliary (new lists are created while merging).

No call to ``sorted()`` / ``list.sort()`` is used by the algorithm.  New
sorting algorithms (e.g. quick sort, insertion sort from other labs) only need
to follow the ``SortFn`` signature and be added to ``SORTERS``.
"""

from __future__ import annotations

from typing import Any, Callable, Optional, Sequence, TypeVar

from .errors import AlgorithmError

T = TypeVar("T")
KeyFn = Callable[[Any], Any]
SortFn = Callable[..., list]


def _merge(left: list, right: list, key: KeyFn, stats: Optional[dict]) -> list:
    """Merge two sorted lists.  ``<=`` on the left run keeps the sort stable."""
    merged: list = []
    i = j = 0
    while i < len(left) and j < len(right):
        if stats is not None:
            stats["comparisons"] += 1
        if key(left[i]) <= key(right[j]):
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged


def _sort(items: list, key: KeyFn, depth: int, trace: Optional[list],
          label: Callable[[Any], Any], stats: Optional[dict]) -> list:
    if len(items) <= 1:
        return list(items)
    mid = len(items) // 2
    if trace is not None:
        trace.append({"type": "split", "depth": depth,
                      "items": [label(x) for x in items],
                      "left": [label(x) for x in items[:mid]],
                      "right": [label(x) for x in items[mid:]]})
    left = _sort(items[:mid], key, depth + 1, trace, label, stats)
    right = _sort(items[mid:], key, depth + 1, trace, label, stats)
    result = _merge(left, right, key, stats)
    if trace is not None:
        trace.append({"type": "merge", "depth": depth,
                      "left": [label(x) for x in left],
                      "right": [label(x) for x in right],
                      "result": [label(x) for x in result]})
    return result


def merge_sort(items: Sequence[T], key: Optional[KeyFn] = None, *,
               trace: Optional[list] = None,
               label: Optional[Callable[[T], Any]] = None,
               stats: Optional[dict] = None) -> list[T]:
    """Return a new list sorted ascending by ``key`` (identity by default).

    Args:
        items: input sequence (not modified).
        key: function returning a comparable value (tuples allowed).
        trace: if given, split/merge events are appended (for visualisation).
        label: maps an item to a JSON-friendly label used in ``trace``.
        stats: if given, ``stats["comparisons"]`` is incremented per comparison.
    """
    key_fn: KeyFn = key if key is not None else (lambda x: x)
    label_fn = label if label is not None else (lambda x: x)
    if stats is not None:
        stats.setdefault("comparisons", 0)
    return _sort(list(items), key_fn, 0, trace, label_fn, stats)


SORTERS: dict[str, SortFn] = {"merge": merge_sort}


def get_sorter(name: str) -> SortFn:
    """Look up a registered sorting algorithm by name."""
    try:
        return SORTERS[name]
    except KeyError:
        raise AlgorithmError(f"Unknown sorting algorithm '{name}'. Available: {', '.join(SORTERS)}") from None
