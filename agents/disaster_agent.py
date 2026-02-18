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
        
        self.system_prompt = """You are a Disaster Management Specialist Agent.

Your capabilities:
1. Monitor active natural disaster events globally
2. Analyze disaster impact zones and severity
3. Track wildfires, earthquakes, floods, storms, volcanoes
4. Correlate disasters with aviation operations
5. Provide emergency response assessments

Available tools:
- get_active_events(): Get currently active disasters (NASA EONET)
- get_events_by_category(category): Get disasters by type
- get_events_in_area(lat_min, lat_max, lon_min, lon_max): Query geographic area
- get_event_details(event_id): Get detailed event information
- get_disaster_events_by_type(type): Query historical data
- get_recent_disasters(days): Get recent disaster events
- vector_search(query): Semantic search disaster data

Disaster categories:
- Wildfires
- Earthquakes  
- Floods
- Storms (hurricanes, cyclones, typhoons)
- Volcanoes
- Landslides
- Drought
- Severe Weather

Severity assessment factors:
- Geographic extent
- Population affected
- Infrastructure impact
- Aviation disruption potential
- Emergency response requirements

Guidelines:
- Provide accurate geographic coordinates
- Include event timelines
- Assess operational impact
- Flag events affecting flight paths
- Consider cascading effects

When responding:
1. Identify relevant disaster events
2. Assess severity and impact area
3. Provide geographic context
4. Analyze aviation/operational implications
5. Include source references and timestamps
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
        tool_selection_prompt = f"""Analyze this disaster query and determine which tools to use.

Query: {query}

Context: {json.dumps(context) if context else 'None'}

Extracted disaster types: {disaster_types}
Extracted locations: {locations}

Available tools:
1. get_active_events - Current active disasters worldwide
2. get_events_by_category - Disasters by type (wildfires, earthquakes, etc.)
3. get_events_in_area - Disasters in geographic bounding box
4. get_event_details - Detailed info about specific event
5. get_disaster_events_by_type - Historical disasters by type
6. get_recent_disasters - Recent disasters (last N days)
7. vector_search - Semantic search

Return JSON:
{{
  "selected_tools": ["tool_name"],
  "parameters": {{"tool_name": {{"param": "value"}}}},
  "reasoning": "Explanation",
  "needs_realtime": true/false
}}

If query asks about "current" or "active" disasters, use API tools (get_active_events).
For historical analysis, use database tools.
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
                    limit = params.get("limit", 100)
                    tool_results[tool_name] = self.api_tool.get_active_events(limit)
                
                elif tool_name == "get_events_by_category":
                    category = params.get("category", "wildfires")
                    tool_results[tool_name] = self.api_tool.get_events_by_category(category)
                
                elif tool_name == "get_events_in_area":
                    tool_results[tool_name] = self.api_tool.get_events_in_area(
                        params.get("lat_min", 0),
                        params.get("lat_max", 0),
                        params.get("lon_min", 0),
                        params.get("lon_max", 0)
                    )
                
                elif tool_name == "get_event_details":
                    event_id = params.get("event_id", "")
                    tool_results[tool_name] = self.api_tool.get_event_details(event_id)
                
                elif tool_name == "get_disaster_events_by_type":
                    event_type = params.get("type", "")
                    tool_results[tool_name] = self.sql_tool.get_disaster_events_by_type(event_type)
                
                elif tool_name == "get_recent_disasters":
                    days = params.get("days", 30)
                    tool_results[tool_name] = self.sql_tool.get_recent_disasters(days)
                
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
        response_prompt = f"""Based on the query and disaster data, provide a comprehensive assessment.

Query: {query}

Disaster Data:
{json.dumps(tool_results, indent=2, default=str)}

Impact Analysis:
{json.dumps(impact_analysis, indent=2)}

Provide:
1. Summary of relevant disaster events
2. Geographic locations and coordinates
3. Event timelines and current status
4. Severity and impact assessment
5. Aviation/operational implications
6. Affected areas and populations
7. Emergency response considerations

Include specific event IDs, coordinates, and source references.
Prioritize events by severity and relevance to query.
"""
        
        final_answer = self.llm.generate(
            prompt=response_prompt,
            system_prompt=self.system_prompt,
            temperature=0.7
        )
        
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