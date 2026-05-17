# DisasterRAG Fine-Tuning and System Design Plan

## What Has Been Done So Far

The project now has a working local fallback path for offline use:

- Ollama is installed locally on the machine.
- `qwen2.5:3b` is downloaded and available through the local Ollama daemon.
- The LLM client supports Groq as primary and Ollama as fallback.
- Agent builders now refresh against the active provider.
- DSPy is configured to switch between Groq and Ollama.
- A local training-data pipeline was added under `training/`.
- The benchmark runs were converted into planner, answer, and preference datasets.

Current generated training artifacts:

- `data/training/sft_tool_planner.jsonl`
- `data/training/sft_answerer.jsonl`
- `data/training/dpo_preferences.jsonl`
- `data/training/summary.json`

## Current System Design

The current architecture is a hub-and-spoke agent system:

- `main.py` initializes the app, database, vector store, agents, orchestrator, and scheduler.
- `agents/orchestrator_agent.py` classifies the query, decomposes it, invokes specialized agents, and optionally runs consensus.
- `agents/flight_agent.py`, `agents/weather_agent.py`, and `agents/disaster_agent.py` execute domain-specific tool calls.
- `utils/llm_client.py` manages Groq primary + Ollama fallback behavior.
- `tools/` contains API and SQL wrappers that are used by the agents.
- `utils/database.py` and the `data/` directory hold operational and historical disaster data.

## What Should Change in the System Design

The design should evolve from a static agent runtime into a closed-loop learning system.

### 1. Add a trace logging layer

Every query should generate a structured trajectory record:

- user query
- timestamp
- detected query type
- selected agents
- tools called per agent
- intermediate results
- consensus decision
- fallback usage
- final response
- latency
- user feedback, if any

This is the most important design change because it creates the training signal.

### 2. Add a feedback store

Keep a dedicated training table or JSONL export for:

- thumbs up / thumbs down
- corrected answers
- missing tool suggestions
- route corrections
- hallucination flags
- answer usefulness scores

This allows preference tuning later without manually curating every example.

### 3. Add model versioning

Treat the local Ollama model as a versioned artifact:

- base model: `qwen2.5:3b`
- fine-tuned model: `qwen2.5:3b-disaster-v1`
- candidate model: `qwen2.5:3b-disaster-v2`

The app should read the active local model from config or environment so you can switch versions without code edits.

### 4. Add a training job boundary

Fine-tuning should not happen inside the live application.

Instead, split the system into:

- online inference service
- offline data extraction job
- offline training job
- model packaging job

That keeps the runtime stable and makes retraining repeatable.

## How to Add Fine-Tuning Dynamically

Use a pipeline with four stages:

1. **Collect traces** from live usage and benchmark runs.
2. **Build datasets** for planner SFT, answer SFT, and preference training.
3. **Train locally** using DPO or ORPO on the Qwen base model.
4. **Export and register** the new model in Ollama, then switch the app to the new model alias.

Dynamic behavior means:

- the app continues serving traffic while training runs offline,
- the new model is versioned and tested before promotion,
- the config chooses the active local Ollama model name at startup,
- fallback remains available even during upgrade cycles.

## How to Use the Data Stored in the Database

Your SQLite and Chroma data should serve three purposes:

### 1. Retrieval for inference

Use operational data to ground the final answer at runtime.

Examples:

- active alerts from SQLite
- weather history from ingestion tables
- flight data from ADS-B records
- vector search for similar historical incidents

### 2. Synthetic training example generation

Use the database to create structured prompts:

- query + retrieved rows + expected agent
- query + tool evidence + expected final answer style
- query + historical incident similarities + ideal recommendation

### 3. Preference labeling

Use database-backed evidence to score candidate answers:

- correct routing gets higher reward
- grounded answers get higher reward
- irrelevant tools or unsupported claims get lower reward

## How to Prepare a Synthetic Dataset

Use a layered synthetic-data strategy.

### Planner data

Create examples of:

