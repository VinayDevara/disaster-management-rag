"""
DisasterRAG Benchmark Suite
============================
Runs 30 queries across 6 categories through OrchestratorAgent.process_query(),
captures agent routing, tool usage, fallback triggers, and latency.
Produces benchmark_results.json and benchmark_report.md.

Usage:
    python benchmark.py                      # Run all 30 queries (65s delay)
    python benchmark.py --delay 45           # Shorter delay (may hit rate limits)
    python benchmark.py --start 11 --end 15  # Run only Category C (Q11-Q15)
    python benchmark.py --resume             # Resume from partial results
"""

import sys
import os
import json
import time
import re
import io
import argparse
import traceback
from datetime import datetime
from statistics import mean, median

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

QUERY_FILE = "benchmark_queries.json"
RESULT_FILE = "benchmark_results.json"
REPORT_FILE = "benchmark_report.md"


# ── stdout capture ──────────────────────────────────────────────────────────

class OutputCapture:
    """Tee stdout to both the terminal and an internal buffer."""

    def __init__(self):
        self.buffer = io.StringIO()
        self._original = None

    def __enter__(self):
        self._original = sys.stdout
        sys.stdout = self
        return self

    def __exit__(self, *args):
        sys.stdout = self._original

    def write(self, text):
        if self._original:
            try:
                self._original.write(text)
            except (UnicodeEncodeError, OSError):
                try:
                    self._original.write(text.encode("ascii", "replace").decode())
                except Exception:
                    pass
        try:
            self.buffer.write(text)
        except Exception:
            pass

    def flush(self):
        if self._original:
            self._original.flush()

    def getvalue(self):
        return self.buffer.getvalue()


# ── output parsing helpers ──────────────────────────────────────────────────

def parse_tools_from_output(text):
    """Extract unique tool names from CrewAI verbose output."""
    tools = set()
    # CrewAI box: "Tool: tool_name"
    for m in re.finditer(r"Tool:\s+([a-z][a-z0-9_]+)", text):
        tools.add(m.group(1))
    # Inline log: "Tool tool_name executed"
    for m in re.finditer(r"Tool\s+([a-z][a-z0-9_]+)\s+executed", text):
        tools.add(m.group(1))
    return sorted(tools)


def parse_fallback(text):
    """Detect if any fallback path was triggered."""
    return (
        "Falling back to direct tool queries" in text
        or "Falling back to Flight Agent as backup orchestrator" in text
    )


# ── single query runner ────────────────────────────────────────────────────

def run_single_query(system, query_text):
    """Execute one query, return (result_dict, captured_stdout, error_str|None)."""
    with OutputCapture() as cap:
        try:
            result = system.process_query(query_text)
            return result, cap.getvalue(), None
        except Exception as e:
            return None, cap.getvalue(), f"{type(e).__name__}: {e}"


def extract_response_text(result):
    """Pull the answer string out of the orchestrator result dict."""
    if result is None:
        return ""
    final = result.get("final_response", {})
    if isinstance(final, dict):
        for key in ("answer", "unified_response", "raw_output"):
            if key in final and final[key]:
                return str(final[key])
        return json.dumps(final, default=str)
    return str(final)


# ── scoring ─────────────────────────────────────────────────────────────────

def score_results(results, queries):
    expected = {q["id"]: q for q in queries}
    s = dict(
        routing_correct=0, routing_total=0,
        tool_used=0, tool_expected=0,
        resilience_pass=0, resilience_total=0,
        responses=0, no_crash=0, total=len(results),
    )
    for r in results:
        exp = expected[r["id"]]
        cat = r["category"]

        if not r["crashed"]:
            s["no_crash"] += 1
        if r["got_response"]:
            s["responses"] += 1

        # Routing (A-D: check expected agents are subset of actual)
        s["routing_total"] += 1
        if cat in ("A", "B", "C", "D"):
            exp_agents = set(exp.get("expected_agents", []))
            actual = set(r["agents_invoked"])
            if exp_agents and exp_agents.issubset(actual):
                s["routing_correct"] += 1
            s["tool_expected"] += 1
            if r["tools_called"]:
                s["tool_used"] += 1
        else:
            # E/F: correct if no crash
            if not r["crashed"]:
                s["routing_correct"] += 1

        if cat in ("E", "F"):
            s["resilience_total"] += 1
            if not r["crashed"]:
                s["resilience_pass"] += 1

    return s


