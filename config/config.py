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
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    GROQ_TOOL_MODEL = os.getenv("GROQ_TOOL_MODEL", "qwen/qwen3-32b")
    
    # API Keys
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
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
        
        if not cls.GROQ_API_KEY:
            errors.append("GROQ_API_KEY is not set")
        
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