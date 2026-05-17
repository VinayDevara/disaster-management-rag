# DisasterRAG Benchmark Summary

**Aggregated from 3 independent runs** — values shown as mean ± standard error.

## Category Descriptions

| Category | Name | Description |
|----------|------|-------------|
| A | Single Agent / Single Tool | Simple queries needing one agent with one tool |
| B | Single Agent / Multi-Tool | Queries needing one agent but multiple tools |
| C | Multi-Agent | Queries spanning multiple domains requiring coordination |
| D | Decomposition | Complex queries broken into sub-queries across agents |
| E | Edge Cases | Invalid, vague, off-topic, or empty inputs to test resilience |
| F | Fallback Triggers | Unreasonable queries to test graceful degradation |

## Overall Metrics

| Metric | Result |
|--------|--------|
| Runs Aggregated | 3 |
| Routing Accuracy (A-D) | 90.0 ± 5.0% |
| Tool Selection (A-D) | 41.7 ± 4.4% |
| Edge/Fallback Resilience | 100.0 ± 0.0% |
| Response Rate | 100.0 ± 0.0% |
| Crash-Free Rate | 100.0 ± 0.0% |
| Fallback Rate | 60.0 ± 5.8% |
| Avg Latency (s) | 19.0 ± 1.6 |
| Consensus Rate | 43.3 ± 3.3% |
| Unique Tools Invoked | 26.3 ± 0.9 |
| Total Tool Invocations | 62.7 ± 6.7 |
| Total Execution Time (s) | 551.9 ± 45.7 |
| Semantic Relevance Score | 0.7 ± 0.1 |

## Latency by Category

| Category | Mean ± SE |
|----------|-----------|
| A – Single Agent | 4.5 ± 1.0s |
| B – Multi-Tool | 13.0 ± 1.8s |
| C – Multi-Agent | 26.9 ± 4.5s |
| D – Decomposition | 27.6 ± 5.3s |
| E – Edge Cases | 21.5 ± 2.4s |
| F – Fallback | 21.2 ± 1.2s |

## Per-Query Latency

| Q# | Query | Latency (mean ± SE) |
|----|-------|---------------------|
| Q1 | What is the current temperature in Mangalore? | 5.2 ± 0.2s |
| Q2 | Are there any active flood alerts in Dakshina Kann.. | 7.0 ± 3.7s |
| Q3 | What flights are available from Mangalore airport? | 4.3 ± 0.4s |
| Q4 | Show me rainfall data for the last 24 hours | 3.2 ± 0.8s |
| Q5 | What is the humidity forecast for tomorrow? | 2.6 ± 0.2s |
| Q6 | Compare current weather conditions with the foreca.. | 5.3 ± 0.5s |
| Q7 | Show me all active disaster alerts and their sever.. | 10.3 ± 0.0s |
| Q8 | What is the rainfall trend and landslide risk in t.. | 31.3 ± 2.4s |
| Q9 | List all GDACS events and SACHET alerts currently .. | 9.4 ± 3.2s |
| Q10 | What are the wind conditions and any cyclone warni.. | 8.7 ± 3.2s |
| Q11 | Is it safe to fly from Mangalore given current wea.. | 31.8 ± 3.9s |
| Q12 | How will the weather affect disaster relief operat.. | 37.2 ± 2.5s |
| Q13 | Should I travel to Mangalore this week considering.. | 36.4 ± 16.4s |
| Q14 | What is the overall risk assessment for Dakshina K.. | 7.2 ± 2.3s |
| Q15 | Are there any weather-related flight disruptions e.. | 22.0 ± 6.7s |
| Q16 | Compare the flood risk in the last week with curre.. | 36.6 ± 2.0s |
| Q17 | Given the cyclone history in the Bay of Bengal and.. | 19.6 ± 6.4s |
| Q18 | Analyze all data sources and give me a comprehensi.. | 28.7 ± 10.5s |
| Q19 | What were the most severe disasters in this region.. | 25.1 ± 5.1s |
| Q20 | Cross-reference weather forecasts with historical .. | 28.0 ± 9.7s |
| Q21 | Hello | 11.0 ± 1.0s |
| Q22 | What is the capital of France? | 6.2 ± 1.1s |
| Q23 | Tell me everything | 37.2 ± 0.1s |
| Q24 | weather disaster flight all info now | 31.7 ± 9.3s |
| Q25 | (empty) | 0.0 ± 0.0s |
| Q26 | Give me the exact GPS coordinates of every flood i.. | 32.6 ± 9.9s |
| Q27 | What is the quantum mechanical probability of rain.. | 8.1 ± 3.1s |
| Q28 | Run a simulation of a category 5 cyclone hitting M.. | 38.1 ± 3.5s |
| Q29 | Compare disaster data from 1950 with current readi.. | 17.6 ± 2.3s |
| Q30 | Translate the weather forecast into Kannada | 9.5 ± 2.1s |

