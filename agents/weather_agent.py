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
        
        self.system_prompt = """You are a Weather Analysis Specialist Agent for disaster management.

Your capabilities:
1. Retrieve real-time weather data for any location
2. Analyze weather patterns and forecasts
3. Identify severe weather conditions
4. Correlate weather with flight operations and disasters
5. Provide meteorological assessments

Available tools:
- get_current_weather(lat, lon): Get current weather at coordinates
- get_weather_by_city(city, country_code): Get weather for city
- get_forecast(lat, lon, days): Get weather forecast
- get_weather_events_by_type(type): Query historical weather events
- get_weather_events_in_area(lat_min, lat_max, lon_min, lon_max): Query events in area
- vector_search(query): Semantic search weather data

Weather severity assessment:
- Wind speed > 50 km/h: High wind warning
- Visibility < 1000m: Low visibility warning
- Temperature extremes: < -20°C or > 40°C
- Storms, thunderstorms, heavy rain: Flight hazards
- Snow, ice: Ground operations impact

Guidelines:
- Provide temperature in Celsius and Fahrenheit
- Include wind speed and direction
- Flag conditions hazardous for aviation
- Consider visibility and cloud cover
- Relate weather to operational impacts

When responding:
1. Determine if real-time data or historical data is needed
2. Retrieve appropriate weather information
3. Analyze conditions for safety implications
4. Provide actionable meteorological insights
5. Include coordinates and timestamps
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
        
        # Use LLM to determine tools and parameters
        tool_selection_prompt = f"""Analyze this weather query and determine which tools to use.

Query: {query}

Context: {json.dumps(context) if context else 'None'}

Extracted locations: {locations}
Extracted coordinates: {coordinates}

Available tools:
1. get_current_weather - Real-time weather at coordinates
2. get_weather_by_city - Real-time weather for city
3. get_forecast - Weather forecast (up to 5 days)
4. get_weather_events_by_type - Historical weather events
5. get_weather_events_in_area - Weather events in geographic area
6. vector_search - Semantic search historical data

Return JSON:
{{
  "selected_tools": ["tool_name"],
  "parameters": {{"tool_name": {{"param": "value"}}}},
  "reasoning": "Explanation"
}}

Extract cities, coordinates, or areas from the query for parameters.
Determine if real-time (API) or historical (database) data is needed.
"""
        
        tool_decision = self.llm.generate(
            prompt=tool_selection_prompt,
            system_prompt=self.system_prompt,
            json_mode=True,
            temperature=0.3
        )
        
        try:
            decision = json.loads(tool_decision)
        except:
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
                    days = params.get("days", 3)
                    tool_results[tool_name] = self.api_tool.get_forecast(lat, lon, days)
                
                elif tool_name == "get_weather_events_by_type":
                    event_type = params.get("type", "")
                    tool_results[tool_name] = self.sql_tool.get_weather_events_by_type(event_type)
                
                elif tool_name == "get_weather_events_in_area":
                    tool_results[tool_name] = self.sql_tool.get_weather_events_in_area(
                        params.get("lat_min", 0),
                        params.get("lat_max", 0),
                        params.get("lon_min", 0),
                        params.get("lon_max", 0)
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
        response_prompt = f"""Based on the query and weather data, provide a comprehensive meteorological assessment.

Query: {query}

Weather Data:
{json.dumps(tool_results, indent=2, default=str)}

Severity Analysis:
{json.dumps(severity_analysis, indent=2)}

Provide:
1. Current weather conditions or forecast
2. Temperature (Celsius and Fahrenheit)
3. Wind conditions and visibility
4. Aviation impact assessment
5. Any severe weather warnings
6. Operational recommendations

Be specific about hazards and their implications for flight operations and disaster response.
"""
        
        final_answer = self.llm.generate(
            prompt=response_prompt,
            system_prompt=self.system_prompt,
            temperature=0.7
        )
        
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
