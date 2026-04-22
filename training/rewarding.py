"""Reward scoring helpers for DisasterRAG local fine-tuning.

These heuristics are tuned for the repo's agent-scope setup:
- route to the right agent(s)
- pick the right tools for the domain
- avoid crashes and empty answers
- prefer consensus when queries span multiple domains
"""

from __future__ import annotations

from statistics import mean
from typing import Any, Dict, Iterable, List, Tuple


AGENT_DOMAIN_KEYWORDS = {
    "weather": [
        "weather", "temperature", "rain", "rainfall", "wind", "humidity",
        "forecast", "storm", "cyclone", "precipitation", "cloud",
    ],
    "disaster": [
        "disaster", "flood", "earthquake", "alert", "gdacs", "sachet",
        "landslide", "emergency", "risk", "severity", "relief", "hazard",
    ],
    "flight": [
        "flight", "fly", "airport", "aircraft", "plane", "aviation",
        "mangalore", "disruption",
    ],
}

TOOL_DOMAIN = {
    "get_current_weather": ["weather", "temperature", "wind", "humidity", "conditions"],
    "get_forecast": ["forecast", "weather", "tomorrow", "next", "predict"],
    "get_weather_by_city": ["weather", "city", "conditions"],
    "get_openmeteo_forecasts": ["forecast", "weather", "predict", "next"],
    "get_gpm_rainfall": ["rainfall", "rain", "precipitation", "gpm"],
    "get_heavy_rainfall": ["rain", "heavy", "rainfall", "precipitation"],
    "get_high_precipitation_forecasts": ["rain", "precipitation", "forecast"],
    "get_weather_events_in_area": ["weather", "events", "area", "storm"],
    "vector_search_weather": ["weather", "search", "similar"],
    "get_active_events": ["disaster", "events", "active", "alert"],
    "get_active_official_alerts": ["alert", "official", "warning", "sachet"],
    "get_events_by_category": ["disaster", "flood", "cyclone", "earthquake", "category"],
    "get_gdacs_events": ["gdacs", "disaster", "global"],
    "get_gdacs_events_by_severity": ["gdacs", "severity", "disaster", "alert"],
    "get_recent_disasters": ["disaster", "recent", "event"],
    "get_disaster_events_by_type": ["disaster", "type", "flood", "cyclone"],
    "get_official_alerts": ["alert", "official", "sachet", "warning"],
    "vector_search_disasters": ["disaster", "search", "similar"],
    "get_high_risk_landslide": ["landslide", "risk", "slope"],
    "get_landslide_snapshot": ["landslide", "snapshot", "risk"],
    "get_all_flights": ["flight", "plane", "aircraft", "fly"],
    "get_flights_in_area": ["flight", "area", "near"],
    "get_flights_near_location": ["flight", "near", "location", "mangalore"],
    "get_flight_by_callsign": ["flight", "callsign"],
    "get_flight_by_hex": ["flight", "hex", "icao"],
    "get_flight_trajectory": ["flight", "trajectory", "path"],
    "get_emergency_flights": ["emergency", "flight", "squawk"],
    "vector_search_flights": ["flight", "search", "similar"],
}


def _coerce_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, dict):
        for key in ("answer", "response", "content", "unified_response", "raw_output"):
            if key in value and value[key]:
                nested = _coerce_text(value[key])
                if nested:
                    return nested
        return ""
    if isinstance(value, list):
        return "\n".join(_coerce_text(item) for item in value if _coerce_text(item))
    return str(value).strip()


def extract_assistant_text(result: Dict[str, Any]) -> str:
    """Pull the final assistant text from a benchmark result record."""
    if not isinstance(result, dict):
        return ""
    for key in ("final_response", "answer", "response", "content", "unified_response", "raw_output"):
        text = _coerce_text(result.get(key))
        if text:
            return text
    return ""


def extract_tool_names(result: Dict[str, Any]) -> List[str]:
    tools = result.get("tools_called") or []
    if isinstance(tools, list):
        return sorted({str(tool).strip() for tool in tools if str(tool).strip()})
    if isinstance(tools, str):
        return [tool.strip() for tool in tools.split(",") if tool.strip()]
    return []


def tool_alignment_score(query_text: str, tools_called: Iterable[str]) -> float:
    q = (query_text or "").lower()
    tools = list(tools_called or [])
    if not q:
        return 1.0 if tools else 0.5
    if not tools:
        return 0.0

    scores: List[float] = []
    for tool in tools:
        kws = TOOL_DOMAIN.get(tool, [])
        if not kws:
            scores.append(0.3)
            continue
        matches = sum(1 for kw in kws if kw in q)
        scores.append(min(matches / max(len(kws), 1), 1.0))
    return round(mean(scores), 3) if scores else 0.0


def agent_alignment_score(query_text: str, agents_invoked: Iterable[str]) -> float:
    q = (query_text or "").lower()
    agents = list(agents_invoked or [])
    if not q:
        return 1.0 if agents else 0.5

    expected = {
        agent for agent, keywords in AGENT_DOMAIN_KEYWORDS.items()
        if any(keyword in q for keyword in keywords)
    }
    if not expected:
        return 1.0 if not agents else 0.6
    if not agents:
        return 0.0
    overlap = len(expected & set(agents))
    return round(overlap / len(expected), 3)


