"""
DisasterRAG Extended Benchmark Suite — 100 Queries
====================================================
Same strategy as benchmark.py but uses:
  - benchmark_queries_100.json   (input)
  - benchmark_results_100.json   (output results)
  - benchmark_report_100.md      (output report)
  - benchmark_results_100_metrics.json

Usage:
    python benchmark_100.py                   # All 100 queries
    python benchmark_100.py --delay 30        # Shorter delay
    python benchmark_100.py --start 1 --end 20
    python benchmark_100.py --resume
"""

import sys, os, json, time, re, io, argparse, traceback
from datetime import datetime
from statistics import mean, median

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

QUERY_FILE  = "benchmark_queries_100.json"
RESULT_FILE = "benchmark_results_100.json"
REPORT_FILE = "benchmark_report_100.md"
RUNS_DIR    = "benchmark_runs_100"

# ── stdout capture ───────────────────────────────────────────────────────────

class OutputCapture:
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


# ── helpers ──────────────────────────────────────────────────────────────────

def parse_tools_from_output(text):
    tools = set()
    for m in re.finditer(r"Tool:\s+([a-z][a-z0-9_]+)", text):
        tools.add(m.group(1))
    for m in re.finditer(r"Tool\s+([a-z][a-z0-9_]+)\s+executed", text):
        tools.add(m.group(1))
    return sorted(tools)


def parse_fallback(text):
    return (
        "Falling back to direct tool queries" in text
        or "Falling back to Flight Agent as backup orchestrator" in text
    )


def run_single_query(system, query_text):
    with OutputCapture() as cap:
        try:
            result = system.process_query(query_text)
            return result, cap.getvalue(), None
        except Exception as e:
            return None, cap.getvalue(), f"{type(e).__name__}: {e}"


def extract_response_text(result):
    if result is None:
        return ""
    final = result.get("final_response", {})
    if isinstance(final, dict):
        for key in ("answer", "unified_response", "raw_output"):
            if key in final and final[key]:
                return str(final[key])
        return json.dumps(final, default=str)
    return str(final)


# ── semantic scoring ─────────────────────────────────────────────────────────

AGENT_DOMAIN_KEYWORDS = {
    "weather":  ["weather","temperature","rain","rainfall","wind","humidity",
                 "forecast","storm","cyclone","precipitation","climate","cloud",
                 "sea","visibility","landslide","gpm","pressure"],
    "disaster": ["disaster","flood","earthquake","alert","gdacs","sachet",
                 "landslide","emergency","risk","severity","relief","hazard",
                 "cyclone","rescue"],
    "flight":   ["flight","fly","airport","aircraft","plane","aviation",
                 "mangalore","disruption","squawk","callsign","airborne"],
}

TOOL_DOMAIN = {
    "get_current_weather":           ["weather","temperature","wind","humidity","conditions"],
    "get_forecast":                  ["forecast","weather","tomorrow","next","predict"],
    "get_weather_by_city":           ["weather","city","conditions"],
    "get_openmeteo_forecasts":       ["forecast","weather","predict","next"],
    "get_gpm_rainfall":              ["rainfall","rain","precipitation","gpm"],
    "get_heavy_rainfall":            ["rain","heavy","rainfall","precipitation"],
    "get_high_precipitation_forecasts": ["rain","precipitation","forecast"],
    "get_weather_events_in_area":    ["weather","events","area","storm"],
    "vector_search_weather":         ["weather","search","similar"],
    "get_active_events":             ["disaster","events","active","alert"],
    "get_active_official_alerts":    ["alert","official","warning","sachet"],
    "get_events_by_category":        ["disaster","flood","cyclone","earthquake","category"],
    "get_gdacs_events":              ["gdacs","disaster","global"],
    "get_gdacs_events_by_severity":  ["gdacs","severity","disaster","alert"],
    "get_recent_disasters":          ["disaster","recent","event"],
    "get_disaster_events_by_type":   ["disaster","type","flood","cyclone"],
    "get_official_alerts":           ["alert","official","sachet","warning"],
    "vector_search_disasters":       ["disaster","search","similar"],
    "get_high_risk_landslide":       ["landslide","risk","slope"],
    "get_landslide_snapshot":        ["landslide","snapshot","risk"],
    "get_all_flights":               ["flight","plane","aircraft","fly"],
    "get_flights_in_area":           ["flight","area","near"],
    "get_flights_near_location":     ["flight","near","location","mangalore"],
    "get_flight_by_callsign":        ["flight","callsign"],
    "get_flight_by_hex":             ["flight","hex","icao"],
    "get_flight_trajectory":         ["flight","trajectory","path"],
    "get_emergency_flights":         ["emergency","flight","squawk"],
    "vector_search_flights":         ["flight","search","similar"],
}


