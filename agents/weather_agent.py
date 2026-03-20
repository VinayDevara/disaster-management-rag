"""
Weather Agent - Handles weather-related queries
Uses Weather API, Vector DB, and LLM reasoning
"""
from typing import Dict, List, Optional, Any
from utils.llm_client import get_llm_client
from utils.database import DatabaseManager
from utils.vector_db import VectorDBManager
from tools.sql_tool import WeatherSQLTool
from tools.api_tool import WeatherAPITool
import json
import dspy
from pydantic import BaseModel, Field

class WeatherToolSelection(BaseModel):
    selected_tools: list[str] = Field(description="List of tools to use")
    parameters: dict = Field(description="Parameters for each tool. You MUST analyze the query and explicitly provide dynamic values for integers like 'limit' (e.g., 50 for broad queries, 5 for specific) or 'days' rather than letting the system use arbitrary defaults.")
    reasoning: str = Field(description="Why these tools and specific dynamic parameters were selected")

class SelectWeatherTools(dspy.Signature):
    """Analyze a weather query and determine which tools to use for an Environment & Maritime Agent.
    
    Tools:
    1. get_current_weather
    2. get_weather_by_city
    3. get_forecast
    4. get_weather_events_by_type
    5. get_weather_events_in_area
    6. vector_search
    """
    query: str = dspy.InputField()
    context: str = dspy.InputField()
    extracted_locations: str = dspy.InputField()
    extracted_coordinates: str = dspy.InputField()
    output: WeatherToolSelection = dspy.OutputField()

class GenerateWeatherResponse(dspy.Signature):
    """Generate a comprehensive meteorological and maritime assessment based on weather data."""
    query: str = dspy.InputField()
    weather_data: str = dspy.InputField()
    severity_analysis: str = dspy.InputField()
    response: str = dspy.OutputField(desc="""1. Conditions/forecast\n2. Temperature\n3. Wind/visibility/maritime state\n4. Aviation impact\n5. Warnings""")

