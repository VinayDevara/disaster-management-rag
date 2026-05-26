# Disaster Management RAG

**Multi-Agent Disaster Intelligence Platform for Emergency Decision Support**

A production-oriented Agentic Retrieval-Augmented Generation (RAG) system that combines specialized AI agents, real-time intelligence sources, vector retrieval, structured reasoning, and consensus-driven decision making to support disaster response operations.

The platform orchestrates domain-specific agents across aviation, weather intelligence, and disaster monitoring to generate unified situational assessments and emergency response recommendations.

---

## Overview

Disaster response requires synthesizing information from multiple heterogeneous sources:

* Aviation activity
* Meteorological conditions
* Active disaster events
* Historical incidents
* Geographic risk factors
* Emergency alerts

Traditional RAG systems retrieve information and generate responses but lack structured reasoning across domains.

Disaster Management RAG introduces a multi-agent architecture where specialized agents independently analyze different intelligence streams and collaboratively generate a consensus-driven operational assessment.

---

## Key Capabilities

### Multi-Agent Intelligence

The system consists of specialized agents operating as independent reasoning units:

| Agent              | Responsibility                                        |
| ------------------ | ----------------------------------------------------- |
| Orchestrator Agent | Query understanding, decomposition, routing           |
| Flight Agent       | Aviation intelligence and flight monitoring           |
| Weather Agent      | Weather analysis and risk assessment                  |
| Disaster Agent     | Disaster event monitoring and emergency intelligence  |
| Consensus Agent    | Cross-agent correlation and final response generation |

---

### Agentic Query Decomposition

Complex queries are automatically decomposed into domain-specific tasks.

Example:

> "Are there any aircraft currently operating near regions affected by severe weather alerts?"

The system may:

1. Query flight intelligence
2. Query weather intelligence
3. Correlate geographic overlap
4. Generate risk assessment
5. Produce unified emergency recommendations

---

### Retrieval-Augmented Intelligence

Supports:

* Structured database retrieval
* Vector similarity search
* Historical incident retrieval
* Context augmentation
* Semantic knowledge grounding

---

### Consensus-Based Reasoning

Unlike traditional single-agent systems, responses are generated through a consensus workflow.

The Consensus Agent:

* Aggregates outputs from all participating agents
* Identifies correlations
* Detects cross-domain patterns
* Performs severity assessment
* Produces unified emergency command plans

---

### Explainable Agent Trajectories

Every execution can be logged as a complete reasoning trace.

Captured information includes:

* Agent decisions
* Query decomposition
* Tool invocations
* Intermediate observations
* Consensus generation steps
* Final response

This enables:

* Auditing
* Debugging
* Evaluation
* Research reproducibility

---

## System Architecture

```text
                        ┌─────────────────────┐
                        │      User Query     │
                        └──────────┬──────────┘
                                   │
                                   ▼
                    ┌────────────────────────────┐
                    │     Orchestrator Agent     │
                    │      DSPy-Based Router     │
                    └──────────┬─────────────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
         ▼                     ▼                     ▼

 ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
 │ Flight Agent│     │Weather Agent│     │DisasterAgent│
 └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
        │                   │                   │
        ▼                   ▼                   ▼

  Flight Data        Weather Data      Disaster Events
  Vector Search      Vector Search      Vector Search
  Tool Calling       Tool Calling       Tool Calling

         └─────────────────────────────────────────┘
                               │
                               ▼

                  ┌──────────────────────┐
                  │   Consensus Agent    │
                  │  Cross-Intelligence  │
                  └──────────┬───────────┘
                             │
                             ▼

                Unified Emergency Assessment
```

---

## Technology Stack

### AI Layer

* DSPy
* CrewAI
* Ollama
* Qwen Models
* Retrieval-Augmented Generation

### Backend

* FastAPI
* Pydantic
* Uvicorn

### Data Layer

* ChromaDB
* Vector Embeddings
* Structured Databases

### Observability

* Structured Logging
* Trajectory Logging
* Benchmark Framework
* Metrics Evaluation

### Infrastructure

* Python 3.11+
* Docker Compatible
* Local LLM Deployment
* API-First Design

---

## Repository Structure