def semantic_score(query_text, tools_called, agents_invoked):
    q = query_text.lower()
    if not q.strip():
        return (1.0, 1.0, 1.0)
    query_domains = {a for a, kws in AGENT_DOMAIN_KEYWORDS.items() if any(k in q for k in kws)}
    if not query_domains:
        agent_rel = 1.0
    elif not agents_invoked:
        agent_rel = 0.0
    else:
        agent_rel = len(query_domains & set(agents_invoked)) / len(query_domains)
    if not tools_called:
        tool_rel = 0.5 if agents_invoked else 0.0
    else:
        scores = []
        for tool in tools_called:
            kws = TOOL_DOMAIN.get(tool, [])
            if kws:
                scores.append(min(sum(1 for k in kws if k in q) / max(len(kws), 1), 1.0))
            else:
                scores.append(0.3)
        tool_rel = mean(scores) if scores else 0.0
    return (round(tool_rel, 3), round(agent_rel, 3), round(0.6 * agent_rel + 0.4 * tool_rel, 3))


# ── scoring ───────────────────────────────────────────────────────────────────

def _pct(num, den):
    return num / den * 100 if den else 0


def score_results(results, queries):
    expected = {q["id"]: q for q in queries}
    s = dict(routing_correct=0, routing_total=0,
             tool_used=0, tool_expected=0,
             resilience_pass=0, resilience_total=0,
             responses=0, no_crash=0, total=len(results))
    all_tools, total_invoc, sem_scores = set(), 0, []
    consensus_count = fallback_count = 0

    for r in results:
        exp = expected[r["id"]]
        cat = r["category"]
        if not r["crashed"]:          s["no_crash"] += 1
        if r["got_response"]:         s["responses"] += 1
        if r.get("consensus_applied"): consensus_count += 1
        if r.get("fallback_used"):     fallback_count += 1
        for t in r["tools_called"]:   all_tools.add(t)
        total_invoc += len(r["tools_called"])
        _, _, combined = semantic_score(r["query"], r["tools_called"], r["agents_invoked"])
        sem_scores.append(combined)

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
            if not r["crashed"]:
                s["routing_correct"] += 1

        if cat in ("E", "F"):
            s["resilience_total"] += 1
            if not r["crashed"]:
                s["resilience_pass"] += 1

    total_time = sum(r["response_time_sec"] for r in results)
    s.update(
        total_execution_time=round(total_time, 1),
        average_latency=round(total_time / len(results), 1) if results else 0,
        fallback_triggered_pct=round(fallback_count / len(results) * 100, 1) if results else 0,
        consensus_applied_pct=round(consensus_count / len(results) * 100, 1) if results else 0,
        unique_tools_invoked=len(all_tools),
        total_tool_invocations=total_invoc,
        semantic_relevance_score=round(mean(sem_scores), 3) if sem_scores else 0,
        fallback_count=fallback_count,
        consensus_count=consensus_count,
    )
    return s


# ── report ────────────────────────────────────────────────────────────────────