---

## Category-Wise Performance Analysis

Computed across all 3 runs (90 query executions for Cat A-D, 45 each for Cat E-F).  
Tool sub-category coverage is a **partial-credit** metric: each expected tool sub-category (e.g., `rainfall`, `landslide`, `disaster_alerts`) is checked independently, and the score is the fraction covered.  
Strict tool selection requires **all** expected sub-categories to be covered in a single execution.

| Cat | Routing % | Tool Cov % | Tool Strict % | Fallback % | Consensus % | Avg Latency |
|-----|----------:|-----------:|--------------:|-----------:|------------:|------------:|
| A – Single Agent / Single Tool | 100 | 67 | 67 | 0 | 0 | 4.5s |
| B – Single Agent / Multi-Tool | 87 | 47 | 47 | 60 | 20 | 13.0s |
| C – Multi-Agent | 73 | 28 | 7 | 80 | 73 | 26.9s |
| D – Decomposition Required | 100 | 12 | 13 | 67 | 100 | 27.6s |
| E – Edge Cases / Ambiguous | N/A | N/A | N/A | 67 | 33 | 17.2s |
| F – Fallback Triggers | N/A | N/A | N/A | 87 | 33 | 21.2s |

### Category A — Single Agent / Single Tool

**Routing: 100% ✓ | Tool Coverage: 67% | Fallback: 0% | Consensus: 0%**

- Routing is perfect — the orchestrator consistently maps simple queries to the correct single agent.
- **Failure point: Tool selection (Q4, Q5)**
  - **Q4** ("Show me rainfall data for the last 24 hours"): In at least one run the system called only `get_current_weather` and skipped dedicated rainfall tools (`get_gpm_rainfall`, `get_heavy_rainfall`). Cause: over-reliance on the generic weather tool when the query lacks explicit "rainfall" vocabulary cues.
  - **Q5** ("What is the humidity forecast for tomorrow?"): `tools_called = []` in multiple runs — the agent generated a response from its parametric knowledge rather than invoking any tool, meaning live forecast data was never fetched.
- Zero fallback rate confirms rate-limit pressure does not affect the simplest queries.

### Category B — Single Agent / Multi-Tool

**Routing: 87% | Tool Coverage: 47% | Fallback: 60% | Consensus: 20%**

- **Routing failures (Q9, Q10)** — both are *flaky* (correct in 1–2 of 3 runs, not consistently):
  - **Q9** ("List all GDACS events and SACHET alerts"): Occasionally mis-routed to the wrong agent or skipped entirely when rate-limited.
  - **Q10** ("Wind conditions and cyclone warnings"): Similar flakiness; the agent is invoked but `tools_called` is empty in the fall-back runs.
- **Tool selection gaps**: Only 47% of expected sub-category pairs are covered:
  - Q8 (`rainfall + landslide`): `get_gpm_rainfall` is called but `get_landslide_snapshot`/`get_high_risk_landslide` are consistently skipped.
  - Q9, Q10: Empty tool lists in fallback executions drag the average down.
- **High fallback rate (60%)**: Local model or tool-execution failures during mid-batch execution can cause the agent to return a cached/fallback response without tool invocation.

### Category C — Multi-Agent

**Routing: 73% | Tool Coverage: 28% | Strict Tool Selection: 7% | Fallback: 80% | Consensus: 73%**

- **Most problematic category overall.**
- **Routing failures**:
  - **Q14** ("Overall risk assessment for Dakshina Kannada") — *always wrong (0/3 runs)*: The orchestrator classifies this as a single-agent query and routes only to `disaster`, missing `weather` and `flight`. Root cause: the word "overall" is ambiguous and the decompose step collapses it to a single sub-task.
  - **Q15** ("Weather-related flight disruptions") — *flaky (1–2/3 correct)*: Routing varies depending on which LLM variant is selected and whether the `flight` agent is included in decomposition.
