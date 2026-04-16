#!/usr/bin/env python3
"""
qor_trends.py — Cross-design QoR metric trending for digital chip design agents.

Reads memory/<domain>/experiences.jsonl files and produces a QoR trend table
(and optional matplotlib chart) for a named design across runs.

Usage:
    python3 tools/qor_trends.py --design <name> [options]

Options:
    --design  NAME      Design name to filter (required)
    --domain  DOMAIN    Limit to one domain (default: all domains)
    --metric  FIELD     Specific metric field to plot (default: all numeric)
    --plot              Emit a matplotlib chart (requires matplotlib)
    --output  FILE      Save chart to FILE instead of displaying (implies --plot)
    --memory-root PATH  Path to the memory/ directory (default: auto-detect)
    --min-runs N        Minimum runs required to include a domain (default: 2)

Examples:
    # Print trend table for all domains where design "aes_core" appears
    python3 tools/qor_trends.py --design aes_core

    # Show WNS trend for synthesis domain only
    python3 tools/qor_trends.py --design aes_core --domain synthesis --metric wns_ns

    # Save a chart of all metrics to a file
    python3 tools/qor_trends.py --design aes_core --plot --output aes_core_qor.png

Exit codes:
    0  — table/chart produced
    1  — no matching runs found for the given design
    2  — unexpected error
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

VALID_DOMAINS = [
    "architecture",
    "compiler",
    "dft",
    "firmware",
    "formal",
    "fpga",
    "hls",
    "pd",
    "rtl-design",
    "soc",
    "sta",
    "synthesis",
    "verification",
]

# Numeric metric fields per domain
NUMERIC_METRICS: dict[str, list[str]] = {
    "architecture": ["estimated_mhz", "estimated_area_um2"],
    "compiler": ["regression_pass_rate"],
    "dft": ["scan_coverage_pct", "atpg_fault_coverage_pct"],
    "firmware": ["flash_size_kb"],
    "formal": ["proved", "failed", "unknown"],
    "fpga": ["lut_count", "fmax_mhz"],
    "hls": ["latency_cycles", "dsp_count"],
    "pd": ["wns_ns", "drc_violations", "lvs_errors", "gds_area_um2"],
    "rtl-design": ["lint_errors", "cdc_violations"],
    "soc": ["ip_blocks_integrated", "memory_map_conflicts"],
    "sta": ["setup_wns_ns", "hold_wns_ns", "tns_ns", "failing_paths"],
    "synthesis": ["wns_ns", "cells", "area_um2", "lec_unmatched"],
    "verification": ["functional_coverage_pct", "regression_failures", "assertions_triggered"],
}

# Metrics where higher is better (used for regression detection)
HIGHER_IS_BETTER = {
    "estimated_mhz", "fmax_mhz", "isa_tests_passed", "regression_pass_rate",
    "scan_coverage_pct", "atpg_fault_coverage_pct", "bsp_tests_passed",
    "proved", "ip_blocks_integrated", "functional_coverage_pct",
    "ii_achieved", "timing_met", "abi_compliant", "simulation_pass",
    "synth_check_pass", "build_pass",
}


def find_memory_root(script_path: Path) -> Path:
    """Walk up from script location to find the memory/ directory."""
    candidate = script_path.resolve().parent
    for _ in range(5):
        mem = candidate / "memory"
        if mem.is_dir():
            return mem
        candidate = candidate.parent
    raise FileNotFoundError(
        "Could not locate memory/ directory. Use --memory-root to specify it explicitly."
    )


def load_domain_records(memory_root: Path, domain: str) -> list[dict]:
    jsonl = memory_root / domain / "experiences.jsonl"
    if not jsonl.exists():
        return []
    records: list[dict] = []
    with jsonl.open("r", encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                records.append(json.loads(raw))
            except json.JSONDecodeError:
                print(f"  [warn] {domain}: malformed JSON on line {lineno}, skipping", file=sys.stderr)
    return records


def filter_by_design(records: list[dict], design_name: str) -> list[dict]:
    name_lower = design_name.lower()
    return [
        r for r in records
        if isinstance(r.get("design_name"), str)
        and r["design_name"].lower() == name_lower
    ]


def extract_series(
    records: list[dict],
    domain: str,
    metric_filter: str | None,
) -> dict[str, list[tuple[str, float]]]:
    """
    Returns { metric_field: [(timestamp, value), ...] } sorted by timestamp.
    Only includes numeric values. Optionally filtered to a single metric.
    """
    fields = NUMERIC_METRICS.get(domain, [])
    if metric_filter:
        fields = [f for f in fields if f == metric_filter]

    series: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for rec in records:
        ts = rec.get("timestamp", "")
        km = rec.get("key_metrics") or {}
        for field in fields:
            val = km.get(field)
            if isinstance(val, (int, float)):
                series[field].append((ts, float(val)))

    # Sort each series chronologically
    for field in series:
        series[field].sort(key=lambda x: x[0])

    return dict(series)


def detect_regression(field: str, values: list[float]) -> str | None:
    """
    Return a warning string if the last value is worse than the previous,
    otherwise None.
    """
    if len(values) < 2:
        return None
    prev, last = values[-2], values[-1]
    if field in HIGHER_IS_BETTER:
        if last < prev:
            return f"REGRESSION: {prev:.3g} -> {last:.3g} (lower is worse)"
    else:
        if last > prev:
            return f"REGRESSION: {prev:.3g} -> {last:.3g} (higher is worse)"
    return None


def print_table(
    design: str,
    domain_series: dict[str, dict[str, list[tuple[str, float]]]],
    min_runs: int,
) -> int:
    """Print the QoR trend table. Returns number of rows printed."""
    rows = 0
    for domain, series in sorted(domain_series.items()):
        if not series:
            continue
        # Count distinct runs for this domain/design
        run_count = max(len(pts) for pts in series.values()) if series else 0
        if run_count < min_runs:
            continue

        print(f"\n{'='*72}")
        print(f"Domain: {domain}  |  Design: {design}  |  Runs: {run_count}")
        print(f"{'='*72}")
        print(f"  {'Metric':<35} {'Min':>10} {'Max':>10} {'Latest':>10}  Alert")
        print(f"  {'-'*35} {'-'*10} {'-'*10} {'-'*10}  -----")

        for field, points in sorted(series.items()):
            values = [v for _, v in points]
            if not values:
                continue
            alert = detect_regression(field, values) or ""
            print(
                f"  {field:<35} {min(values):>10.4g} {max(values):>10.4g} "
                f"{values[-1]:>10.4g}  {alert}"
            )
            rows += 1

    return rows


def plot_chart(
    design: str,
    domain_series: dict[str, dict[str, list[tuple[str, float]]]],
    min_runs: int,
    output_file: str | None,
) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print(
            "[error] matplotlib is not installed. Install it with:\n"
            "  pip install matplotlib\n"
            "Or run without --plot for a text-only table.",
            file=sys.stderr,
        )
        sys.exit(2)

    # Collect all (domain, field, points) with enough data
    plots = []
    for domain, series in sorted(domain_series.items()):
        for field, points in sorted(series.items()):
            if len(points) >= min_runs:
                plots.append((domain, field, points))

    if not plots:
        print("[warn] No series with enough runs to plot.", file=sys.stderr)
        return

    ncols = 2
    nrows = (len(plots) + 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(14, 4 * nrows), squeeze=False)
    fig.suptitle(f"QoR Trends — Design: {design}", fontsize=14, fontweight="bold")

    for idx, (domain, field, points) in enumerate(plots):
        ax = axes[idx // ncols][idx % ncols]
        xs = list(range(1, len(points) + 1))
        ys = [v for _, v in points]
        labels = [ts[:10] if ts else str(i) for i, (ts, _) in enumerate(points, 1)]

        ax.plot(xs, ys, marker="o", linewidth=1.5)
        ax.set_title(f"{domain} / {field}", fontsize=9)
        ax.set_xlabel("Run #")
        ax.set_ylabel(field)
        ax.set_xticks(xs)
        ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=7)
        ax.grid(True, linestyle="--", alpha=0.5)

        # Highlight regression
        if len(ys) >= 2:
            alert = detect_regression(field, ys)
            if alert:
                ax.axvline(x=xs[-1], color="red", linestyle=":", linewidth=1.2)
                ax.set_title(f"{domain} / {field}  ⚠", fontsize=9, color="red")

    # Hide unused subplots
    for idx in range(len(plots), nrows * ncols):
        axes[idx // ncols][idx % ncols].set_visible(False)

    plt.tight_layout()

    if output_file:
        plt.savefig(output_file, dpi=150, bbox_inches="tight")
        print(f"Chart saved to: {output_file}")
    else:
        plt.show()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="QoR metric trending across chip-design orchestrator runs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--design", required=True, metavar="NAME", help="Design name to filter")
    parser.add_argument(
        "--domain",
        metavar="DOMAIN",
        choices=VALID_DOMAINS,
        default=None,
        help="Limit to one domain (default: all)",
    )
    parser.add_argument(
        "--metric",
        metavar="FIELD",
        default=None,
        help="Specific metric field to show (default: all numeric fields)",
    )
    parser.add_argument("--plot", action="store_true", help="Show matplotlib chart")
    parser.add_argument(
        "--output",
        metavar="FILE",
        default=None,
        help="Save chart to FILE instead of displaying (implies --plot)",
    )
    parser.add_argument(
        "--memory-root",
        metavar="PATH",
        default=None,
        help="Path to the memory/ directory",
    )
    parser.add_argument(
        "--min-runs",
        type=int,
        default=2,
        metavar="N",
        help="Minimum runs required to include a series (default: 2)",
    )
    args = parser.parse_args()

    # Resolve memory root
    if args.memory_root:
        memory_root = Path(args.memory_root)
    else:
        try:
            memory_root = find_memory_root(Path(__file__))
        except FileNotFoundError as exc:
            print(f"[error] {exc}", file=sys.stderr)
            sys.exit(2)

    if not memory_root.is_dir():
        print(f"[error] memory root not found: {memory_root}", file=sys.stderr)
        sys.exit(2)

    domains = [args.domain] if args.domain else VALID_DOMAINS

    # Load and filter records
    domain_series: dict[str, dict[str, list[tuple[str, float]]]] = {}
    total_runs = 0
    for domain in domains:
        all_records = load_domain_records(memory_root, domain)
        design_records = filter_by_design(all_records, args.design)
        if not design_records:
            continue
        series = extract_series(design_records, domain, args.metric)
        if series:
            domain_series[domain] = series
            total_runs += len(design_records)

    if not domain_series:
        print(
            f"No runs found for design '{args.design}'"
            + (f" in domain '{args.domain}'" if args.domain else "")
            + ".\n"
            f"Check that the design name matches exactly what orchestrators recorded\n"
            f"in memory/<domain>/experiences.jsonl (field: 'design_name').",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"\nQoR Trend Report")
    print(f"Design:      {args.design}")
    print(f"Total runs:  {total_runs}")
    print(f"Domains:     {', '.join(sorted(domain_series))}")
    if args.metric:
        print(f"Metric filter: {args.metric}")

    rows = print_table(args.design, domain_series, args.min_runs)

    if rows == 0:
        print(
            f"\n[info] No series met the --min-runs={args.min_runs} threshold. "
            "Try --min-runs 1 to see single-run data."
        )

    if args.output or args.plot:
        plot_chart(args.design, domain_series, args.min_runs, args.output)


if __name__ == "__main__":
    main()
