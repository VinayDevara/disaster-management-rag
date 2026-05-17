# DisasterRAG Implementation Plan: API Reliability + Local Ollama Migration

## 1) Objectives

You want to do three things before full execution work starts:

1. Verify each disaster/weather source API pipeline is working.
2. Identify all likely failure points and harden retry/fallback behavior.
3. Replace Groq dependency with a local Ollama model that supports tool calling and multi-step reasoning on your laptop (RTX 3050 4 GB VRAM, 16 GB RAM), then set up safe continual domain adaptation.

This document is the exact execution plan for the next conversation when you say continue.

## 2) Reality Check on Current Codebase

Current backend uses Groq (not Grok) as hard dependency in several places.

Known issues already visible in code that can cause silent or hard failures:

1. SQL column mismatches in read tools:
- tools/sql_tool.py uses issued_at/expires_at for official_alerts, but table uses onset/expires/fetched_at.
- tools/sql_tool.py uses event_date for external_events, but table uses start_time/fetched_at.
- tools/sql_tool.py uses iso_time/lat/lon/wind_kt for historical_cyclones, but table uses timestamp/latitude/longitude/wind_kts.

2. IBTrACS parse-to-DB mapping mismatch:
- ingestion/sources/ibtracs_ingestor.py outputs keys like iso_time, lat, lon, wind_kt.
- utils/database.py batch_insert_historical_cyclones expects timestamp, latitude, longitude, wind_kts, storm_name.

3. Consensus data extraction blind spot:
- agents/consensus_agent.py expects structured tool_results for correlation/severity logic.
- agents mostly return raw_output string and hardcoded data_count = 1, reducing actual confidence and severity accuracy.

4. LLM provider hardcoded to Groq:
- utils/llm_client.py hardwires Groq client and dspy.LM('groq/...').
- CrewAI LLM constructors in all agents are hardcoded to groq/... models.

These become Phase 0 blockers before performance tuning.

## 3) Recommended Local Model for Your Hardware

Primary recommendation (best balance for 4 GB VRAM + tool use):
- qwen2.5:3b-instruct (Ollama)

Secondary fallback model:
- llama3.2:3b-instruct (Ollama)

Why this pair:
- 3B class models fit your memory envelope better than 7B for stable local inference.
- Qwen 2.5 3B is generally better for instruction-following and structured outputs at small size.
- You can keep temperature low for tool-calling reliability.

Important constraint:
- Reliable multi-step reasoning with strict tool plans is still limited on 3B models.
- For hard queries, keep a provider fallback ladder (local first, cloud second) until local quality is proven.

## 4) Execution Phases

## Phase 0: Baseline and Blocker Fixes (must-do first)

Deliverables:
- Fix schema mismatches and return-structure mismatches before writing broad tests.

Tasks:
- [ ] Fix SQLTool query columns for official_alerts, external_events, historical_cyclones.
- [ ] Align IBTrACS ingestor output keys with DB insert expectations.
- [ ] Improve agent result payloads to include structured tool_results and real data_count/event_count.
- [ ] Ensure consensus logic reads actual returned structures.

Files to modify:
- tools/sql_tool.py
- ingestion/sources/ibtracs_ingestor.py
- utils/database.py (if needed for compatibility helpers)
- agents/flight_agent.py
- agents/weather_agent.py
- agents/disaster_agent.py
- agents/consensus_agent.py

Acceptance criteria:
- No SQL runtime errors from existing tool methods.
- Consensus receives non-empty structured inputs when tools run.
- data_count reflects actual retrieved records.

## Phase 1: API Source Test Coverage (source-by-source)

Test strategy:
- Unit tests with mocked HTTP responses for each source parser + edge cases.
- Integration tests against local SQLite to validate insert/upsert behavior.
- Health-check script to run all source pipelines and summarize pass/fail.

New test files to add:
- tests/sources/test_sachet_ingestor.py
- tests/sources/test_gdacs_ingestor.py
- tests/sources/test_openmeteo_ingestor.py
- tests/sources/test_gpm_ingestor.py
- tests/sources/test_lhasa_ingestor.py
- tests/sources/test_ibtracs_ingestor.py
- tests/sources/test_eonet_api_tool.py
- tests/sources/test_openweather_api_tool.py
- tests/integration/test_ingestion_scheduler_cycles.py
- tests/integration/test_source_fetch_log_and_raw_payload_store.py

For each source, test at least these cases:

1. Success path
- Valid payload parses and writes expected row count.

2. Timeout/network failure
- Exception handled, fetch log status = error, zero writes.

3. Rate limit / server errors
- 429/5xx handled by retry and final state is logged.

4. Empty payload / malformed payload
- Graceful handling, no crash, no invalid inserts.

5. Idempotency
- Re-running same payload does not duplicate unique rows unexpectedly.

6. Field drift
- Missing optional fields still parse without crash.

Acceptance criteria:
- 90%+ pass on source tests.
- Every source has at least one failure-mode test.
- source_fetch_log has entries for success and failure scenarios.

