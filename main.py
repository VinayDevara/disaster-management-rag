"""
Main Disaster Management RAG System
Multimodal Agentic RAG with CrewAI + DSPy
Flight Tracking • Weather Analysis • Disaster Monitoring
"""
import sys
import os
from pathlib import Path

os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("USE_TF", "0")

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config.config import Config
from utils.database import DatabaseManager
from utils.vector_db import VectorDBManager
from utils.llm_client import get_llm_client
from agents.orchestrator_agent import OrchestratorAgent
from agents.flight_agent import FlightAgent
from agents.weather_agent import WeatherAgent
from agents.disaster_agent import DisasterAgent
from agents.consensus_agent import ConsensusAgent
from ingestion.scheduler import IngestionScheduler
import json
import logging
from datetime import datetime
from colorama import Fore, Style, init
from utils.trajectory_logger import TrajectoryLogger

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'  # Keep it clean for the console
)
logger = logging.getLogger("DisasterRAGSystem")

from colorama import Fore, Style, init
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
try:
    from supabase import create_client, Client as _SupabaseClient
    _SUPABASE_AVAILABLE = True
except ImportError:
    _SUPABASE_AVAILABLE = False
    _SupabaseClient = None


app = FastAPI()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase = None
if _SUPABASE_AVAILABLE and SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[  "http://localhost:3000","http://127.0.0.1:3000","http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize colorama for Windows
init(autoreset=True)


class DisasterRAGSystem:
    """
    Main system class that coordinates all agents via the hub orchestrator.
    """

    def __init__(self):
        logger.info(f"{Fore.CYAN}{'='*80}")
        logger.info(f"{Fore.CYAN}🚀 Initializing Disaster Management RAG System (CrewAI + DSPy)")
        logger.info(f"{Fore.CYAN}{'='*80}\n")

        # Core components
        logger.info(f"{Fore.YELLOW}📊 Initializing database...")
        self.db = DatabaseManager()

        logger.info(f"{Fore.YELLOW}🔍 Initializing vector database...")
        self.vector_db = VectorDBManager()

        logger.info(f"{Fore.YELLOW}🤖 Initializing LLM client...")
        self.llm = get_llm_client()

        # Sub-agents (CrewAI-based)
        logger.info(f"{Fore.YELLOW}✈️  Initializing Flight Agent (CrewAI)...")
        self.flight_agent = FlightAgent(self.db, self.vector_db)

        logger.info(f"{Fore.YELLOW}🌤️  Initializing Weather Agent (CrewAI)...")
        self.weather_agent = WeatherAgent(self.db, self.vector_db)

        logger.info(f"{Fore.YELLOW}🔥 Initializing Disaster Agent (CrewAI)...")
        self.disaster_agent = DisasterAgent(self.db, self.vector_db)

        logger.info(f"{Fore.YELLOW}🤝 Initializing Consensus Agent (DSPy)...")
        self.consensus_agent = ConsensusAgent(self.db)

        # Hub orchestrator — holds direct connections to every sub-agent
        logger.info(f"{Fore.YELLOW}🎯 Initializing Hub Orchestrator...")
        self.orchestrator = OrchestratorAgent(
            flight_agent=self.flight_agent,
            weather_agent=self.weather_agent,
            disaster_agent=self.disaster_agent,
            consensus_agent=self.consensus_agent,
        )

        # Ingestion scheduler (started later via FastAPI lifecycle)
        self.scheduler = IngestionScheduler(self.db)

        logger.info(f"\n{Fore.GREEN}✅ System initialized successfully!\n")

    def process_query(self, query: str) -> dict:
        """
        Process user query through the hub orchestrator.
        The orchestrator handles classification, agent invocation (with retry),
        re-invocation, consensus, and fallback — all internally.
        """
        logger.info(f"\n{Fore.CYAN}{'='*80}")
        logger.info(f"{Fore.CYAN}📝 Processing Query: {query}")
        logger.info(f"{Fore.CYAN}{'='*80}\n")
        
        trajectory_logger = TrajectoryLogger(query=query)

        result = self.orchestrator.process_query(query, trajectory_logger=trajectory_logger)
        
        # Save final trajectory
        final_answer = result.get("final_response", {}).get("answer") or result.get("final_response", {}).get("unified_response", "No answer generated")
        trajectory_logger.finish(final_answer=final_answer)

        # Display summary
        meta = result.get("metadata", {})
        logger.info(f"{Fore.GREEN}   Agents used: {meta.get('agents_used', [])}")
        logger.info(f"   Consensus: {meta.get('consensus_applied', False)}")
        logger.info(f"   Orchestrator: {meta.get('orchestrator', 'primary')}{Style.RESET_ALL}")

        return result

    # ── Data loading helpers ────────────────────────────────────────────────

    def load_adsb_data(self, excel_path: str = None):
        """Load ADS-B data from Excel file."""
        excel_path = excel_path or Config.ADSB_DATA_PATH

        if not os.path.exists(excel_path):
            print(f"{Fore.RED}❌ ADS-B data file not found: {excel_path}{Style.RESET_ALL}")
            return False

        print(f"\n{Fore.CYAN}Loading ADS-B data from: {excel_path}{Style.RESET_ALL}")
        self.db.load_adsb_data(excel_path)

        print(f"{Fore.GREEN}✅ ADS-B data loaded into SQL (vector sync handled by DB){Style.RESET_ALL}\n")

        return True

    def load_disaster_data(self):
        """Load current disaster data from APIs."""
        print(f"\n{Fore.CYAN}Loading current disaster events...{Style.RESET_ALL}")

        events = self.disaster_agent.api_tool.get_active_events(limit=50)
        for event in events:
            self.db.insert_disaster_event(event)

        # Fetch weather-specific categories separately from EONET
        _WEATHER_CATS = ["severeStorms", "floods", "drought", "snow",
                         "tempExtremes", "dustHaze"]
        weather_count = 0
        seen_ids = set()
        for cat in _WEATHER_CATS:
            cat_events = self.disaster_agent.api_tool.get_events_by_category(cat, limit=20)
            for event in cat_events:
                eid = event.get("event_id")
                if eid in seen_ids:
                    continue
                seen_ids.add(eid)
                # Insert into disaster_events as well (idempotent via REPLACE)
                self.db.insert_disaster_event(event)
                self.db.insert_weather_event({
                    "event_id": eid,
                    "event_type": event.get("event_type", cat),
                    "title": event.get("title"),
                    "description": event.get("description"),
                    "lat": event.get("lat"),
                    "lon": event.get("lon"),
                    "location_name": None,
                    "severity": None,
                    "start_time": event.get("start_date"),
                    "end_time": None,
                    "source": "eonet",
                    "metadata": {"sources": event.get("sources", []),
                                 "categories": event.get("categories", [])},
                })
                weather_count += 1

        print(f"{Fore.GREEN}✅ Loaded {len(events)} disaster events, {weather_count} weather events{Style.RESET_ALL}\n")

    def show_statistics(self):
        """Show system statistics."""
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{Fore.CYAN}📊 System Statistics")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

        aircraft_count = self.db.execute_query("SELECT COUNT(*) as count FROM aircraft")[0]["count"]
        disaster_count = self.db.execute_query("SELECT COUNT(*) as count FROM disaster_events")[0]["count"]
        weather_count = self.db.execute_query("SELECT COUNT(*) as count FROM weather_events")[0]["count"]

        print(f"  {Fore.YELLOW}Database Records:{Style.RESET_ALL}")
        print(f"    Aircraft:        {Fore.MAGENTA}{aircraft_count}{Style.RESET_ALL}")
        print(f"    Disaster Events: {Fore.MAGENTA}{disaster_count}{Style.RESET_ALL}")
        print(f"    Weather Events:  {Fore.MAGENTA}{weather_count}{Style.RESET_ALL}\n")

        print(f"  {Fore.YELLOW}Vector Database Collections:{Style.RESET_ALL}")
        print(f"    Flights:   {Fore.MAGENTA}{self.vector_db.get_collection_count('flights')}{Style.RESET_ALL}")
        print(f"    Weather:   {Fore.MAGENTA}{self.vector_db.get_collection_count('weather')}{Style.RESET_ALL}")
        print(f"    Disasters: {Fore.MAGENTA}{self.vector_db.get_collection_count('disasters')}{Style.RESET_ALL}\n")

    def interactive_mode(self):
        """Run system in interactive chat mode."""
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{Fore.CYAN}💬 Interactive Mode - Disaster Management RAG Chatbot")
        print(f"{Fore.CYAN}{'='*80}\n")
        print(f"{Fore.YELLOW}Commands:")
        print(f"  - Type your question about flights, weather, or disasters")
        print(f"  - 'load data' - Load ADS-B and disaster data")
        print(f"  - 'stats' - Show system statistics")
        print(f"  - 'exit' or 'quit' - Exit the system")
        print(f"{Style.RESET_ALL}\n")

        while True:
            try:
                user_input = input(f"{Fore.GREEN}You: {Style.RESET_ALL}").strip()

                if not user_input:
                    continue

                if user_input.lower() in ["exit", "quit", "q"]:
                    print(f"\n{Fore.CYAN}👋 Goodbye!{Style.RESET_ALL}\n")
                    break
                elif user_input.lower() == "load data":
                    self.load_adsb_data()
                    self.load_disaster_data()
                    continue
                elif user_input.lower() == "stats":
                    self.show_statistics()
                    continue

                result = self.process_query(user_input)

                # Display response
                print(f"\n{Fore.CYAN}{'─'*80}")
                print(f"{Fore.CYAN}Assistant:{Style.RESET_ALL}\n")

                final = result.get("final_response", {})
                if "unified_response" in final:
                    print(final["unified_response"])
                elif "answer" in final:
                    print(final["answer"])
                else:
                    print(f"{Fore.RED}Error: Unable to generate response{Style.RESET_ALL}")

                print(f"\n{Fore.CYAN}{'─'*80}{Style.RESET_ALL}\n")

            except KeyboardInterrupt:
                print(f"\n\n{Fore.CYAN}👋 Goodbye!{Style.RESET_ALL}\n")
                break
            except Exception as e:
                print(f"\n{Fore.RED}❌ Error: {e}{Style.RESET_ALL}\n")


# ── Singleton system instance for FastAPI ───────────────────────────────────

_system: DisasterRAGSystem = None


def get_system() -> DisasterRAGSystem:
    global _system
    if _system is None:
        _system = DisasterRAGSystem()
    return _system


# ── FastAPI endpoints ───────────────────────────────────────────────────────

@app.post("/api/query")
async def api_query(payload: dict):
    """Process a user query through the RAG system."""
    query = payload.get("query", "")
    if not query:
        return {"error": "No query provided"}
    system = get_system()
    result = system.process_query(query)
    return result


@app.get("/api/health")
async def health():
    return {"status": "ok", "system": "DisasterRAG (CrewAI + DSPy)"}


# ── FastAPI lifecycle: start / stop ingestion scheduler ─────────────────

@app.on_event("startup")
async def _startup():
    system = get_system()
    await system.scheduler.start()


@app.on_event("shutdown")
async def _shutdown():
    global _system
    if _system is not None:
        await _system.scheduler.stop()

class FeedbackRequest(BaseModel):
    rating: int
    category: str
    comment: str
    page: Optional[str] = None


@app.post("/api/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    if supabase is None:
        return {"error": "Supabase is not configured"}

    feedback_data = {
        "rating": feedback.rating,
        "category": feedback.category,
        "comment": feedback.comment,
        "page": feedback.page,
    }

    response = supabase.table("feedback").insert(feedback_data).execute()

    return {
        "message": "Feedback submitted successfully",
        "received": response.data
    }


# ── GNews articles endpoints ───────────────────────────────────────────

class GnewsArticlesPayload(BaseModel):
    articles: list

@app.post("/api/gnews/articles")
async def store_gnews_articles(payload: GnewsArticlesPayload):
    """Receive GNews articles from the frontend and store in SQLite."""
    db = get_system().db
    articles = payload.articles
    if not articles:
        return {"stored": 0, "message": "No articles provided"}
    count = db.upsert_gnews_articles_bulk(articles)
    return {"stored": count, "message": f"Stored {count} articles"}


@app.get("/api/gnews/articles")
async def get_gnews_articles(
    limit: int = Query(50, ge=1, le=500),
    region: str = Query(None),
):
    """Get stored GNews disaster news articles."""
    db = get_system().db
    return db.get_latest_gnews_articles(limit=limit, region=region)


# ── Debug / inspection endpoints ────────────────────────────────────────

@app.get("/api/alerts/latest")
async def latest_alerts(limit: int = Query(50, ge=1, le=500),
                        district: str = Query(None)):
    db = get_system().db
    return db.get_latest_alerts(limit=limit, district=district)


@app.get("/api/forecast/latest")
async def latest_forecast(limit: int = Query(100, ge=1, le=500),
                          location: str = Query(None)):
    db = get_system().db
    return db.get_latest_forecasts(limit=limit, location=location)


@app.get("/api/rainfall/latest")
async def latest_rainfall(limit: int = Query(50, ge=1, le=500)):
    db = get_system().db
    return db.get_latest_rainfall(limit=limit)


@app.get("/api/landslide/latest")
async def latest_landslide(limit: int = Query(50, ge=1, le=500)):
    db = get_system().db
    return db.get_latest_landslide_snapshot(limit=limit)


@app.get("/api/events/latest")
async def latest_events(limit: int = Query(50, ge=1, le=500),
                        event_type: str = Query(None)):
    db = get_system().db
    return db.get_latest_external_events(limit=limit, event_type=event_type)


@app.get("/api/ingestion/status")
async def ingestion_status(limit: int = Query(20, ge=1, le=200)):
    db = get_system().db
    return db.get_ingestion_status(limit=limit)


# ── CLI entry point ────────────────────────────────────────────────────────

def main():
    print(f"""
{Fore.CYAN}╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║        Disaster Management Multimodal Agentic RAG System      ║
║              CrewAI + DSPy  •  Hub Orchestrator               ║
║                                                                ║
║  Flight Tracking • Weather Analysis • Disaster Monitoring     ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
""")

    system = DisasterRAGSystem()
    system.interactive_mode()


if __name__ == "__main__":
    main()
