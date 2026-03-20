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
import dspy
from pydantic import BaseModel, Field

class FlightToolSelection(BaseModel):
    selected_tools: list[str] = Field(description="List of tools to use")
    parameters: dict = Field(description="Parameters for each tool. You MUST analyze the query and explicitly provide dynamic values for integers like 'limit' (e.g., 50 for broad queries, 5 for specific), 'radius_deg', 'min_altitude', or 'hours' rather than letting the system use arbitrary defaults.")
    reasoning: str = Field(description="Why these tools and specific dynamic parameters were selected")

class SelectFlightTools(dspy.Signature):
    """Analyze a flight-related query and determine which tools to use.
    
    Tools:
    1. get_all_flights - Get recent flights
    2. get_flight_by_callsign - Search specific flight number
    3. get_flight_by_hex - Search by aircraft identifier
    4. get_flights_in_area - Search by geographic bounding box
    5. get_emergency_flights - Find emergency situations
    6. get_flight_trajectory - Get flight path history
    7. get_flights_near_location - Find flights near coordinates
    8. vector_search - Semantic search for complex queries
    """
    query: str = dspy.InputField()
    context: str = dspy.InputField()
    output: FlightToolSelection = dspy.OutputField()

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
        self.tool_predictor = dspy.Predict(SelectFlightTools)
        self.response_predictor = dspy.ChainOfThought(GenerateFlightResponse)
        
        self.system_prompt = """You are a Flight & Aviation Surveillance Agent for disaster management.

Your capabilities:
1. Query ADS-B flight data using SQL
2. Search flight information using semantic search
3. Analyze flight patterns and trajectories
4. Identify emergency situations and diversions
5. Assist search & rescue operations by tracking relevant flights within a disaster area.

Guidelines:
- Always verify flight callsigns and hex codes
- Consider altitude, speed, and location context
- Flag emergency squawks (7500, 7600, 7700)
- Provide coordinates when relevant
- Use vector search for natural language queries
- Be precise with technical aviation terminology
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
        
        # Use DSPy to determine which tools to use
        try:
            result = self.tool_predictor(
                query=query,
                context=json.dumps(context) if context else 'None'
            )
            decision = result.output.model_dump() if hasattr(result.output, 'model_dump') else result.output.dict()
        except Exception as e:
            print(f"⚠️ DSPy tool selection failed: {e}")
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
                    limit = params.get("limit")
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
                        params.get("limit")
                    )
                
                elif tool_name == "get_emergency_flights":
                    tool_results[tool_name] = self.sql_tool.get_emergency_flights(params.get("limit"))
                
                elif tool_name == "get_flight_trajectory":
                    hex_code = params.get("hex_code", "")
                    tool_results[tool_name] = self.sql_tool.get_flight_trajectory(hex_code)
                
                elif tool_name == "get_flights_near_location":
                    tool_results[tool_name] = self.sql_tool.get_flights_near_location(
                        params.get("lat", 0),
                        params.get("lon", 0),
                        params.get("radius_deg"),
                        params.get("limit")
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
        
        # Generate final response using DSPy
        try:
            result = self.response_predictor(
                query=query,
                tool_results=json.dumps(tool_results, indent=2, default=str)
            )
            final_answer = result.response
        except Exception as e:
            print(f"⚠️ DSPy flight response generation failed: {e}")
            final_answer = f"Error generating flight response: {e}"
        
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