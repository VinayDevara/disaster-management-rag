# DisasterRAG DSPy Upgrade & Role Repurposing

## DSPy Integration
The project was migrated to use the `dspy-ai` library for more robust structured prompt generation and query classification.
- Global DSPy initialization logic using `dspy.Groq` was added to `utils/llm_client.py`.
- **Orchestrator Agent**: Upgraded from raw JSON string parsing to using `dspy.Signature` and `dspy.Predict` for classifying the query and breaking it down properly.
- **Evacuation & Logistics Agent** (formerly Disaster Agent): Updated tools and output pipelines to analyze the data explicitly through a `dspy.ChainOfThought` pipeline.
- **Flight & Aviation Surveillance Agent** (formerly Flight Agent): Integrated `dspy.Predict` and `dspy.ChainOfThought`. The agent shifts its focus towards utilizing aircraft data to handle emergency queries and execute search & rescue surveillances securely within a disaster area.
- **Environment & Maritime Agent** (formerly Weather Agent): Replaced the tool reasoning and severe weather generation with DSPy predictors.
- **Emergency Command Agent** (formerly Consensus Agent): Utilizes `dspy.ChainOfThought` to digest responses from the above agents to issue robust action plans.

## Dynamic Tool Parameter Safety
Hardcoded "magic numbers" (such as default extraction limits and datetime values) were addressed across `sql_tool.py` and `api_tool.py`.
1. The DSPy signatures guiding the agents were explicitly instructed via `pydantic.Field` properties to predict and specify dynamic logic numbers directly instead of blindly relying on fallback parameters.
2. Safeguards were added directly to `sql_tool.py` and `api_tool.py` to bound whatever numbers the LLMs predict (e.g., maximum returned rows bounded to 500, max weather forecast restricted to 5 days). This prevents database crashes and arbitrary API runaway usage if an agent hallucinates a massive parameter.

## Purpose of the Upgrade
By shifting to DSPy, the platform enhances precision, handles complex disaster logic explicitly, and moves away from prone-to-fail JSON block string extractions. The entire pipeline functions in a significantly stronger structure meant exclusively for tackling natural disaster intelligence logic globally.
