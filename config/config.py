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
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-70b-8192")
    
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
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "8000"))
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
    TOP_P = float(os.getenv("TOP_P", "0.9"))
    
    # Agent Configuration
    ENABLE_FLIGHT_AGENT = os.getenv("ENABLE_FLIGHT_AGENT", "true").lower() == "true"
    ENABLE_WEATHER_AGENT = os.getenv("ENABLE_WEATHER_AGENT", "true").lower() == "true"
    ENABLE_DISASTER_AGENT = os.getenv("ENABLE_DISASTER_AGENT", "true").lower() == "true"
    ENABLE_CONSENSUS_AGENT = os.getenv("ENABLE_CONSENSUS_AGENT", "true").lower() == "true"
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "disaster_rag.log")
    
    # API Endpoints
    EONET_API_URL = "https://eonet.gsfc.nasa.gov/api/v3/events"
    OPENWEATHER_API_URL = "https://api.openweathermap.org/data/2.5"
    
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
        
        return errors

# Validate configuration on import
config_errors = Config.validate()
if config_errors:
    print("⚠️  Configuration warnings:")
    for error in config_errors:
        print(f"   - {error}")