CAT_NAMES = {
    "A": "Single Agent / Single Tool",
    "B": "Single Agent / Multi-Tool",
    "C": "Multi-Agent",
    "D": "Decomposition Required",
    "E": "Edge Cases / Ambiguous",
    "F": "Fallback Triggers",
}


def build_report(results, queries, scores):
    expected = {q["id"]: q for q in queries}
    cat_bucket = {}
    for r in results:
        cat_bucket.setdefault(r["category"], []).append(r)

    routing_pct = _pct(scores["routing_correct"], scores["routing_total"])
    tool_pct    = _pct(scores["tool_used"],       scores["tool_expected"])
    resil_pct   = _pct(scores["resilience_pass"], scores["resilience_total"])
    resp_pct    = _pct(scores["responses"],        scores["total"])
    crash_pct   = _pct(scores["no_crash"],         scores["total"])

    single_t = [r["response_time_sec"] for r in (cat_bucket.get("A",[]) + cat_bucket.get("B",[])) if r["response_time_sec"] > 0]
    multi_t  = [r["response_time_sec"] for r in (cat_bucket.get("C",[]) + cat_bucket.get("D",[])) if r["response_time_sec"] > 0]
    avg_single = mean(single_t) if single_t else 0
    avg_multi  = mean(multi_t)  if multi_t  else 0

    L = []
    L.append("# DisasterRAG Extended Benchmark Report — 100 Queries\n")
    L.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  ")
    L.append(f"**Queries Executed:** {scores['total']}  ")
    L.append(f"**Total Execution Time:** {sum(r['response_time_sec'] for r in results):.1f}s  ")
    L.append("**Architecture:** CrewAI + DSPy | Local Ollama `qwen2.5:3b`  ")
    L.append("")

    L.append("## Overall Metrics\n")
    L.append("| Metric | Result |")
    L.append("|--------|--------|")
    L.append(f"| Total Queries | {scores['total']} |")
    L.append(f"| Total Execution Time | {scores['total_execution_time']} s |")
    L.append(f"| Average Latency | {scores['average_latency']} s |")
    L.append(f"| Routing Accuracy | {routing_pct:.1f}% |")
    L.append(f"| Tool Selection Rate | {tool_pct:.1f}% |")
    L.append(f"| Edge/Fallback Resilience | {resil_pct:.1f}% |")
    L.append(f"| Fallback Triggered | {scores['fallback_triggered_pct']}% |")
    L.append(f"| Consensus Applied | {scores['consensus_applied_pct']}% |")
    L.append(f"| Unique Tools Invoked | {scores['unique_tools_invoked']} |")
    L.append(f"| Total Tool Invocations | {scores['total_tool_invocations']} |")
    L.append(f"| Semantic Relevance Score | {scores['semantic_relevance_score']:.3f} |")
    L.append("")

    L.append("## Targets\n")
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

    L.append("## Latency by Category\n")
    L.append("| Category | Queries | Avg (s) | Min (s) | Max (s) | Median (s) |")
    L.append("|----------|---------|---------|---------|---------|------------|")
    for cat in "ABCDEF":
        times = [r["response_time_sec"] for r in cat_bucket.get(cat, []) if r["response_time_sec"] > 0] or [0]
        L.append(f"| {cat} — {CAT_NAMES[cat]} | {len(cat_bucket.get(cat,[]))} | "
                 f"{mean(times):.1f} | {min(times):.1f} | {max(times):.1f} | {median(times):.1f} |")
    L.append("")

    L.append("## Per-Query Results\n")
    L.append("| # | Cat | Query | Expected | Actual Agents | Tools | Fallback | Time | Status |")
    L.append("|---|-----|-------|----------|---------------|-------|----------|------|--------|")
    for r in results:
        exp = expected[r["id"]]
        exp_agents = set(exp.get("expected_agents", []))
        actual = set(r["agents_invoked"])
        if r["crashed"]:
            status = "❌ CRASH"
        elif r["category"] in ("A","B","C","D") and exp_agents and exp_agents.issubset(actual):
            status = "✅ PASS"
        elif r["category"] in ("E","F") and not r["crashed"]:
            status = "✅ PASS"
        elif r["category"] in ("A","B","C","D"):
            status = "⚠️ ROUTE"
        else:
            status = "⚠️"
        q_short = (r["query"][:35] + "..") if len(r["query"]) > 35 else (r["query"] or "(empty)")
        L.append(f"| Q{r['id']} | {r['category']} | {q_short} | "
                 f"{', '.join(exp.get('expected_agents',[])) or 'any'} | "
                 f"{', '.join(r['agents_invoked']) or '—'} | "
                 f"{len(r['tools_called'])} | {'Yes' if r['fallback_used'] else 'No'} | "
                 f"{r['response_time_sec']:.1f}s | {status} |")
    L.append("")

    L.append("## Category Breakdown\n")
    def _cat_pass(cat):
        if cat in "ABCD":
            return sum(1 for r in cat_bucket.get(cat,[])
                       if not r["crashed"]
                       and set(expected[r["id"]].get("expected_agents",[])).issubset(set(r["agents_invoked"])))
        return sum(1 for r in cat_bucket.get(cat,[]) if not r["crashed"])

    for cat in "ABCDEF":
        p = _cat_pass(cat)
        t = len(cat_bucket.get(cat, []))
        bar = "█" * p + "░" * (t - p)
        L.append(f"- **Category {cat}** ({CAT_NAMES[cat]}): **{p}/{t}** passed  `{bar}`")
    L.append("")

    return "\n".join(L)


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="DisasterRAG 100-Query Benchmark")
    parser.add_argument("--delay", type=int, default=30,
                        help="Seconds between queries (default: 30)")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end",   type=int, default=100)
    parser.add_argument("--resume", action="store_true",
                        help="Skip already-completed queries in benchmark_results_100.json")
    args = parser.parse_args()

    with open(QUERY_FILE, "r", encoding="utf-8") as f:
        all_queries = json.load(f)

    existing, completed_ids = [], set()
    if args.resume and os.path.exists(RESULT_FILE):
        with open(RESULT_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)
        completed_ids = {r["id"] for r in existing}
        print(f"Resuming: {len(completed_ids)} already done, skipping.")

    queries_to_run = [
        q for q in all_queries
        if args.start <= q["id"] <= args.end and q["id"] not in completed_ids
    ]

    if not queries_to_run:
        print("No new queries to run.")
        if existing:
            scores = score_results(existing, all_queries)
            report = build_report(existing, all_queries, scores)
            with open(REPORT_FILE, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"Report saved: {REPORT_FILE}")
        return

    total_est = len(queries_to_run) * (args.delay + 35)
    print(f"\n{'='*80}")
    print(f"  DisasterRAG Extended Benchmark — 100 Queries")
    print(f"  Queries: {len(queries_to_run)} (Q{queries_to_run[0]['id']}–Q{queries_to_run[-1]['id']})")
    print(f"  Delay: {args.delay}s between queries")
    print(f"  Estimated time: ~{total_est // 60}m {total_est % 60}s")
    print(f"{'='*80}\n")

    print("Initializing DisasterRAGSystem...")
    from main import DisasterRAGSystem
    system = DisasterRAGSystem()
    print("System ready.\n")

    results = list(existing)

    for i, q in enumerate(queries_to_run):
        qid, query_text, cat = q["id"], q["query"], q["category"]
        print(f"\n{'='*80}")
        print(f"  [{i+1}/{len(queries_to_run)}]  Q{qid}  Category {cat} — {CAT_NAMES[cat]}")
        print(f"  \"{query_text}\"")
        print(f"{'='*80}\n")

        t0 = time.time()

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
            tools   = parse_tools_from_output(captured)
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
                meta    = result.get("metadata", {})
                cls_info = result.get("classification", {})
                resp    = extract_response_text(result)
                entry   = {
                    "id": qid, "query": query_text, "category": cat,
                    "agents_invoked": meta.get("agents_used", []),
                    "tools_called": tools,
                    "fallback_used": fallback,
                    "response_time_sec": elapsed,
                    "got_response": bool(resp),
                    "response_length": len(str(resp)),
                    "crashed": False, "error": None,
                    "classification_type": cls_info.get("query_type", "unknown"),
                    "consensus_applied": meta.get("consensus_applied", False),
                }

        results.append(entry)

        # Save incrementally
        with open(RESULT_FILE, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        tag = "CRASH" if entry["crashed"] else "OK"
        print(f"\n  >> {tag} | agents={entry['agents_invoked']} "
              f"tools={len(entry['tools_called'])} fallback={entry['fallback_used']} "
              f"time={entry['response_time_sec']}s resp={entry['response_length']}ch")

        if i < len(queries_to_run) - 1:
            print(f"  >> Waiting {args.delay}s...")
            time.sleep(args.delay)

    # Final report
    all_results = sorted(results, key=lambda r: r["id"])
    scores  = score_results(all_results, all_queries)
    report  = build_report(all_results, all_queries, scores)

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report)

    metrics = {
        "total_queries":               scores["total"],
        "total_execution_time":        scores["total_execution_time"],
        "average_latency":             scores["average_latency"],
        "routing_accuracy_pct":        round(_pct(scores["routing_correct"],  scores["routing_total"]),  1),
        "tool_selection_rate_pct":     round(_pct(scores["tool_used"],        scores["tool_expected"]),  1),
        "edge_fallback_resilience_pct":round(_pct(scores["resilience_pass"],  scores["resilience_total"]),1),
        "fallback_triggered_pct":      scores["fallback_triggered_pct"],
        "consensus_applied_pct":       scores["consensus_applied_pct"],
        "unique_tools_invoked":        scores["unique_tools_invoked"],
        "total_tool_invocations":      scores["total_tool_invocations"],
        "semantic_relevance_score":    scores["semantic_relevance_score"],
        "response_rate_pct":           round(_pct(scores["responses"], scores["total"]), 1),
        "crash_free_pct":              round(_pct(scores["no_crash"],  scores["total"]), 1),
    }
    metrics_file = RESULT_FILE.replace(".json", "_metrics.json")
    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(f"\n{'='*80}")
    print("  BENCHMARK COMPLETE (100 QUERIES)")
    print(f"{'='*80}")
    rt, te, re_ = scores["routing_total"], scores["tool_expected"], scores["resilience_total"]
    t = scores["total"]
    print(f"  Total Queries:         {t}")
    print(f"  Total Execution Time:  {scores['total_execution_time']}s")
    print(f"  Average Latency:       {scores['average_latency']}s")
    print(f"  Routing Accuracy:      {scores['routing_correct']}/{rt} = {_pct(scores['routing_correct'],rt):.0f}%")
    print(f"  Tool Selection Rate:   {scores['tool_used']}/{te} = {_pct(scores['tool_used'],te):.0f}%")
    print(f"  Edge/Fallback Resil.:  {scores['resilience_pass']}/{re_} = {_pct(scores['resilience_pass'],re_):.0f}%")
    print(f"  Semantic Relevance:    {scores['semantic_relevance_score']:.3f}")
    print(f"  Response Rate:         {scores['responses']}/{t} = {_pct(scores['responses'],t):.0f}%")
    print(f"  Crash-Free:            {scores['no_crash']}/{t} = {_pct(scores['no_crash'],t):.0f}%")
    print(f"\n  Results: {RESULT_FILE}")
    print(f"  Metrics: {metrics_file}")
    print(f"  Report:  {REPORT_FILE}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
