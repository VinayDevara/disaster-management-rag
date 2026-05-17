# Local Fine-Tuning Plan for Ollama Qwen2.5:3B

This repo now runs Ollama/Qwen locally. For offline operation, the important part is not just inference with Ollama; it is improving the local model on your agent traces so tool selection and disaster reasoning get better over time.

## Why this approach fits this codebase

The agent scope in DisasterRAG is already structured around:

- query classification in the orchestrator
- agent routing for flight, weather, and disaster domains
- tool invocation traces in the benchmark runs
- consensus synthesis for cross-domain queries

That makes the repo a good fit for preference optimization instead of generic language-model tuning.

## Recommended training strategy

Use a 2-stage local tuning pipeline:

1. Supervised fine-tuning for routing and tool planning.
2. Preference optimization for better disaster reasoning and fewer bad tool choices.

For this case, the most practical methods are:

- DPO, because you already have multiple benchmark runs that can be ranked into chosen/rejected pairs.
- ORPO, because it can train from preference data without a separate reward model.
- GRPO or PPO-style RL only if you later add a stronger reward loop and have enough GPU headroom.

For your hardware, DPO or ORPO is the realistic choice. Pure RL on a 3B model is possible but usually slower and more fragile than it needs to be here.

## What the scripts generate

Run:

```bash
python training/build_finetune_data.py
```

It creates:

- `data/training/sft_tool_planner.jsonl`
- `data/training/sft_answerer.jsonl`
- `data/training/dpo_preferences.jsonl`
- `data/training/summary.json`

The planner dataset is the most important one for tool calling. It teaches the model which agent scope and tool plan fit a query. The preference file is the most important one for disaster-time inference quality.

The current benchmark artifacts in this repo record routing, tool, and response-size metadata rather than full assistant completions, so the answer and preference files are synthetic-but-grounded. That is enough to start local tuning, and it becomes much stronger once you add live trace logging from the running orchestrator.

## How to use the outputs

1. Fine-tune the base Qwen model with the planner dataset first.
2. Continue with DPO or ORPO using the preference pairs.
3. Export the merged result to GGUF.
4. Import the quantized model into Ollama with a `Modelfile` that points to the new GGUF.

## Practical note

This repository can prepare the training data, but the actual weight update still needs a training environment with the right ML stack and GPU support. The scripts here are designed to make that handoff clean and repeatable.
