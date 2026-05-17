"""Quick local test: verify Qwen tool calling through Ollama."""
from utils.llm_client import get_llm_client

TOOLS = [
    {"type": "function", "function": {"name": "get_active_events", "description": "Get currently active disaster events worldwide.", "parameters": {"type": "object", "properties": {"limit": {"type": "integer", "description": "Max events to return"}}, "required": []}}},
    {"type": "function", "function": {"name": "get_events_by_category", "description": "Get disaster events filtered by category such as wildfires, volcanoes, or severeStorms.", "parameters": {"type": "object", "properties": {"category": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["category"]}}},
    {"type": "function", "function": {"name": "get_events_in_area", "description": "Get disaster events within a geographic bounding box.", "parameters": {"type": "object", "properties": {"lat_min": {"type": "number"}, "lat_max": {"type": "number"}, "lon_min": {"type": "number"}, "lon_max": {"type": "number"}, "limit": {"type": "integer"}}, "required": ["lat_min", "lat_max", "lon_min", "lon_max"]}}},
    {"type": "function", "function": {"name": "get_event_details", "description": "Get detailed information about a specific disaster event by its ID.", "parameters": {"type": "object", "properties": {"event_id": {"type": "string"}}, "required": ["event_id"]}}},
    {"type": "function", "function": {"name": "get_disaster_events_by_type", "description": "Get historical disaster events by type from the database.", "parameters": {"type": "object", "properties": {"event_type": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["event_type"]}}},
    {"type": "function", "function": {"name": "get_recent_disasters", "description": "Get recent disaster events from the database.", "parameters": {"type": "object", "properties": {"days": {"type": "integer"}, "limit": {"type": "integer"}}, "required": []}}},
    {"type": "function", "function": {"name": "vector_search_disasters", "description": "Semantic search across the disaster knowledge base.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "get_official_alerts", "description": "Get latest SACHET/NDMA official disaster warnings for Dakshina Karnataka.", "parameters": {"type": "object", "properties": {"district": {"type": "string"}, "limit": {"type": "integer"}}, "required": []}}},
    {"type": "function", "function": {"name": "get_active_official_alerts", "description": "Get currently active non-expired official disaster alerts.", "parameters": {"type": "object", "properties": {"limit": {"type": "integer"}}, "required": []}}},
    {"type": "function", "function": {"name": "get_gdacs_events", "description": "Get latest GDACS flood and cyclone events.", "parameters": {"type": "object", "properties": {"event_type": {"type": "string"}, "limit": {"type": "integer"}}, "required": []}}},
    {"type": "function", "function": {"name": "get_gdacs_events_by_severity", "description": "Get GDACS events filtered by severity level such as red, orange, or green.", "parameters": {"type": "object", "properties": {"severity": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["severity"]}}},
    {"type": "function", "function": {"name": "get_historical_cyclones", "description": "Get IBTrACS historical cyclone data for the North Indian Ocean basin.", "parameters": {"type": "object", "properties": {"basin": {"type": "string"}, "limit": {"type": "integer"}}, "required": []}}},
    {"type": "function", "function": {"name": "get_intense_cyclones", "description": "Get historical cyclones above a wind speed threshold in knots.", "parameters": {"type": "object", "properties": {"min_wind_kt": {"type": "number"}, "limit": {"type": "integer"}}, "required": []}}},
]

QUERY = "give one recent landslide in india and its current condition"

client = get_llm_client()
print(f"Using provider: {client._active_provider}")
print(f"Model: {client.model}")

result = client.generate_with_tools(
    prompt=QUERY,
    system_prompt="Use the available tools to answer with grounded evidence.",
    tools=TOOLS,
)

if result.get("tool_calls"):
    tc = result["tool_calls"][0]
    print(f"  ✅ Tool call SUCCESS: {tc['name']}({tc['arguments']})")
elif result.get("content"):
    content_preview = result["content"][:200]
    print(f"  ⚠️ No tool call, got text: {content_preview}")
else:
    print(f"  ❓ Unexpected response: {result}")
