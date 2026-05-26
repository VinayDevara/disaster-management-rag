"""
Flight Agent - CrewAI + DSPy Implementation
Handles ADS-B flight tracking queries using CrewAI tools and DSPy structured output
"""
from typing import Dict, List, Optional, Any
from utils.llm_client import get_llm_client, get_crewai_llm, get_crewai_tool_llm
from utils.database import DatabaseManager
from utils.vector_db import VectorDBManager
from tools.sql_tool import SQLTool
from agents.dspy_signatures import GenerateFlightResponse
from config.config import Config
import json
import dspy
from crewai import Agent, Task, Crew, LLM
from crewai.tools import BaseTool
import logging

logger = logging.getLogger(__name__)


def create_flight_tools(sql_tool: SQLTool, vector_db: VectorDBManager) -> List[BaseTool]:
    """Factory: create CrewAI tools wrapping flight SQL/vector operations."""

    def _truncate(text, max_len=2000):
        return text[:max_len] + "...(truncated)" if len(text) > max_len else text

    class _GetAllFlights(BaseTool):
        name: str = "get_all_flights"
        description: str = "Get all recent flights from ADS-B database."

        def _run(self, limit: str = "50") -> str:
            try:
                results = sql_tool.get_all_flights(int(limit))
                return _truncate(json.dumps(results[:5], default=str))
            except Exception as e:
                return json.dumps({"error": str(e)})

    class _GetFlightByCallsign(BaseTool):
        name: str = "get_flight_by_callsign"
        description: str = "Search for a specific flight by callsign or flight number."

        def _run(self, callsign: str) -> str:
            try:
                results = sql_tool.get_flight_by_callsign(str(callsign).strip())
                return _truncate(json.dumps(results, default=str))
            except Exception as e:
                return json.dumps({"error": str(e)})

    class _GetFlightByHex(BaseTool):
        name: str = "get_flight_by_hex"
        description: str = "Search for a flight by hex aircraft identifier."

        def _run(self, hex_code: str) -> str:
            try:
                results = sql_tool.get_flight_by_hex(str(hex_code).strip())
                return _truncate(json.dumps(results, default=str))
            except Exception as e:
                return json.dumps({"error": str(e)})

    class _GetFlightsInArea(BaseTool):
        name: str = "get_flights_in_area"
        description: str = "Search flights within a geographic bounding box."

        def _run(self, lat_min: str = "0", lat_max: str = "0",
                 lon_min: str = "0", lon_max: str = "0", limit: str = "50") -> str:
            try:
                results = sql_tool.get_flights_in_area(
                    float(lat_min), float(lat_max),
                    float(lon_min), float(lon_max), int(limit)
                )
                return _truncate(json.dumps(results[:5], default=str))
            except Exception as e:
                return json.dumps({"error": str(e)})

    class _GetEmergencyFlights(BaseTool):
        name: str = "get_emergency_flights"
        description: str = "Find flights with emergency squawk codes 7500, 7600, or 7700."

        def _run(self, limit: str = "50") -> str:
            try:
                results = sql_tool.get_emergency_flights(int(limit))
                return _truncate(json.dumps(results[:5], default=str))
            except Exception as e:
                return json.dumps({"error": str(e)})

    class _GetFlightTrajectory(BaseTool):
        name: str = "get_flight_trajectory"
        description: str = "Get flight path history for an aircraft."

        def _run(self, hex_code: str) -> str:
            try:
                results = sql_tool.get_flight_trajectory(str(hex_code).strip())
                return _truncate(json.dumps(results[:5], default=str))
            except Exception as e:
                return json.dumps({"error": str(e)})

    class _GetFlightsNearLocation(BaseTool):
        name: str = "get_flights_near_location"
        description: str = "Find flights near specific coordinates."

        def _run(self, lat: str = "0", lon: str = "0",
                 radius_deg: str = "2.0", limit: str = "50") -> str:
            try:
                results = sql_tool.get_flights_near_location(
                    float(lat), float(lon), float(radius_deg), int(limit)
                )
                return _truncate(json.dumps(results[:5], default=str))
            except Exception as e:
                return json.dumps({"error": str(e)})

    class _VectorSearchFlights(BaseTool):
        name: str = "vector_search_flights"
        description: str = "Semantic search across the flight knowledge base."

        def _run(self, query: str) -> str:
            try:
                results = vector_db.search("flights", str(query), n_results=5)
                return _truncate(json.dumps({
                    "documents": results["documents"],
                    "metadatas": results["metadatas"]
                }, default=str))
            except Exception as e:
                return json.dumps({"error": str(e)})

    return [
        _GetAllFlights(), _GetFlightByCallsign(), _GetFlightByHex(),
        _GetFlightsInArea(), _GetEmergencyFlights(), _GetFlightTrajectory(),
        _GetFlightsNearLocation(), _VectorSearchFlights(),
    ]


