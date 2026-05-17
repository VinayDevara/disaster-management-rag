# DisasterRAG Benchmark Report

**Date:** 2026-03-30 02:13  
**Queries Executed:** 30  
**Total Execution Time:** 557.6s  
**Architecture:** CrewAI 1.11 + DSPy | Local Ollama (`qwen2.5:3b` reasoning + tool-calling)  

## Methodology

| Step | What happened |
|------|--------------|
| 1. Query Set | 30 queries loaded from `benchmark_queries.json`, split into 6 categories (A-F) covering single-agent, multi-agent, decomposition, edge-case, and fallback scenarios. |
| 2. System Init | `DisasterRAGSystem` initialised — SQLite DB, ChromaDB vectors, 3 CrewAI agents (Flight, Weather, Disaster), DSPy orchestrator, Consensus agent. |
| 3. Execution | Each query passed to `OrchestratorAgent.process_query()`. Stdout captured to extract tool names and fallback triggers. |
| 4. Routing Check | DSPy classifier routes to primary + secondary agents. We check if the *expected* agents are a **subset** of the agents actually invoked. |
| 5. Tool Check | For Categories A-D we verify at least one CrewAI tool was called (tool selection accuracy). |
| 6. Resilience Check | For Categories E-F (edge cases / fallbacks) the pass criterion is simply *no crash*. |
| 7. Rate-Limit Handling | A configurable delay between queries keeps local inference stable under repeated requests. |
| 8. Scoring | Metrics computed and this report generated automatically. |

## Overall Metrics

| Metric | Result |
|--------|--------|
| Total Queries | 30 |
| Total Execution Time | 557.6 s |
| Average Latency | 18.6 s |
| Routing Accuracy | 96.7% |
| Tool Selection Rate | 40.0% |
| Edge/Fallback Resilience | 100.0% |
| Fallback Triggered | 70.0% |
| Consensus Applied | 46.7% |
| Unique Tools Invoked | 25 |
| Total Tool Invocations | 52 |
| Semantic Relevance Score | 0.744 |

## Targets

| Metric | Score | Target | Status |
|--------|-------|--------|--------|
| Routing Accuracy | 96.7% | > 80% | ✅ |
| Tool Selection Accuracy | 40.0% | > 75% | ❌ |
| Edge-Case Resilience | 100.0% | 100% | ✅ |
| Response Rate | 100.0% | > 90% | ✅ |
| Crash-Free Rate | 100.0% | 100% | ✅ |
| Avg Latency (single-agent) | 7.8s | < 10s | ✅ |
| Avg Latency (multi-agent) | 27.6s | < 20s | ❌ |

## Latency by Category

| Category | Queries | Avg (s) | Min (s) | Max (s) | Median (s) |
|----------|---------|---------|---------|---------|------------|
| A — Single Agent / Single Tool | 5 | 3.1 | 2.2 | 4.8 | 2.9 |
| B — Single Agent / Multi-Tool | 5 | 12.6 | 4.7 | 29.9 | 9.5 |
| C — Multi-Agent | 5 | 22.9 | 2.5 | 42.3 | 16.5 |
| D — Decomposition Required | 5 | 32.3 | 16.4 | 46.1 | 31.2 |
| E — Edge Cases / Ambiguous | 5 | 22.8 | 7.2 | 37.2 | 23.5 |
| F — Fallback Triggers | 5 | 22.4 | 7.7 | 43.9 | 18.0 |

## Per-Query Results

