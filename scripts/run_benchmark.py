"""Run the full benchmark (6 dataset sizes) and write CSV, JSON and PNG graphs to docs/benchmarks.

Usage (from the project root):   python scripts/run_benchmark.py [--repeats 5] [--seed 42]
All numbers are real measurements taken on the machine that runs this script.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from app.services import benchmark, exports  # noqa: E402

STAGES = [("sorting", "Merge Sort"), ("knapsack", "0/1 Knapsack DP"), ("dijkstra", "Dijkstra (one source)"), ("routing", "Nearest Neighbour route")]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--sizes", type=int, nargs="+", default=[10, 50, 100, 500, 1000, 5000])
    a = ap.parse_args()
    out = ROOT / "docs" / "benchmarks"
    out.mkdir(parents=True, exist_ok=True)
    res = benchmark.run_benchmark(a.sizes, a.repeats, a.seed)
    (out / "results.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    (out / "results.csv").write_text(exports.benchmark_csv(res), encoding="utf-8", newline="")
    ns = [r["n"] for r in res["rows"]]
    for key, title, fname, unit in (("median_ms", "Median runtime per stage", "runtime.png", "ms"), ("peak_kb", "Peak memory per stage (tracemalloc)", "memory.png", "KiB")):
        fig, ax = plt.subplots(figsize=(7.5, 4.4))
        for stage, label in STAGES:
            ax.plot(ns, [max(r[stage][key], 1e-3) for r in res["rows"]], marker="o", label=label)
        ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("parcels (n)"); ax.set_ylabel(unit)
        ax.set_title(f"{title} (measured, repeats={a.repeats}, seed={a.seed})"); ax.grid(True, which="both", alpha=0.3); ax.legend()
        fig.tight_layout(); fig.savefig(out / fname, dpi=150); plt.close(fig)
    print(f"Wrote results.csv, results.json, runtime.png, memory.png to {out}")
    for r in res["rows"]:
        print(r["n"], {s: r[s]["median_ms"] for s, _ in STAGES})


if __name__ == "__main__":
    main()