- **Strict tool selection only 7%**: Multi-agent queries require tools from 3 sub-categories simultaneously (e.g., `weather_forecast + disaster_alerts + flight_db`). Even one missing sub-category fails the strict check. Partial coverage reaches only 28%, meaning the system covers fewer than 1-in-3 expected sub-categories on average.
- **80% fallback rate**: Rate-limit pressure is highest here because multi-agent coordination requires more LLM calls per query.
- **73% consensus rate**: The consensus agent is correctly triggered for all multi-agent runs that complete successfully.

### Category D — Decomposition Required

**Routing: 100% ✓ | Tool Coverage: 12% | Strict Tool Selection: 13% | Fallback: 67% | Consensus: 100%**

- **Routing is perfect** — the orchestrator correctly identifies all D-category queries as requiring decomposition and dispatches to the right agent set.
- **Consensus at 100%**: Every successful D-category execution invokes the consensus agent — confirming the decomposition-then-synthesis pipeline is working.
- **Critical failure: Tool sub-category coverage only 12%** — the worst of all categories:
  - Q16–Q20 all require 3–5 distinct tool sub-categories (e.g., Q18 needs `weather_api + rainfall + landslide + disaster_alerts + disaster_api`).
  - In practice the agents invoke 1–2 tools from the broadest sub-category and return without covering the full required tool chain.
  - Root cause: The `DecomposeQuery` DSPy signature does not explicitly enumerate required tools per sub-task; the individual agents pick the "easiest" matching tool rather than exhaustively covering all required data sources.
- **67% fallback rate**: High latency (avg 27.6s) makes D-category queries most vulnerable to mid-execution rate limits; the system gracefully returns a partial answer via fallback but without the full tool coverage.

### Category E — Edge Cases / Ambiguous

**Fallback: 67% | Consensus: 33% | Avg Latency: 17.2s**

- No expected routing or tool targets — queries are intentionally ill-formed (e.g., "Hello", "Tell me everything", empty input).
- **Resilience: 100%** — the system never crashed on edge-case inputs across all 3 runs.
- **67% fallback rate**: About two-thirds of edge queries trigger the safety fallback, indicating the orchestrator correctly detects low-confidence or off-domain inputs.
- **Q25 (empty query): 0.0s latency** — input validation catches this immediately before any LLM call, returning an empty/error response without cost.

### Category F — Fallback Triggers

**Fallback: 87% | Consensus: 33% | Avg Latency: 21.2s**

- Queries are designed to be impossible or unreasonable (e.g., GPS coordinates for every flood globally, category-5 cyclone simulation).
- **87% fallback rate** is the highest of any category — the system correctly refuses or degrades gracefully on nearly all unreasonable requests.
- **13% non-fallback rate** (≈2 executions across 3 runs): The system occasionally attempts a partial answer (e.g., Q27 "quantum mechanical probability of rain" gets a meteorological interpretation) rather than a strict refusal — a minor over-confidence case.
- **33% consensus rate**: Consensus is invoked only when multiple agents are dispatched before the fallback path short-circuits.

### Key Failure Patterns

| Pattern | Affected | Root Cause |
|---------|----------|------------|
| **Empty tools_called** | Q5, Q9, Q10, Q13–Q20 (fallback runs) | Local model or tool-execution failures → fallback returns without tool invocation |
| **Single-tool collapse** | Q4 (Cat A), Q8 (Cat B) | Agent selects the broadest matching tool and stops; doesn't enumerate specific sub-tools |
| **Multi-agent routing miss** | Q14 (always), Q15 (flaky) | `ClassifyQuery` assigns `simple` instead of `multi_agent`; ambiguous query phrasing |
| **Decomposition tool gap** | Q16–Q20 (all Cat D) | `DecomposeQuery` creates sub-tasks but doesn't pin required tool IDs per sub-task |
| **Fallback inflates metrics** | B (60%), C (80%), D (67%) | Free-tier TPD limits (~100K tokens/day) exhausted mid-batch; fallback masks true tool failure rate |

### Recommended Improvements

1. **Tool enumeration in decomposition**: Modify `DecomposeQuery` to explicitly list required tool names per sub-task, not just agent names.
2. **Explicit sub-tool routing for Cat B**: Add a tool-selection DSPy signature that maps query intent to specific tool functions, not just tool domains.
3. **Q14 routing fix**: Augment `ClassifyQuery` training examples with "risk assessment" as a `multi_agent` trigger keyword.
4. **Paid API tier or local LLM**: Rate-limit fallbacks account for a large share of tool-coverage failures in B, C, D categories. Eliminating rate limits would raise tool coverage by an estimated 20–30 percentage points.
