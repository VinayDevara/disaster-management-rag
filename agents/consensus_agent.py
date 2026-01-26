"""
Consensus Agent - Correlates data from multiple agents
Performs cross-intelligence analysis and generates unified responses
"""
from typing import Dict, List, Any, Optional
from utils.llm_client import get_llm_client
from utils.database import DatabaseManager
import json
import math

class ConsensusAgent:
    """
    Consensus agent that:
    1. Receives results from multiple specialized agents
    2. Identifies correlations and patterns
    3. Performs cross-domain intelligence analysis
    4. Generates unified, coherent responses
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.llm = get_llm_client()
        self.db = db_manager
        
        self.system_prompt = """You are a Consensus Agent for disaster management cross-intelligence.

Your role is to:
1. Synthesize information from multiple specialized agents
2. Identify correlations between flight, weather, and disaster data
3. Detect patterns and causal relationships
4. Generate comprehensive, unified responses
5. Prioritize critical information

Cross-Intelligence Capabilities:
- Flight-Disaster Correlation: Identify flights affected by disasters
- Weather-Flight Correlation: Assess weather impact on aviation
- Weather-Disaster Correlation: Link weather patterns to disasters
- Geographic Correlation: Find spatial relationships
- Temporal Correlation: Identify time-based patterns

Analysis Priorities:
1. Safety-critical information (emergencies, severe weather, disasters)
2. Operational impact (flight diversions, delays, closures)
3. Geographic proximity (distance between entities)
4. Temporal relevance (current vs. historical)
5. Causality (weather causing disasters affecting flights)

Response Structure:
1. Executive Summary: Key findings and critical alerts
2. Cross-Domain Analysis: Correlations and relationships
3. Detailed Findings: Information from each domain
4. Geographic Context: Locations, coordinates, maps
5. Recommendations: Actionable insights
6. Sources: Data provenance and timestamps