```text
.
├── agents/
│   ├── orchestrator_agent.py
│   ├── flight_agent.py
│   ├── weather_agent.py
│   ├── disaster_agent.py
│   ├── consensus_agent.py
│   └── dspy_signatures.py
│
├── ingestion/
│   ├── scheduler.py
│   └── pipelines/
│
├── config/
│   └── config.py
│
├── tools/
│   └── intelligence_tools/
│
├── utils/
│   ├── database.py
│   ├── vector_db.py
│   ├── llm_client.py
│   └── trajectory_logger.py
│
├── training/
├── logs/
├── data/
│
├── benchmark.py
├── measure_metrics.py
├── analyze_benchmark.py
│
└── main.py
```

---

## Getting Started

### Prerequisites

* Python 3.11+
* Ollama
* Qwen Model
* Git

---

### Clone Repository

```bash
git clone https://github.com/<org>/disaster-management-rag.git

cd disaster-management-rag
```

---

### Create Environment

```bash
python -m venv .venv

source .venv/bin/activate
```

Windows:

```powershell
.venv\Scripts\activate
```

---

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

### Configure Environment

Create:

```bash
.env
```

Example:

```env
OLLAMA_BASE_URL=http://localhost:11434

OLLAMA_MODEL=qwen2.5:3b

OLLAMA_TOOL_MODEL=qwen2.5:3b

SUPABASE_URL=<optional>

SUPABASE_SERVICE_ROLE_KEY=<optional>
```

---

### Pull Required Model

```bash
ollama pull qwen2.5:3b
```

---

### Launch API

```bash
python main.py
```

or

```bash
uvicorn main:app --reload
```

---

## Example Query

```json
{
  "query": "Identify active weather hazards affecting nearby flight operations."
}
```

Example workflow:

```text
Query Classification
        ↓
Task Decomposition
        ↓
Flight Analysis
        ↓
Weather Analysis
        ↓
Cross-Agent Correlation
        ↓
Consensus Generation
        ↓
Emergency Recommendation
```

---

## Observability

### Trajectory Logging

Every execution can be recorded as a structured reasoning trace.

Example:

```json
{
  "step": 1,
  "thought": "...",
  "action": "...",
  "observation": "..."
}
```

Useful for:

* Explainability
* Agent debugging
* Failure analysis
* Research evaluation

---

## Evaluation Framework

The repository includes benchmarking utilities for measuring:

### Retrieval Metrics

* MRR
* Precision
* Recall
* Context Relevance

### Agent Metrics

* Routing Accuracy
* Tool Usage Success Rate
* Consensus Quality
* Hallucination Reduction

### System Metrics

* End-to-End Latency
* Token Utilization
* Query Completion Rate

---

## Design Principles

### Grounded Responses

Agents are instructed to:

* Never fabricate facts
* Never invent disaster events
* Never hallucinate flight information
* Always rely on retrieved evidence

---

### Modular Agents

New intelligence domains can be added without changing orchestration logic.

Examples:

* Satellite Intelligence Agent
* Maritime Agent
* Social Media Monitoring Agent
* Infrastructure Risk Agent

---

### Human-Auditable Decisions

Every major system decision is logged and traceable.

This supports:

* Government deployments
* Emergency operation centers
* Research environments
* Safety-critical workflows

---

## Extending the Platform

### Adding a New Agent

1. Create new agent implementation

```python
class SatelliteAgent:
    pass
```

2. Register with orchestrator

```python
self.agents["satellite"] = satellite_agent
```

3. Add DSPy routing signatures

```python
class ClassifySatelliteQuery(dspy.Signature):
    ...
```

4. Add consensus integration

```python
agent_results["satellite"]
```

---

## Research Contributions

This project explores:

* Agentic RAG Systems
* Multi-Agent Reasoning
* Consensus-Based Intelligence Fusion
* Disaster Response Decision Support
* Explainable AI Workflows
* Structured Agent Evaluation

---

## Roadmap

* Real-time streaming intelligence
* Distributed agent execution
* Human-in-the-loop validation
* Multi-modal satellite ingestion
* Geospatial visualization
* Autonomous emergency planning
* Reinforcement learning for agent coordination

---

## Disclaimer

This platform is intended to support decision-makers and analysts. It should not be used as the sole source of information for emergency response actions without validation from official authorities and operational systems.