class FlightAgent:
    """
    CrewAI-based Flight & Aviation Surveillance Agent.

    Uses CrewAI for tool selection/execution and DSPy for structured response generation.
    Also serves as the backup orchestrator if the primary orchestrator fails.
    """

    def __init__(self, db_manager: DatabaseManager, vector_db: VectorDBManager):
        self.db = db_manager
        self.vector_db = vector_db
        self.sql_tool = SQLTool(db_manager)

        # CrewAI tools and agent
        self.tools = create_flight_tools(self.sql_tool, self.vector_db)
        self.crew_agent = Agent(
            role="Flight & Aviation Surveillance Agent",
            goal=(
                "Track and analyze ADS-B flight data for disaster management. "
                "ALWAYS use at least one tool to fetch real data before answering. "
                "Never answer from your own knowledge alone — call a tool first."
            ),
            backstory=(
                "You are an expert in ADS-B flight data analysis and aviation safety. "
                "You assist disaster management by tracking flights in affected areas "
                "and identifying emergency situations using live database tools."
            ),
            tools=self.tools,
            llm=get_crewai_llm(),
            verbose=True,
            max_retry_limit=3,
            max_iter=5,
        )

        # DSPy for structured response generation
        self.response_predictor = dspy.ChainOfThought(GenerateFlightResponse)

    def process(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process flight-related query using CrewAI agent + DSPy response synthesis.
        """
        logger.info(f"✈️  Flight Agent processing: {query}")

        trajectory_logger = context.get('trajectory_logger') if context else None
        context_str = json.dumps({k:v for k,v in (context or {}).items() if k != 'trajectory_logger'}, default=str) if context else "No additional context."
        
        def step_callback(step_output):
            if not trajectory_logger or not step_output: return
            if isinstance(step_output, list) and len(step_output) == 0: return
            
            try:
                thought = ""
                action = ""
                action_input = {}
                observation = ""
                
                if isinstance(step_output, list):
                    step_output = step_output[-1]
                
                if isinstance(step_output, tuple) and len(step_output) >= 2:
                    action_obj, obs = step_output[0], step_output[1]
                    thought = getattr(action_obj, 'log', getattr(action_obj, 'thought', ''))
                    action = getattr(action_obj, 'tool', str(action_obj))
                    action_input = getattr(action_obj, 'tool_input', {})
                    observation = str(obs)
                elif hasattr(step_output, 'return_values') or step_output.__class__.__name__ == 'AgentFinish':
                    # It's an AgentFinish object
                    thought = getattr(step_output, 'log', getattr(step_output, 'thought', ''))
                    action = "AgentFinish"
                    observation = getattr(step_output, 'return_values', str(step_output))
                else:
                    thought = getattr(step_output, 'thought', getattr(step_output, 'log', getattr(step_output, 'text', '')))
                    action = getattr(step_output, 'tool', getattr(step_output, 'action', ''))
                    action_input = getattr(step_output, 'tool_input', getattr(step_output, 'action_input', {}))
                    observation = getattr(step_output, 'result', getattr(step_output, 'observation', str(step_output)))
                    
                trajectory_logger.log_step(
                    thought=str(thought),
                    action=str(action),
                    action_input=action_input if isinstance(action_input, dict) else {"input": str(action_input)},
                    observation=str(observation)[:1000]
                )
            except Exception as e:
                logger.warning(f"Failed to log step: {e}")
                
        self.crew_agent.step_callback = step_callback

        task = Task(
            description=(
                f"Flight query: {query}\n"
                f"Context: {context_str}\n"
                "Step 1: Call get_all_flights or another flight tool to fetch real data.\n"
                "Step 2: Analyze the results for the query.\n"
                "Step 3: Report callsigns, positions, altitudes, and any emergency situations."
            ),
            expected_output=(
                "Concise flight analysis with real data points including "
                "callsigns, altitude, emergency status, and key findings."
            ),
            agent=self.crew_agent,
        )

        # Refresh the local LLM before each call so tool instructions stay current.
        self.crew_agent.llm = get_crewai_llm()
        crew = Crew(agents=[self.crew_agent], tasks=[task], verbose=True, respect_context_window=True, function_calling_llm=f"ollama/{Config.OLLAMA_TOOL_MODEL}")

        try:
            crew_result = crew.kickoff()
            raw_output = str(crew_result)
        except Exception as e:
            logger.warning(f"⚠️ CrewAI flight execution failed: {e}")
            logger.info("🔄 Falling back to direct tool queries...")
            raw_output = self._fallback_direct_query(query)

        # Use DSPy for structured response generation
        try:
            dspy_result = self.response_predictor(
                query=query,
                tool_results=raw_output,
            )
            answer = dspy_result.response
        except Exception as e:
            logger.warning(f"⚠️ DSPy flight response generation failed: {e}")
            answer = raw_output

        return {
            "agent": "flight",
            "query": query,
            "answer": answer,
            "raw_output": raw_output,
            "data_count": 1,
            "status": "success" if "Error" not in raw_output else "partial",
        }

    def _fallback_direct_query(self, query: str) -> str:
        """Bypass CrewAI and call tools directly when LLM tool calling fails."""
        results = []
        q = query.lower()

        try:
            vr = self.vector_db.search("flights", query, n_results=5)
            docs = vr.get("documents", [])
            if docs and docs[0]:
                flat = docs[0] if isinstance(docs[0], list) else docs
                results.append("Flight knowledge base:\n" + "\n".join(str(d) for d in flat[:5]))
        except Exception:
            pass

        try:
            flights = self.sql_tool.get_all_flights(limit=20)
            if flights:
                results.append("Recent flights:\n" + json.dumps(flights[:10], default=str))
        except Exception:
            pass

        try:
            emergencies = self.sql_tool.get_emergency_flights(limit=10)
            if emergencies:
                results.append("Emergency flights:\n" + json.dumps(emergencies[:5], default=str))
        except Exception:
            pass

        return "\n\n".join(results) if results else "No flight data available for this query."

    # ── Backup orchestrator capability ──────────────────────────────────────

    def process_as_orchestrator(
        self,
        query: str,
        agents: Dict[str, Any],
        consensus_agent: Any,
        error_msg: str,
        trajectory_logger=None,
    ) -> Dict[str, Any]:
        """
        Fallback orchestrator mode.
        When the primary orchestrator fails, FlightAgent takes over and runs
        all available agents with a simplified strategy.
        """
        from datetime import datetime

        logger.info("🔄 Flight Agent acting as BACKUP orchestrator")
        logger.warning(f"   Primary orchestrator error: {error_msg}")
        start_time = datetime.now()

        agent_results = {}

        # Try every agent, collect whatever works
        for agent_name, agent in agents.items():
            try:
                logger.info(f"   → Invoking {agent_name.title()} Agent...")
                result = agent.process(query, context={"trajectory_logger": trajectory_logger})
                agent_results[agent_name] = result
                data_count = result.get("data_count", 0) or result.get("event_count", 0)
                logger.info(f"     ✓ Retrieved {data_count} data points")
            except Exception as e:
                logger.warning(f"     ✗ {agent_name.title()} Agent failed: {e}")
                agent_results[agent_name] = {
                    "agent": agent_name,
                    "answer": f"Agent unavailable: {e}",
                    "status": "failed",
                    "data_count": 0,
                }

        # If multiple successful results, try consensus
        successful = {k: v for k, v in agent_results.items() if v.get("status") != "failed"}

        final_response = None
        if len(successful) > 1:
            try:
                logger.info("   → Running consensus on available results...")
                final_response = consensus_agent.process(
                    query, agent_results, {"query_type": "complex"}
                )
            except Exception as e:
                logger.warning(f"     ✗ Consensus failed: {e}")

        # Fall back to best single agent result
        if final_response is None:
            for result in agent_results.values():
                if result.get("status") != "failed":
                    final_response = result
                    break

        if final_response is None:
            final_response = {
                "answer": (
                    f"System degraded. Primary orchestrator error: {error_msg}. "
                    "All agents failed to produce results."
                ),
                "status": "degraded",
            }

        end_time = datetime.now()
        return {
            "query": query,
            "timestamp": start_time.isoformat(),
            "execution_time_seconds": (end_time - start_time).total_seconds(),
            "agent_results": agent_results,
            "final_response": final_response,
            "metadata": {
                "agents_used": list(agent_results.keys()),
                "orchestrator": "backup_flight_agent",
                "primary_error": error_msg,
            },
        }

    # ── Helper methods ──────────────────────────────────────────────────────

    def get_emergency_status(self) -> List[Dict]:
        """Get current emergency flights."""
        return self.sql_tool.get_emergency_flights(limit=50)

    def get_flights_in_disaster_area(
        self, lat: float, lon: float, radius_deg: float = 2.0
    ) -> List[Dict]:
        """Get flights potentially affected by a disaster in an area."""
        return self.sql_tool.get_flights_near_location(lat, lon, radius_deg)


if __name__ == "__main__":
    from config.config import Config

    db = DatabaseManager()
    vector_db = VectorDBManager()
    agent = FlightAgent(db, vector_db)

    result = agent.process("Show me all emergency flights")
    logger.info(json.dumps(result, indent=2, default=str))
