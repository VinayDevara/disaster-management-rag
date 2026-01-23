"""
Flight Agent - Handles ADS-B flight tracking queries
Uses SQL, Vector DB, and LLM reasoning
"""
from typing import Dict, List, Optional, Any
from utils.llm_client import get_llm_client
from utils.database import DatabaseManager
from utils.vector_db import VectorDBManager
from tools.sql_tool import SQLTool
import json

class FlightAgent:
    """
    Specialized agent for flight tracking and ADS-B data analysis
    
    Capabilities:
    - Query flight information by callsign, hex, location
    - Track flight trajectories
    - Identify emergency situations
    - Analyze flight patterns
    """
    
    def __init__(self, db_manager: DatabaseManager, vector_db: VectorDBManager):
        self.llm = get_llm_client()
        self.db = db_manager
        self.vector_db = vector_db
        self.sql_tool = SQLTool(db_manager)
        
        self.system_prompt = """You are a Flight Tracking Specialist Agent for disaster management.

Your capabilities:
1. Query ADS-B flight data using SQL
2. Search flight information using semantic search
3. Analyze flight patterns and trajectories
4. Identify emergency situations and diversions
5. Correlate flight data with geographic locations

Available tools:
- get_all_flights(limit): Get recent flights
- get_flight_by_callsign(callsign): Search by flight number
- get_flight_by_hex(hex_code): Search by aircraft hex code
- get_flights_in_area(lat_min, lat_max, lon_min, lon_max): Get flights in area
- get_emergency_flights(): Get flights with emergency status
- get_flight_trajectory(hex_code): Get flight path
- get_flights_near_location(lat, lon, radius_deg): Get flights near coordinates
- vector_search(query): Semantic search across flight data

Guidelines:
- Always verify flight callsigns and hex codes
- Consider altitude, speed, and location context
- Flag emergency squawks (7500, 7600, 7700)
- Provide coordinates when relevant
- Use vector search for natural language queries
- Be precise with technical aviation terminology

When responding:
1. First determine which tool(s) to use based on the query
2. Execute the appropriate queries
3. Analyze the results using your aviation expertise
4. Provide clear, actionable information
5. Include relevant coordinates and timestamps
"""
    
    def process(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process flight-related query
        
        Args:
            query: User query about flights
            context: Optional context from orchestrator
            
        Returns:
            Response dictionary with data and answer
        """
        print(f"✈️  Flight Agent processing: {query}")
        
        # Use LLM to determine which tools to use
        tool_selection_prompt = f"""Analyze this flight-related query and determine which tools to use.

Query: {query}

Context: {json.dumps(context) if context else 'None'}

Available tools:
1. get_all_flights - Get recent flights
2. get_flight_by_callsign - Search specific flight number
3. get_flight_by_hex - Search by aircraft identifier
4. get_flights_in_area - Search by geographic bounding box
5. get_emergency_flights - Find emergency situations
6. get_flight_trajectory - Get flight path history
7. get_flights_near_location - Find flights near coordinates
8. vector_search - Semantic search for complex queries

Return a JSON object with:
{{
  "selected_tools": ["tool_name1", "tool_name2"],
  "parameters": {{"tool_name1": {{"param": "value"}}, ...}},
  "reasoning": "Why these tools were selected"
}}

If the query mentions specific flight numbers, hex codes, or locations, extract them for parameters.
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
                "reasoning": "Default to semantic search"
            }
        
        # Execute selected tools
        tool_results = {}
        
        for tool_name in decision.get("selected_tools", []):
            params = decision.get("parameters", {}).get(tool_name, {})
            
            try:
                if tool_name == "get_all_flights":
                    limit = params.get("limit", 100)
                    tool_results[tool_name] = self.sql_tool.get_all_flights(limit)
                
                elif tool_name == "get_flight_by_callsign":
                    callsign = params.get("callsign", "")
                    tool_results[tool_name] = self.sql_tool.get_flight_by_callsign(callsign)
                
                elif tool_name == "get_flight_by_hex":
                    hex_code = params.get("hex_code", "")
                    tool_results[tool_name] = self.sql_tool.get_flight_by_hex(hex_code)
                
                elif tool_name == "get_flights_in_area":
                    tool_results[tool_name] = self.sql_tool.get_flights_in_area(
                        params.get("lat_min", 0),
                        params.get("lat_max", 0),
                        params.get("lon_min", 0),
                        params.get("lon_max", 0),
                        params.get("limit", 100)
                    )
                
                elif tool_name == "get_emergency_flights":
                    tool_results[tool_name] = self.sql_tool.get_emergency_flights()
                
                elif tool_name == "get_flight_trajectory":
                    hex_code = params.get("hex_code", "")
                    tool_results[tool_name] = self.sql_tool.get_flight_trajectory(hex_code)
                
                elif tool_name == "get_flights_near_location":
                    tool_results[tool_name] = self.sql_tool.get_flights_near_location(
                        params.get("lat", 0),
                        params.get("lon", 0),
                        params.get("radius_deg", 1.0)
                    )
                
                elif tool_name == "vector_search":
                    search_query = params.get("query", query)
                    search_results = self.vector_db.search("flights", search_query, n_results=10)
                    tool_results[tool_name] = {
                        "documents": search_results["documents"],
                        "metadatas": search_results["metadatas"]
                    }
            
            except Exception as e:
                tool_results[tool_name] = {"error": str(e)}
        
        # Generate final response using LLM
        response_prompt = f"""Based on the query and retrieved data, provide a comprehensive answer.

Query: {query}

Tool Results:
{json.dumps(tool_results, indent=2, default=str)}

Provide:
1. Direct answer to the query
2. Relevant flight details (callsign, position, altitude, status)
3. Any emergency or safety concerns
4. Geographic context if applicable
5. Timestamps and tracking information

Be specific and technical where appropriate. Include coordinates for mapping.
"""
        
        final_answer = self.llm.generate(
            prompt=response_prompt,
            system_prompt=self.system_prompt,
            temperature=0.7
        )
        
        return {
            "agent": "flight",
            "query": query,
            "tool_selection": decision,
            "tool_results": tool_results,
            "answer": final_answer,
            "data_count": sum(len(v) if isinstance(v, list) else 1 for v in tool_results.values())
        }
    
    def get_emergency_status(self) -> List[Dict]:
        """Get current emergency flights - helper method"""
        return self.sql_tool.get_emergency_flights(limit=50)
    
    def get_flights_in_disaster_area(
        self,
        lat: float,
        lon: float,
        radius_deg: float = 2.0
    ) -> List[Dict]:
        """
        Get flights potentially affected by disaster in area
        
        Args:
            lat: Disaster latitude
            lon: Disaster longitude
            radius_deg: Search radius in degrees
            
        Returns:
            List of affected flights
        """
        return self.sql_tool.get_flights_near_location(lat, lon, radius_deg)


if __name__ == "__main__":
    # Test flight agent
    from config.config import Config
    
    db = DatabaseManager()
    vector_db = VectorDBManager()
    agent = FlightAgent(db, vector_db)
    
    # Test query
    result = agent.process("Show me all emergency flights")
    print(json.dumps(result, indent=2, default=str))
