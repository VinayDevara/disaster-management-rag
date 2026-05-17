"""
Multi-Run Benchmark Analysis
=============================
Reads all benchmark_runs/run_*.json files, computes mean ± standard error
for every metric, and prints a clean summary + updates benchmark_summary.md.

Usage:
    python analyze_multirun.py
"""

import json
import os
import glob
import math
from collections import defaultdict
from statistics import mean, stdev

RUNS_DIR = "benchmark_runs"
QUERIES_FILE = "benchmark_queries.json"
SUMMARY_FILE = "benchmark_summary.md"


def load_runs():
    """Load all run_*.json files from benchmark_runs/."""
    pattern = os.path.join(RUNS_DIR, "run_*.json")
    files = sorted(f for f in glob.glob(pattern) if "_metrics" not in os.path.basename(f))
    if not files:
        print(f"No run files found in {RUNS_DIR}/")
        return []
    runs = []
    for f in files:
        with open(f, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        run_name = os.path.basename(f).replace(".json", "")
        runs.append({"name": run_name, "results": data})
        print(f"  Loaded {run_name}: {len(data)} queries")
    return runs


def load_queries():
    with open(QUERIES_FILE, "r", encoding="utf-8") as f:
        return {q["id"]: q for q in json.load(f)}


def compute_run_metrics(results, qmap):
    """Compute all metrics for a single run. Returns a dict of floats."""
    n = len(results)

    # Routing accuracy (Cat A-D)
    route_correct = 0
    route_total = 0
    for r in results:
        q = qmap[r["id"]]
        if r["category"] in ("A", "B", "C", "D"):
            expected = set(q.get("expected_agents", []))
            actual = set(r["agents_invoked"])
            route_total += 1
            if expected and expected.issubset(actual):
                route_correct += 1

    # Tool selection (Cat A-D)
    tool_hit = sum(1 for r in results if r["category"] in ("A", "B", "C", "D") and r["tools_called"])
    tool_total = sum(1 for r in results if r["category"] in ("A", "B", "C", "D"))

    # Edge-case resilience (Cat E+F)
    edge_ok = sum(1 for r in results if r["category"] in ("E", "F") and not r["crashed"])
    edge_total = sum(1 for r in results if r["category"] in ("E", "F"))

    # Response rate
    resp_ok = sum(1 for r in results if r["got_response"])

    # Crash-free
    no_crash = sum(1 for r in results if not r["crashed"])

    # Fallback rate
    fallback_count = sum(1 for r in results if r["fallback_used"])

    # Latency
    times = [r["response_time_sec"] for r in results if r["response_time_sec"] > 0]
    avg_latency = mean(times) if times else 0

    # Latency by category
    cat_latency = {}
    for cat in "ABCDEF":
        cat_times = [r["response_time_sec"] for r in results
                     if r["category"] == cat and r["response_time_sec"] > 0]
        cat_latency[f"latency_{cat}"] = mean(cat_times) if cat_times else 0

    # Tools invoked
    all_tools = set()
    total_tools = 0
    for r in results:
        for t in r["tools_called"]:
            all_tools.add(t)
        total_tools += len(r["tools_called"])

    # Consensus applied
    consensus_count = sum(1 for r in results if r.get("consensus_applied"))

    # Total execution time
    total_exec_time = sum(r["response_time_sec"] for r in results)

    # Semantic relevance (import scoring from benchmark)
    try:
        from benchmark import semantic_score
        sem_scores = []
        for r in results:
            _, _, combined = semantic_score(r["query"], r["tools_called"], r["agents_invoked"])
            sem_scores.append(combined)
        sem_mean = mean(sem_scores) if sem_scores else 0
    except ImportError:
        sem_mean = 0

    metrics = {
        "routing_accuracy": route_correct / route_total * 100 if route_total else 0,
        "tool_selection": tool_hit / tool_total * 100 if tool_total else 0,
        "edge_resilience": edge_ok / edge_total * 100 if edge_total else 0,
        "response_rate": resp_ok / n * 100 if n else 0,
        "crash_free": no_crash / n * 100 if n else 0,
        "fallback_rate": fallback_count / n * 100 if n else 0,
        "avg_latency": avg_latency,
        "total_tool_invocations": total_tools,
        "unique_tools_invoked": len(all_tools),
        "consensus_rate": consensus_count / n * 100 if n else 0,
        "total_execution_time": total_exec_time,
        "semantic_relevance": sem_mean,
    }
    metrics.update(cat_latency)

    # Per-query latency (for per-query ± error)
    per_query_time = {r["id"]: r["response_time_sec"] for r in results}
    metrics["_per_query_time"] = per_query_time

    # Per-query routing correctness
    per_query_route = {}
    for r in results:
        q = qmap[r["id"]]
        if r["category"] in ("A", "B", "C", "D"):
            expected = set(q.get("expected_agents", []))
            actual = set(r["agents_invoked"])
            per_query_route[r["id"]] = 1 if expected.issubset(actual) else 0
    metrics["_per_query_route"] = per_query_route

    return metrics


def mean_se(values):
    """Compute mean ± standard error."""
    n = len(values)
    if n == 0:
        return 0, 0
    m = mean(values)
    if n == 1:
        return m, 0
    se = stdev(values) / math.sqrt(n)
    return m, se


def fmt(m, se, is_pct=True, decimals=1):
    """Format as mean ± SE string."""
    if is_pct:
        return f"{m:.{decimals}f} ± {se:.{decimals}f}%"
    else:
        return f"{m:.{decimals}f} ± {se:.{decimals}f}"


def print_multirun_report(all_metrics, n_runs):
    """Print console report and return markdown lines."""
    W = 80
    print(f"\n{'=' * W}")
    print(f"  MULTI-RUN BENCHMARK ANALYSIS  ({n_runs} runs)")
    print(f"{'=' * W}")

    # Aggregate each metric across runs
    metric_keys = [
        ("routing_accuracy",  "Routing Accuracy (A-D)",   True),
        ("tool_selection",    "Tool Selection (A-D)",      True),
        ("edge_resilience",   "Edge/Fallback Resilience",  True),
        ("response_rate",     "Response Rate",             True),
        ("crash_free",        "Crash-Free Rate",           True),
        ("fallback_rate",     "Fallback Rate",             True),
        ("avg_latency",       "Avg Latency (s)",           False),
        ("consensus_rate",    "Consensus Rate",            True),
        ("unique_tools_invoked", "Unique Tools Invoked",    False),
        ("total_tool_invocations", "Total Tool Invocations", False),
        ("total_execution_time", "Total Execution Time (s)", False),
        ("semantic_relevance", "Semantic Relevance Score",  False),
    ]

    print(f"\n  {'Metric':<30s}  {'Mean ± SE':>20s}  {'Per-Run Values'}")
    print(f"  {'─' * 30}  {'─' * 20}  {'─' * 30}")

    md_rows = []

    for key, label, is_pct in metric_keys:
        values = [m[key] for m in all_metrics]
        m, se = mean_se(values)
        per_run = "  ".join(f"R{i+1}={v:.1f}" for i, v in enumerate(values))
        result_str = fmt(m, se, is_pct)
        print(f"  {label:<30s}  {result_str:>20s}  {per_run}")
        md_rows.append((label, result_str))

    # Category latency
    print(f"\n  {'Latency by Category':}")
    print(f"  {'Category':<12s}  {'Mean ± SE (s)':>16s}  {'Per-Run'}")
    print(f"  {'─' * 12}  {'─' * 16}  {'─' * 30}")

    cat_names = {
        "A": "Single Agent", "B": "Multi-Tool", "C": "Multi-Agent",
        "D": "Decomposition", "E": "Edge Cases", "F": "Fallback",
    }

    cat_md_rows = []
    for cat in "ABCDEF":
        key = f"latency_{cat}"
        values = [m[key] for m in all_metrics]
        m, se = mean_se(values)
        per_run = "  ".join(f"R{i+1}={v:.1f}" for i, v in enumerate(values))
        result_str = f"{m:.1f} ± {se:.1f}s"
        print(f"  Cat {cat} {cat_names[cat]:<12s}  {result_str:>16s}  {per_run}")
        cat_md_rows.append((f"{cat} – {cat_names[cat]}", result_str))

    # Per-query latency across runs
    print(f"\n  Per-Query Latency (mean ± SE across {n_runs} runs):")
    print(f"  {'Q#':>4s}  {'Cat':>3s}  {'Mean ± SE (s)':>16s}  {'Per-Run'}")
    print(f"  {'─' * 4}  {'─' * 3}  {'─' * 16}  {'─' * 30}")

    query_ids = sorted(all_metrics[0]["_per_query_time"].keys())
    pq_md_rows = []
    for qid in query_ids:
        values = [m["_per_query_time"].get(qid, 0) for m in all_metrics]
        m, se = mean_se(values)
        cat = None
        for run_m in all_metrics:
            # find category from first run that has this query
            break
        # Use first run to get category
        per_run = "  ".join(f"{v:.1f}" for v in values)
        print(f"  Q{qid:02d}        {m:>6.1f} ± {se:>4.1f}s      {per_run}")
        pq_md_rows.append((qid, f"{m:.1f} ± {se:.1f}"))

    # Per-query routing consistency 
    print(f"\n  Routing Consistency (Cat A-D across {n_runs} runs):")
    print(f"  {'Q#':>4s}  {'Correct in N runs':>20s}  {'Consistency'}")
    print(f"  {'─' * 4}  {'─' * 20}  {'─' * 20}")

    route_qids = sorted(all_metrics[0].get("_per_query_route", {}).keys())
    for qid in route_qids:
        values = [m["_per_query_route"].get(qid, 0) for m in all_metrics]
        correct_count = sum(values)
        consistency = correct_count / n_runs * 100
        bar = "█" * correct_count + "░" * (n_runs - correct_count)
        label = "stable" if consistency == 100 else ("flaky" if consistency > 0 else "always wrong")
        print(f"  Q{qid:02d}  {correct_count}/{n_runs}                   {bar}  {label}")

    print(f"\n{'=' * W}")
    print(f"  Analysis complete. {n_runs} runs aggregated.")
    print(f"{'=' * W}\n")

    return md_rows, cat_md_rows, pq_md_rows


def write_summary(md_rows, cat_md_rows, pq_md_rows, n_runs, all_metrics, qmap):
    """Write/overwrite benchmark_summary.md with ± error values."""

    # Load first run to get query text
    first_run = all_metrics[0]
    # Read original queries for text
    with open(QUERIES_FILE, "r", encoding="utf-8") as f:
        queries = json.load(f)
    query_text = {q["id"]: q["query"] for q in queries}

    lines = []
    lines.append("# DisasterRAG Benchmark Summary")
    lines.append("")
    lines.append(f"**Aggregated from {n_runs} independent runs** — values shown as mean ± standard error.")
    lines.append("")

    lines.append("## Category Descriptions")
    lines.append("")
    lines.append("| Category | Name | Description |")
    lines.append("|----------|------|-------------|")
    lines.append("| A | Single Agent / Single Tool | Simple queries needing one agent with one tool |")
    lines.append("| B | Single Agent / Multi-Tool | Queries needing one agent but multiple tools |")
    lines.append("| C | Multi-Agent | Queries spanning multiple domains requiring coordination |")
    lines.append("| D | Decomposition | Complex queries broken into sub-queries across agents |")
    lines.append("| E | Edge Cases | Invalid, vague, off-topic, or empty inputs to test resilience |")
    lines.append("| F | Fallback Triggers | Unreasonable queries to test graceful degradation |")
    lines.append("")

    lines.append("## Overall Metrics")
    lines.append("")
    lines.append("| Metric | Result |")
    lines.append("|--------|--------|")
    lines.append(f"| Runs Aggregated | {n_runs} |")
    for label, result in md_rows:
        lines.append(f"| {label} | {result} |")
    lines.append("")

    lines.append("## Latency by Category")
    lines.append("")
    lines.append("| Category | Mean ± SE |")
    lines.append("|----------|-----------|")
    for label, result in cat_md_rows:
        lines.append(f"| {label} | {result} |")
    lines.append("")

    lines.append("## Per-Query Latency")
    lines.append("")
    lines.append("| Q# | Query | Latency (mean ± SE) |")
    lines.append("|----|-------|---------------------|")
    for qid, result in pq_md_rows:
        qt = query_text.get(qid, "") or "(empty)"
        qt_short = qt[:50] + ".." if len(qt) > 50 else qt
        lines.append(f"| Q{qid} | {qt_short} | {result}s |")
    lines.append("")

    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Updated {SUMMARY_FILE} with ± error values from {n_runs} runs.")


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    print("Loading benchmark runs...")
    runs = load_runs()

    if not runs:
        print("No runs found. Run the benchmark first:")
        print("  python benchmark.py --run 1 --delay 65")
        print("  python benchmark.py --run 2 --delay 65")
        print("  python benchmark.py --run 3 --delay 65")
        return

    n_runs = len(runs)
    print(f"\nFound {n_runs} run(s).\n")

    if n_runs < 2:
        print("WARNING: Only 1 run found. Standard error will be 0.")
        print("Run more benchmarks with: python benchmark.py --run 2 --delay 65\n")

    qmap = load_queries()

    # Compute metrics for each run
    all_metrics = []
    for run in runs:
        metrics = compute_run_metrics(run["results"], qmap)
        all_metrics.append(metrics)

    # Print report and get markdown data
    md_rows, cat_md_rows, pq_md_rows = print_multirun_report(all_metrics, n_runs)

    # Write updated summary
    write_summary(md_rows, cat_md_rows, pq_md_rows, n_runs, all_metrics, qmap)


if __name__ == "__main__":
    main()
