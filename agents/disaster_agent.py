"""
Disaster Agent - Handles disaster event queries
Uses Disaster API, Vector DB, and LLM reasoning
"""
from typing import Dict, List, Optional, Any
from utils.llm_client import get_llm_client
from utils.database import DatabaseManager
from utils.vector_db import VectorDBManager
from tools.sql_tool import DisasterSQLTool
from tools.api_tool import DisasterAPITool
import json
import dspy
from pydantic import BaseModel, Field

class DisasterToolSelection(BaseModel):
    selected_tools: list[str] = Field(description="List of tools to use")
    parameters: dict = Field(description="Parameters for each tool, e.g. {'get_events_in_area': {'lat_min': 10, 'limit': 20}}. You MUST analyze the query and explicitly provide dynamic values for integers like 'limit' (e.g., 50 for broad queries, 5 for specific) or 'days' rather than letting the system use arbitrary defaults.")
    reasoning: str = Field(description="Explanation for tool selection and dynamic parameter choices")
    needs_realtime: bool = Field(description="Whether real-time data is needed", default=True)

class SelectDisasterTools(dspy.Signature):
    """Analyze a disaster query and determine which tools to use for an Evacuation & Logistics Agent.
    
    Tools:
    1. get_active_events - Current active disasters
    2. get_events_by_category - Disasters by type
    3. get_events_in_area - Disasters in geographic bounding box
    4. get_event_details - Detailed info
    5. get_disaster_events_by_type - Historical disasters
    6. get_recent_disasters - Recent disasters
    7. vector_search - Semantic search
    """
    query: str = dspy.InputField()
    context: str = dspy.InputField()
    extracted_disaster_types: str = dspy.InputField()
    extracted_locations: str = dspy.InputField()
    output: DisasterToolSelection = dspy.OutputField()

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

