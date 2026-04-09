"""
Consensus Agent - CrewAI + DSPy Implementation
Correlates data from multiple agents, performs cross-intelligence analysis,
and generates unified emergency command plans.
"""
from typing import Dict, List, Any, Optional
from utils.llm_client import get_llm_client
from utils.database import DatabaseManager
from agents.dspy_signatures import GenerateEmergencyCommandPlan
import json
import math
import dspy


class ConsensusAgent:
    """
    Consensus agent that:
    1. Receives results from multiple specialized agents
    2. Identifies correlations and patterns
    3. Performs cross-domain intelligence analysis
    4. Generates unified, coherent emergency command plans using DSPy
    """

    def __init__(self, db_manager: DatabaseManager):
        self.llm = get_llm_client()
        self.db = db_manager
        self.response_predictor = dspy.ChainOfThought(GenerateEmergencyCommandPlan)

    def process(
        self,
        original_query: str,
        agent_results: Dict[str, Any],
        classification: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Process results from multiple agents and generate consensus."""
        print(f"🤝 Consensus Agent processing {len(agent_results)} agent results")

        try:
            extracted_data = self._extract_key_data(agent_results)
            correlations = self._find_correlations(extracted_data, agent_results)
            geographic_analysis = self._analyze_geography(extracted_data)
            severity_assessment = self._assess_severity(agent_results, correlations)

            # Generate unified response using DSPy
            try:
                result = self.response_predictor(
                    original_query=original_query,
                    agent_results=json.dumps(agent_results, indent=2, default=str),
                    extracted_key_data=json.dumps(extracted_data, indent=2, default=str),
                    correlations_found=json.dumps(correlations, indent=2, default=str),
                    geographic_analysis=json.dumps(geographic_analysis, indent=2, default=str),
                    severity_assessment=json.dumps(severity_assessment, indent=2),
                )
                unified_response = result.response
            except Exception as e:
                print(f"⚠️ DSPy unified response generation failed: {e}")
                unified_response = f"Error generating unified emergency plan: {e}"

            return {
                "query": original_query,
                "agent_results_summary": {
                    agent: {
                        "data_count": r.get("data_count", 0),
                        "status": "success" if "answer" in r else "error",
                    }
                    for agent, r in agent_results.items()
                },
                "extracted_data": extracted_data,
                "correlations": correlations,
                "geographic_analysis": geographic_analysis,
                "severity_assessment": severity_assessment,
                "unified_response": unified_response,
                "confidence": self._calculate_confidence(agent_results, correlations),
                "status": "success",
            }

        except Exception as e:
            print(f"⚠️ Consensus generation failed: {str(e)}")
            return self._generate_fallback_response(original_query, agent_results, str(e))

    def _generate_fallback_response(
        self, original_query: str, agent_results: Dict[str, Any], error_message: str
    ) -> Dict[str, Any]:
        """Generate a fallback response by concatenating agent results."""
        print("🔄 Generating fallback response...")

        fallback_parts = [
            f"**Note:** Comprehensive analysis is currently unavailable due to a system error "
            f"({error_message}). Below are the raw findings from specialized agents.\n"
        ]

        for agent_name, result in agent_results.items():
            fallback_parts.append(f"### {agent_name.capitalize()} Agent Findings")
            if "answer" in result:
                fallback_parts.append(result["answer"])
            else:
                fallback_parts.append("No specific findings reported.")
            fallback_parts.append("")

        return {
            "query": original_query,
            "agent_results_summary": {
                agent: {"data_count": r.get("data_count", 0), "status": "fallback"}
                for agent, r in agent_results.items()
            },
            "extracted_data": {},
            "correlations": [],
            "geographic_analysis": {},
            "severity_assessment": {"level": "unknown", "score": 0},
            "unified_response": "\n".join(fallback_parts),
            "confidence": 0.5,
            "status": "fallback",
            "error": error_message,
        }

    def _extract_key_data(self, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key data points from agent results with safe type conversion."""
        extracted = {
            "flights": [],
            "disasters": [],
            "weather_conditions": [],
            "locations": set(),
            "coordinates": [],
        }

        for agent_name, result in agent_results.items():
            # Handle both CrewAI (raw_output) and legacy (tool_results) formats
            raw = result.get("raw_output", "")
            tool_results = result.get("tool_results", {})

            if agent_name == "flight":
                for tool_name, data in tool_results.items():
                    if isinstance(data, list):
                        for item in data[:10]:
                            if isinstance(item, dict):
                                try:
                                    lat = float(item["lat"]) if item.get("lat") is not None else None
                                    lon = float(item["lon"]) if item.get("lon") is not None else None
                                except (ValueError, TypeError):
                                    lat, lon = None, None

                                extracted["flights"].append({
                                    "hex": item.get("hex") or item.get("aircraft__hex"),
                                    "flight": item.get("flight") or item.get("aircraft__flight"),
                                    "lat": lat, "lon": lon,
                                    "altitude": item.get("alt_baro"),
                                    "emergency": item.get("emergency", "none"),
                                })
                                if lat is not None and lon is not None:
                                    extracted["coordinates"].append({
                                        "type": "flight", "lat": lat, "lon": lon,
                                        "label": item.get("flight") or item.get("hex"),
                                    })

            elif agent_name == "disaster":
                for tool_name, data in tool_results.items():
                    if isinstance(data, list):
                        for item in data[:10]:
                            if isinstance(item, dict):
                                try:
                                    lat = float(item["lat"]) if item.get("lat") is not None else None
                                    lon = float(item["lon"]) if item.get("lon") is not None else None
                                except (ValueError, TypeError):
                                    lat, lon = None, None

                                extracted["disasters"].append({
                                    "title": item.get("title"),
                                    "type": item.get("event_type"),
                                    "lat": lat, "lon": lon,
                                    "location": item.get("location_name"),
                                })
                                if lat is not None and lon is not None:
                                    extracted["coordinates"].append({
                                        "type": "disaster", "lat": lat, "lon": lon,
                                        "label": item.get("title") or item.get("event_type"),
                                    })

            elif agent_name == "weather":
                for tool_name, data in tool_results.items():
                    if isinstance(data, dict) and "error" not in data:
                        extracted["weather_conditions"].append(data)
                        coords = data.get("coordinates", {})
                        try:
                            lat = float(coords["lat"]) if coords.get("lat") is not None else None
                            lon = float(coords["lon"]) if coords.get("lon") is not None else None
                        except (ValueError, TypeError):
                            lat, lon = None, None
                        if lat is not None and lon is not None:
                            extracted["coordinates"].append({
                                "type": "weather", "lat": lat, "lon": lon,
                                "label": data.get("location", "Weather Station"),
                            })

        extracted["locations"] = list(extracted["locations"])
        return extracted

    def _find_correlations(
        self, extracted_data: Dict[str, Any], agent_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find correlations between different data domains."""
        correlations = []

        for flight in extracted_data.get("flights", []):
            flight_lat, flight_lon = flight.get("lat"), flight.get("lon")
            if flight_lat is None or flight_lon is None:
                continue
            for disaster in extracted_data.get("disasters", []):
                disaster_lat, disaster_lon = disaster.get("lat"), disaster.get("lon")
                if disaster_lat is None or disaster_lon is None:
                    continue
                distance = self._calculate_distance(
                    flight_lat, flight_lon, disaster_lat, disaster_lon
                )
                if distance < 500:
                    correlations.append({
                        "type": "flight-disaster",
                        "entity1": {
                            "type": "flight",
                            "id": flight.get("flight") or flight.get("hex"),
                            "location": f"{flight_lat}, {flight_lon}",
                        },
                        "entity2": {
                            "type": "disaster",
                            "id": disaster.get("title"),
                            "location": f"{disaster_lat}, {disaster_lon}",
                        },
                        "distance_km": round(distance, 2),
                        "severity": "high" if distance < 100 else "medium",
                        "description": (
                            f"Flight {flight.get('flight', 'unknown')} is "
                            f"{round(distance)} km from {disaster.get('title', 'disaster')}"
                        ),
                    })

        return correlations

    def _calculate_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """Haversine distance in km."""
        R = 6371
        try:
            lat1_r, lat2_r = math.radians(float(lat1)), math.radians(float(lat2))
            dlat = math.radians(float(lat2) - float(lat1))
            dlon = math.radians(float(lon2) - float(lon1))
            a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
            return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        except Exception:
            return 9999.0

    def _analyze_geography(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze geographic distribution of entities."""
        coordinates = extracted_data.get("coordinates", [])
        if not coordinates:
            return {"status": "no_geographic_data"}

        lats = [float(c["lat"]) for c in coordinates if c.get("lat") is not None]
        lons = [float(c["lon"]) for c in coordinates if c.get("lon") is not None]
        if not lats or not lons:
            return {"status": "no_valid_coordinates"}

        return {
            "bounding_box": {
                "north": max(lats), "south": min(lats),
                "east": max(lons), "west": min(lons),
            },
            "center": {"lat": sum(lats) / len(lats), "lon": sum(lons) / len(lons)},
            "entity_count": len(coordinates),
            "entity_types": {
                "flights": len([c for c in coordinates if c["type"] == "flight"]),
                "disasters": len([c for c in coordinates if c["type"] == "disaster"]),
                "weather": len([c for c in coordinates if c["type"] == "weather"]),
            },
        }

    def _assess_severity(
        self, agent_results: Dict[str, Any], correlations: List[Dict]
    ) -> Dict[str, Any]:
        """Assess overall situation severity."""
        severity = {"level": "normal", "score": 0, "factors": []}

        for agent_name, result in agent_results.items():
            if agent_name == "flight":
                tool_results = result.get("tool_results", {})
                emergency_flights = tool_results.get("get_emergency_flights", [])
                if emergency_flights:
                    severity["score"] += len(emergency_flights) * 10
                    severity["factors"].append(f"{len(emergency_flights)} emergency flights")
            elif agent_name == "weather":
                ws = result.get("severity_analysis", {})
                if ws.get("level") == "critical":
                    severity["score"] += 20
                    severity["factors"].append("Critical weather conditions")
                elif ws.get("level") == "high":
                    severity["score"] += 10
                    severity["factors"].append("Severe weather")
            elif agent_name == "disaster":
                imp = result.get("impact_analysis", {})
                if imp.get("severity") == "critical":
                    severity["score"] += 25
                    severity["factors"].append("Critical disaster events")
                elif imp.get("severity") == "high":
                    severity["score"] += 15
                    severity["factors"].append("High-impact disasters")

        high_corr = [c for c in correlations if c.get("severity") == "high"]
        if high_corr:
            severity["score"] += len(high_corr) * 5
            severity["factors"].append(f"{len(high_corr)} high-risk correlations")

        if severity["score"] >= 30:
            severity["level"] = "critical"
        elif severity["score"] >= 15:
            severity["level"] = "high"
        elif severity["score"] >= 5:
            severity["level"] = "moderate"

        return severity

    def _calculate_confidence(
        self, agent_results: Dict[str, Any], correlations: List[Dict]
    ) -> float:
        confidence = 1.0
        for result in agent_results.values():
            if result.get("status") == "failed":
                confidence -= 0.3
            elif result.get("status") == "partial":
                confidence -= 0.15
        if correlations:
            confidence += len(correlations) * 0.05
        return max(0.0, min(1.0, confidence))


if __name__ == "__main__":
    from config.config import Config

    db = DatabaseManager()
    agent = ConsensusAgent(db)

    mock_results = {
        "flight": {
            "answer": "Found flight",
            "data_count": 1,
            "status": "success",
            "tool_results": {
                "get_all_flights": [{"lat": 12.5, "lon": 75.5, "flight": "TEST01"}]
            },
        },
        "disaster": {
            "answer": "Found wildfire",
            "data_count": 1,
            "status": "success",
            "tool_results": {
                "get_active_events": [{"lat": "13.0", "lon": "75.0", "title": "Fire"}]
            },
        },
    }

    result = agent.process(
        "Are there flights near wildfires?",
        mock_results,
        {"query_type": "complex"},
    )
    print(json.dumps(result, indent=2, default=str))
