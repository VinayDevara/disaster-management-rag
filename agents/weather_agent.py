"""
Weather Agent - CrewAI + DSPy Implementation
Handles weather-related queries using CrewAI tools and DSPy structured output
"""
from typing import Dict, List, Optional, Any
from utils.llm_client import get_llm_client, get_crewai_llm, get_crewai_tool_llm
from utils.database import DatabaseManager
from utils.vector_db import VectorDBManager
from tools.sql_tool import WeatherSQLTool, ForecastSQLTool, RainfallSQLTool, LandslideSQLTool
from tools.api_tool import WeatherAPITool
from agents.dspy_signatures import GenerateWeatherResponse
from config.config import Config
import json
import dspy
from crewai import Agent, Task, Crew, LLM
from crewai.tools import BaseTool
import logging

logger = logging.getLogger(__name__)


def create_weather_tools(
    sql_tool: WeatherSQLTool, api_tool: WeatherAPITool, vector_db: VectorDBManager,
    forecast_sql: ForecastSQLTool = None,
    rainfall_sql: RainfallSQLTool = None,
    landslide_sql: LandslideSQLTool = None,
) -> List[BaseTool]:
    """Factory: create CrewAI tools wrapping weather SQL/API/vector operations."""

    def _truncate(text, max_len=2000):
        return text[:max_len] + "...(truncated)" if len(text) > max_len else text

    class _GetCurrentWeather(BaseTool):
        name: str = "get_current_weather"
        description: str = "Get current weather conditions by coordinates."

        def _run(self, lat: str = "0", lon: str = "0") -> str:
            try:
                result = api_tool.get_current_weather(float(lat), float(lon))
                return _truncate(json.dumps(result, default=str))
            except Exception as e:
                return json.dumps({"error": str(e)})

    class _GetWeatherByCity(BaseTool):
        name: str = "get_weather_by_city"
        description: str = "Get weather for a city by name."

        def _run(self, city: str = "", country_code: str = None) -> str:
            try:
                result = api_tool.get_weather_by_city(str(city), country_code)
                return _truncate(json.dumps(result, default=str))
            except Exception as e:
                return json.dumps({"error": str(e)})

    class _GetForecast(BaseTool):
        name: str = "get_forecast"
        description: str = "Get weather forecast for coordinates."

        def _run(self, lat: str = "0", lon: str = "0", days: str = "3") -> str:
            try:
                result = api_tool.get_forecast(float(lat), float(lon), int(days))
                return _truncate(json.dumps(result, default=str))
            except Exception as e:
                return json.dumps({"error": str(e)})

    class _GetWeatherEventsByType(BaseTool):
        name: str = "get_weather_events_by_type"
        description: str = "Get historical weather events by type from the database."

        def _run(self, event_type: str = "", limit: str = "20") -> str:
            try:
                results = sql_tool.get_weather_events_by_type(str(event_type), int(limit))
                return _truncate(json.dumps(results[:5], default=str))
            except Exception as e:
                return json.dumps({"error": str(e)})

    class _GetWeatherEventsInArea(BaseTool):
        name: str = "get_weather_events_in_area"
        description: str = "Get weather events within a geographic bounding box."

        def _run(self, lat_min: str = "0", lat_max: str = "0",
                 lon_min: str = "0", lon_max: str = "0", limit: str = "20") -> str:
            try:
                results = sql_tool.get_weather_events_in_area(
                    float(lat_min), float(lat_max),
                    float(lon_min), float(lon_max), int(limit)
                )
                return _truncate(json.dumps(results[:5], default=str))
            except Exception as e:
                return json.dumps({"error": str(e)})

    class _VectorSearchWeather(BaseTool):
        name: str = "vector_search_weather"
        description: str = "Semantic search across the weather knowledge base."

        def _run(self, query: str) -> str:
            try:
                results = vector_db.search("weather", str(query), n_results=5)
                return _truncate(json.dumps({
                    "documents": results["documents"],
                    "metadatas": results["metadatas"]
                }, default=str))
            except Exception as e:
                return json.dumps({"error": str(e)})

    # ── New tools for ingested external data ──────────────────────────

    class _GetOpenMeteoForecasts(BaseTool):
        name: str = "get_openmeteo_forecasts"
        description: str = "Get latest Open-Meteo hourly forecasts for Dakshina Karnataka region."

        def _run(self, location: str = "", limit: str = "48") -> str:
            if forecast_sql is None:
                return json.dumps({"error": "ForecastSQLTool not available"})
            try:
                if location:
                    results = forecast_sql.get_forecasts_for_location(str(location), int(limit))
                else:
                    results = forecast_sql.get_latest_forecasts(limit=int(limit))
                return _truncate(json.dumps(results[:5], default=str))
            except Exception as e:
                return json.dumps({"error": str(e)})

    class _GetHighPrecipitation(BaseTool):
        name: str = "get_high_precipitation_forecasts"
        description: str = "Get forecast periods with precipitation above a threshold in mm."

        def _run(self, threshold: str = "5.0", limit: str = "50") -> str:
            if forecast_sql is None:
                return json.dumps({"error": "ForecastSQLTool not available"})
            try:
                results = forecast_sql.get_high_precipitation_forecasts(float(threshold), int(limit))
                return _truncate(json.dumps(results[:5], default=str))
            except Exception as e:
                return json.dumps({"error": str(e)})

    class _GetGPMRainfall(BaseTool):
        name: str = "get_gpm_rainfall"
        description: str = "Get latest NASA GPM IMERG satellite rainfall observations."

        def _run(self, limit: str = "50") -> str:
            if rainfall_sql is None:
                return json.dumps({"error": "RainfallSQLTool not available"})
            try:
                results = rainfall_sql.get_latest_rainfall(limit=int(limit))
                return _truncate(json.dumps(results[:5], default=str))
            except Exception as e:
                return json.dumps({"error": str(e)})

    class _GetHeavyRainfall(BaseTool):
        name: str = "get_heavy_rainfall"
        description: str = "Get rainfall observations exceeding a threshold in mm."

        def _run(self, threshold: str = "10.0", limit: str = "50") -> str:
            if rainfall_sql is None:
                return json.dumps({"error": "RainfallSQLTool not available"})
            try:
                results = rainfall_sql.get_heavy_rainfall(float(threshold), int(limit))
                return _truncate(json.dumps(results[:5], default=str))
            except Exception as e:
                return json.dumps({"error": str(e)})

    class _GetLandslideSnapshot(BaseTool):
        name: str = "get_landslide_snapshot"
        description: str = "Get latest NASA LHASA landslide nowcast snapshot for the region."

        def _run(self, limit: str = "50") -> str:
            if landslide_sql is None:
                return json.dumps({"error": "LandslideSQLTool not available"})
            try:
                results = landslide_sql.get_latest_snapshot(limit=int(limit))
                return _truncate(json.dumps(results[:5], default=str))
            except Exception as e:
                return json.dumps({"error": str(e)})

    class _GetHighRiskLandslide(BaseTool):
        name: str = "get_high_risk_landslide"
        description: str = "Get landslide cells with high risk or probability >= 0.7."

        def _run(self, limit: str = "50") -> str:
            if landslide_sql is None:
                return json.dumps({"error": "LandslideSQLTool not available"})
            try:
                results = landslide_sql.get_high_risk_cells(limit=int(limit))
                return _truncate(json.dumps(results[:5], default=str))
            except Exception as e:
                return json.dumps({"error": str(e)})

    tools = [
        _GetCurrentWeather(), _GetWeatherByCity(), _GetForecast(),
        _GetWeatherEventsByType(), _GetWeatherEventsInArea(), _VectorSearchWeather(),
    ]

    # Conditionally include enrichment tools
    if forecast_sql is not None:
        tools.extend([_GetOpenMeteoForecasts(), _GetHighPrecipitation()])
    if rainfall_sql is not None:
        tools.extend([_GetGPMRainfall(), _GetHeavyRainfall()])
    if landslide_sql is not None:
        tools.extend([_GetLandslideSnapshot(), _GetHighRiskLandslide()])

    return tools


