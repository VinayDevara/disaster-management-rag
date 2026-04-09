"""
Disaster Agent - CrewAI + DSPy Implementation
Handles disaster event queries using CrewAI tools and DSPy structured output
"""
from typing import Dict, List, Optional, Any
from utils.llm_client import get_llm_client
from utils.database import DatabaseManager
from utils.vector_db import VectorDBManager
from tools.sql_tool import DisasterSQLTool, AlertsSQLTool, ExternalEventsSQLTool, CycloneSQLTool
from tools.api_tool import DisasterAPITool
from agents.dspy_signatures import GenerateDisasterResponse
from config.config import Config
import json
import dspy
from crewai import Agent, Task, Crew, LLM
from crewai.tools import BaseTool


def _get_crewai_llm():
    return LLM(
        model=f"groq/{Config.GROQ_MODEL}",
        api_key=Config.GROQ_API_KEY,
        temperature=Config.TEMPERATURE,
        max_tokens=512,
        num_retries=3,
        timeout=120,
    )


def _get_tool_calling_llm():
    return LLM(
        model=f"groq/{Config.GROQ_TOOL_MODEL}",
        api_key=Config.GROQ_API_KEY,
        temperature=0.1,
        max_tokens=512,
        num_retries=3,
        timeout=120,
    )


