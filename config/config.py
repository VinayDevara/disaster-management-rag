"""
Configuration Manager for Disaster RAG System
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

class Config:
    """Central configuration class"""
    
    # LLM Configuration
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
    OLLAMA_TOOL_MODEL = os.getenv("OLLAMA_TOOL_MODEL", OLLAMA_MODEL)
    QWEN_SYSTEM_PROMPT = os.getenv(
        "QWEN_SYSTEM_PROMPT",
        """You are DisasterRAG, an AI assistant specializing in disaster management intelligence.
You run locally via Ollama (Qwen 2.5) and serve a multi-agent system with three specialist domains:
Flight Tracking, Weather Analysis, and Disaster/Emergency Management.

═══════════════════════════════════════════════════════════════
CRITICAL GROUNDING RULES
═══════════════════════════════════════════════════════════════
1. NEVER invent, fabricate, or hallucinate data. This includes coordinates, severity levels,
   alert statuses, flight positions, weather readings, or any factual claim.
2. ALL factual answers MUST come from tool outputs, database rows, or vector search results.
3. If no tool data is available, explicitly say: "No data available from tools for this query."
4. If a tool returns an error, report the error honestly and try alternative tools.

═══════════════════════════════════════════════════════════════
HOW TOOL CALLING WORKS
═══════════════════════════════════════════════════════════════
You have access to tools provided via the Ollama function-calling API.
When you receive a user query:

Step 1 — CLASSIFY the query domain(s):
  • FLIGHT domain: aircraft tracking, ADS-B data, callsigns, emergency squawks, flight paths
  • WEATHER domain: temperature, rain, forecast, wind, humidity, cyclone, landslide risk
  • DISASTER domain: active disasters, EONET events, GDACS alerts, SACHET/NDMA warnings,
    evacuation plans, flood risk, earthquake, wildfire, volcanic activity

Step 2 — SELECT the right tool(s) for the domain:

  FLIGHT TOOLS:
  - get_all_flights(limit) — list recent flights from ADS-B database
  - get_flight_by_callsign(callsign) — find a specific flight
  - get_flight_by_hex(hex_code) — find by ICAO hex identifier
  - get_flights_in_area(lat_min, lat_max, lon_min, lon_max, limit) — geographic search
  - get_emergency_flights(limit) — flights with squawk 7500/7600/7700
  - get_flight_trajectory(hex_code) — flight path history
  - get_flights_near_location(lat, lon, radius_deg, limit) — proximity search
  - vector_search_flights(query) — semantic search across flight knowledge

  WEATHER TOOLS:
  - get_current_weather(lat, lon) — live weather at coordinates
  - get_weather_by_city(city, country_code) — live weather by city name
  - get_forecast(lat, lon, days) — multi-day weather forecast
  - get_weather_events_by_type(event_type, limit) — historical weather events
  - get_weather_events_in_area(lat_min, lat_max, lon_min, lon_max, limit) — area search
  - get_openmeteo_forecasts(location, limit) — Open-Meteo hourly forecasts
  - get_high_precipitation_forecasts(threshold, limit) — heavy rain forecasts
  - get_gpm_rainfall(limit) — NASA GPM satellite rainfall data
  - get_heavy_rainfall(threshold, limit) — rainfall above threshold
  - get_landslide_snapshot(limit) — NASA LHASA landslide nowcast
  - get_high_risk_landslide(limit) — high-risk landslide cells
  - vector_search_weather(query) — semantic search across weather knowledge

  DISASTER TOOLS:
  - get_active_events(limit) — currently active disaster events worldwide (NASA EONET)
  - get_events_by_category(category, limit) — filter by: wildfires, volcanoes,
    severeStorms, floods, earthquakes, landslides, drought, dustHaze
  - get_events_in_area(lat_min, lat_max, lon_min, lon_max, limit) — geographic filter
  - get_event_details(event_id) — detailed info about one event
  - get_disaster_events_by_type(event_type, limit) — database historical events
  - get_recent_disasters(days, limit) — recent events from database
  - get_official_alerts(district, limit) — SACHET/NDMA official alerts
  - get_active_official_alerts(limit) — currently active official alerts
  - get_gdacs_events(event_type, limit) — GDACS flood/cyclone events
  - get_gdacs_events_by_severity(severity, limit) — GDACS by severity (red/orange/green)
  - get_historical_cyclones(basin, limit) — IBTrACS historical cyclone data
  - get_intense_cyclones(min_wind_kt, limit) — cyclones above wind threshold
  - vector_search_disasters(query) — semantic search across disaster knowledge

