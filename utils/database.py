# """
# Database Manager for ADS-B and Disaster Data
# Handles SQLite operations with optimized schema for low-resource queries
# """
# import sqlite3
# import pandas as pd
# from typing import List, Dict, Optional, Any
# from pathlib import Path
# from config.config import Config
# import json
# from datetime import datetime

# class DatabaseManager:
#     """
#     SQLite Database Manager for disaster management system
#     Optimized for edge devices with efficient indexing
#     """
    
#     def __init__(self, db_path: Optional[str] = None):
#         self.db_path = db_path or Config.SQLITE_DB_PATH
#         self.conn = None
#         self.initialize_database()
    
#     def connect(self):
#         """Establish database connection"""
#         if not self.conn:
#             self.conn = sqlite3.connect(self.db_path)
#             self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
#         return self.conn
    
#     def close(self):
#         """Close database connection"""
#         if self.conn:
#             self.conn.close()
#             self.conn = None
    
#     def initialize_database(self):
#         """Create tables with optimized schema matching EXACT Excel columns"""
#         conn = self.connect()
#         cursor = conn.cursor()
        
#         # ADS-B Aircraft Table (Updated with EXACT column names)
#         cursor.execute("""
#         CREATE TABLE IF NOT EXISTS aircraft (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             now REAL,
#             messages INTEGER,
#             aircraft__hex TEXT,
#             aircraft__flight TEXT,
#             aircraft__alt_baro INTEGER,
#             aircraft__alt_geom INTEGER,
#             aircraft__gs REAL,
#             aircraft__ias INTEGER,
#             aircraft__tas INTEGER,
#             aircraft__mach REAL,
#             aircraft__track REAL,
#             aircraft__track_rate REAL,
#             aircraft__roll REAL,
#             aircraft__mag_heading REAL,
#             aircraft__baro_rate INTEGER,
#             aircraft__geom_rate INTEGER,
#             aircraft__squawk INTEGER,
#             aircraft__emergency TEXT,
#             aircraft__category TEXT,
#             aircraft__nav_qnh REAL,
#             aircraft__nav_altitude_mcp INTEGER,
#             aircraft__nav_altitude_fms INTEGER,
#             aircraft__nav_heading REAL,
#             aircraft__lat REAL,
#             aircraft__lon REAL,
#             aircraft__nic INTEGER,
#             aircraft__rc INTEGER,
#             aircraft__seen_pos REAL,
#             aircraft__version INTEGER,
#             aircraft__nic_baro INTEGER,
#             aircraft__nac_p INTEGER,
#             aircraft__nac_v INTEGER,
#             aircraft__sil INTEGER,
#             aircraft__sil_type TEXT,
#             aircraft__gva INTEGER,
#             aircraft__sda INTEGER,
#             aircraft__messages INTEGER,
#             aircraft__seen REAL,
#             aircraft__rssi REAL,
#             _sheet TEXT,
#             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#         )
#         """)
        
#         # Create indexes for common queries (Updated to use new column names)
#         cursor.execute("CREATE INDEX IF NOT EXISTS idx_aircraft_hex ON aircraft(aircraft__hex)")
#         cursor.execute("CREATE INDEX IF NOT EXISTS idx_aircraft_flight ON aircraft(aircraft__flight)")
#         cursor.execute("CREATE INDEX IF NOT EXISTS idx_aircraft_location ON aircraft(aircraft__lat, aircraft__lon)")
#         cursor.execute("CREATE INDEX IF NOT EXISTS idx_aircraft_emergency ON aircraft(aircraft__emergency)")
        
#         # Weather Events Table
#         cursor.execute("""
#         CREATE TABLE IF NOT EXISTS weather_events (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             event_id TEXT UNIQUE,
#             event_type TEXT NOT NULL,
#             title TEXT,
#             description TEXT,
#             lat REAL,
#             lon REAL,
#             location_name TEXT,
#             severity TEXT,
#             start_time TIMESTAMP,
#             end_time TIMESTAMP,
#             source TEXT,
#             metadata TEXT,
#             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#         )
#         """)
        
#         cursor.execute("CREATE INDEX IF NOT EXISTS idx_weather_type ON weather_events(event_type)")
#         cursor.execute("CREATE INDEX IF NOT EXISTS idx_weather_location ON weather_events(lat, lon)")
#         cursor.execute("CREATE INDEX IF NOT EXISTS idx_weather_time ON weather_events(start_time)")
        
#         # Disaster Events Table (from EONET)
#         cursor.execute("""
#         CREATE TABLE IF NOT EXISTS disaster_events (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             event_id TEXT UNIQUE NOT NULL,
#             title TEXT NOT NULL,
#             description TEXT,
#             event_type TEXT,
#             lat REAL,
#             lon REAL,
#             location_name TEXT,
#             severity TEXT,
#             start_date TEXT,
#             end_date TEXT,
#             sources TEXT,
#             categories TEXT,
#             metadata TEXT,
#             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#         )
#         """)
        
#         cursor.execute("CREATE INDEX IF NOT EXISTS idx_disaster_type ON disaster_events(event_type)")
#         cursor.execute("CREATE INDEX IF NOT EXISTS idx_disaster_location ON disaster_events(lat, lon)")
#         cursor.execute("CREATE INDEX IF NOT EXISTS idx_disaster_date ON disaster_events(start_date)")
        
#         # Cross-Intelligence Correlations Table
#         cursor.execute("""
#         CREATE TABLE IF NOT EXISTS correlations (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             correlation_type TEXT NOT NULL,
#             entity1_type TEXT NOT NULL,
#             entity1_id INTEGER NOT NULL,
#             entity2_type TEXT NOT NULL,
#             entity2_id INTEGER NOT NULL,
#             correlation_score REAL,
#             reasoning TEXT,
#             metadata TEXT,
#             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#         )
#         """)
        