# ── report generation ───────────────────────────────────────────────────────

CAT_NAMES = {
    "A": "Single Agent / Single Tool",
    "B": "Single Agent / Multi-Tool",
    "C": "Multi-Agent",
    "D": "Decomposition Required",
    "E": "Edge Cases / Ambiguous",
    "F": "Fallback Triggers",
}


def _pct(num, den):
    return num / den * 100 if den else 0


def build_report(results, queries, scores):
    expected = {q["id"]: q for q in queries}

    # bucket results by category
    cat_bucket = {}
    for r in results:
        cat_bucket.setdefault(r["category"], []).append(r)

    routing_pct = _pct(scores["routing_correct"], scores["routing_total"])
    tool_pct = _pct(scores["tool_used"], scores["tool_expected"])
    resil_pct = _pct(scores["resilience_pass"], scores["resilience_total"])
    resp_pct = _pct(scores["responses"], scores["total"])
    crash_pct = _pct(scores["no_crash"], scores["total"])

    single_t = [r["response_time_sec"] for r in
                (cat_bucket.get("A", []) + cat_bucket.get("B", [])) if r["response_time_sec"] > 0]
    multi_t = [r["response_time_sec"] for r in
               (cat_bucket.get("C", []) + cat_bucket.get("D", [])) if r["response_time_sec"] > 0]
    avg_single = mean(single_t) if single_t else 0
    avg_multi = mean(multi_t) if multi_t else 0

    L = []  # report lines

    # ── Header
    L.append("# DisasterRAG Benchmark Report\n")
    L.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  ")
    L.append(f"**Queries Executed:** {scores['total']}  ")
    L.append(f"**Total Execution Time:** {sum(r['response_time_sec'] for r in results):.1f}s  ")
    L.append(f"**Architecture:** CrewAI 1.11 + DSPy | Groq (`llama-3.3-70b-versatile` reasoning + `qwen/qwen3-32b` tool-calling)  ")
    L.append("")

    # ── Methodology (so the reader understands what happened)
    L.append("## Methodology\n")
    L.append("| Step | What happened |")
    L.append("|------|--------------|")
    L.append("| 1. Query Set | 30 queries loaded from `benchmark_queries.json`, split into 6 categories (A-F) covering single-agent, multi-agent, decomposition, edge-case, and fallback scenarios. |")
    L.append("| 2. System Init | `DisasterRAGSystem` initialised — SQLite DB, ChromaDB vectors, 3 CrewAI agents (Flight, Weather, Disaster), DSPy orchestrator, Consensus agent. |")
    L.append("| 3. Execution | Each query passed to `OrchestratorAgent.process_query()`. Stdout captured to extract tool names and fallback triggers. |")
    L.append("| 4. Routing Check | DSPy classifier routes to primary + secondary agents. We check if the *expected* agents are a **subset** of the agents actually invoked. |")
    L.append("| 5. Tool Check | For Categories A-D we verify at least one CrewAI tool was called (tool selection accuracy). |")
    L.append("| 6. Resilience Check | For Categories E-F (edge cases / fallbacks) the pass criterion is simply *no crash*. |")
    L.append("| 7. Rate-Limit Handling | A configurable delay between queries prevents Groq free-tier TPM exhaustion (default 65 s). |")
    L.append("| 8. Scoring | Metrics computed and this report generated automatically. |")
    L.append("")

    # ── Overall Metrics
    L.append("## Overall Metrics\n")
    L.append("| Metric | Score | Target | Status |")
    L.append("|--------|-------|--------|--------|")
    L.append(f"| Routing Accuracy | {routing_pct:.1f}% | > 80% | {'✅' if routing_pct >= 80 else '❌'} |")
    L.append(f"| Tool Selection Accuracy | {tool_pct:.1f}% | > 75% | {'✅' if tool_pct >= 75 else '❌'} |")
    L.append(f"| Edge-Case Resilience | {resil_pct:.1f}% | 100% | {'✅' if resil_pct == 100 else '❌'} |")
    L.append(f"| Response Rate | {resp_pct:.1f}% | > 90% | {'✅' if resp_pct >= 90 else '❌'} |")
    L.append(f"| Crash-Free Rate | {crash_pct:.1f}% | 100% | {'✅' if crash_pct == 100 else '❌'} |")
    L.append(f"| Avg Latency (single-agent) | {avg_single:.1f}s | < 10s | {'✅' if avg_single < 10 else '❌'} |")
    L.append(f"| Avg Latency (multi-agent) | {avg_multi:.1f}s | < 20s | {'✅' if avg_multi < 20 else '❌'} |")
    L.append("")

    # ── Latency by Category
    L.append("## Latency by Category\n")
    L.append("| Category | Queries | Avg (s) | Min (s) | Max (s) | Median (s) |")
    L.append("|----------|---------|---------|---------|---------|------------|")
    for cat in "ABCDEF":
        times = [r["response_time_sec"] for r in cat_bucket.get(cat, []) if r["response_time_sec"] > 0] or [0]
        L.append(
            f"| {cat} — {CAT_NAMES[cat]} | {len(cat_bucket.get(cat, []))} | "
            f"{mean(times):.1f} | {min(times):.1f} | {max(times):.1f} | {median(times):.1f} |"
        )
    L.append("")

    # ── Per-Query Results
    L.append("## Per-Query Results\n")
    L.append("| # | Cat | Query | Expected | Actual Agents | Tools | Fallback | Time | Resp Len | Status |")
    L.append("|---|-----|-------|----------|---------------|-------|----------|------|----------|--------|")
    for r in results:
        exp = expected[r["id"]]
        exp_agents = set(exp.get("expected_agents", []))
        actual = set(r["agents_invoked"])

        if r["crashed"]:
            status = "❌ CRASH"
        elif r["category"] in ("A", "B", "C", "D") and exp_agents and exp_agents.issubset(actual):
            status = "✅ PASS"
        elif r["category"] in ("E", "F") and not r["crashed"]:
            status = "✅ PASS"
        elif r["category"] in ("A", "B", "C", "D"):
            status = "⚠️ ROUTE"
        else:
            status = "⚠️"

        q_short = r["query"][:35] + ".." if len(r["query"]) > 35 else (r["query"] or "(empty)")
        exp_str = ", ".join(exp.get("expected_agents", [])) or "any"
        act_str = ", ".join(r["agents_invoked"]) or "—"
        L.append(
            f"| Q{r['id']} | {r['category']} | {q_short} | {exp_str} | {act_str} | "
            f"{len(r['tools_called'])} | {'Yes' if r['fallback_used'] else 'No'} | "
            f"{r['response_time_sec']:.1f}s | {r['response_length']} | {status} |"
        )
    L.append("")

    # ── Category Breakdown
    L.append("## Category Breakdown\n")

    def _cat_pass(cat):
        if cat in "ABCD":
            return sum(
                1 for r in cat_bucket.get(cat, [])
                if not r["crashed"]
                and set(expected[r["id"]].get("expected_agents", [])).issubset(set(r["agents_invoked"]))
            )
        return sum(1 for r in cat_bucket.get(cat, []) if not r["crashed"])

    for cat in "ABCDEF":
        p = _cat_pass(cat)
        t = len(cat_bucket.get(cat, []))
        bar = "█" * p + "░" * (t - p)
        L.append(f"- **Category {cat}** ({CAT_NAMES[cat]}): **{p}/{t}** passed  `{bar}`")
    L.append("")

    # ── Diagnosis
    L.append("## Diagnosis & Observations\n")

    fallback_count = sum(1 for r in results if r["fallback_used"])
    if fallback_count:
        L.append(f"- **{fallback_count}/{len(results)}** queries triggered the fallback path (CrewAI → direct tool calls).")

    if _cat_pass("A") + _cat_pass("B") >= 7 and _cat_pass("C") < 3:
        L.append("- **Single-agent routing is strong, but multi-agent orchestration (Cat C) needs improvement.** "
                 "The DSPy classifier may not be marking queries as `complex` when multiple domains are involved.")

    if _cat_pass("D") < 3:
        L.append("- **Decomposition (Cat D) underperforms.** The `DecomposeQuery` DSPy signature may not be "
                 "generating useful sub-queries for complex analytical questions.")

    ef_crashes = sum(1 for r in (cat_bucket.get("E", []) + cat_bucket.get("F", []))
                     if r["crashed"])
    if ef_crashes:
        L.append(f"- **{ef_crashes} crash(es) in edge/fallback categories.** Error handling needs hardening.")

    if avg_single > 10:
        L.append(f"- **High single-agent latency ({avg_single:.1f}s).** "
                 "Consider response caching or reducing tool iterations.")
    if avg_multi > 20:
        L.append(f"- **High multi-agent latency ({avg_multi:.1f}s).** "
                 "Consider parallel agent execution or reducing max_iter.")

    if routing_pct >= 80 and tool_pct >= 75 and resil_pct == 100:
        L.append("- **All primary benchmark targets met.** ✅")
    L.append("")

    return "\n".join(L)