class DisasterAgent:
    """
    Specialized agent for disaster event monitoring and analysis
    
    Capabilities:
    - Track active natural disasters
    - Query historical disaster events
    - Analyze disaster impact areas
    - Correlate disasters with flights and weather
    - Provide disaster severity assessments
    """
    
    def __init__(self, db_manager: DatabaseManager, vector_db: VectorDBManager):
        self.llm = get_llm_client()
        self.db = db_manager
        self.vector_db = vector_db
        self.sql_tool = DisasterSQLTool(db_manager)
        self.api_tool = DisasterAPITool()
        self.tool_predictor = dspy.Predict(SelectDisasterTools)
        self.response_predictor = dspy.ChainOfThought(GenerateDisasterResponse)
        
        self.system_prompt = """You are an Evacuation & Logistics Agent for disaster management.

Your capabilities:
1. Rapid generation of authenticated urban evacuation plans.
2. Comprehensive emergency logistics planning.
3. Analyze disaster impact zones and severity.
4. Correlate disasters with aviation operations.

Severity assessment factors:
- Geographic extent and population affected.
- Infrastructure impact and logistics.
- Evacuation route viability.
- Aviation disruption potential.
"""
    
    def process(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process disaster-related query
        
        Args:
            query: User query about disasters
            context: Optional context from orchestrator
            
        Returns:
            Response dictionary with data and answer
        """
        print(f"🔥 Disaster Agent processing: {query}")
        
        # Extract entities
        entities = self.llm.extract_entities(query)
        disaster_types = entities.get("disaster_types", [])
        locations = entities.get("locations", [])
        
        # Determine tools to use
        try:
            result = self.tool_predictor(
                query=query,
                context=json.dumps(context) if context else 'None',
                extracted_disaster_types=str(disaster_types),
                extracted_locations=str(locations)
            )
            decision = result.output.model_dump() if hasattr(result.output, 'model_dump') else result.output.dict()
        except Exception as e:
            print(f"⚠️ DSPy tool selection failed: {e}")
            decision = {
                "selected_tools": ["get_active_events"],
                "parameters": {},
                "reasoning": "Default to active events"
            }
        
        # Execute tools
        tool_results = {}
        
        for tool_name in decision.get("selected_tools", []):
            params = decision.get("parameters", {}).get(tool_name, {})
            
            try:
                if tool_name == "get_active_events":
                    tool_results[tool_name] = self.api_tool.get_active_events(params.get("limit"))
                
                elif tool_name == "get_events_by_category":
                    tool_results[tool_name] = self.api_tool.get_events_by_category(
                        params.get("category"),
                        params.get("limit")
                    )
                
                elif tool_name == "get_events_in_area":
                    tool_results[tool_name] = self.api_tool.get_events_in_area(
                        params.get("lat_min", 0),
                        params.get("lat_max", 0),
                        params.get("lon_min", 0),
                        params.get("lon_max", 0),
                        params.get("limit")
                    )
                
                elif tool_name == "get_event_details":
                    tool_results[tool_name] = self.api_tool.get_event_details(params.get("event_id"))
                
                elif tool_name == "get_disaster_events_by_type":
                    tool_results[tool_name] = self.sql_tool.get_disaster_events_by_type(
                        params.get("type"),
                        params.get("limit")
                    )
                
                elif tool_name == "get_recent_disasters":
                    tool_results[tool_name] = self.sql_tool.get_recent_disasters(
                        params.get("days"),
                        params.get("limit")
                    )
                
                elif tool_name == "vector_search":
                    search_query = params.get("query", query)
                    search_results = self.vector_db.search("disasters", search_query, n_results=10)
                    tool_results[tool_name] = {
                        "documents": search_results["documents"],
                        "metadatas": search_results["metadatas"]
                    }
            
            except Exception as e:
                tool_results[tool_name] = {"error": str(e)}
        
        # Analyze disaster severity and impact
        impact_analysis = self._analyze_impact(tool_results)
        
        # Generate response
        try:
            result = self.response_predictor(
                query=query,
                disaster_data=json.dumps(tool_results, default=str),
                impact_analysis=json.dumps(impact_analysis)
            )
            final_answer = result.response
        except Exception as e:
            print(f"⚠️ DSPy response generation failed: {e}")
            final_answer = f"Error generating response: {e}\n\nRaw Data:\n{json.dumps(impact_analysis)}"
        
        return {
            "agent": "disaster",
            "query": query,
            "tool_selection": decision,
            "tool_results": tool_results,
            "impact_analysis": impact_analysis,
            "answer": final_answer,
            "event_count": sum(len(v) if isinstance(v, list) else 1 for v in tool_results.values())
        }
    
    def _analyze_impact(self, tool_results: Dict) -> Dict[str, Any]:
        """
        Analyze disaster impact from retrieved data
        
        Returns:
            Impact assessment dictionary
        """
        impact = {
            "severity": "low",
            "affected_areas": [],
            "event_types": [],
            "aviation_risk": "minimal",
            "response_priority": "routine",
            "total_events": 0
        }
        
        all_events = []
        
        # Collect all events from results
        for tool_name, data in tool_results.items():
            if isinstance(data, list):
                all_events.extend(data)
                impact["total_events"] += len(data)
        
        # Analyze events
        high_severity_count = 0
        event_type_counts = {}
        
        for event in all_events:
            if isinstance(event, dict):
                # Track event types
                event_type = event.get("event_type", "unknown")
                event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
                
                # Extract locations
                location = event.get("location_name") or f"{event.get('lat', 'N/A')}, {event.get('lon', 'N/A')}"
                if location not in impact["affected_areas"]:
                    impact["affected_areas"].append(location)
                
                # Check severity indicators
                title = event.get("title", "").lower()
                if any(word in title for word in ["major", "severe", "catastrophic", "extreme"]):
                    high_severity_count += 1
        
        # Determine overall severity
        if high_severity_count > 5:
            impact["severity"] = "critical"
            impact["aviation_risk"] = "high"
            impact["response_priority"] = "immediate"
        elif high_severity_count > 2:
            impact["severity"] = "high"
            impact["aviation_risk"] = "moderate"
            impact["response_priority"] = "urgent"
        elif impact["total_events"] > 10:
            impact["severity"] = "moderate"
            impact["aviation_risk"] = "low-moderate"
            impact["response_priority"] = "elevated"
        
        impact["event_types"] = list(event_type_counts.keys())
        impact["event_breakdown"] = event_type_counts
        
        return impact
    
    def get_disasters_near_location(self, lat: float, lon: float, radius_deg: float = 5.0) -> List[Dict]:
        """
        Get disasters near specific location
        
        Args:
            lat: Latitude
            lon: Longitude
            radius_deg: Search radius in degrees
            
        Returns:
            List of nearby disasters
        """
        return self.api_tool.get_events_in_area(
            lat - radius_deg,
            lat + radius_deg,
            lon - radius_deg,
            lon + radius_deg
        )
    
    def get_active_disasters_summary(self) -> Dict:
        """Get summary of all active disasters"""
        events = self.api_tool.get_active_events(limit=200)
        
        return {
            "total_events": len(events),
            "events": events,
            "impact_analysis": self._analyze_impact({"active": events})
        }


if __name__ == "__main__":
    # Test disaster agent
    db = DatabaseManager()
    vector_db = VectorDBManager()
    agent = DisasterAgent(db, vector_db)
    
    result = agent.process("What active wildfires are happening right now?")
    print(json.dumps(result, indent=2, default=str))