- query -> primary agent
- query -> secondary agents
- query -> tool plan
- query -> consensus needed or not

### Answer data

Create grounded answer targets that teach structure:

- summarize the risk
- cite relevant region and time window
- mention operational implications
- keep uncertainty explicit

### Preference data

Create chosen/rejected pairs from:

- good routing vs wrong routing
- grounded vs hallucinated answer
- concise vs verbose but irrelevant answer
- consensus-aware vs consensus-ignoring response

### Hard negatives

Add deliberately bad samples:

- wrong agent selected
- no tool used when tools were needed
- unsupported certainty
- disaster answer with missing location or time context

## Which RL Technique Fits Best

For this system, the best order is:

### Recommended now: DPO or ORPO

Why:

- You already have benchmark runs that can be ranked.
- You do not need a separate reward model at first.
- It is much easier to run locally on a 3B model.
- It is more stable than full RL for this use case.

### Use later: GRPO or PPO-style RL

Only move to a stronger RL setup if you later have:

- enough preference data,
- a stable reward signal,
- a reliable evaluator for answer quality,
- enough GPU headroom.

### Best practical recommendation

For DisasterRAG, DPO is the best first choice.

If you want a simpler preference-based variant, use ORPO.

If you want policy optimization later, graduate to GRPO with a robust reward function.

## How to Log User Trajectories

A trajectory should capture the full decision path.

Store a record like:

- session id
- user id or anonymous hash
- query text
- language model provider used
- active model name
- routed agents
- tool calls
- tool outputs summary
- retries
- fallback events
- final answer
- user feedback
- latency
- outcome label

### Suggested storage format

Use a dedicated table or append-only JSONL file.

Minimum fields:

- `trajectory_id`
- `timestamp`
- `query`
- `route`
- `tools`
- `final_response`
- `feedback`
- `reward_score`

### When to log

Log at these points:

- request received
- after classification
- after each agent call
- after consensus
- after final response
- after user feedback

## How to Use the Trajectory Logs as a Feedback Loop

The loop should be:

1. Collect live trajectories.
2. Filter for successful and failed cases.
3. Rank outputs using reward heuristics.
4. Build preference pairs.
5. Fine-tune the local model.
6. Evaluate against benchmark queries.
7. Promote the new model only if it improves routing and answer quality.

This creates a self-improving loop without retraining on every single request.

## Suggested Execution Plan

### Phase 1: Instrumentation

- Add structured trajectory logging to the orchestrator.
- Capture all tool calls and final answers.
- Store user feedback and corrections.

### Phase 2: Dataset generation

- Export benchmark runs and live traces.
- Generate planner SFT data.
- Generate grounded answer SFT data.
- Generate preference pairs.

### Phase 3: Local tuning

- Fine-tune the Qwen base model with planner SFT.
- Run DPO or ORPO on preference pairs.
- Quantize the merged model for Ollama.

### Phase 4: Integration

- Register the fine-tuned model in Ollama.
- Add a model alias in config.
- Switch the app to the new model version.

### Phase 5: Validation

- Re-run benchmark queries.
- Compare routing accuracy, tool selection, and latency.
- Verify offline response quality.

### Phase 6: Continuous improvement

- Keep collecting trajectories.
- Periodically rebuild datasets.
- Retrain only when enough new data exists.

## Concrete Modifications I Recommend Next

1. Add a trajectory logger in the orchestrator.
2. Add a feedback endpoint or feedback table.
3. Add a dataset exporter for live traces.
4. Add a training runner for DPO/ORPO.
5. Add model-version config for Ollama.
6. Add evaluation scripts that compare old vs new model behavior.

## Bottom Line

The right path for this project is not full RL first. It is:

- structured logging,
- synthetic + live dataset generation,
- SFT for routing/tool behavior,
- DPO or ORPO for preference improvement,
- then optional stronger RL later.

That fits the repo, the hardware, and the disaster-response agent scope much better than trying to jump directly into PPO-style training.