class WeatherAgent:
    """
    Specialized agent for weather data analysis
    
    Capabilities:
    - Real-time weather data retrieval
    - Weather forecasting
    - Historical weather event analysis
    - Severe weather identification
    - Geographic weather patterns
    """
    
    def __init__(self, db_manager: DatabaseManager, vector_db: VectorDBManager):
        self.llm = get_llm_client()
        self.db = db_manager
        self.vector_db = vector_db
        self.sql_tool = WeatherSQLTool(db_manager)
        self.api_tool = WeatherAPITool()
        self.tool_predictor = dspy.Predict(SelectWeatherTools)
        self.response_predictor = dspy.ChainOfThought(GenerateWeatherResponse)
        
        self.system_prompt = """You are an Environment & Maritime Agent for disaster management.

Your capabilities:
1. Retrieve real-time weather data for any location.
2. Analyze weather patterns, forecasts, and maritime conditions (e.g., cyclones, tidal surges).
3. Identify severe weather conditions.
4. Correlate weather with flight operations and disasters.

Guidelines:
- Provide temperature in Celsius and Fahrenheit
- Include wind speed and direction, focusing on maritime severity
- Flag conditions hazardous for aviation or coastal regions
- Consider visibility and cloud cover
- Relate weather to operational impacts
"""
    
    def process(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process weather-related query
        
        Args:
            query: User query about weather
            context: Optional context from orchestrator
            
        Returns:
            Response dictionary with data and answer
        """
        print(f"🌤️  Weather Agent processing: {query}")
        
        # Extract entities from query
        entities = self.llm.extract_entities(query)
        locations = entities.get("locations", [])
        coordinates = entities.get("coordinates", [])
        
        # Use DSPy to determine tools and parameters
        try:
            result = self.tool_predictor(
                query=query,
                context=json.dumps(context) if context else 'None',
                extracted_locations=str(locations),
                extracted_coordinates=str(coordinates)
            )
            decision = result.output.model_dump() if hasattr(result.output, 'model_dump') else result.output.dict()
        except Exception as e:
            print(f"⚠️ DSPy tool selection failed: {e}")
            decision = {
                "selected_tools": ["vector_search"],
                "parameters": {"vector_search": {"query": query}},
                "reasoning": "Default fallback"
            }
        
        # Execute selected tools
        tool_results = {}
        
        for tool_name in decision.get("selected_tools", []):
            params = decision.get("parameters", {}).get(tool_name, {})
            
            try:
                if tool_name == "get_current_weather":
                    lat = params.get("lat", 0)
                    lon = params.get("lon", 0)
                    tool_results[tool_name] = self.api_tool.get_current_weather(lat, lon)
                
                elif tool_name == "get_weather_by_city":
                    city = params.get("city", "")
                    country = params.get("country_code")
                    tool_results[tool_name] = self.api_tool.get_weather_by_city(city, country)
                
                elif tool_name == "get_forecast":
                    lat = params.get("lat", 0)
                    lon = params.get("lon", 0)
                    days = params.get("days")
                    tool_results[tool_name] = self.api_tool.get_forecast(lat, lon, days)
                
                elif tool_name == "get_weather_events_by_type":
                    event_type = params.get("type", "")
                    tool_results[tool_name] = self.sql_tool.get_weather_events_by_type(event_type, params.get("limit"))
                
                elif tool_name == "get_weather_events_in_area":
                    tool_results[tool_name] = self.sql_tool.get_weather_events_in_area(
                        params.get("lat_min", 0),
                        params.get("lat_max", 0),
                        params.get("lon_min", 0),
                        params.get("lon_max", 0),
                        params.get("limit")
                    )
                
                elif tool_name == "vector_search":
                    search_query = params.get("query", query)
                    search_results = self.vector_db.search("weather", search_query, n_results=10)
                    tool_results[tool_name] = {
                        "documents": search_results["documents"],
                        "metadatas": search_results["metadatas"]
                    }
            
            except Exception as e:
                tool_results[tool_name] = {"error": str(e)}
        
        # Analyze weather severity
        severity_analysis = self._analyze_severity(tool_results)
        
        # Generate final response
        try:
            result = self.response_predictor(
                query=query,
                weather_data=json.dumps(tool_results, default=str),
                severity_analysis=json.dumps(severity_analysis)
            )
            final_answer = result.response
        except Exception as e:
            print(f"⚠️ DSPy response generation failed: {e}")
            final_answer = f"Error generating meteorological response: {e}\nRaw Analysis: {json.dumps(severity_analysis)}"
        
        return {
            "agent": "weather",
            "query": query,
            "tool_selection": decision,
            "tool_results": tool_results,
            "severity_analysis": severity_analysis,
            "answer": final_answer,
            "data_count": len(tool_results)
        }
    
    def _analyze_severity(self, tool_results: Dict) -> Dict[str, Any]:
        """
        Analyze weather severity from retrieved data
        
        Returns:
            Severity assessment dictionary
        """
        severity = {
            "level": "normal",
            "warnings": [],
            "flight_impact": "minimal",
            "hazards": []
        }
        
        # Check current weather
        for tool_name, data in tool_results.items():
            if "current_weather" in tool_name or "weather_by_city" in tool_name:
                if isinstance(data, dict) and "error" not in data:
                    # Wind check
                    wind_speed = data.get("wind_speed", 0)
                    if wind_speed > 50:
                        severity["warnings"].append(f"High winds: {wind_speed} km/h")
                        severity["level"] = "high"
                        severity["hazards"].append("Strong winds")
                    
                    # Visibility check
                    visibility = data.get("visibility", 10000)
                    if visibility < 1000:
                        severity["warnings"].append(f"Low visibility: {visibility}m")
                        severity["level"] = "high"
                        severity["hazards"].append("Poor visibility")
                    
                    # Weather type check
                    weather = data.get("weather", "").lower()
                    if any(w in weather for w in ["storm", "thunder", "tornado"]):
                        severity["warnings"].append(f"Severe weather: {weather}")
                        severity["level"] = "critical"
                        severity["hazards"].append("Severe weather system")
                        severity["flight_impact"] = "severe"
                    
                    # Temperature extremes
                    temp = data.get("temperature", 20)
                    if temp < -20:
                        severity["warnings"].append(f"Extreme cold: {temp}°C")
                        severity["hazards"].append("Extreme cold")
                    elif temp > 40:
                        severity["warnings"].append(f"Extreme heat: {temp}°C")
                        severity["hazards"].append("Extreme heat")
        
        if severity["warnings"]:
            severity["flight_impact"] = "moderate" if severity["level"] == "normal" else "severe"
        
        return severity
    
    def get_weather_for_location(self, lat: float, lon: float) -> Dict:
        """Helper method to get weather for coordinates"""
        return self.api_tool.get_current_weather(lat, lon)
    
    def get_weather_for_disaster_area(self, lat: float, lon: float) -> Dict:
        """Get weather conditions in disaster area"""
        current = self.api_tool.get_current_weather(lat, lon)
        forecast = self.api_tool.get_forecast(lat, lon, days=3)
        
        return {
            "current": current,
            "forecast": forecast,
            "severity": self._analyze_severity({"current": current})
        }


if __name__ == "__main__":
    # Test weather agent
    db = DatabaseManager()
    vector_db = VectorDBManager()
    agent = WeatherAgent(db, vector_db)
    
    result = agent.process("What's the weather in London?")
    print(json.dumps(result, indent=2, default=str))