def create_disaster_tools(
    sql_tool: DisasterSQLTool, api_tool: DisasterAPITool, vector_db: VectorDBManager,
    alerts_sql: AlertsSQLTool = None,
    events_sql: ExternalEventsSQLTool = None,
    cyclone_sql: CycloneSQLTool = None,
) -> List[BaseTool]:
    """Factory: create CrewAI tools wrapping disaster SQL/API/vector operations."""

    def _truncate(text, max_len=2000):
        return text[:max_len] + "...(truncated)" if len(text) > max_len else text

    class _GetActiveEvents(BaseTool):
        name: str = "get_active_events"
        description: str = "Get currently active disaster events worldwide."

        def _run(self, limit: str = "50") -> str:
            try:
                results = api_tool.get_active_events(int(limit))
                return _truncate(json.dumps(results[:5], default=str))
            except Exception as e:
                return json.dumps({"error": str(e)})

    class _GetEventsByCategory(BaseTool):
        name: str = "get_events_by_category"
        description: str = "Get disaster events filtered by category such as wildfires, volcanoes, or severeStorms."

        def _run(self, category: str = "", limit: str = "20") -> str:
            try:
                results = api_tool.get_events_by_category(str(category), int(limit))
                return _truncate(json.dumps(results[:5], default=str))
            except Exception as e:
                return json.dumps({"error": str(e)})

    class _GetEventsInArea(BaseTool):
        name: str = "get_events_in_area"
        description: str = "Get disaster events within a geographic bounding box."

        def _run(self, lat_min: str = "0", lat_max: str = "0",
                 lon_min: str = "0", lon_max: str = "0", limit: str = "20") -> str:
            try:
                results = api_tool.get_events_in_area(
                    float(lat_min), float(lat_max),
                    float(lon_min), float(lon_max), int(limit)
                )
                return _truncate(json.dumps(results[:5], default=str))
            except Exception as e:
                return json.dumps({"error": str(e)})

    class _GetEventDetails(BaseTool):
        name: str = "get_event_details"
        description: str = "Get detailed information about a specific disaster event by its ID."

        def _run(self, event_id: str = "") -> str:
            try:
                result = api_tool.get_event_details(str(event_id))
                return _truncate(json.dumps(result, default=str))
            except Exception as e:
                return json.dumps({"error": str(e)})

    class _GetDisasterEventsByType(BaseTool):
        name: str = "get_disaster_events_by_type"
        description: str = "Get historical disaster events by type from the database."

        def _run(self, event_type: str = "", limit: str = "20") -> str:
            try:
                results = sql_tool.get_disaster_events_by_type(str(event_type), int(limit))
                return _truncate(json.dumps(results[:5], default=str))
            except Exception as e:
                return json.dumps({"error": str(e)})

    class _GetRecentDisasters(BaseTool):
        name: str = "get_recent_disasters"
        description: str = "Get recent disaster events from the database."

        def _run(self, days: str = "7", limit: str = "20") -> str:
            try:
                results = sql_tool.get_recent_disasters(int(days), int(limit))
                return _truncate(json.dumps(results[:5], default=str))
            except Exception as e:
                return json.dumps({"error": str(e)})

    class _VectorSearchDisasters(BaseTool):
        name: str = "vector_search_disasters"
        description: str = "Semantic search across the disaster knowledge base."

        def _run(self, query: str) -> str:
            try:
                results = vector_db.search("disasters", str(query), n_results=5)
                return _truncate(json.dumps({
                    "documents": results["documents"],
                    "metadatas": results["metadatas"]
                }, default=str))
            except Exception as e:
                return json.dumps({"error": str(e)})

    # ── New tools for ingested external data ──────────────────────────

    class _GetOfficialAlerts(BaseTool):
        name: str = "get_official_alerts"
        description: str = "Get latest SACHET/NDMA official disaster warnings for Dakshina Karnataka."

        def _run(self, district: str = None, limit: str = "50") -> str:
            if alerts_sql is None:
                return json.dumps({"error": "AlertsSQLTool not available"})
            try:
                results = alerts_sql.get_latest_alerts(limit=int(limit), district=district or None)
                return _truncate(json.dumps(results[:5], default=str))
            except Exception as e:
                return json.dumps({"error": str(e)})

    class _GetActiveAlerts(BaseTool):
        name: str = "get_active_official_alerts"
        description: str = "Get currently active non-expired official disaster alerts."

        def _run(self, limit: str = "50") -> str:
            if alerts_sql is None:
                return json.dumps({"error": "AlertsSQLTool not available"})
            try:
                results = alerts_sql.get_active_alerts(limit=int(limit))
                return _truncate(json.dumps(results[:5], default=str))
            except Exception as e:
                return json.dumps({"error": str(e)})

    class _GetGDACSEvents(BaseTool):
        name: str = "get_gdacs_events"
        description: str = "Get latest GDACS flood and cyclone events."

        def _run(self, event_type: str = None, limit: str = "50") -> str:
            if events_sql is None:
                return json.dumps({"error": "ExternalEventsSQLTool not available"})
            try:
                results = events_sql.get_latest_events(limit=int(limit), event_type=event_type or None)
                return _truncate(json.dumps(results[:5], default=str))
            except Exception as e:
                return json.dumps({"error": str(e)})

    class _GetGDACSEventsBySeverity(BaseTool):
        name: str = "get_gdacs_events_by_severity"
        description: str = "Get GDACS events filtered by severity level such as red, orange, or green."

        def _run(self, severity: str = "", limit: str = "50") -> str:
            if events_sql is None:
                return json.dumps({"error": "ExternalEventsSQLTool not available"})
            try:
                results = events_sql.get_events_by_severity(str(severity), int(limit))
                return _truncate(json.dumps(results[:5], default=str))
            except Exception as e:
                return json.dumps({"error": str(e)})

    class _GetHistoricalCyclones(BaseTool):
        name: str = "get_historical_cyclones"
        description: str = "Get IBTrACS historical cyclone data for the North Indian Ocean basin."

        def _run(self, basin: str = "NI", limit: str = "50") -> str:
            if cyclone_sql is None:
                return json.dumps({"error": "CycloneSQLTool not available"})
            try:
                results = cyclone_sql.get_cyclones_in_basin(str(basin), int(limit))
                return _truncate(json.dumps(results[:5], default=str))
            except Exception as e:
                return json.dumps({"error": str(e)})

    class _GetIntenseCyclones(BaseTool):
        name: str = "get_intense_cyclones"
        description: str = "Get historical cyclones above a wind speed threshold in knots."

        def _run(self, min_wind_kt: str = "64", limit: str = "50") -> str:
            if cyclone_sql is None:
                return json.dumps({"error": "CycloneSQLTool not available"})
            try:
                results = cyclone_sql.get_intense_cyclones(float(min_wind_kt), int(limit))
                return _truncate(json.dumps(results[:5], default=str))
            except Exception as e:
                return json.dumps({"error": str(e)})

    tools = [
        _GetActiveEvents(), _GetEventsByCategory(), _GetEventsInArea(),
        _GetEventDetails(), _GetDisasterEventsByType(), _GetRecentDisasters(),
        _VectorSearchDisasters(),
    ]

    if alerts_sql is not None:
        tools.extend([_GetOfficialAlerts(), _GetActiveAlerts()])
    if events_sql is not None:
        tools.extend([_GetGDACSEvents(), _GetGDACSEventsBySeverity()])
    if cyclone_sql is not None:
        tools.extend([_GetHistoricalCyclones(), _GetIntenseCyclones()])

    return tools