#         cursor.execute("CREATE INDEX IF NOT EXISTS idx_correlation_type ON correlations(correlation_type)")
        
#         conn.commit()
#         print("✅ Database initialized successfully")
    
#     def load_adsb_data(self, excel_path: str):
#         """
#         Load ADS-B data from Excel file into database
#         Keeps exact column names as requested.
#         """
#         conn = self.connect()
        
#         try:
#             # Read all sheets
#             excel_file = pd.ExcelFile(excel_path)
#             total_records = 0
            
#             for sheet_name in excel_file.sheet_names:
#                 df = pd.read_excel(excel_path, sheet_name=sheet_name)
                
#                 # Add the _sheet column if it's missing in the dataframe
#                 if '_sheet' not in df.columns:
#                     df['_sheet'] = sheet_name

#                 # Filter dataframe to only include valid columns that match our schema
#                 # This ensures we don't crash on weird extra Excel columns
#                 valid_columns = [
#                     'now', 'messages', 'aircraft__hex', 'aircraft__flight',
#                     'aircraft__alt_baro', 'aircraft__alt_geom', 'aircraft__gs',
#                     'aircraft__ias', 'aircraft__tas', 'aircraft__mach', 'aircraft__track',
#                     'aircraft__track_rate', 'aircraft__roll', 'aircraft__mag_heading',
#                     'aircraft__baro_rate', 'aircraft__geom_rate', 'aircraft__squawk',
#                     'aircraft__emergency', 'aircraft__category', 'aircraft__nav_qnh',
#                     'aircraft__nav_altitude_mcp', 'aircraft__nav_altitude_fms',
#                     'aircraft__nav_heading', 'aircraft__lat', 'aircraft__lon',
#                     'aircraft__nic', 'aircraft__rc', 'aircraft__seen_pos',
#                     'aircraft__version', 'aircraft__nic_baro', 'aircraft__nac_p',
#                     'aircraft__nac_v', 'aircraft__sil', 'aircraft__sil_type',
#                     'aircraft__gva', 'aircraft__sda', 'aircraft__messages',
#                     'aircraft__seen', 'aircraft__rssi', '_sheet'
#                 ]
                
#                 # Only keep columns that exist in the dataframe AND our schema
#                 cols_to_keep = [col for col in valid_columns if col in df.columns]
#                 df_final = df[cols_to_keep]

#                 # Insert data without renaming
#                 df_final.to_sql('aircraft', conn, if_exists='append', index=False)
#                 total_records += len(df)
                
#                 print(f"✅ Loaded {len(df)} records from sheet: {sheet_name}")
            
#             conn.commit()
#             print(f"✅ Total ADS-B records loaded: {total_records}")
            
#         except Exception as e:
#             print(f"❌ Error loading ADS-B data: {e}")
#             conn.rollback()
    
#     def insert_weather_event(self, event_data: Dict[str, Any]):
#         """Insert weather event into database"""
#         conn = self.connect()
#         cursor = conn.cursor()
        
#         try:
#             cursor.execute("""
#                 INSERT OR REPLACE INTO weather_events 
#                 (event_id, event_type, title, description, lat, lon, location_name, 
#                  severity, start_time, end_time, source, metadata)
#                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#             """, (
#                 event_data.get('event_id'),
#                 event_data.get('event_type'),
#                 event_data.get('title'),
#                 event_data.get('description'),
#                 event_data.get('lat'),
#                 event_data.get('lon'),
#                 event_data.get('location_name'),
#                 event_data.get('severity'),
#                 event_data.get('start_time'),
#                 event_data.get('end_time'),
#                 event_data.get('source'),
#                 json.dumps(event_data.get('metadata', {}))
#             ))
#             conn.commit()
#         except Exception as e:
#             print(f"❌ Error inserting weather event: {e}")
#             conn.rollback()
    
#     def insert_disaster_event(self, event_data: Dict[str, Any]):
#         """Insert disaster event into database"""
#         conn = self.connect()
#         cursor = conn.cursor()
        
#         try:
#             cursor.execute("""
#                 INSERT OR REPLACE INTO disaster_events 
#                 (event_id, title, description, event_type, lat, lon, location_name,
#                  severity, start_date, end_date, sources, categories, metadata)
#                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#             """, (
#                 event_data.get('event_id'),
#                 event_data.get('title'),
#                 event_data.get('description'),
#                 event_data.get('event_type'),
#                 event_data.get('lat'),
#                 event_data.get('lon'),
#                 event_data.get('location_name'),
#                 event_data.get('severity'),
#                 event_data.get('start_date'),
#                 event_data.get('end_date'),
#                 json.dumps(event_data.get('sources', [])),
#                 json.dumps(event_data.get('categories', [])),
#                 json.dumps(event_data.get('metadata', {}))
#             ))
#             conn.commit()
#         except Exception as e:
#             print(f"❌ Error inserting disaster event: {e}")
#             conn.rollback()
    
#     def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
#         """
#         Execute SQL query and return results
        
#         Args:
#             query: SQL query string
#             params: Query parameters
            
#         Returns:
#             List of result dictionaries
#         """
#         conn = self.connect()
#         cursor = conn.cursor()
        
#         try:
#             cursor.execute(query, params)
#             columns = [description[0] for description in cursor.description]
#             results = []
            
#             for row in cursor.fetchall():
#                 results.append(dict(zip(columns, row)))
            
#             return results
#         except Exception as e:
#             print(f"❌ Query error: {e}")
#             return []
    
#     def __enter__(self):
#         """Context manager entry"""
#         self.connect()
#         return self
    
#     def __exit__(self, exc_type, exc_val, exc_tb):
#         """Context manager exit"""
#         self.close()


# if __name__ == "__main__":
#     # Test database initialization
#     db = DatabaseManager()
#     print("Database initialized successfully!")
    