def sample_reward(query_meta: Dict[str, Any], result: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
    """Score a benchmark result for preference tuning.

    The reward is intentionally shaped for DisasterRAG's agent scope:
    - routing accuracy matters most
    - tool alignment matters next
    - crash-free, grounded answers matter
    - consensus is rewarded when the query spans multiple domains
    """

    query = query_meta.get("query", "")
    category = str(query_meta.get("category", "")).upper()
    expected_agents = query_meta.get("expected_agents") or []
    actual_agents = result.get("agents_invoked") or []
    tools_called = extract_tool_names(result)

    got_response = bool(result.get("got_response"))
    crashed = bool(result.get("crashed"))
    fallback_used = bool(result.get("fallback_used"))
    consensus_applied = bool(result.get("consensus_applied"))

    agent_score = agent_alignment_score(query, actual_agents)
    tool_score = tool_alignment_score(query, tools_called)

    expected_set = set(expected_agents)
    actual_set = set(actual_agents)
    routing_score = 1.0 if not expected_set else (1.0 if expected_set.issubset(actual_set) else len(expected_set & actual_set) / len(expected_set))

    response_score = 1.0 if got_response and not crashed else (0.3 if got_response else 0.0)
    stability_score = 1.0 if not crashed else 0.0

    if category in {"A", "B", "C", "D"}:
        consensus_score = 1.0 if (category in {"C", "D"} and consensus_applied) else (0.8 if category in {"A", "B"} and not consensus_applied else 0.5)
        fallback_penalty = 0.1 if fallback_used else 0.0
    else:
        consensus_score = 1.0 if not consensus_applied else 0.8
        fallback_penalty = 0.0

    combined = (
        0.30 * routing_score
        + 0.20 * tool_score
        + 0.20 * agent_score
        + 0.20 * response_score
        + 0.10 * stability_score
        + 0.05 * consensus_score
        - fallback_penalty
    )

    combined = max(0.0, min(1.0, round(combined, 3)))
    components = {
        "routing": round(routing_score, 3),
        "tool": round(tool_score, 3),
        "agent": round(agent_score, 3),
        "response": round(response_score, 3),
        "stability": round(stability_score, 3),
        "consensus": round(consensus_score, 3),
        "fallback_penalty": round(fallback_penalty, 3),
    }
    return combined, components


def make_planner_target(query_meta: Dict[str, Any], result: Dict[str, Any]) -> str:
    tools_called = extract_tool_names(result)
    agents = result.get("agents_invoked") or query_meta.get("expected_agents") or []
    primary_agent = agents[0] if agents else "none"
    secondary_agents = agents[1:] if len(agents) > 1 else []

    payload = {
        "primary_agent": primary_agent,
        "secondary_agents": secondary_agents,
        "tool_plan": tools_called,
        "reasoning": result.get("classification_type", "benchmark-derived"),
    }
    return json_dumps_compact(payload)


def make_answer_context(query_meta: Dict[str, Any], result: Dict[str, Any]) -> str:
    """Create a compact evidence summary for answer-style SFT."""
    fields = {
        "query": query_meta.get("query", ""),
        "category": query_meta.get("category", ""),
        "agents_invoked": result.get("agents_invoked", []),
        "tools_called": extract_tool_names(result),
        "fallback_used": bool(result.get("fallback_used")),
        "consensus_applied": bool(result.get("consensus_applied")),
        "response_length": result.get("response_length", 0),
    }
    return json_dumps_compact(fields)


def make_answer_target(query_meta: Dict[str, Any], result: Dict[str, Any]) -> str:
    """Create a grounded natural-language target answer for SFT.

    This is intentionally synthetic because the benchmark traces in this repo
    record routing/tooling metadata but not the full assistant completion.
    The target still teaches the model the right structure: route, inspect,
    correlate, and answer conservatively.
    """
    agents = result.get("agents_invoked") or query_meta.get("expected_agents") or []
    tools = extract_tool_names(result)
    tool_list = ", ".join(tools[:8]) if tools else "the relevant local tools"
    agent_list = ", ".join(agents) if agents else "the appropriate agent"
    fallback_note = " Fallback tools were used due to primary tool failure." if result.get("fallback_used") else ""

    return (
        f"I will route this query through {agent_list} and verify it with {tool_list}. "
        f"Then I will synthesize a grounded disaster-response answer based on the retrieved evidence, "
        f"highlighting operational risk, affected area, and any immediate safety implications.{fallback_note}"
    )


def make_rejected_target(query_meta: Dict[str, Any]) -> str:
    """Create an intentionally weak completion for preference training."""
    return (
        "I cannot determine the correct agent or tools, so I will answer generically "
        "without checking local evidence or cross-domain risk signals."
    )


def json_dumps_compact(payload: Dict[str, Any]) -> str:
    import json

    return json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
