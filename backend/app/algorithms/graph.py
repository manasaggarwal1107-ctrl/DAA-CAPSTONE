"""Weighted adjacency-list graph, binary min-heap and Dijkstra's algorithm.

Dijkstra uses a hand-written binary min-heap with lazy deletion:
    time  O((V + E) log V), space O(V + E).
Negative (or non-finite) edge weights are rejected on insertion because
Dijkstra is only correct for non-negative weights.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Optional

from .errors import AlgorithmError, NegativeWeightError, UnknownNodeError


class MinHeap:
    """Binary min-heap of ``(priority, sequence, item)``; sequence breaks ties FIFO."""

    def __init__(self) -> None:
        self._a: list[tuple[float, int, Any]] = []
        self._seq = 0

    def __len__(self) -> int:
        return len(self._a)

    def push(self, priority: float, item: Any) -> None:
        self._seq += 1
        a = self._a
        a.append((priority, self._seq, item))
        i = len(a) - 1
        while i > 0:
            parent = (i - 1) // 2
            if a[i][:2] < a[parent][:2]:
                a[i], a[parent] = a[parent], a[i]
                i = parent
            else:
                break

    def pop(self) -> tuple[float, Any]:
        a = self._a
        if not a:
            raise IndexError("pop from empty heap")
        top = a[0]
        last = a.pop()
        if a:
            a[0] = last
            i, n = 0, len(a)
            while True:
                left, right, smallest = 2 * i + 1, 2 * i + 2, i
                if left < n and a[left][:2] < a[smallest][:2]:
                    smallest = left
                if right < n and a[right][:2] < a[smallest][:2]:
                    smallest = right
                if smallest == i:
                    break
                a[i], a[smallest] = a[smallest], a[i]
                i = smallest
        return top[0], top[2]


class Graph:
    """Directed weighted graph stored as an adjacency list.

    Undirected roads are stored as two arcs (``bidirectional=True``).
    """

    def __init__(self) -> None:
        self._adj: dict[str, list[tuple[str, float]]] = {}

    # ---- nodes -------------------------------------------------------
    def add_node(self, name: str) -> None:
        self._adj.setdefault(name, [])

    def has_node(self, name: str) -> bool:
        return name in self._adj

    def remove_node(self, name: str) -> None:
        self._require(name)
        del self._adj[name]
        for src in self._adj:
            self._adj[src] = [(d, w) for d, w in self._adj[src] if d != name]

    def nodes(self) -> list[str]:
        return list(self._adj)

    # ---- edges -------------------------------------------------------
    def _require(self, name: str) -> None:
        if name not in self._adj:
            raise UnknownNodeError(f"Unknown location '{name}'")

    def _set_arc(self, a: str, b: str, weight: float) -> None:
        arcs = self._adj[a]
        for idx, (dst, _) in enumerate(arcs):
            if dst == b:
                arcs[idx] = (b, weight)
                return
        arcs.append((b, weight))

    def add_edge(self, a: str, b: str, weight: float, bidirectional: bool = True) -> None:
        self._require(a)
        self._require(b)
        if a == b:
            raise AlgorithmError("A road cannot connect a location to itself")
        if isinstance(weight, bool) or not isinstance(weight, (int, float)) or math.isnan(weight) or math.isinf(weight):
            raise AlgorithmError("Road distance must be a finite number")
        if weight < 0:
            raise NegativeWeightError(f"Road distance must not be negative (got {weight})")
        self._set_arc(a, b, float(weight))
        if bidirectional:
            self._set_arc(b, a, float(weight))

    def remove_edge(self, a: str, b: str, bidirectional: bool = True) -> None:
        self._require(a)
        self._require(b)
        found = any(d == b for d, _ in self._adj[a])
        self._adj[a] = [(d, w) for d, w in self._adj[a] if d != b]
        if bidirectional:
            found = found or any(d == a for d, _ in self._adj[b])
            self._adj[b] = [(d, w) for d, w in self._adj[b] if d != a]
        if not found:
            raise AlgorithmError(f"No road between '{a}' and '{b}'")

    def neighbours(self, name: str) -> list[tuple[str, float]]:
        self._require(name)
        return self._adj[name]

    def edges(self) -> list[dict]:
        """Roads as dicts; a reciprocal pair with equal weight is one bidirectional road."""
        out: list[dict] = []
        for a, arcs in self._adj.items():
            for b, w in arcs:
                reverse = next((rw for d, rw in self._adj.get(b, []) if d == a), None)
                if reverse is not None and reverse == w:
                    if a < b:
                        out.append({"a": a, "b": b, "weight": w, "bidirectional": True})
                else:
                    out.append({"a": a, "b": b, "weight": w, "bidirectional": False})
        return out


@dataclass
class DijkstraResult:
    source: str
    dist: dict[str, float]
    prev: dict[str, Optional[str]]
    steps: list[dict] = field(default_factory=list)

    def reachable(self, node: str) -> bool:
        return node in self.dist

    def path_to(self, target: str) -> Optional[list[str]]:
        """Node list from source to target, or ``None`` if unreachable."""
        if target not in self.dist:
            return None
        path = [target]
        while path[-1] != self.source:
            path.append(self.prev[path[-1]])  # type: ignore[arg-type]
        path.reverse()
        return path


def dijkstra(graph: Graph, source: str, *, target: Optional[str] = None,
             trace: bool = False) -> DijkstraResult:
    """Single-source shortest paths from ``source`` (early exit if ``target`` given)."""
    if not graph.has_node(source):
        raise UnknownNodeError(f"Unknown location '{source}'")
    if target is not None and not graph.has_node(target):
        raise UnknownNodeError(f"Unknown location '{target}'")

    dist: dict[str, float] = {source: 0.0}
    prev: dict[str, Optional[str]] = {source: None}
    done: set[str] = set()
    heap = MinHeap()
    heap.push(0.0, source)
    steps: list[dict] = []

    while len(heap):
        d, u = heap.pop()
        if u in done:                    # stale heap entry (lazy deletion)
            continue
        done.add(u)
        relaxed: list[dict] = []
        if target is None or u != target:
            for v, w in graph.neighbours(u):
                if v in done:
                    continue
                nd = d + w
                old = dist.get(v)
                improved = old is None or nd < old
                if improved:
                    dist[v] = nd
                    prev[v] = u
                    heap.push(nd, v)
                if trace:
                    relaxed.append({"to": v, "candidate": round(nd, 4),
                                    "previous": None if old is None else round(old, 4),
                                    "improved": improved})
        if trace:
            steps.append({"visit": u, "distance": round(d, 4), "relaxed": relaxed,
                          "distances": {k: round(x, 4) for k, x in dist.items()},
                          "settled": sorted(done)})
        if target is not None and u == target:
            break
    return DijkstraResult(source, dist, prev, steps)


def shortest_path(graph: Graph, source: str, target: str) -> tuple[Optional[list[str]], Optional[float]]:
    """Convenience wrapper: ``(path, distance)`` or ``(None, None)`` if unreachable."""
    res = dijkstra(graph, source, target=target)
    path = res.path_to(target)
    return (path, res.dist[target]) if path is not None else (None, None)