class WeatherAgent:
    """
    CrewAI-based Environment & Maritime Agent.

    Uses CrewAI for tool selection/execution and DSPy for structured response generation.
    """

    def __init__(self, db_manager: DatabaseManager, vector_db: VectorDBManager):
        self.db = db_manager
        self.vector_db = vector_db
        self.sql_tool = WeatherSQLTool(db_manager)
        self.api_tool = WeatherAPITool()
        self.llm = get_llm_client()

        # New SQL tools for ingested data
        self.forecast_sql = ForecastSQLTool(db_manager)
        self.rainfall_sql = RainfallSQLTool(db_manager)
        self.landslide_sql = LandslideSQLTool(db_manager)

        # CrewAI tools and agent
        self.tools = create_weather_tools(
            self.sql_tool, self.api_tool, self.vector_db,
            forecast_sql=self.forecast_sql,
            rainfall_sql=self.rainfall_sql,
            landslide_sql=self.landslide_sql,
        )
        self.crew_agent = Agent(
            role="Environment & Maritime Agent",
            goal=(
                "Retrieve and analyze weather data for disaster management. "
                "ALWAYS use at least one tool to fetch real data before answering. "
                "Never answer from your own knowledge alone — call a tool first."
            ),
            backstory=(
                "You are an expert meteorologist and maritime analyst. "
                "You provide weather intelligence for disaster management operations, "
                "including rainfall, landslide risk, and severe weather identification."
            ),
            tools=self.tools,
            llm=get_crewai_llm(),
            verbose=True,
            max_retry_limit=3,
            max_iter=5,
        )

        # DSPy for structured response generation
        self.response_predictor = dspy.ChainOfThought(GenerateWeatherResponse)

    def process(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process weather-related query using CrewAI agent + DSPy response synthesis.
        """
        logger.info(f"🌤️  Weather Agent processing: {query}")

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
                f"Weather query: {query}\n"
                f"Context: {context_str}\n"
                "Step 1: Call get_weather_by_city or get_current_weather to fetch real data.\n"
                "Step 2: If rainfall or landslide risk is asked, also call get_gpm_rainfall or get_landslide_snapshot.\n"
                "Step 3: Report temperature, wind, precipitation, warnings, and any severe hazards."
            ),
            expected_output=(
                "Meteorological assessment with current conditions, hazards, "
                "and operational impact for disaster management."
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
            logger.warning(f"⚠️ CrewAI weather execution failed: {e}")
            logger.info("🔄 Falling back to direct tool queries...")
            raw_output = self._fallback_direct_query(query)

        # Analyze severity from raw output
        severity_analysis = self._analyze_severity_from_output(raw_output)

        # Use DSPy for structured response generation
        try:
            dspy_result = self.response_predictor(
                query=query,
                weather_data=raw_output,
                severity_analysis=json.dumps(severity_analysis),
            )
            answer = dspy_result.response
        except Exception as e:
            logger.warning(f"⚠️ DSPy weather response generation failed: {e}")
            answer = raw_output

        return {
            "agent": "weather",
            "query": query,
            "answer": answer,
            "raw_output": raw_output,
            "severity_analysis": severity_analysis,
            "data_count": 1,
            "status": "success" if "Error" not in raw_output else "partial",
        }

    def _analyze_severity_from_output(self, raw_output: str) -> Dict[str, Any]:
        """Basic severity analysis from raw tool output."""
        severity = {
            "level": "normal",
            "warnings": [],
            "flight_impact": "minimal",
            "hazards": [],
        }

        output_lower = raw_output.lower()
        if any(w in output_lower for w in ["storm", "thunder", "tornado", "hurricane", "cyclone"]):
            severity["level"] = "critical"
            severity["hazards"].append("Severe weather system")
            severity["flight_impact"] = "severe"
        elif any(w in output_lower for w in ["high wind", "strong wind", "gale"]):
            severity["level"] = "high"
            severity["hazards"].append("Strong winds")
            severity["flight_impact"] = "moderate"
        elif any(w in output_lower for w in ["fog", "low visibility", "icing"]):
            severity["level"] = "moderate"
            severity["hazards"].append("Visibility or icing hazard")
            severity["flight_impact"] = "moderate"

        return severity

    def _fallback_direct_query(self, query: str) -> str:
        """Bypass CrewAI and call tools directly when LLM tool calling fails."""
        results = []
        q = query.lower()

        try:
            vr = self.vector_db.search("weather", query, n_results=5)
            docs = vr.get("documents", [])
            if docs and docs[0]:
                flat = docs[0] if isinstance(docs[0], list) else docs
                results.append("Weather knowledge base:\n" + "\n".join(str(d) for d in flat[:5]))
        except Exception:
            pass

        city_names = []
        for city in ["mangalore", "udupi", "london", "new york", "mumbai",
                      "delhi", "bangalore", "chennai", "kolkata", "hyderabad"]:
            if city in q:
                city_names.append(city)

        for city in city_names:
            try:
                weather = self.api_tool.get_weather_by_city(city)
                if weather and "error" not in weather:
                    results.append(f"Weather for {city}:\n" + json.dumps(weather, default=str))
            except Exception:
                pass

        if not city_names:
            try:
                weather = self.api_tool.get_current_weather(12.9141, 74.8560)
                if weather and "error" not in weather:
                    results.append("Current weather (Mangalore):\n" + json.dumps(weather, default=str))
            except Exception:
                pass

        try:
            forecasts = self.forecast_sql.get_latest_forecasts(limit=10)
            if forecasts:
                results.append("Latest forecasts:\n" + json.dumps(forecasts[:5], default=str))
        except Exception:
            pass

        try:
            rainfall = self.rainfall_sql.get_latest_rainfall(limit=10)
            if rainfall:
                results.append("Latest rainfall:\n" + json.dumps(rainfall[:5], default=str))
        except Exception:
            pass

        if any(w in q for w in ["landslide", "slope", "risk", "lhasa"]):
            try:
                snapshot = self.landslide_sql.get_latest_snapshot(limit=10)
                if snapshot:
                    results.append("Landslide snapshot:\n" + json.dumps(snapshot[:5], default=str))
            except Exception:
                pass

        return "\n\n".join(results) if results else "No weather data available for this query."

    # ── Helper methods ──────────────────────────────────────────────────────

    def get_weather_for_location(self, lat: float, lon: float) -> Dict:
        return self.api_tool.get_current_weather(lat, lon)

    def get_weather_for_disaster_area(self, lat: float, lon: float) -> Dict:
        current = self.api_tool.get_current_weather(lat, lon)
        forecast = self.api_tool.get_forecast(lat, lon, days=3)
        return {
            "current": current,
            "forecast": forecast,
            "severity": self._analyze_severity_from_output(json.dumps(current, default=str)),
        }


if __name__ == "__main__":
    db = DatabaseManager()
    vector_db = VectorDBManager()
    agent = WeatherAgent(db, vector_db)

    result = agent.process("What's the weather in London?")
    logger.info(json.dumps(result, indent=2, default=str))
