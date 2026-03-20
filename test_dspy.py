import dspy
from pydantic import BaseModel
from utils.llm_client import get_llm_client

# Initialize
llm = get_llm_client()

class ClassificationResult(BaseModel):
    query_type: str
    primary_agent: str
    secondary_agents: list[str]
    requires_cross_intelligence: bool
    reasoning: str

class ClassifyQuery(dspy.Signature):
    """Classify user query into agents: flight, weather, disaster."""
    query: str = dspy.InputField()
    output: ClassificationResult = dspy.OutputField()

predictor = dspy.Predict(ClassifyQuery)
result = predictor(query="Are flights affected by wildfires in LA?")
print(result.output)