When correlating data:
- Calculate geographic distances between entities
- Assess temporal overlaps
- Identify causal chains
- Quantify risk levels
- Provide confidence scores for correlations
"""
    
    def process(
        self,
        original_query: str,
        agent_results: Dict[str, Any],
        classification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process results from multiple agents and generate consensus
        """
        print(f"🤝 Consensus Agent processing {len(agent_results)} agent results")
        
        # Extract key data points from each agent
        extracted_data = self._extract_key_data(agent_results)
        
        # Perform correlation analysis
        correlations = self._find_correlations(extracted_data, agent_results)
        
        # Calculate geographic relationships
        geographic_analysis = self._analyze_geography(extracted_data)
        
        # Assess overall situation severity
        severity_assessment = self._assess_severity(agent_results, correlations)
        
        # Generate unified response using LLM
        consensus_prompt = f"""Synthesize the following information into a comprehensive response.

Original Query: {original_query}

Agent Results:
{json.dumps(agent_results, indent=2, default=str)}

Extracted Key Data:
{json.dumps(extracted_data, indent=2, default=str)}

Correlations Found:
{json.dumps(correlations, indent=2, default=str)}

Geographic Analysis:
{json.dumps(geographic_analysis, indent=2, default=str)}

Severity Assessment:
{json.dumps(severity_assessment, indent=2)}

Generate a comprehensive response that:
1. Directly answers the original query
2. Highlights critical safety information
3. Explains relevant correlations between domains
4. Provides geographic context with coordinates
5. Includes operational recommendations
6. Cites specific data points and sources

Structure your response clearly with sections for:
- Executive Summary
- Detailed Analysis
- Geographic Context
- Correlations and Insights
- Recommendations

Be specific, actionable, and prioritize safety-critical information.
"""
        
        unified_response = self.llm.generate(
            prompt=consensus_prompt,
            system_prompt=self.system_prompt,
            temperature=0.7
        )
        
        return {
            "query": original_query,
            "agent_results_summary": {
                agent: {
                    "data_count": result.get("data_count", 0),
                    "status": "success" if "answer" in result else "error"
                }
                for agent, result in agent_results.items()
            },
            "extracted_data": extracted_data,
            "correlations": correlations,
            "geographic_analysis": geographic_analysis,
            "severity_assessment": severity_assessment,
            "unified_response": unified_response,
            "confidence": self._calculate_confidence(agent_results, correlations)
        }
    
    def _extract_key_data(self, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key data points from agent results with safe type conversion"""
        extracted = {
            "flights": [],
            "disasters": [],
            "weather_conditions": [],
            "locations": set(),
            "coordinates": []
        }
        
        for agent_name, result in agent_results.items():
            tool_results = result.get("tool_results", {})
            
            if agent_name == "flight":
                # Extract flight data
                for tool_name, data in tool_results.items():
                    if isinstance(data, list):
                        for item in data[:10]:  # Limit to top 10
                            if isinstance(item, dict):
                                # Safe float conversion
                                try:
                                    lat = float(item.get("lat")) if item.get("lat") is not None else None
                                    lon = float(item.get("lon")) if item.get("lon") is not None else None
                                except (ValueError, TypeError):
                                    lat, lon = None, None

                                extracted["flights"].append({
                                    "hex": item.get("hex") or item.get("aircraft__hex"),
                                    "flight": item.get("flight") or item.get("aircraft__flight"),
                                    "lat": lat,
                                    "lon": lon,
                                    "altitude": item.get("alt_baro"),
                                    "emergency": item.get("emergency", "none")
                                })
                                
                                if lat is not None and lon is not None:
                                    extracted["coordinates"].append({
                                        "type": "flight",
                                        "lat": lat,
                                        "lon": lon,
                                        "label": item.get("flight") or item.get("hex")
                                    })
            
            elif agent_name == "disaster":
                # Extract disaster data
                for tool_name, data in tool_results.items():
                    if isinstance(data, list):
                        for item in data[:10]:
                            if isinstance(item, dict):
                                # Safe float conversion
                                try:
                                    lat = float(item.get("lat")) if item.get("lat") is not None else None
                                    lon = float(item.get("lon")) if item.get("lon") is not None else None
                                except (ValueError, TypeError):
                                    lat, lon = None, None

                                extracted["disasters"].append({
                                    "title": item.get("title"),
                                    "type": item.get("event_type"),
                                    "lat": lat,
                                    "lon": lon,
                                    "location": item.get("location_name")
                                })
                                
                                if lat is not None and lon is not None:
                                    extracted["coordinates"].append({
                                        "type": "disaster",
                                        "lat": lat,
                                        "lon": lon,
                                        "label": item.get("title") or item.get("event_type")
                                    })
            
            elif agent_name == "weather":
                # Extract weather data
                for tool_name, data in tool_results.items():
                    if isinstance(data, dict) and "error" not in data:
                        extracted["weather_conditions"].append(data)
                        
                        coords = data.get("coordinates", {})
                        # Safe float conversion
                        try:
                            lat = float(coords.get("lat")) if coords.get("lat") is not None else None
                            lon = float(coords.get("lon")) if coords.get("lon") is not None else None
                        except (ValueError, TypeError):
                            lat, lon = None, None

                        if lat is not None and lon is not None:
                            extracted["coordinates"].append({
                                "type": "weather",
                                "lat": lat,
                                "lon": lon,
                                "label": data.get("location", "Weather Station")
                            })
        
        extracted["locations"] = list(extracted["locations"])
        
        return extracted
    
    def _find_correlations(
        self,
        extracted_data: Dict[str, Any],
        agent_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Find correlations between different data domains
        """
        correlations = []
        
        # Flight-Disaster correlation
        for flight in extracted_data.get("flights", []):
            flight_lat = flight.get("lat")
            flight_lon = flight.get("lon")
            
            if flight_lat is None or flight_lon is None:
                continue
            
            for disaster in extracted_data.get("disasters", []):
                disaster_lat = disaster.get("lat")
                disaster_lon = disaster.get("lon")
                
                if disaster_lat is None or disaster_lon is None:
                    continue
                
                distance = self._calculate_distance(
                    flight_lat, flight_lon,
                    disaster_lat, disaster_lon
                )
                
                # If within 500km, consider correlated
                if distance < 500:
                    correlations.append({
                        "type": "flight-disaster",
                        "entity1": {
                            "type": "flight",
                            "id": flight.get("flight") or flight.get("hex"),
                            "location": f"{flight_lat}, {flight_lon}"
                        },
                        "entity2": {
                            "type": "disaster",
                            "id": disaster.get("title"),
                            "location": f"{disaster_lat}, {disaster_lon}"
                        },
                        "distance_km": round(distance, 2),
                        "severity": "high" if distance < 100 else "medium",
                        "description": f"Flight {flight.get('flight', 'unknown')} is {round(distance)} km from {disaster.get('title', 'disaster')}"
                    })
        
        return correlations
    
    def _calculate_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        Calculate distance between two coordinates using Haversine formula
        Returns distance in kilometers
        """
        R = 6371  # Earth's radius in km
        
        try:
            lat1_rad = math.radians(float(lat1))
            lat2_rad = math.radians(float(lat2))
            delta_lat = math.radians(float(lat2) - float(lat1))
            delta_lon = math.radians(float(lon2) - float(lon1))
            
            a = (math.sin(delta_lat / 2) ** 2 +
                 math.cos(lat1_rad) * math.cos(lat2_rad) *
                 math.sin(delta_lon / 2) ** 2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            
            return R * c
        except Exception:
            return 9999.0  # Return far distance on error
    
    def _analyze_geography(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze geographic distribution of entities"""
        coordinates = extracted_data.get("coordinates", [])
        
        if not coordinates:
            return {"status": "no_geographic_data"}
        
        # Calculate bounding box
        # Ensure all values are floats to avoid TypeError
        lats = [float(c["lat"]) for c in coordinates if c.get("lat") is not None]
        lons = [float(c["lon"]) for c in coordinates if c.get("lon") is not None]
        
        if not lats or not lons:
            return {"status": "no_valid_coordinates"}
        
        return {
            "bounding_box": {
                "north": max(lats),
                "south": min(lats),
                "east": max(lons),
                "west": min(lons)
            },
            "center": {
                "lat": sum(lats) / len(lats),
                "lon": sum(lons) / len(lons)
            },
            "entity_count": len(coordinates),
            "entity_types": {
                "flights": len([c for c in coordinates if c["type"] == "flight"]),
                "disasters": len([c for c in coordinates if c["type"] == "disaster"]),
                "weather": len([c for c in coordinates if c["type"] == "weather"])
            }
        }
    
    def _assess_severity(
        self,
        agent_results: Dict[str, Any],
        correlations: List[Dict]
    ) -> Dict[str, Any]:
        """Assess overall situation severity"""
        severity = {
            "level": "normal",
            "score": 0,
            "factors": []
        }
        
        # Check for emergencies
        for agent_name, result in agent_results.items():
            if agent_name == "flight":
                tool_results = result.get("tool_results", {})
                emergency_flights = tool_results.get("get_emergency_flights", [])
                if emergency_flights:
                    severity["score"] += len(emergency_flights) * 10
                    severity["factors"].append(f"{len(emergency_flights)} emergency flights")
            
            elif agent_name == "weather":
                weather_severity = result.get("severity_analysis", {})
                if weather_severity.get("level") == "critical":
                    severity["score"] += 20
                    severity["factors"].append("Critical weather conditions")
                elif weather_severity.get("level") == "high":
                    severity["score"] += 10
                    severity["factors"].append("Severe weather")
            
            elif agent_name == "disaster":
                impact = result.get("impact_analysis", {})
                if impact.get("severity") == "critical":
                    severity["score"] += 25
                    severity["factors"].append("Critical disaster events")
                elif impact.get("severity") == "high":
                    severity["score"] += 15
                    severity["factors"].append("High-impact disasters")
        
        # Add correlation severity
        high_severity_correlations = [c for c in correlations if c.get("severity") == "high"]
        if high_severity_correlations:
            severity["score"] += len(high_severity_correlations) * 5
            severity["factors"].append(f"{len(high_severity_correlations)} high-risk correlations")
        
        # Determine level
        if severity["score"] >= 30:
            severity["level"] = "critical"
        elif severity["score"] >= 15:
            severity["level"] = "high"
        elif severity["score"] >= 5:
            severity["level"] = "moderate"
        
        return severity
    
    def _calculate_confidence(
        self,
        agent_results: Dict[str, Any],
        correlations: List[Dict]
    ) -> float:
        """Calculate confidence score for consensus"""
        confidence = 1.0
        
        # Reduce confidence for errors
        for result in agent_results.values():
            tool_results = result.get("tool_results", {})
            for data in tool_results.values():
                if isinstance(data, dict) and "error" in data:
                    confidence -= 0.2
        
        # Increase confidence for correlations
        if correlations:
            confidence += len(correlations) * 0.05
        
        return max(0.0, min(1.0, confidence))


if __name__ == "__main__":
    # Test consensus agent
    from config.config import Config
    db = DatabaseManager()
    agent = ConsensusAgent(db)
    
    # Mock agent results with string coordinates (simulating the bug)
    mock_results = {
        "flight": {
            "answer": "Found flight",
            "data_count": 1,
            "tool_results": {"get_all_flights": [{"lat": 12.5, "lon": 75.5, "flight": "TEST01"}]}
        },
        "disaster": {
            "answer": "Found wildfire",
            "data_count": 1,
            "tool_results": {"get_active_events": [{"lat": "13.0", "lon": "75.0", "title": "Fire"}]}
        }
    }
    
    result = agent.process(
        "Are there flights near wildfires?",
        mock_results,
        {"query_type": "complex"}
    )
     
    print(json.dumps(result, indent=2, default=str))