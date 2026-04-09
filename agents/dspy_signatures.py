"""
Centralized DSPy Signatures for Disaster RAG System
Structured input/output definitions using DSPy + Pydantic
"""
import dspy
from pydantic import BaseModel, Field


# ─── Orchestrator Signatures ─────────────────────────────────────────────────

class ClassificationOutput(BaseModel):
    query_type: str = Field(description="'simple' or 'complex'")
    primary_agent: str = Field(description="'flight', 'weather', or 'disaster'")
    secondary_agents: list[str] = Field(description="List of secondary agents needed")
    requires_cross_intelligence: bool = Field(description="True if multiple domains need to correlate")
    reasoning: str = Field(description="Explanation for classification")


class ClassifyQuery(dspy.Signature):
    """Classify user queries for a disaster management system.

    1. FLIGHT AGENT - Flight tracking and ADS-B data, aircraft surveillance.
    2. WEATHER AGENT - Current weather, forecasts, severe weather, maritime conditions.
    3. DISASTER AGENT - Natural disasters, urban evacuation plans, emergency logistics.

    Query Classification Guidelines:
    - SIMPLE queries need ONE agent
    - COMPLEX queries need MULTIPLE agents
    - Cross-intelligence queries require correlation between domains

    Examples:
    - "What flights are near Los Angeles?" -> Flight Agent only (simple)
    - "Show active wildfires" -> Disaster Agent only (simple)
    - "Are flights affected by California wildfires?" -> Flight + Disaster (complex)
    - "What's the weather in the hurricane zone and are flights diverted?" -> Weather + Flight (complex)
    """
    query: str = dspy.InputField(desc="The user query to classify")
    output: ClassificationOutput = dspy.OutputField()


class SubqueriesOutput(BaseModel):
    flight: str = Field(description="Specific flight question, or empty string if not needed", default="")
    weather: str = Field(description="Specific weather question, or empty string if not needed", default="")
    disaster: str = Field(description="Specific disaster question, or empty string if not needed", default="")


class DecomposeQuery(dspy.Signature):
    """Break down a complex query into specific sub-queries for each agent.
    Create focused sub-queries that each agent can answer independently."""
    query: str = dspy.InputField(desc="Original user query")
    primary_agent: str = dspy.InputField()
    secondary_agents: str = dspy.InputField()
    output: SubqueriesOutput = dspy.OutputField()


class ReinvocationDecision(BaseModel):
    needs_reinvocation: bool = Field(
        description="Whether any agent needs to be re-invoked with a refined query"
    )
    reinvocations: dict = Field(
        description="Dict mapping agent_name to refined_query string for agents needing re-invocation",
        default_factory=dict
    )
    reasoning: str = Field(description="Explanation for reinvocation decision")


class EvaluateResults(dspy.Signature):
    """Evaluate agent results to decide if any agent needs re-invocation with a refined query.

    Consider:
    - Did the agent return useful data (data_count > 0)?
    - Does the answer address the original query?
    - Is cross-domain data needed that wasn't fetched?
    - Would a more specific sub-query yield better results?

    Only request reinvocation if results are clearly insufficient.
    """
    original_query: str = dspy.InputField()
    agent_results: str = dspy.InputField(desc="Summary of each agent's results including data counts and answer previews")
    classification: str = dspy.InputField(desc="Original query classification")
    output: ReinvocationDecision = dspy.OutputField()


# ─── Flight Agent Signatures ────────────────────────────────────────────────

class GenerateFlightResponse(dspy.Signature):
    """Generate a comprehensive answer based on flight data. Include:
    1. Direct answer to the query
    2. Relevant flight details (callsign, position, altitude, status)
    3. Any emergency or safety concerns
    4. Geographic context if applicable
    5. Timestamps and tracking information
    """
    query: str = dspy.InputField()
    tool_results: str = dspy.InputField()
    response: str = dspy.OutputField()


# ─── Weather Agent Signatures ───────────────────────────────────────────────

class GenerateWeatherResponse(dspy.Signature):
    """Generate a comprehensive meteorological and maritime assessment based on weather data."""
    query: str = dspy.InputField()
    weather_data: str = dspy.InputField()
    severity_analysis: str = dspy.InputField()
    response: str = dspy.OutputField(
        desc="1. Conditions/forecast\n2. Temperature\n3. Wind/visibility/maritime state\n4. Aviation impact\n5. Warnings"
    )


# ─── Disaster Agent Signatures ──────────────────────────────────────────────

class GenerateDisasterResponse(dspy.Signature):
    """Generate a comprehensive Evacuation & Logistics assessment based on disaster data. Include:
    1. Summary of relevant disaster events & Locations
    2. Urban Evacuation Plans
    3. Comprehensive emergency logistics planning
    4. Severity and Aviation/operational implications
    """
    query: str = dspy.InputField()
    disaster_data: str = dspy.InputField(desc="JSON string of tool findings")
    impact_analysis: str = dspy.InputField(desc="JSON string of impact analysis")
    response: str = dspy.OutputField()


# ─── Consensus Agent Signatures ─────────────────────────────────────────────

class GenerateEmergencyCommandPlan(dspy.Signature):
    """Synthesize information from specialized agents to generate a comprehensive disaster action plan."""
    original_query: str = dspy.InputField()
    agent_results: str = dspy.InputField()
    extracted_key_data: str = dspy.InputField()
    correlations_found: str = dspy.InputField()
    geographic_analysis: str = dspy.InputField()
    severity_assessment: str = dspy.InputField()
    response: str = dspy.OutputField(
        desc="1. Executive Summary\n2. Cross-Domain Analysis\n3. Detailed Findings\n4. Geographic Context\n5. Recommendations & Logistics"
    )