#     # Test query
#     results = db.execute_query("SELECT COUNT(*) as count FROM aircraft")
#     print(f"Total aircraft records: {results[0]['count'] if results else 0}")

"""
Database Manager for ADS-B and Disaster Data
Handles SQLite operations with optimized schema for low-resource queries

✅ FastAPI-safe: uses new SQLite connection per operation (check_same_thread=False)
✅ Avoids "Internal Server Error" caused by shared connection across threads
"""
import sqlite3
import pandas as pd
from typing import List, Dict, Optional, Any
from config.config import Config
import json
import logging
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    SQLite Database Manager for disaster management system
    Optimized for edge devices with efficient indexing
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or Config.SQLITE_DB_PATH
        self._vector_db = None
        self.initialize_database()

    # ----------------------------
    # VECTOR SYNC (OPTIONAL)
    # ----------------------------
    def set_vector_db(self, vector_db):
        """Inject a VectorDBManager instance (optional)."""
        self._vector_db = vector_db

    def _get_vector_db(self):
        """Lazy init to avoid loading embeddings unless enabled."""
        if not Config.ENABLE_VECTOR_SYNC:
            return None
        if self._vector_db is None:
            try:
                from utils.vector_db import VectorDBManager
                self._vector_db = VectorDBManager()
            except Exception as exc:
                logger.error("Vector DB init failed: %s", exc)
                self._vector_db = None
        return self._vector_db

    def _sync_flights_to_vector(self, records: List[Dict[str, Any]]):
        vector_db = self._get_vector_db()
        if not vector_db or not records:
            return
        try:
            vector_db.add_flight_data(records)
        except Exception as exc:
            logger.error("Vector sync flight error: %s", exc)

    def _sync_weather_event(self, event_data: Dict[str, Any]):
        vector_db = self._get_vector_db()
        if not vector_db or not event_data:
            return
        try:
            vector_db.add_weather_event(event_data)
        except Exception as exc:
            logger.error("Vector sync weather error: %s", exc)

    def _sync_disaster_event(self, event_data: Dict[str, Any]):
        vector_db = self._get_vector_db()
        if not vector_db or not event_data:
            return
        try:
            payload = {
                "event_id": event_data.get("event_id")
                or event_data.get("external_id")
                or str(uuid.uuid4()),
                "event_type": event_data.get("event_type")
                or event_data.get("alert_type")
                or "",
                "title": event_data.get("title") or "",
                "description": event_data.get("description") or "",
                "lat": event_data.get("lat")
                if event_data.get("lat") is not None else event_data.get("latitude"),
                "lon": event_data.get("lon")
                if event_data.get("lon") is not None else event_data.get("longitude"),
                "location_name": event_data.get("location_name")
                or event_data.get("district")
                or event_data.get("region")
                or "",
                "severity": event_data.get("severity"),
                "start_date": event_data.get("start_date")
                or event_data.get("start_time")
                or event_data.get("onset"),
            }
            vector_db.add_disaster_event(payload)
        except Exception as exc:
            logger.error("Vector sync disaster error: %s", exc)

    # ----------------------------
    # CONNECTION (THREAD-SAFE)
    # ----------------------------
    def connect(self):
        """
        Create a NEW connection each time (thread-safe for FastAPI).
        """
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    # ----------------------------
    # INIT DB
    # ----------------------------
    def initialize_database(self):
        """Create tables with optimized schema matching EXACT Excel columns"""
        conn = self.connect()
        cursor = conn.cursor()

        # ADS-B Aircraft Table (Exact column names)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS aircraft (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            now REAL,
            messages INTEGER,
            aircraft__hex TEXT,
            aircraft__flight TEXT,
            aircraft__alt_baro INTEGER,
            aircraft__alt_geom INTEGER,
            aircraft__gs REAL,
            aircraft__ias INTEGER,
            aircraft__tas INTEGER,
            aircraft__mach REAL,
            aircraft__track REAL,
            aircraft__track_rate REAL,
            aircraft__roll REAL,
            aircraft__mag_heading REAL,
            aircraft__baro_rate INTEGER,
            aircraft__geom_rate INTEGER,
            aircraft__squawk INTEGER,
            aircraft__emergency TEXT,
            aircraft__category TEXT,
            aircraft__nav_qnh REAL,
            aircraft__nav_altitude_mcp INTEGER,
            aircraft__nav_altitude_fms INTEGER,
            aircraft__nav_heading REAL,
            aircraft__lat REAL,
            aircraft__lon REAL,
            aircraft__nic INTEGER,
            aircraft__rc INTEGER,
            aircraft__seen_pos REAL,
            aircraft__version INTEGER,
            aircraft__nic_baro INTEGER,
            aircraft__nac_p INTEGER,
            aircraft__nac_v INTEGER,
            aircraft__sil INTEGER,
            aircraft__sil_type TEXT,
            aircraft__gva INTEGER,
            aircraft__sda INTEGER,
            aircraft__messages INTEGER,
            aircraft__seen REAL,
            aircraft__rssi REAL,
            _sheet TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_aircraft_hex ON aircraft(aircraft__hex)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_aircraft_flight ON aircraft(aircraft__flight)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_aircraft_location ON aircraft(aircraft__lat, aircraft__lon)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_aircraft_emergency ON aircraft(aircraft__emergency)")

        # Weather Events Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS weather_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT UNIQUE,
            event_type TEXT NOT NULL,
            title TEXT,
            description TEXT,
            lat REAL,
            lon REAL,
            location_name TEXT,
            severity TEXT,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            source TEXT,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_weather_type ON weather_events(event_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_weather_location ON weather_events(lat, lon)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_weather_time ON weather_events(start_time)")

        # Disaster Events Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS disaster_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            event_type TEXT,
            lat REAL,
            lon REAL,
            location_name TEXT,
            severity TEXT,
            start_date TEXT,
            end_date TEXT,
            sources TEXT,
            categories TEXT,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_disaster_type ON disaster_events(event_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_disaster_location ON disaster_events(lat, lon)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_disaster_date ON disaster_events(start_date)")

        # Correlations Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS correlations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            correlation_type TEXT NOT NULL,
            entity1_type TEXT NOT NULL,
            entity1_id INTEGER NOT NULL,
            entity2_type TEXT NOT NULL,
            entity2_id INTEGER NOT NULL,
            correlation_score REAL,
            reasoning TEXT,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_correlation_type ON correlations(correlation_type)")

        # ── New ingestion tables ─────────────────────────────────────────

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS source_fetch_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_name TEXT NOT NULL,
            fetch_url TEXT,
            fetch_started_at TEXT,
            fetch_completed_at TEXT,
            status TEXT,
            http_status INTEGER,
            etag_sent TEXT,
            etag_received TEXT,
            records_processed INTEGER DEFAULT 0,
            error_message TEXT,
            metadata TEXT
        )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sfl_source ON source_fetch_log(source_name)")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_payload_store (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_name TEXT NOT NULL,
            payload_type TEXT,
            external_id TEXT,
            payload_hash TEXT,
            payload_text TEXT,
            payload_json TEXT,
            file_path TEXT,
            fetched_at TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rps_source ON raw_payload_store(source_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rps_extid ON raw_payload_store(external_id)")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS official_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_name TEXT NOT NULL,
            external_id TEXT NOT NULL,
            alert_type TEXT,
            title TEXT,
            description TEXT,
            severity TEXT,
            urgency TEXT,
            certainty TEXT,
            area_desc TEXT,
            district TEXT,
            state TEXT,
            latitude REAL,
            longitude REAL,
            onset TEXT,
            expires TEXT,
            status TEXT,
            source_url TEXT,
            raw_payload_ref INTEGER,
            fetched_at TEXT,
            updated_at TEXT DEFAULT (datetime('now')),
            UNIQUE(source_name, external_id)
        )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_oa_source ON official_alerts(source_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_oa_extid ON official_alerts(external_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_oa_district ON official_alerts(district)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_oa_state ON official_alerts(state)")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS forecast_signals_hot (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_name TEXT NOT NULL,
            location_name TEXT,
            district TEXT,
            latitude REAL,
            longitude REAL,
            forecast_time TEXT,
            precipitation REAL,
            precipitation_probability REAL,
            showers REAL,
            rain REAL,
            wind_gusts_10m REAL,
            weather_code INTEGER,
            cape REAL,
            cloud_cover REAL,
            risk_score REAL,
            raw_payload_ref INTEGER,
            fetched_at TEXT
        )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fsh_source ON forecast_signals_hot(source_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fsh_ftime ON forecast_signals_hot(forecast_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fsh_district ON forecast_signals_hot(district)")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS forecast_signals_warm (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_name TEXT NOT NULL,
            location_name TEXT,
            district TEXT,
            latitude REAL,
            longitude REAL,
            forecast_time TEXT,
            precipitation REAL,
            precipitation_probability REAL,
            showers REAL,
            rain REAL,
            wind_gusts_10m REAL,
            weather_code INTEGER,
            cape REAL,
            cloud_cover REAL,
            risk_score REAL,
            raw_payload_ref INTEGER,
            fetched_at TEXT
        )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fsw_source ON forecast_signals_warm(source_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fsw_ftime ON forecast_signals_warm(forecast_time)")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS rainfall_observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_name TEXT NOT NULL,
            external_id TEXT,
            location_name TEXT,
            district TEXT,
            latitude REAL,
            longitude REAL,
            observation_time TEXT,
            rainfall_mm REAL,
            aggregation_window TEXT,
            dataset_metadata TEXT,
            raw_payload_ref INTEGER,
            fetched_at TEXT,
            UNIQUE(source_name, external_id, observation_time)
        )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ro_source ON rainfall_observations(source_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ro_obstime ON rainfall_observations(observation_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ro_district ON rainfall_observations(district)")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS landslide_snapshot_current (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_name TEXT NOT NULL,
            region_name TEXT,
            district TEXT,
            snapshot_time TEXT,
            latitude REAL,
            longitude REAL,
            probability REAL,
            risk_level TEXT,
            exposure_population INTEGER,
            exposure_roads REAL,
            metadata TEXT,
            raw_payload_ref INTEGER,
            fetched_at TEXT
        )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_lsc_source ON landslide_snapshot_current(source_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_lsc_snaptime ON landslide_snapshot_current(snapshot_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_lsc_district ON landslide_snapshot_current(district)")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS external_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_name TEXT NOT NULL,
            external_id TEXT NOT NULL,
            event_type TEXT,
            title TEXT,
            description TEXT,
            severity TEXT,
            country TEXT,
            region TEXT,
            latitude REAL,
            longitude REAL,
            start_time TEXT,
            end_time TEXT,
            source_url TEXT,
            raw_payload_ref INTEGER,
            fetched_at TEXT,
            updated_at TEXT DEFAULT (datetime('now')),
            UNIQUE(source_name, external_id)
        )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ee_source ON external_events(source_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ee_extid ON external_events(external_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ee_etype ON external_events(event_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ee_start ON external_events(start_time)")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS historical_cyclones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_name TEXT NOT NULL,
            storm_id TEXT,
            storm_name TEXT,
            basin TEXT,
            season TEXT,
            timestamp TEXT,
            latitude REAL,
            longitude REAL,
            wind_kts REAL,
            pressure_mb REAL,
            category TEXT,
            metadata TEXT,
            raw_payload_ref INTEGER,
            created_at TEXT DEFAULT (datetime('now'))
        )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hc_stormid ON historical_cyclones(storm_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hc_ts ON historical_cyclones(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hc_source ON historical_cyclones(source_name)")

        # ── GNews articles table ─────────────────────────────────────────
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS gnews_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_url TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            source_name TEXT,
            source_url TEXT,
            image_url TEXT,
            published_at TEXT,
            severity TEXT,
            region TEXT,
            fetched_at TEXT DEFAULT (datetime('now')),
            created_at TEXT DEFAULT (datetime('now'))
        )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_gna_published ON gnews_articles(published_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_gna_region ON gnews_articles(region)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_gna_severity ON gnews_articles(severity)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_gna_fetched ON gnews_articles(fetched_at)")

        conn.commit()
        conn.close()
        print("✅ Database initialized successfully")

    # ----------------------------
    # LOAD ADSB EXCEL
    # ----------------------------
    def load_adsb_data(self, excel_path: str):
        """
        Load ADS-B data from Excel file into database.
        Keeps exact column names as requested.
        """
        conn = self.connect()
        try:
            excel_file = pd.ExcelFile(excel_path)
            total_records = 0

            valid_columns = [
                'now', 'messages', 'aircraft__hex', 'aircraft__flight',
                'aircraft__alt_baro', 'aircraft__alt_geom', 'aircraft__gs',
                'aircraft__ias', 'aircraft__tas', 'aircraft__mach', 'aircraft__track',
                'aircraft__track_rate', 'aircraft__roll', 'aircraft__mag_heading',
                'aircraft__baro_rate', 'aircraft__geom_rate', 'aircraft__squawk',
                'aircraft__emergency', 'aircraft__category', 'aircraft__nav_qnh',
                'aircraft__nav_altitude_mcp', 'aircraft__nav_altitude_fms',
                'aircraft__nav_heading', 'aircraft__lat', 'aircraft__lon',
                'aircraft__nic', 'aircraft__rc', 'aircraft__seen_pos',
                'aircraft__version', 'aircraft__nic_baro', 'aircraft__nac_p',
                'aircraft__nac_v', 'aircraft__sil', 'aircraft__sil_type',
                'aircraft__gva', 'aircraft__sda', 'aircraft__messages',
                'aircraft__seen', 'aircraft__rssi', '_sheet'
            ]

            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_path, sheet_name=sheet_name)

                if '_sheet' not in df.columns:
                    df['_sheet'] = sheet_name

                cols_to_keep = [c for c in valid_columns if c in df.columns]
                df_final = df[cols_to_keep]

                df_final.to_sql('aircraft', conn, if_exists='append', index=False)
                total_records += len(df_final)

                # Sync new flight rows into vector DB
                self._sync_flights_to_vector(df_final.to_dict(orient="records"))

                print(f"✅ Loaded {len(df_final)} records from sheet: {sheet_name}")

            conn.commit()
            print(f"✅ Total ADS-B records loaded: {total_records}")

        except Exception as e:
            print(f"❌ Error loading ADS-B data: {e}")
            conn.rollback()
        finally:
            conn.close()

    # ----------------------------
    # INSERT EVENTS
    # ----------------------------
    def insert_weather_event(self, event_data: Dict[str, Any]):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO weather_events
                (event_id, event_type, title, description, lat, lon, location_name,
                 severity, start_time, end_time, source, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_data.get('event_id'),
                event_data.get('event_type'),
                event_data.get('title'),
                event_data.get('description'),
                event_data.get('lat'),
                event_data.get('lon'),
                event_data.get('location_name'),
                event_data.get('severity'),
                event_data.get('start_time'),
                event_data.get('end_time'),
                event_data.get('source'),
                json.dumps(event_data.get('metadata', {}))
            ))
            conn.commit()
            self._sync_weather_event(event_data)
        except Exception as e:
            print(f"❌ Error inserting weather event: {e}")
            conn.rollback()
        finally:
            conn.close()

    def insert_disaster_event(self, event_data: Dict[str, Any]):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO disaster_events
                (event_id, title, description, event_type, lat, lon, location_name,
                 severity, start_date, end_date, sources, categories, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_data.get('event_id'),
                event_data.get('title'),
                event_data.get('description'),
                event_data.get('event_type'),
                event_data.get('lat'),
                event_data.get('lon'),
                event_data.get('location_name'),
                event_data.get('severity'),
                event_data.get('start_date'),
                event_data.get('end_date'),
                json.dumps(event_data.get('sources', [])),
                json.dumps(event_data.get('categories', [])),
                json.dumps(event_data.get('metadata', {}))
            ))
            conn.commit()
            self._sync_disaster_event(event_data)
        except Exception as e:
            print(f"❌ Error inserting disaster event: {e}")
            conn.rollback()
        finally:
            conn.close()

    # ----------------------------
    # INGESTION HELPERS
    # ----------------------------

    def log_source_fetch(self, source_name: str, fetch_url: str,
                         fetch_started_at: str, fetch_completed_at: str,
                         status: str, http_status: int = None,
                         etag_sent: str = None, etag_received: str = None,
                         records_processed: int = 0, error_message: str = None,
                         metadata: dict = None) -> int:
        """Log an ingestion fetch attempt."""
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO source_fetch_log
                (source_name, fetch_url, fetch_started_at, fetch_completed_at,
                 status, http_status, etag_sent, etag_received,
                 records_processed, error_message, metadata)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (source_name, fetch_url, fetch_started_at, fetch_completed_at,
                  status, http_status, etag_sent, etag_received,
                  records_processed, error_message,
                  json.dumps(metadata) if metadata else None))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error("log_source_fetch error: %s", e)
            conn.rollback()
            return -1
        finally:
            conn.close()

    def store_raw_payload(self, source_name: str, payload_type: str,
                          external_id: str = None, payload_hash: str = None,
                          payload_text: str = None, payload_json: dict = None,
                          file_path: str = None, fetched_at: str = None) -> int:
        """Store a raw payload record."""
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO raw_payload_store
                (source_name, payload_type, external_id, payload_hash,
                 payload_text, payload_json, file_path, fetched_at)
                VALUES (?,?,?,?,?,?,?,?)
            """, (source_name, payload_type, external_id, payload_hash,
                  payload_text,
                  json.dumps(payload_json) if payload_json else None,
                  file_path, fetched_at or datetime.utcnow().isoformat()))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error("store_raw_payload error: %s", e)
            conn.rollback()
            return -1
        finally:
            conn.close()

    def list_raw_payloads_older_than(self, cutoff_iso: str) -> List[Dict[str, Any]]:
        """Return raw payload rows older than the cutoff timestamp."""
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT id, file_path FROM raw_payload_store WHERE fetched_at < ?",
                (cutoff_iso,),
            )
            cols = [d[0] for d in cursor.description] if cursor.description else []
            return [dict(zip(cols, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error("list_raw_payloads_older_than error: %s", e)
            return []
        finally:
            conn.close()

    def delete_raw_payloads_older_than(self, cutoff_iso: str) -> int:
        """Delete raw payload rows older than the cutoff timestamp."""
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "DELETE FROM raw_payload_store WHERE fetched_at < ?",
                (cutoff_iso,),
            )
            deleted = cursor.rowcount
            conn.commit()
            return deleted
        except Exception as e:
            logger.error("delete_raw_payloads_older_than error: %s", e)
            conn.rollback()
            return 0
        finally:
            conn.close()

    def upsert_official_alert(self, data: Dict[str, Any]) -> bool:
        """Upsert an official alert (SACHET/NDMA)."""
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO official_alerts
                (source_name, external_id, alert_type, title, description,
                 severity, urgency, certainty, area_desc, district, state,
                 latitude, longitude, onset, expires, status, source_url,
                 raw_payload_ref, fetched_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?, datetime('now'))
                ON CONFLICT(source_name, external_id) DO UPDATE SET
                    alert_type=excluded.alert_type,
                    title=excluded.title,
                    description=excluded.description,
                    severity=excluded.severity,
                    urgency=excluded.urgency,
                    certainty=excluded.certainty,
                    area_desc=excluded.area_desc,
                    district=excluded.district,
                    state=excluded.state,
                    latitude=excluded.latitude,
                    longitude=excluded.longitude,
                    onset=excluded.onset,
                    expires=excluded.expires,
                    status=excluded.status,
                    source_url=excluded.source_url,
                    raw_payload_ref=excluded.raw_payload_ref,
                    fetched_at=excluded.fetched_at,
                    updated_at=datetime('now')
            """, (
                data.get("source_name"), data.get("external_id"),
                data.get("alert_type"), data.get("title"),
                data.get("description"), data.get("severity"),
                data.get("urgency"), data.get("certainty"),
                data.get("area_desc"), data.get("district"),
                data.get("state"), data.get("latitude"),
                data.get("longitude"), data.get("onset"),
                data.get("expires"), data.get("status"),
                data.get("source_url"), data.get("raw_payload_ref"),
                data.get("fetched_at"),
            ))
            conn.commit()
            self._sync_disaster_event(data)
            return True
        except Exception as e:
            logger.error("upsert_official_alert error: %s", e)
            conn.rollback()
            return False
        finally:
            conn.close()

    def replace_forecast_window(self, source_name: str, location_name: str,
                                rows: List[Dict[str, Any]]) -> int:
        """Delete current hot forecasts for source+location then insert new rows."""
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "DELETE FROM forecast_signals_hot WHERE source_name=? AND location_name=?",
                (source_name, location_name),
            )
            count = 0
            for r in rows:
                cursor.execute("""
                    INSERT INTO forecast_signals_hot
                    (source_name, location_name, district, latitude, longitude,
                     forecast_time, precipitation, precipitation_probability,
                     showers, rain, wind_gusts_10m, weather_code, cape,
                     cloud_cover, risk_score, raw_payload_ref, fetched_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    source_name, location_name, r.get("district"),
                    r.get("latitude"), r.get("longitude"),
                    r.get("forecast_time"), r.get("precipitation"),
                    r.get("precipitation_probability"), r.get("showers"),
                    r.get("rain"), r.get("wind_gusts_10m"),
                    r.get("weather_code"), r.get("cape"),
                    r.get("cloud_cover"), r.get("risk_score"),
                    r.get("raw_payload_ref"), r.get("fetched_at"),
                ))
                count += 1
            conn.commit()
            return count
        except Exception as e:
            logger.error("replace_forecast_window error: %s", e)
            conn.rollback()
            return 0
        finally:
            conn.close()

    def move_hot_forecasts_to_warm(self, older_than_hours: int = None) -> int:
        """Move hot forecast rows older than threshold into warm storage."""
        hours = older_than_hours or Config.HOT_RETENTION_HOURS
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO forecast_signals_warm
                SELECT * FROM forecast_signals_hot
                WHERE forecast_time < ?
            """, (cutoff,))
            cursor.execute(
                "DELETE FROM forecast_signals_hot WHERE forecast_time < ?",
                (cutoff,),
            )
            moved = cursor.rowcount
            conn.commit()
            return moved
        except Exception as e:
            logger.error("move_hot_forecasts_to_warm error: %s", e)
            conn.rollback()
            return 0
        finally:
            conn.close()

    def append_rainfall_observation(self, data: Dict[str, Any]) -> bool:
        """Append a rainfall observation (deduplicated)."""
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO rainfall_observations
                (source_name, external_id, location_name, district,
                 latitude, longitude, observation_time,
                 rainfall_mm, aggregation_window, dataset_metadata,
                 raw_payload_ref, fetched_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                data.get("source_name"), data.get("external_id"),
                data.get("location_name"), data.get("district"),
                data.get("latitude"), data.get("longitude"),
                data.get("observation_time"), data.get("rainfall_mm"),
                data.get("aggregation_window"),
                json.dumps(data.get("dataset_metadata")) if data.get("dataset_metadata") else None,
                data.get("raw_payload_ref"), data.get("fetched_at"),
            ))
            conn.commit()
            return True
        except Exception as e:
            logger.error("append_rainfall_observation error: %s", e)
            conn.rollback()
            return False
        finally:
            conn.close()

    def replace_landslide_snapshot(self, source_name: str,
                                   rows: List[Dict[str, Any]]) -> int:
        """Replace the current landslide snapshot for a source."""
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "DELETE FROM landslide_snapshot_current WHERE source_name=?",
                (source_name,),
            )
            count = 0
            for r in rows:
                cursor.execute("""
                    INSERT INTO landslide_snapshot_current
                    (source_name, region_name, district, snapshot_time,
                     latitude, longitude, probability, risk_level,
                     exposure_population, exposure_roads, metadata,
                     raw_payload_ref, fetched_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    source_name, r.get("region_name"), r.get("district"),
                    r.get("snapshot_time"), r.get("latitude"),
                    r.get("longitude"), r.get("probability"),
                    r.get("risk_level"), r.get("exposure_population"),
                    r.get("exposure_roads"),
                    json.dumps(r.get("metadata")) if r.get("metadata") else None,
                    r.get("raw_payload_ref"), r.get("fetched_at"),
                ))
                count += 1
            conn.commit()
            return count
        except Exception as e:
            logger.error("replace_landslide_snapshot error: %s", e)
            conn.rollback()
            return 0
        finally:
            conn.close()

    def upsert_external_event(self, data: Dict[str, Any]) -> bool:
        """Upsert a GDACS-style external event."""
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO external_events
                (source_name, external_id, event_type, title, description,
                 severity, country, region, latitude, longitude,
                 start_time, end_time, source_url, raw_payload_ref,
                 fetched_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?, datetime('now'))
                ON CONFLICT(source_name, external_id) DO UPDATE SET
                    event_type=excluded.event_type,
                    title=excluded.title,
                    description=excluded.description,
                    severity=excluded.severity,
                    country=excluded.country,
                    region=excluded.region,
                    latitude=excluded.latitude,
                    longitude=excluded.longitude,
                    start_time=excluded.start_time,
                    end_time=excluded.end_time,
                    source_url=excluded.source_url,
                    raw_payload_ref=excluded.raw_payload_ref,
                    fetched_at=excluded.fetched_at,
                    updated_at=datetime('now')
            """, (
                data.get("source_name"), data.get("external_id"),
                data.get("event_type"), data.get("title"),
                data.get("description"), data.get("severity"),
                data.get("country"), data.get("region"),
                data.get("latitude"), data.get("longitude"),
                data.get("start_time"), data.get("end_time"),
                data.get("source_url"), data.get("raw_payload_ref"),
                data.get("fetched_at"),
            ))
            conn.commit()
            self._sync_disaster_event(data)
            return True
        except Exception as e:
            logger.error("upsert_external_event error: %s", e)
            conn.rollback()
            return False
        finally:
            conn.close()

    def batch_insert_historical_cyclones(self, rows: List[Dict[str, Any]]) -> int:
        """Batch insert IBTrACS historical cyclone rows (insert-or-ignore)."""
        conn = self.connect()
        cursor = conn.cursor()
        count = 0
        try:
            for r in rows:
                cursor.execute("""
                    INSERT OR IGNORE INTO historical_cyclones
                    (source_name, storm_id, storm_name, basin, season,
                     timestamp, latitude, longitude, wind_kts, pressure_mb,
                     category, metadata, raw_payload_ref)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    r.get("source_name", "ibtracs"), r.get("storm_id"),
                    r.get("storm_name"), r.get("basin"), r.get("season"),
                    r.get("timestamp"), r.get("latitude"), r.get("longitude"),
                    r.get("wind_kts"), r.get("pressure_mb"),
                    r.get("category"),
                    json.dumps(r.get("metadata")) if r.get("metadata") else None,
                    r.get("raw_payload_ref"),
                ))
                count += 1
            conn.commit()
            return count
        except Exception as e:
            logger.error("batch_insert_historical_cyclones error: %s", e)
            conn.rollback()
            return count
        finally:
            conn.close()

    def archive_old_records(self, table: str, time_col: str,
                            older_than_days: int) -> int:
        """Delete records older than N days from a given table.
        (Cold archival to file should happen before calling this.)"""
        cutoff = (datetime.utcnow() - timedelta(days=older_than_days)).isoformat()
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"DELETE FROM [{table}] WHERE [{time_col}] < ?", (cutoff,)
            )
            deleted = cursor.rowcount
            conn.commit()
            return deleted
        except Exception as e:
            logger.error("archive_old_records error on %s: %s", table, e)
            conn.rollback()
            return 0
        finally:
            conn.close()

    # ----------------------------
    # READ HELPERS (latest data)
    # ----------------------------

    def get_latest_alerts(self, limit: int = 50,
                          district: str = None) -> List[Dict]:
        conn = self.connect()
        cursor = conn.cursor()
        try:
            if district:
                cursor.execute("""
                    SELECT * FROM official_alerts
                    WHERE district LIKE ?
                    ORDER BY fetched_at DESC LIMIT ?
                """, (f"%{district}%", limit))
            else:
                cursor.execute("""
                    SELECT * FROM official_alerts
                    ORDER BY fetched_at DESC LIMIT ?
                """, (limit,))
            cols = [d[0] for d in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_latest_forecasts(self, limit: int = 100,
                             location: str = None) -> List[Dict]:
        conn = self.connect()
        cursor = conn.cursor()
        try:
            if location:
                cursor.execute("""
                    SELECT * FROM forecast_signals_hot
                    WHERE location_name LIKE ?
                    ORDER BY forecast_time DESC LIMIT ?
                """, (f"%{location}%", limit))
            else:
                cursor.execute("""
                    SELECT * FROM forecast_signals_hot
                    ORDER BY forecast_time DESC LIMIT ?
                """, (limit,))
            cols = [d[0] for d in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_latest_rainfall(self, limit: int = 50) -> List[Dict]:
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT * FROM rainfall_observations
                ORDER BY observation_time DESC LIMIT ?
            """, (limit,))
            cols = [d[0] for d in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_latest_landslide_snapshot(self, limit: int = 50) -> List[Dict]:
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT * FROM landslide_snapshot_current
                ORDER BY snapshot_time DESC LIMIT ?
            """, (limit,))
            cols = [d[0] for d in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_latest_external_events(self, limit: int = 50,
                                   event_type: str = None) -> List[Dict]:
        conn = self.connect()
        cursor = conn.cursor()
        try:
            if event_type:
                cursor.execute("""
                    SELECT * FROM external_events
                    WHERE event_type LIKE ?
                    ORDER BY fetched_at DESC LIMIT ?
                """, (f"%{event_type}%", limit))
            else:
                cursor.execute("""
                    SELECT * FROM external_events
                    ORDER BY fetched_at DESC LIMIT ?
                """, (limit,))
            cols = [d[0] for d in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_ingestion_status(self, limit: int = 20) -> List[Dict]:
        """Return most recent fetch-log entries per source."""
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT * FROM source_fetch_log
                ORDER BY fetch_completed_at DESC LIMIT ?
            """, (limit,))
            cols = [d[0] for d in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]
        finally:
            conn.close()

    # ----------------------------
    # GNEWS ARTICLES HELPERS
    # ----------------------------

    def upsert_gnews_article(self, data: Dict[str, Any]) -> bool:
        """Insert or update a single GNews article (deduped by article_url)."""
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO gnews_articles
                (article_url, title, description, source_name, source_url,
                 image_url, published_at, severity, region, fetched_at)
                VALUES (?,?,?,?,?,?,?,?,?, datetime('now'))
                ON CONFLICT(article_url) DO UPDATE SET
                    title=excluded.title,
                    description=excluded.description,
                    source_name=excluded.source_name,
                    source_url=excluded.source_url,
                    image_url=excluded.image_url,
                    published_at=excluded.published_at,
                    severity=excluded.severity,
                    region=excluded.region,
                    fetched_at=datetime('now')
            """, (
                data.get("url") or data.get("article_url"),
                data.get("title"),
                data.get("description"),
                data.get("source_name") or data.get("source"),
                data.get("source_url"),
                data.get("image_url") or data.get("image"),
                data.get("published_at"),
                data.get("severity"),
                data.get("region"),
            ))
            conn.commit()
            return True
        except Exception as e:
            logger.error("upsert_gnews_article error: %s", e)
            conn.rollback()
            return False
        finally:
            conn.close()

    def upsert_gnews_articles_bulk(self, articles: List[Dict[str, Any]]) -> int:
        """Bulk upsert GNews articles. Returns count of successfully upserted rows."""
        conn = self.connect()
        cursor = conn.cursor()
        count = 0
        try:
            for data in articles:
                url = data.get("url") or data.get("article_url")
                if not url:
                    continue
                cursor.execute("""
                    INSERT INTO gnews_articles
                    (article_url, title, description, source_name, source_url,
                     image_url, published_at, severity, region, fetched_at)
                    VALUES (?,?,?,?,?,?,?,?,?, datetime('now'))
                    ON CONFLICT(article_url) DO UPDATE SET
                        title=excluded.title,
                        description=excluded.description,
                        source_name=excluded.source_name,
                        source_url=excluded.source_url,
                        image_url=excluded.image_url,
                        published_at=excluded.published_at,
                        severity=excluded.severity,
                        region=excluded.region,
                        fetched_at=datetime('now')
                """, (
                    url,
                    data.get("title"),
                    data.get("description"),
                    data.get("source_name") or data.get("source"),
                    data.get("source_url"),
                    data.get("image_url") or data.get("image"),
                    data.get("published_at"),
                    data.get("severity"),
                    data.get("region"),
                ))
                count += 1
            conn.commit()
            return count
        except Exception as e:
            logger.error("upsert_gnews_articles_bulk error: %s", e)
            conn.rollback()
            return count
        finally:
            conn.close()

    def get_latest_gnews_articles(self, limit: int = 50,
                                  region: str = None) -> List[Dict]:
        """Get latest stored GNews articles, optionally filtered by region."""
        conn = self.connect()
        cursor = conn.cursor()
        try:
            if region:
                cursor.execute("""
                    SELECT * FROM gnews_articles
                    WHERE region = ?
                    ORDER BY published_at DESC LIMIT ?
                """, (region, limit))
            else:
                cursor.execute("""
                    SELECT * FROM gnews_articles
                    ORDER BY published_at DESC LIMIT ?
                """, (limit,))
            cols = [d[0] for d in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]
        finally:
            conn.close()

    def search_gnews_articles(self, keyword: str, limit: int = 20) -> List[Dict]:
        """Search stored GNews articles by keyword in title and description."""
        conn = self.connect()
        cursor = conn.cursor()
        try:
            pattern = f"%{keyword}%"
            cursor.execute("""
                SELECT * FROM gnews_articles
                WHERE title LIKE ? OR description LIKE ?
                ORDER BY published_at DESC LIMIT ?
            """, (pattern, pattern, limit))
            cols = [d[0] for d in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]
        finally:
            conn.close()

    # ----------------------------
    # QUERY
    # ----------------------------
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)

            # For INSERT/UPDATE queries
            if cursor.description is None:
                conn.commit()
                return []

            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]

        except Exception as e:
            print(f"❌ Query error: {e}")
            return []
        finally:
            conn.close()


if __name__ == "__main__":
    db = DatabaseManager()
    print("Database initialized successfully!")

    results = db.execute_query("SELECT COUNT(*) as count FROM aircraft")
    print(f"Total aircraft records: {results[0]['count'] if results else 0}")