Step 3 — CALL the selected tool(s) with appropriate parameters.
  • Always provide reasonable defaults: limit=20, days=7, radius_deg=2.0
  • Use geographic coordinates for the Dakshina Karnataka region when no location is
    specified: Mangalore (12.9141, 74.8560), Udupi (13.3409, 74.7421)
  • For bounding box queries in the region: lat 12.5–13.6, lon 74.5–75.4

Step 4 — SYNTHESIZE the tool results into a clear, actionable answer:
  • Cite which tools provided the data
  • Include specific numbers, coordinates, timestamps from the tool output
  • Assess severity: low / moderate / high / critical
  • Note operational implications for disaster response teams
  • If multiple domains are relevant, correlate findings across domains

═══════════════════════════════════════════════════════════════
RESPONSE FORMAT RULES
═══════════════════════════════════════════════════════════════
- Keep answers concise, factual, and operational — suitable for disaster response teams.
- Use bullet points and structured formatting for clarity.
- When asked for JSON, return ONLY valid JSON with no extra text.
- When multiple data sources contribute, list them.
- Always state data limitations honestly (e.g., "ADS-B data is from loaded samples,
  not real-time" or "EONET API returned 0 events for this category").

═══════════════════════════════════════════════════════════════
MULTI-DOMAIN QUERY HANDLING
═══════════════════════════════════════════════════════════════
For queries spanning multiple domains (e.g., "Are flights affected by the wildfire?"):
1. Gather data from EACH relevant domain using appropriate tools
2. Look for geographic correlations (events near each other)
3. Assess cross-domain impact (e.g., disaster affecting flight routes)
4. Provide a unified operational assessment

═══════════════════════════════════════════════════════════════
ERROR HANDLING
═══════════════════════════════════════════════════════════════
- If a tool fails, report the failure and try the next best tool
- If all tools fail, use vector search as a fallback for stored knowledge
- Never silently skip errors — always mention what failed and why
- If the API is unreachable, suggest the user check connectivity
""",
    )
    
    # API Keys
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
    GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "")
    NASA_API_KEY = os.getenv("NASA_API_KEY", "DEMO_KEY")
    
    # Database Paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    SQLITE_DB_PATH = str(DATA_DIR / "disaster_rag.db")
    VECTOR_DB_PATH = str(DATA_DIR / "chromadb")
    
    # ADS-B Data
    ADSB_DATA_PATH = os.getenv("ADSB_DATA_PATH", str(DATA_DIR / "adsb_sample.xlsx"))
    
    # Embedding Model
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    
    # LLM Parameters
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
    TOP_P = float(os.getenv("TOP_P", "0.9"))
    
    # Agent Configuration
    ENABLE_FLIGHT_AGENT = os.getenv("ENABLE_FLIGHT_AGENT", "true").lower() == "true"
    ENABLE_WEATHER_AGENT = os.getenv("ENABLE_WEATHER_AGENT", "true").lower() == "true"
    ENABLE_DISASTER_AGENT = os.getenv("ENABLE_DISASTER_AGENT", "true").lower() == "true"
    ENABLE_CONSENSUS_AGENT = os.getenv("ENABLE_CONSENSUS_AGENT", "true").lower() == "true"
    
    # Orchestrator Resilience
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))
    MAX_REINVOCATIONS = int(os.getenv("MAX_REINVOCATIONS", "2"))
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "disaster_rag.log")
    
    # API Endpoints (existing)
    EONET_API_URL = "https://eonet.gsfc.nasa.gov/api/v3/events"
    OPENWEATHER_API_URL = "https://api.openweathermap.org/data/2.5"

    # ── Region defaults (Dakshina Karnataka) ─────────────────────────────
    REGION_NAME = os.getenv("REGION_NAME", "Mangalore-Udupi")
    REGION_STATE = os.getenv("REGION_STATE", "Karnataka")
    REGION_COUNTRY = os.getenv("REGION_COUNTRY", "India")
    DISTRICT_FILTERS = os.getenv(
        "DISTRICT_FILTERS",
        "Udupi,Dakshina Kannada,Mangaluru,Mangalore",
    ).split(",")
    MANGALORE_LAT = float(os.getenv("MANGALORE_LAT", "12.9141"))
    MANGALORE_LON = float(os.getenv("MANGALORE_LON", "74.8560"))
    UDUPI_LAT = float(os.getenv("UDUPI_LAT", "13.3409"))
    UDUPI_LON = float(os.getenv("UDUPI_LON", "74.7421"))
    # bounding box: [south_lat, north_lat, west_lon, east_lon]
    REGION_BBOX = [
        float(x) for x in os.getenv(
            "REGION_BBOX", "12.5,13.6,74.5,75.4"
        ).split(",")
    ]

    # ── Polling intervals ────────────────────────────────────────────────
    POLL_MINUTES_SACHET = int(os.getenv("POLL_MINUTES_SACHET", "10"))
    POLL_MINUTES_OPENMETEO = int(os.getenv("POLL_MINUTES_OPENMETEO", "30"))
    POLL_MINUTES_GPM = int(os.getenv("POLL_MINUTES_GPM", "60"))
    POLL_HOURS_LHASA = int(os.getenv("POLL_HOURS_LHASA", "6"))
    POLL_MINUTES_GDACS = int(os.getenv("POLL_MINUTES_GDACS", "15"))
    POLL_DAYS_IBTRACS = int(os.getenv("POLL_DAYS_IBTRACS", "7"))

    # ── External source URLs ─────────────────────────────────────────────
    # SACHET / NDMA  (no dedicated API key expected; configure feed URLs)
    SACHET_FEED_URLS = os.getenv(
        "SACHET_FEED_URLS",
        "https://sachet.ndma.gov.in/cap_public_website/FetchAllAlertDetails",
    ).split(",")
    SACHET_CAP_URLS = os.getenv(
        "SACHET_CAP_URLS",
        "https://sachet.ndma.gov.in/cap_public_website/FetchCAPAlertDetails",
    ).split(",")

    # GDACS  (no key expected)
    GDACS_FEED_FLOODS_URL = os.getenv(
        "GDACS_FEED_FLOODS_URL",
        "https://www.gdacs.org/xml/rss_fl.xml",
    )
    GDACS_FEED_CYCLONES_URL = os.getenv(
        "GDACS_FEED_CYCLONES_URL",
        "https://www.gdacs.org/xml/rss_tc.xml",
    )

    # Open-Meteo  (no API key needed for free non-commercial use)
    OPENMETEO_BASE_URL = os.getenv(
        "OPENMETEO_BASE_URL",
        "https://api.open-meteo.com/v1/forecast",
    )

    # NASA GPM IMERG / PMM Publisher  (may need Earthdata credentials)
    GPM_PUBLISHER_URL = os.getenv(
        "GPM_PUBLISHER_URL",
        "https://pmmpublisher.pps.eosdis.nasa.gov/opensearch",
    )

    # NASA LHASA  (may need Earthdata credentials for expanded access)
    LHASA_SERVICE_URL = os.getenv(
        "LHASA_SERVICE_URL",
        "https://maps.nccs.nasa.gov/arcgis/rest/services/global_landslide_nowcast/MapServer",
    )

    # IBTrACS  (public historical dataset, no key expected)
    IBTRACS_SOURCE_URL = os.getenv(
        "IBTRACS_SOURCE_URL",
        "https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/"
        "v04r01/access/csv/ibtracs.NI.list.v04r01.csv",
    )

    # ── Retention / archival ─────────────────────────────────────────────
    HOT_RETENTION_HOURS = int(os.getenv("HOT_RETENTION_HOURS", "24"))
    WARM_RETENTION_DAYS = int(os.getenv("WARM_RETENTION_DAYS", "30"))
    COLD_ARCHIVE_DIR = str(
        Path(os.getenv("COLD_ARCHIVE_DIR", str(DATA_DIR / "archive")))
    )
    RAW_PAYLOAD_DIR = str(
        Path(os.getenv("RAW_PAYLOAD_DIR", str(DATA_DIR / "raw_payloads")))
    )

    # ── Optional Earthdata auth (GPM / LHASA) ───────────────────────────
    EARTHDATA_USERNAME = os.getenv("EARTHDATA_USERNAME", "")
    EARTHDATA_PASSWORD = os.getenv("EARTHDATA_PASSWORD", "")
    EARTHDATA_TOKEN = os.getenv("EARTHDATA_TOKEN", "")

    @classmethod
    def validate(cls):
        """Validate essential configuration"""
        errors = []
        if not cls.OPENWEATHER_API_KEY:
            errors.append("OPENWEATHER_API_KEY is not set (optional but recommended)")
        
        # Create data directory if not exists
        cls.DATA_DIR.mkdir(exist_ok=True)
        # Create archive / payload directories
        Path(cls.COLD_ARCHIVE_DIR).mkdir(parents=True, exist_ok=True)
        Path(cls.RAW_PAYLOAD_DIR).mkdir(parents=True, exist_ok=True)
        
        return errors

# Validate configuration on import
config_errors = Config.validate()
if config_errors:
    print("⚠️  Configuration warnings:")
    for error in config_errors:
        print(f"   - {error}")