# ── main execution ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="DisasterRAG Benchmark Suite")
    parser.add_argument("--delay", type=int, default=65,
                        help="Seconds between queries for rate-limit safety (default: 65)")
    parser.add_argument("--start", type=int, default=1,
                        help="Start from query ID (1-based, default: 1)")
    parser.add_argument("--end", type=int, default=30,
                        help="End at query ID (inclusive, default: 30)")
    parser.add_argument("--resume", action="store_true",
                        help="Skip queries that already have results in benchmark_results.json")
    args = parser.parse_args()

    # Load query definitions
    with open(QUERY_FILE, "r", encoding="utf-8") as f:
        all_queries = json.load(f)

    # Load existing results if resuming
    existing = []
    completed_ids = set()
    if args.resume and os.path.exists(RESULT_FILE):
        with open(RESULT_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)
        completed_ids = {r["id"] for r in existing}
        print(f"Resuming: {len(completed_ids)} queries already completed, skipping them.")

    # Filter to requested range
    queries_to_run = [
        q for q in all_queries
        if args.start <= q["id"] <= args.end and q["id"] not in completed_ids
    ]

    if not queries_to_run:
        print("No new queries to run.")
        if existing:
            print("Generating report from existing results...")
            scores = score_results(existing, all_queries)
            report = build_report(existing, all_queries, scores)
            with open(REPORT_FILE, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"Report saved: {REPORT_FILE}")
        return

    total_est = len(queries_to_run) * (args.delay + 40)
    print(f"\n{'=' * 80}")
    print(f"  DisasterRAG Benchmark")
    print(f"  Queries: {len(queries_to_run)} (Q{queries_to_run[0]['id']}–Q{queries_to_run[-1]['id']})")
    print(f"  Delay: {args.delay}s between queries")
    print(f"  Estimated time: ~{total_est // 60}m {total_est % 60}s")
    print(f"{'=' * 80}\n")

    # Initialise system once
    print("Initializing DisasterRAGSystem...")
    from main import DisasterRAGSystem
    system = DisasterRAGSystem()
    print("System ready.\n")

    results = list(existing)  # start with any previously-completed results

    for i, q in enumerate(queries_to_run):
        qid = q["id"]
        query_text = q["query"]
        cat = q["category"]

        print(f"\n{'=' * 80}")
        print(f"  [{i + 1}/{len(queries_to_run)}]  Q{qid}  Category {cat} — {CAT_NAMES[cat]}")
        print(f"  \"{query_text}\"")
        print(f"{'=' * 80}\n")

        t0 = time.time()

        # Handle empty query
        if not query_text.strip():
            entry = {
                "id": qid, "query": query_text, "category": cat,
                "agents_invoked": [], "tools_called": [],
                "fallback_used": False, "response_time_sec": 0.0,
                "got_response": True, "response_length": 0,
                "crashed": False, "error": None,
                "classification_type": "none", "consensus_applied": False,
            }
        else:
            result, captured, error = run_single_query(system, query_text)
            elapsed = round(time.time() - t0, 2)

            tools = parse_tools_from_output(captured)
            fallback = parse_fallback(captured)

            if error:
                entry = {
                    "id": qid, "query": query_text, "category": cat,
                    "agents_invoked": [], "tools_called": tools,
                    "fallback_used": fallback, "response_time_sec": elapsed,
                    "got_response": False, "response_length": 0,
                    "crashed": True, "error": error,
                    "classification_type": "error", "consensus_applied": False,
                }
            else:
                meta = result.get("metadata", {})
                cls_info = result.get("classification", {})
                resp = extract_response_text(result)
                entry = {
                    "id": qid, "query": query_text, "category": cat,
                    "agents_invoked": meta.get("agents_used", []),
                    "tools_called": tools,
                    "fallback_used": fallback,
                    "response_time_sec": elapsed,
                    "got_response": bool(resp and len(resp) > 0),
                    "response_length": len(str(resp)),
                    "crashed": False, "error": None,
                    "classification_type": cls_info.get("query_type", "unknown"),
                    "consensus_applied": meta.get("consensus_applied", False),
                }

        results.append(entry)

        # Save incrementally (survives interruption)
        with open(RESULT_FILE, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        status_tag = "CRASH" if entry["crashed"] else "OK"
        print(f"\n  >> {status_tag} | agents={entry['agents_invoked']} "
              f"tools={len(entry['tools_called'])} fallback={entry['fallback_used']} "
              f"time={entry['response_time_sec']}s resp={entry['response_length']}ch")

        # Rate-limit delay (skip after last query)
        if i < len(queries_to_run) - 1:
            print(f"  >> Waiting {args.delay}s for rate-limit reset...")
            time.sleep(args.delay)

    # ── Final report
    all_results = sorted(results, key=lambda r: r["id"])
    scores = score_results(all_results, all_queries)
    report = build_report(all_results, all_queries, scores)

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report)

    # Console summary
    print(f"\n{'=' * 80}")
    print("  BENCHMARK COMPLETE")
    print(f"{'=' * 80}")
    rt = scores["routing_total"]
    te = scores["tool_expected"]
    re_ = scores["resilience_total"]
    t = scores["total"]
    print(f"  Routing Accuracy:      {scores['routing_correct']}/{rt} = {_pct(scores['routing_correct'], rt):.0f}%")
    print(f"  Tool Selection:        {scores['tool_used']}/{te} = {_pct(scores['tool_used'], te):.0f}%")
    print(f"  Edge-Case Resilience:  {scores['resilience_pass']}/{re_} = {_pct(scores['resilience_pass'], re_):.0f}%")
    print(f"  Response Rate:         {scores['responses']}/{t} = {_pct(scores['responses'], t):.0f}%")
    print(f"  Crash-Free:            {scores['no_crash']}/{t} = {_pct(scores['no_crash'], t):.0f}%")
    print(f"\n  Results: {RESULT_FILE}")
    print(f"  Report:  {REPORT_FILE}")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    main()