class DisasterAgent:
    """
    CrewAI-based Evacuation & Logistics Agent.

    Uses CrewAI for tool selection/execution and DSPy for structured response generation.
    """

    def __init__(self, db_manager: DatabaseManager, vector_db: VectorDBManager):
        self.db = db_manager
        self.vector_db = vector_db
        self.sql_tool = DisasterSQLTool(db_manager)
        self.api_tool = DisasterAPITool()
        self.llm = get_llm_client()

        # New SQL tools for ingested data
        self.alerts_sql = AlertsSQLTool(db_manager)
        self.events_sql = ExternalEventsSQLTool(db_manager)
        self.cyclone_sql = CycloneSQLTool(db_manager)

        # CrewAI tools and agent
        self.tools = create_disaster_tools(
            self.sql_tool, self.api_tool, self.vector_db,
            alerts_sql=self.alerts_sql,
            events_sql=self.events_sql,
            cyclone_sql=self.cyclone_sql,
        )
        self.crew_agent = Agent(
            role="Evacuation & Logistics Agent",
            goal=(
                "Monitor and analyze disaster events for emergency management. "
                "You MUST use the available tools to gather real data before answering. "
                "Never answer from your own knowledge alone."
            ),
            backstory=(
                "You are an expert in disaster management and emergency logistics. "
                "You ALWAYS call at least one tool to fetch real data before providing an answer. "
                "You rapidly generate urban evacuation plans, assess disaster impact zones, "
                "and plan comprehensive emergency logistics."
            ),
            tools=self.tools,
            llm=_get_crewai_llm(),
            verbose=True,
            max_retry_limit=3,
            max_iter=3,
        )

        # DSPy for structured response generation
        self.response_predictor = dspy.ChainOfThought(GenerateDisasterResponse)

    def process(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process disaster-related query using CrewAI agent + DSPy response synthesis.
        """
        print(f"🔥 Disaster Agent processing: {query}")

        context_str = json.dumps(context, default=str) if context else "No additional context."

        task = Task(
            description=(
                f"Analyze and answer this disaster-related query: {query}\n"
                f"Additional context: {context_str}\n"
                "Use the available tools to gather relevant disaster data. "
                "Include event types, locations, severity, and impact assessments."
            ),
            expected_output=(
                "Comprehensive disaster assessment with event details, "
                "impact analysis, evacuation considerations, and recommendations."
            ),
            agent=self.crew_agent,
        )

        crew = Crew(agents=[self.crew_agent], tasks=[task], verbose=True, respect_context_window=True, function_calling_llm=_get_tool_calling_llm())

        try:
            crew_result = crew.kickoff()
            raw_output = str(crew_result)
        except Exception as e:
            print(f"⚠️ CrewAI disaster execution failed: {e}")
            print("🔄 Falling back to direct tool queries...")
            raw_output = self._fallback_direct_query(query)

        # Analyze impact from raw output
        impact_analysis = self._analyze_impact_from_output(raw_output)

        # Use DSPy for structured response generation
        try:
            dspy_result = self.response_predictor(
                query=query,
                disaster_data=raw_output,
                impact_analysis=json.dumps(impact_analysis),
            )
            answer = dspy_result.response
        except Exception as e:
            print(f"⚠️ DSPy disaster response generation failed: {e}")
            answer = raw_output

        return {
            "agent": "disaster",
            "query": query,
            "answer": answer,
            "raw_output": raw_output,
            "impact_analysis": impact_analysis,
            "event_count": 1,
            "data_count": 1,
            "status": "success" if "Error" not in raw_output else "partial",
        }

    def _analyze_impact_from_output(self, raw_output: str) -> Dict[str, Any]:
        """Basic impact analysis from raw tool output."""
        impact = {
            "severity": "low",
            "aviation_risk": "minimal",
            "response_priority": "routine",
        }

        output_lower = raw_output.lower()
        if any(w in output_lower for w in ["major", "catastrophic", "extreme", "critical"]):
            impact["severity"] = "critical"
            impact["aviation_risk"] = "high"
            impact["response_priority"] = "immediate"
        elif any(w in output_lower for w in ["severe", "significant", "large"]):
            impact["severity"] = "high"
            impact["aviation_risk"] = "moderate"
            impact["response_priority"] = "urgent"
        elif any(w in output_lower for w in ["moderate", "active", "ongoing"]):
            impact["severity"] = "moderate"
            impact["aviation_risk"] = "low-moderate"
            impact["response_priority"] = "elevated"

        return impact

    def _fallback_direct_query(self, query: str) -> str:
        """Bypass CrewAI and call tools directly when LLM tool calling fails."""
        results = []
        q = query.lower()

        try:
            vr = self.vector_db.search("disasters", query, n_results=10)
            docs = vr.get("documents", [])
            if docs and docs[0]:
                flat = docs[0] if isinstance(docs[0], list) else docs
                results.append("Disaster knowledge base:\n" + "\n".join(str(d) for d in flat[:5]))
        except Exception:
            pass

        try:
            recent = self.sql_tool.get_recent_disasters(days=30, limit=10)
            if recent:
                results.append("Recent disasters:\n" + json.dumps(recent[:10], default=str))
        except Exception:
            pass

        try:
            events = self.api_tool.get_active_events(limit=20)
            if events:
                results.append("Active events:\n" + json.dumps(events[:10], default=str))
        except Exception:
            pass

        for kw, cat in [("wildfire", "wildfires"), ("fire", "wildfires"),
                         ("volcano", "volcanoes"), ("storm", "severeStorms"),
                         ("earthquake", "earthquakes"), ("flood", "floods"),
                         ("landslide", "landslides"), ("cyclone", "severeStorms")]:
            if kw in q:
                try:
                    ev = self.api_tool.get_events_by_category(cat, 10)
                    if ev:
                        results.append(f"{cat} events:\n" + json.dumps(ev[:5], default=str))
                except Exception:
                    pass
                break

        try:
            alerts = self.alerts_sql.get_latest_alerts(limit=10)
            if alerts:
                results.append("Official alerts:\n" + json.dumps(alerts[:5], default=str))
        except Exception:
            pass

        try:
            gdacs = self.events_sql.get_latest_events(limit=10)
            if gdacs:
                results.append("GDACS events:\n" + json.dumps(gdacs[:5], default=str))
        except Exception:
            pass

        if any(w in q for w in ["cyclone", "hurricane", "typhoon"]):
            try:
                cyc = self.cyclone_sql.get_cyclones_in_basin("NI", 10)
                if cyc:
                    results.append("Historical cyclones:\n" + json.dumps(cyc[:5], default=str))
            except Exception:
                pass

        return "\n\n".join(results) if results else "No disaster data available for this query."

    # ── Helper methods ──────────────────────────────────────────────────────

    def get_disasters_near_location(
        self, lat: float, lon: float, radius_deg: float = 5.0
    ) -> List[Dict]:
        return self.api_tool.get_events_in_area(
            lat - radius_deg, lat + radius_deg,
            lon - radius_deg, lon + radius_deg,
        )

    def get_active_disasters_summary(self) -> Dict:
        events = self.api_tool.get_active_events(limit=200)
        return {
            "total_events": len(events),
            "events": events,
            "impact_analysis": self._analyze_impact_from_output(json.dumps(events, default=str)),
        }


if __name__ == "__main__":
    db = DatabaseManager()
    vector_db = VectorDBManager()
    agent = DisasterAgent(db, vector_db)

    result = agent.process("What active wildfires are happening right now?")
    print(json.dumps(result, indent=2, default=str))
