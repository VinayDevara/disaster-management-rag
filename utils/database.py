"""
Database Manager for ADS-B and Disaster Data
Handles SQLite operations with optimized schema for low-resource queries
"""
import sqlite3
import pandas as pd
from typing import List, Dict, Optional, Any
from pathlib import Path
from config.config import Config
import json
from datetime import datetime

class DatabaseManager:
    """
    SQLite Database Manager for disaster management system
    Optimized for edge devices with efficient indexing
    """
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or Config.SQLITE_DB_PATH
        self.conn = None
        self.initialize_database()
    
    def connect(self):
        """Establish database connection"""
        if not self.conn:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return self.conn
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def initialize_database(self):
        """Create tables with optimized schema matching EXACT Excel columns"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # ADS-B Aircraft Table (Updated with EXACT column names)
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
        
        # Create indexes for common queries (Updated to use new column names)
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
        
        # Disaster Events Table (from EONET)
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
        
        # Cross-Intelligence Correlations Table
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
        
        conn.commit()
        print("✅ Database initialized successfully")
    
    def load_adsb_data(self, excel_path: str):
        """
        Load ADS-B data from Excel file into database
        Keeps exact column names as requested.
        """
        conn = self.connect()
        
        try:
            # Read all sheets
            excel_file = pd.ExcelFile(excel_path)
            total_records = 0
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_path, sheet_name=sheet_name)
                
                # Add the _sheet column if it's missing in the dataframe
                if '_sheet' not in df.columns:
                    df['_sheet'] = sheet_name

                # Filter dataframe to only include valid columns that match our schema
                # This ensures we don't crash on weird extra Excel columns
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
                
                # Only keep columns that exist in the dataframe AND our schema
                cols_to_keep = [col for col in valid_columns if col in df.columns]
                df_final = df[cols_to_keep]

                # Insert data without renaming
                df_final.to_sql('aircraft', conn, if_exists='append', index=False)
                total_records += len(df)
                
                print(f"✅ Loaded {len(df)} records from sheet: {sheet_name}")
            
            conn.commit()
            print(f"✅ Total ADS-B records loaded: {total_records}")
            
        except Exception as e:
            print(f"❌ Error loading ADS-B data: {e}")
            conn.rollback()
    
    def insert_weather_event(self, event_data: Dict[str, Any]):
        """Insert weather event into database"""
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
        except Exception as e:
            print(f"❌ Error inserting weather event: {e}")
            conn.rollback()
    
    def insert_disaster_event(self, event_data: Dict[str, Any]):
        """Insert disaster event into database"""
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
        except Exception as e:
            print(f"❌ Error inserting disaster event: {e}")
            conn.rollback()
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """
        Execute SQL query and return results
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of result dictionaries
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute(query, params)
            columns = [description[0] for description in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
        except Exception as e:
            print(f"❌ Query error: {e}")
            return []
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


if __name__ == "__main__":
    # Test database initialization
    db = DatabaseManager()
    print("Database initialized successfully!")
    
    # Test query
    results = db.execute_query("SELECT COUNT(*) as count FROM aircraft")
    print(f"Total aircraft records: {results[0]['count'] if results else 0}")