| # | Cat | Query | Expected | Actual Agents | Tools | Fallback | Time | Resp Len | Status |
|---|-----|-------|----------|---------------|-------|----------|------|----------|--------|
| Q1 | A | What is the current temperature in .. | weather | weather | 6 | No | 4.8s | 674 | ✅ PASS |
| Q2 | A | Are there any active flood alerts i.. | disaster | disaster | 4 | No | 2.9s | 782 | ✅ PASS |
| Q3 | A | What flights are available from Man.. | flight | flight | 3 | No | 3.6s | 576 | ✅ PASS |
| Q4 | A | Show me rainfall data for the last .. | weather | weather | 0 | No | 2.2s | 1519 | ✅ PASS |
| Q5 | A | What is the humidity forecast for t.. | weather | weather | 0 | No | 2.2s | 510 | ✅ PASS |
| Q6 | B | Compare current weather conditions .. | weather | weather | 5 | Yes | 4.7s | 1006 | ✅ PASS |
| Q7 | B | Show me all active disaster alerts .. | disaster | disaster | 0 | Yes | 10.3s | 16735 | ✅ PASS |
| Q8 | B | What is the rainfall trend and land.. | weather | disaster, weather | 0 | Yes | 29.9s | 485 | ✅ PASS |
| Q9 | B | List all GDACS events and SACHET al.. | disaster | disaster | 0 | Yes | 9.5s | 16773 | ✅ PASS |
| Q10 | B | What are the wind conditions and an.. | weather | weather | 0 | Yes | 8.4s | 2488 | ✅ PASS |
| Q11 | C | Is it safe to fly from Mangalore gi.. | weather, disaster, flight | flight, weather, disaster | 14 | Yes | 38.9s | 488 | ✅ PASS |
| Q12 | C | How will the weather affect disaste.. | weather, disaster | weather, disaster | 5 | Yes | 42.3s | 488 | ✅ PASS |
| Q13 | C | Should I travel to Mangalore this w.. | weather, disaster | disaster, weather | 0 | No | 14.2s | 1232 | ✅ PASS |
| Q14 | C | What is the overall risk assessment.. | weather, disaster | disaster | 0 | No | 2.5s | 1252 | ⚠️ ROUTE |
| Q15 | C | Are there any weather-related fligh.. | weather, flight | weather, flight | 4 | Yes | 16.5s | 480 | ✅ PASS |
| Q16 | D | Compare the flood risk in the last .. | weather, disaster | disaster, weather | 11 | Yes | 37.5s | 488 | ✅ PASS |
| Q17 | D | Given the cyclone history in the Ba.. | weather, disaster | weather, disaster | 0 | No | 16.4s | 481 | ✅ PASS |
| Q18 | D | Analyze all data sources and give m.. | weather, disaster | disaster, weather | 0 | Yes | 46.1s | 486 | ✅ PASS |
| Q19 | D | What were the most severe disasters.. | disaster | disaster, weather | 0 | Yes | 30.2s | 492 | ✅ PASS |
| Q20 | D | Cross-reference weather forecasts w.. | weather, disaster | weather, disaster | 0 | Yes | 31.2s | 486 | ✅ PASS |
| Q21 | E | Hello | any | disaster | 0 | Yes | 9.9s | 16703 | ✅ PASS |
| Q22 | E | What is the capital of France? | any | flight | 0 | Yes | 7.2s | 3787 | ✅ PASS |
| Q23 | E | Tell me everything | any | disaster, flight, weather | 0 | Yes | 37.2s | 486 | ✅ PASS |
| Q24 | E | weather disaster flight all info no.. | any | disaster, weather, flight | 0 | Yes | 37.1s | 486 | ✅ PASS |
| Q25 | E | (empty) | any | — | 0 | No | 0.0s | 0 | ✅ PASS |
| Q26 | F | Give me the exact GPS coordinates o.. | any | disaster, weather | 0 | Yes | 34.6s | 486 | ✅ PASS |
| Q27 | F | What is the quantum mechanical prob.. | any | weather | 0 | Yes | 7.7s | 2488 | ✅ PASS |
| Q28 | F | Run a simulation of a category 5 cy.. | any | disaster, weather | 0 | Yes | 43.9s | 486 | ✅ PASS |
| Q29 | F | Compare disaster data from 1950 wit.. | any | disaster | 0 | Yes | 18.0s | 16785 | ✅ PASS |
| Q30 | F | Translate the weather forecast into.. | any | weather | 0 | Yes | 7.9s | 2488 | ✅ PASS |

## Category Breakdown

- **Category A** (Single Agent / Single Tool): **5/5** passed  `█████`
- **Category B** (Single Agent / Multi-Tool): **5/5** passed  `█████`
- **Category C** (Multi-Agent): **4/5** passed  `████░`
- **Category D** (Decomposition Required): **5/5** passed  `█████`
- **Category E** (Edge Cases / Ambiguous): **5/5** passed  `█████`
- **Category F** (Fallback Triggers): **5/5** passed  `█████`

## Diagnosis & Observations

- **21/30** queries triggered the fallback path (CrewAI → direct tool calls).
- **High multi-agent latency (27.6s).** Consider parallel agent execution or reducing max_iter.