## Phase 2: System Failure Matrix + Resilience Tests

Create a failure catalog and corresponding tests:

Failure classes:
- External API unavailable or slow.
- Tool call returns malformed arguments.
- Agent returns plain text without tool evidence.
- DSPy generation/parsing failure.
- DB write lock/transaction rollback.
- Empty vector search.
- Partial multi-agent completion.

New tests to add:
- tests/agents/test_orchestrator_retry_and_reinvoke.py
- tests/agents/test_orchestrator_fallback_to_flight_backup.py
- tests/agents/test_consensus_partial_inputs.py
- tests/llm/test_llm_provider_failover.py
- tests/llm/test_tool_call_parsing_robustness.py

Acceptance criteria:
- Retry/fallback behavior deterministic and measurable.
- No uncaught exception can crash orchestrator process_query path.
- Confidence score degrades predictably on partial failures.

## Phase 3: Ollama Provider Integration (local-first)

Design:
- Introduce provider abstraction: groq, ollama, auto.
- Keep same interface so agents and orchestrator do not change business logic.

Config additions:
- LLM_PROVIDER=ollama|groq|auto
- OLLAMA_BASE_URL=http://127.0.0.1:11434
- OLLAMA_MODEL=qwen2.5:3b-instruct
- OLLAMA_TOOL_MODEL=qwen2.5:3b-instruct
- LLM_FALLBACK_ORDER=ollama,groq

Code tasks:
- [ ] Refactor utils/llm_client.py into provider-agnostic client.
- [ ] Add utils/ollama_client.py (chat + tool calls + retries + timeout).
- [ ] Update config/config.py for provider settings.
- [ ] Update agent LLM builders in flight/weather/disaster agents to use selected provider model names.
- [ ] Update DSPy initialization path so it can run with local model endpoint.

Optional compatibility adapter if needed:
- Create utils/llm_factory.py to centralize all model selection and fallback rules.

Acceptance criteria:
- Local query works end-to-end with Ollama only.
- Tool calling works for at least one query per agent.
- If Ollama fails, auto mode falls back to Groq without crash.

## Phase 4: Continual Domain Adaptation (safe, not online self-training)

Important:
- Do not continuously fine-tune directly on live stream in-place.
- Use staged adapter updates to avoid model drift/hallucination spikes.

Pipeline:

1. Data curation job (daily/weekly):
- Pull high-quality tuples from DB and successful tool traces.
- Build supervised instruction dataset and preference pairs.

2. Train lightweight adapters (LoRA/QLoRA):
- Target small 3B base model.
- Keep adapter checkpoints versioned under models/adapters/.

3. Eval gate before deployment:
- Run benchmark_queries.json suite plus safety checks.
- Promote adapter only if metrics improve.

4. Rollback-ready serving:
- Keep previous adapter as hot rollback option.

Files to add:
- training/build_dataset.py
- training/train_lora.py
- training/eval_adapter.py
- models/adapters/README.md
- configs/training_config.yaml

Laptop feasibility note:
- On 4 GB VRAM, true frequent fine-tuning is constrained.
- Practical approach: small-batch periodic adapter training (possibly CPU offload or external GPU), local inference for serving.

## Phase 5: Hallucination Resilience Hardening

Controls to implement:

1. Evidence-gated response rule
- Agent must cite tool outputs/DB rows; otherwise abstain.

2. Structured final answer schema
- facts, uncertainties, actions, confidence, evidence_count.

3. Verification pass
- Add lightweight verifier step that checks consistency between answer and retrieved data.

4. Confidence penalties
- Penalize when response has no tool evidence, stale data, or failed sub-agents.

5. Strict fallback messaging
- Explicitly say what failed and what data is missing.

Tests to add:
- tests/safety/test_evidence_required.py
- tests/safety/test_uncertainty_and_abstention.py
- tests/safety/test_confidence_penalty_rules.py

Acceptance criteria:
- Hallucination-prone responses replaced by evidence-backed or abstained outputs.
- Final responses always indicate source evidence status.

## 5) Suggested Milestone Order (next conversation)

Milestone A
- Phase 0 blocker fixes + minimal regression tests.

Milestone B
- Phase 1 source API tests + health script.

Milestone C
- Phase 2 resilience tests + failure matrix document.

Milestone D
- Phase 3 Ollama integration and provider fallback.

Milestone E
- Phase 5 hallucination guards.

Milestone F
- Phase 4 continual adaptation pipeline (last, after reliability is stable).

## 6) Definition of Done

All of the following must be true:

- Each source ingestor/API has success + failure tests.
- Retry/fallback behavior is validated by tests.
- Local Ollama model can run end-to-end and call tools.
- Auto provider fallback works.
- Hallucination controls enforce evidence-based output.
- Training loop is staged and versioned, not uncontrolled online updates.

## 7) What we will implement first when you say continue

Exact first implementation slice:

1. Fix SQL schema/query mismatches and IBTrACS mapping mismatches.
2. Add tests for those fixes.
3. Add provider abstraction skeleton with Ollama config fields.

Then we will run tests and iterate.
