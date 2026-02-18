# Comprehensive Technical Report: Disaster Management RAG System with Multi-File Excel Support

**Version:** 2.0  
**Date:** 2026-02-01  
**System:** Disaster Management RAG System with Multi-Agent Architecture

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Data Processing Pipeline](#2-data-processing-pipeline)
3. [Database Storage Architecture](#3-database-storage-architecture)
4. [Database Utilization](#4-database-utilization)
5. [Tools and Components](#5-tools-and-components)
6. [Detailed Data Flow](#6-detailed-data-flow)
7. [Code Structure and Architecture](#7-code-structure-and-architecture)
8. [Context Window Implementation](#8-context-window-implementation)
9. [Summary and Conclusions](#9-summary-and-conclusions)

---

## 1. Introduction

### 1.1 System Overview

The Disaster Management RAG (Retrieval-Augmented Generation) System is a sophisticated multi-agent platform designed to correlate and analyze disaster-related data from multiple sources:

- **ADS-B Flight Data**: Real-time aircraft tracking information
- **Weather Events**: Meteorological data from OpenWeather API
- **Disaster Events**: Natural disaster information from NASA EONET API
- **Vector-based Knowledge**: Embedded document storage for semantic search

### 1.2 System Architecture

The system employs a **multi-agent architecture** with specialized agents:

1. **Flight Agent**: Analyzes aircraft data and flight patterns
2. **Weather Agent**: Processes meteorological events and conditions
3. **Disaster Agent**: Tracks natural disasters and catastrophic events
4. **Consensus Agent**: Synthesizes insights from all agents
5. **Orchestrator Agent**: Coordinates agents and manages conversation flow

### 1.3 Key Features

- **Multi-File Excel Support**: Processes 5+ Excel files with multiple sheets
- **Temporal Data Management**: Handles data from September 2025 to January 2026
- **Duplicate Prevention**: Tracks loaded files to avoid redundant processing
- **Context-Aware Conversations**: 10-message context window for coherent interactions
- **Vector Embeddings**: Semantic search capabilities using ChromaDB
- **SQL Analytics**: Complex queries and aggregations on structured data

### 1.4 Technology Stack

```
Programming Language: Python 3.8+
Database Systems:
  - SQLite (Structured data)
  - ChromaDB (Vector embeddings)
LLM: Groq API (llama3-70b-8192)
Embedding Model: all-MiniLM-L6-v2
APIs:
  - OpenWeather API
  - NASA EONET API
Libraries:
  - pandas, openpyxl (Data processing)
  - sentence-transformers (Embeddings)
  - chromadb (Vector database)
  - groq (LLM client)
```

---

## 2. Data Processing Pipeline

### 2.1 Excel Data Ingestion

#### 2.1.1 File Discovery

The system discovers Excel files in the configured data directory:

```python
# In config.py
ADSB_DATA_PATHS = [
    "data/september_2025.xlsx",
    "data/october_2025.xlsx",
    "data/november_2025.xlsx",
    "data/december_2025.xlsx",
    "data/january_2026.xlsx"
]
```

#### 2.1.2 Month Extraction

The system extracts month/year from filenames using regex patterns:

```python
MONTH_PATTERNS = [
    r'(\w+)_(\d{4})',           # september_2025
    r'(\d{4})-(\d{2})',          # 2025-09
    r'(\d{4})_(\w+)',            # 2025_september
    r'(\w+)-(\d{4})',            # september-2025
]
```

**Extraction Logic:**
1. Try each regex pattern sequentially
2. Parse month name (e.g., "september") or number (e.g., "09")
3. Combine into standardized format: `YYYY-MM` (e.g., "2025-09")
4. Default to current year-month if extraction fails

#### 2.1.3 Sheet Processing

Each Excel file may contain multiple sheets representing different data sources or time periods:

```python
def load_adsb_data(excel_path: str):
    xls = pd.ExcelFile(excel_path)
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name)
        # Process each sheet
```

**Processing Steps:**
1. Open Excel file with `pd.ExcelFile()`
2. Iterate through all sheet names
3. Read each sheet into a DataFrame
4. Add metadata columns:
   - `_file_name`: Source filename
   - `_month`: Extracted month (YYYY-MM)
   - `_sheet`: Sheet name
5. Insert records into database

#### 2.1.4 Data Validation

Before insertion, the system validates:

- **Column Compatibility**: Ensures expected columns exist
- **Data Types**: Converts timestamps, numerics appropriately
- **Null Handling**: Manages missing values
- **Duplicate Detection**: Checks if file already loaded

### 2.2 API Data Ingestion

#### 2.2.1 Weather Data (OpenWeather API)

```python
# WeatherAPITool in api_tool.py
def get_weather_by_location(lat: float, lon: float):
    url = f"{OPENWEATHER_API_URL}/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric"
    }
    response = requests.get(url, params=params)
    return response.json()
```

**Data Points Collected:**
- Temperature, humidity, pressure
- Wind speed and direction
- Cloud coverage
- Precipitation
- Visibility

#### 2.2.2 Disaster Data (NASA EONET)

```python
# DisasterAPITool in api_tool.py
def get_disaster_events(category=None, days=30):
    url = EONET_API_URL
    params = {"days": days}
    if category:
        params["category"] = category
    response = requests.get(url, params=params)
    return response.json()
```

**Event Categories:**
- Wildfires
- Severe storms
- Floods
- Volcanoes
- Sea and lake ice
- Earthquakes

### 2.3 Data Transformation

#### 2.3.1 Normalization

The system normalizes data across sources:

```python
# Coordinate normalization
def normalize_coordinates(lat, lon):
    lat = float(lat) if lat is not None else None
    lon = float(lon) if lon is not None else None
    return lat, lon

# Timestamp standardization
def parse_timestamp(ts):
    if isinstance(ts, str):
        return datetime.fromisoformat(ts)
    elif isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts)
    return ts
```

#### 2.3.2 Enrichment

Data enrichment adds derived fields:

```python
# Aircraft data enrichment
df['speed_kmh'] = df['aircraft__gs'] * 1.852  # Convert knots to km/h
df['altitude_meters'] = df['aircraft__alt_baro'] * 0.3048  # Feet to meters
df['is_emergency'] = df['aircraft__emergency'].notna()
```

#### 2.3.3 Deduplication

The system prevents duplicate processing:

```python
def is_file_loaded(file_path: str) -> bool:
    query = """
    SELECT COUNT(*) as count 
    FROM data_loading_status 
    WHERE file_path = ? AND status = 'completed'
    """
    result = execute_query(query, (file_path,))
    return result[0]['count'] > 0
```

---

## 3. Database Storage Architecture

### 3.1 SQLite Database Schema

#### 3.1.1 Aircraft Table

Stores ADS-B flight tracking data:

```sql
CREATE TABLE IF NOT EXISTS aircraft (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Core ADS-B Fields (preserved column names)
    aircraft__hex TEXT,              -- ICAO 24-bit address
    aircraft__flight TEXT,           -- Callsign
    aircraft__alt_baro INTEGER,      -- Altitude (feet)
    aircraft__gs REAL,               -- Ground speed (knots)
    aircraft__track REAL,            -- Track angle (degrees)
    aircraft__lat REAL,              -- Latitude
    aircraft__lon REAL,              -- Longitude
    aircraft__category TEXT,         -- Aircraft category
    aircraft__emergency TEXT,        -- Emergency status
    aircraft__squawk TEXT,           -- Squawk code
    
    -- Temporal Fields
    now REAL,                        -- Timestamp (Unix epoch)
    messages INTEGER,                -- Message count
    seen REAL,                       -- Time since last message
    rssi REAL,                       -- Signal strength
    
    -- Metadata Fields (new in v2.0)
    _file_name TEXT,                 -- Source Excel filename
    _month TEXT,                     -- Month (YYYY-MM format)
    _sheet TEXT,                     -- Sheet name within Excel
    _loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Indexes for Performance:**

```sql
CREATE INDEX idx_aircraft_hex ON aircraft(aircraft__hex);
CREATE INDEX idx_aircraft_flight ON aircraft(aircraft__flight);
CREATE INDEX idx_aircraft_lat ON aircraft(aircraft__lat);
CREATE INDEX idx_aircraft_lon ON aircraft(aircraft__lon);
CREATE INDEX idx_aircraft_emergency ON aircraft(aircraft__emergency);
CREATE INDEX idx_aircraft_timestamp ON aircraft(now);
CREATE INDEX idx_aircraft_file ON aircraft(_file_name);
CREATE INDEX idx_aircraft_month ON aircraft(_month);
CREATE INDEX idx_aircraft_sheet ON aircraft(_sheet);
```

**Design Rationale:**
- Preserved original column names (`aircraft__*`) for compatibility
- Added metadata columns for tracking data provenance
- Indexes on high-cardinality columns for query optimization
- Composite indexes for common query patterns

#### 3.1.2 Weather Events Table

Stores meteorological event data:

```sql
CREATE TABLE IF NOT EXISTS weather_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE,            -- External API ID
    event_type TEXT NOT NULL,        -- Event category
    title TEXT,                      -- Event title/description
    location TEXT,                   -- Location name
    latitude REAL,
    longitude REAL,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    severity TEXT,                   -- Low, Medium, High, Critical
    description TEXT,
    temperature REAL,
    humidity REAL,
    wind_speed REAL,
    precipitation REAL,
    metadata TEXT,                   -- JSON blob for additional data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Indexes:**

```sql
CREATE INDEX idx_weather_type ON weather_events(event_type);
CREATE INDEX idx_weather_location ON weather_events(latitude, longitude);
CREATE INDEX idx_weather_time ON weather_events(start_time, end_time);
CREATE INDEX idx_weather_severity ON weather_events(severity);
```

#### 3.1.3 Disaster Events Table

Stores natural disaster information:

```sql
CREATE TABLE IF NOT EXISTS disaster_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE,            -- NASA EONET event ID
    title TEXT NOT NULL,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    categories TEXT,                 -- JSON array of categories
    sources TEXT,                    -- JSON array of data sources
    geometry TEXT,                   -- JSON for geometries (points, polygons)
    magnitude REAL,
    severity TEXT,
    description TEXT,
    metadata TEXT,                   -- JSON blob
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Indexes:**

```sql
CREATE INDEX idx_disaster_start ON disaster_events(start_date);
CREATE INDEX idx_disaster_categories ON disaster_events(categories);
CREATE INDEX idx_disaster_severity ON disaster_events(severity);
```

#### 3.1.4 Data Loading Status Table (New in v2.0)

Tracks which files have been loaded to prevent duplicates:

```sql
CREATE TABLE IF NOT EXISTS data_loading_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT UNIQUE NOT NULL,
    file_name TEXT,
    month_extracted TEXT,            -- YYYY-MM format
    record_count INTEGER,
    sheet_count INTEGER,
    status TEXT DEFAULT 'pending',   -- pending, loading, completed, failed
    error_message TEXT,
    loaded_at TIMESTAMP,
    duration_seconds REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Design Rationale:**
- Unique constraint on `file_path` prevents duplicate entries
- Status tracking enables recovery from failures
- Performance metrics (record_count, duration) for monitoring

#### 3.1.5 Correlations Table

Stores relationships between entities:

```sql
CREATE TABLE IF NOT EXISTS correlations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    correlation_type TEXT NOT NULL,  -- 'flight-weather', 'flight-disaster', etc.
    entity1_type TEXT,               -- 'aircraft', 'weather_event', 'disaster_event'
    entity1_id INTEGER,
    entity2_type TEXT,
    entity2_id INTEGER,
    correlation_score REAL,          -- 0.0 to 1.0
    reasoning TEXT,                  -- LLM-generated explanation
    metadata TEXT,                   -- JSON blob
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Indexes:**

```sql
CREATE INDEX idx_corr_type ON correlations(correlation_type);
CREATE INDEX idx_corr_entity1 ON correlations(entity1_type, entity1_id);
CREATE INDEX idx_corr_entity2 ON correlations(entity2_type, entity2_id);
CREATE INDEX idx_corr_score ON correlations(correlation_score);
```

### 3.2 Vector Database (ChromaDB)

#### 3.2.1 Collection Structure

The system uses ChromaDB for semantic search:

```python
class VectorDB:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
        self.collection = self.client.get_or_create_collection(
            name="disaster_docs",
            metadata={"description": "Disaster management documents"}
        )
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
```

#### 3.2.2 Document Storage

Documents are stored with embeddings:

```python
def add_documents(self, documents: List[str], metadatas: List[dict], ids: List[str]):
    """
    documents: List of text content
    metadatas: List of metadata dicts (source, type, timestamp)
    ids: Unique identifiers
    """
    embeddings = self.embedding_model.encode(documents).tolist()
    self.collection.add(
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
```

**Metadata Structure:**

```python
{
    "source": "EONET API",           # Data source
    "type": "disaster_event",        # Document type
    "event_id": "EONET_12345",       # External reference
    "timestamp": "2025-09-15T14:30:00Z",
    "category": "wildfire",
    "severity": "high",
    "location": "California, USA"
}
```

#### 3.2.3 Query and Retrieval

```python
def query(self, query_text: str, n_results: int = 5) -> dict:
    """Semantic search for relevant documents"""
    query_embedding = self.embedding_model.encode([query_text]).tolist()
    results = self.collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )
    return results
```

**Return Structure:**

```python
{
    "documents": [["doc1", "doc2", ...]],
    "metadatas": [[{...}, {...}, ...]],
    "distances": [[0.23, 0.45, ...]]  # Cosine distances
}
```

### 3.3 Data Persistence Strategy

#### 3.3.1 SQLite Persistence

- **File Location**: `data/disaster_rag.db`
- **Journal Mode**: WAL (Write-Ahead Logging) for concurrent reads
- **Synchronization**: FULL for data integrity
- **Auto-vacuum**: Enabled to manage file size

#### 3.3.2 ChromaDB Persistence

- **Directory**: `data/chromadb/`
- **Storage**: DuckDB backend (SQLite-like)
- **Indexes**: HNSW (Hierarchical Navigable Small World) for fast similarity search

#### 3.3.3 Backup Strategy

```python
def backup_databases():
    # SQLite backup
    shutil.copy("data/disaster_rag.db", f"backups/disaster_rag_{timestamp}.db")
    
    # ChromaDB backup
    shutil.copytree("data/chromadb", f"backups/chromadb_{timestamp}")
```

---

## 4. Database Utilization

### 4.1 Query Patterns

#### 4.1.1 Flight Queries

**By Callsign:**

```python
def get_flight_by_callsign(callsign: str):
    query = """
    SELECT * FROM aircraft 
    WHERE aircraft__flight = ? 
    ORDER BY now DESC 
    LIMIT 100
    """
    return execute_query(query, (callsign,))
```

**By Geographic Area:**

```python
def get_flights_in_area(min_lat, max_lat, min_lon, max_lon):
    query = """
    SELECT * FROM aircraft
    WHERE aircraft__lat BETWEEN ? AND ?
    AND aircraft__lon BETWEEN ? AND ?
    ORDER BY now DESC
    """
    return execute_query(query, (min_lat, max_lat, min_lon, max_lon))
```

**By Time Range (New in v2.0):**

```python
def get_flights_by_date_range(start_date: str, end_date: str):
    query = """
    SELECT * FROM aircraft
    WHERE _month BETWEEN ? AND ?
    ORDER BY now DESC
    """
    return execute_query(query, (start_date, end_date))
```

**By Month (New in v2.0):**

```python
def get_flights_by_month(month: str, limit: int = 1000):
    query = """
    SELECT * FROM aircraft
    WHERE _month = ?
    ORDER BY now DESC
    LIMIT ?
    """
    return execute_query(query, (month, limit))
```

#### 4.1.2 Aggregation Queries

**Monthly Statistics:**

```python
def get_monthly_flight_statistics():
    query = """
    SELECT 
        _month,
        COUNT(*) as total_flights,
        COUNT(DISTINCT aircraft__hex) as unique_aircraft,
        COUNT(DISTINCT aircraft__flight) as unique_callsigns,
        AVG(aircraft__alt_baro) as avg_altitude,
        AVG(aircraft__gs) as avg_speed,
        SUM(CASE WHEN aircraft__emergency IS NOT NULL THEN 1 ELSE 0 END) as emergency_count
    FROM aircraft
    WHERE _month IS NOT NULL
    GROUP BY _month
    ORDER BY _month
    """
    return execute_query(query)
```

**File Statistics:**

```python
def get_data_statistics():
    query = """
    SELECT 
        _file_name,
        _month,
        COUNT(*) as record_count,
        COUNT(DISTINCT _sheet) as sheet_count,
        MIN(now) as earliest_timestamp,
        MAX(now) as latest_timestamp
    FROM aircraft
    GROUP BY _file_name, _month
    ORDER BY _month, _file_name
    """
    return execute_query(query)
```

#### 4.1.3 Complex Joins

**Flight-Weather Correlation:**

```python
def correlate_flights_weather(time_window_minutes=30, distance_km=50):
    query = """
    SELECT 
        a.aircraft__flight,
        a.aircraft__lat,
        a.aircraft__lon,
        a.now as flight_time,
        w.event_type,
        w.title as weather_title,
        w.severity,
        w.start_time as weather_start,
        ABS(a.now - strftime('%s', w.start_time)) as time_diff_seconds,
        -- Haversine distance calculation
        (6371 * acos(
            cos(radians(a.aircraft__lat)) * cos(radians(w.latitude)) *
            cos(radians(w.longitude) - radians(a.aircraft__lon)) +
            sin(radians(a.aircraft__lat)) * sin(radians(w.latitude))
        )) as distance_km
    FROM aircraft a
    CROSS JOIN weather_events w
    WHERE ABS(a.now - strftime('%s', w.start_time)) < ? * 60
    AND (6371 * acos(
        cos(radians(a.aircraft__lat)) * cos(radians(w.latitude)) *
        cos(radians(w.longitude) - radians(a.aircraft__lon)) +
        sin(radians(a.aircraft__lat)) * sin(radians(w.latitude))
    )) < ?
    ORDER BY time_diff_seconds, distance_km
    """
    return execute_query(query, (time_window_minutes, distance_km))
```

### 4.2 Agent-Database Integration

#### 4.2.1 Flight Agent Queries

The Flight Agent uses SQL tools to analyze aircraft data:

```python
class FlightAgent:
    def analyze_flights(self, query: str):
        # Parse natural language query
        intent = self.parse_intent(query)
        
        if intent == "emergency":
            flights = self.sql_tool.get_emergency_flights()
        elif intent == "area":
            coords = self.extract_coordinates(query)
            flights = self.sql_tool.get_flights_in_area(*coords)
        elif intent == "trajectory":
            callsign = self.extract_callsign(query)
            flights = self.sql_tool.get_flight_trajectory(callsign)
        
        # Generate analysis with LLM
        return self.llm_client.generate_response(
            f"Analyze these flights: {flights}"
        )
```

#### 4.2.2 Weather Agent Queries

The Weather Agent combines API and database queries:

```python
class WeatherAgent:
    def get_weather_context(self, lat: float, lon: float):
        # Real-time API data
        current = self.api_tool.get_weather_by_location(lat, lon)
        
        # Historical database data
        historical = self.sql_tool.get_weather_events_in_area(
            lat - 1, lat + 1, lon - 1, lon + 1
        )
        
        return {
            "current": current,
            "historical": historical
        }
```

#### 4.2.3 Vector Search Integration

Agents use vector search for semantic queries:

```python
class DisasterAgent:
    def find_similar_events(self, description: str):
        # Vector search
        similar_docs = self.vector_db.query(description, n_results=5)
        
        # Extract event IDs
        event_ids = [m['event_id'] for m in similar_docs['metadatas'][0]]
        
        # Fetch full details from SQL
        events = self.sql_tool.get_disaster_events_by_ids(event_ids)
        
        return events
```

### 4.3 Transaction Management

#### 4.3.1 Atomic Operations

Critical operations use transactions:

```python
def load_adsb_data(excel_path: str):
    conn = sqlite3.connect(SQLITE_DB_PATH)
    try:
        conn.execute("BEGIN TRANSACTION")
        
        # Mark file as loading
        conn.execute(
            "INSERT INTO data_loading_status (file_path, status) VALUES (?, 'loading')",
            (excel_path,)
        )
        
        # Load data (may take minutes)
        for sheet in sheets:
            records = process_sheet(sheet)
            conn.executemany("INSERT INTO aircraft (...) VALUES (...)", records)
        
        # Mark as completed
        conn.execute(
            "UPDATE data_loading_status SET status='completed' WHERE file_path=?",
            (excel_path,)
        )
        
        conn.execute("COMMIT")
    except Exception as e:
        conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()
```

#### 4.3.2 Connection Pooling

The system uses thread-safe connection management:

```python
class DatabaseManager:
    def __init__(self):
        self.db_path = SQLITE_DB_PATH
        self._local = threading.local()  # Thread-local storage
    
    def get_connection(self):
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False
            )
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn
```

---

## 5. Tools and Components

### 5.1 SQL Tools

#### 5.1.1 SQLTool Class

Provides high-level query methods:

```python
class SQLTool:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    # Core methods
    def get_all_flights(self, limit=1000): ...
    def get_flight_by_callsign(self, callsign): ...
    def get_flights_in_area(self, min_lat, max_lat, min_lon, max_lon): ...
    def get_emergency_flights(self): ...
    def get_flights_by_altitude_range(self, min_alt, max_alt): ...
    
    # New in v2.0
    def get_flights_by_month(self, month, limit=1000): ...
    def get_flights_by_date_range(self, start_date, end_date): ...
    def get_monthly_flight_statistics(self): ...
    def get_file_loading_history(self): ...
```

#### 5.1.2 WeatherSQLTool Class

```python
class WeatherSQLTool:
    def get_weather_events_by_type(self, event_type): ...
    def get_weather_events_in_area(self, min_lat, max_lat, min_lon, max_lon): ...
    def get_active_weather_events(self): ...
    def get_severe_weather_events(self, min_severity='High'): ...
```

#### 5.1.3 DisasterSQLTool Class

```python
class DisasterSQLTool:
    def get_disaster_events_by_type(self, event_type): ...
    def get_disaster_events_in_area(self, min_lat, max_lat, min_lon, max_lon): ...
    def get_recent_disasters(self, days=30): ...
    def get_high_severity_disasters(self, min_severity='High'): ...
```

### 5.2 API Tools

#### 5.2.1 WeatherAPITool Class

```python
class WeatherAPITool:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5"
    
    def get_weather_by_location(self, lat: float, lon: float): ...
    def get_weather_forecast(self, lat: float, lon: float, days: int = 5): ...
    def get_weather_alerts(self, lat: float, lon: float): ...
```

#### 5.2.2 DisasterAPITool Class

```python
class DisasterAPITool:
    def __init__(self, api_key: str = "DEMO_KEY"):
        self.api_key = api_key
        self.base_url = "https://eonet.gsfc.nasa.gov/api/v3/events"
    
    def get_disaster_events(self, category=None, days=30): ...
    def get_event_by_id(self, event_id: str): ...
    def get_events_by_category(self, category: str): ...
```

### 5.3 LLM Client

#### 5.3.1 LLMClient Class

```python
class LLMClient:
    def __init__(self, api_key: str, model: str = "llama3-70b-8192"):
        self.client = Groq(api_key=api_key)
        self.model = model
    
    def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 8000
    ) -> str:
        """Generate LLM response with conversation history"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
```

#### 5.3.2 Message Formatting

The LLM client handles message formatting for the Groq API:

```python
def format_messages(system_prompt: str, user_query: str, history: List[dict] = None):
    messages = [{"role": "system", "content": system_prompt}]
    
    if history:
        messages.extend(history)
    
    messages.append({"role": "user", "content": user_query})
    
    return messages
```

### 5.4 Vector Database Client

#### 5.4.1 VectorDB Class

```python
class VectorDB:
    def __init__(self, persist_directory: str = "data/chromadb"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection("disaster_docs")
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    
    def add_documents(self, documents, metadatas, ids): ...
    def query(self, query_text, n_results=5): ...
    def delete_documents(self, ids): ...
    def update_documents(self, ids, documents, metadatas): ...
```

### 5.5 Data Loader

#### 5.5.1 Standalone Data Loader Script

```python
class DataLoader:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def load_all_excel_files(self):
        """Load all configured Excel files"""
        for file_path in Config.ADSB_DATA_PATHS:
            if not self.db.is_file_loaded(file_path):
                print(f"Loading {file_path}...")
                self.db.load_adsb_data(file_path)
            else:
                print(f"Skipping {file_path} (already loaded)")
    
    def reload_file(self, file_path: str):
        """Force reload a specific file"""
        self.db.clear_file_data(file_path)
        self.db.load_adsb_data(file_path)
```

**Usage:**

```bash
python data_loader.py --load-all
python data_loader.py --reload data/september_2025.xlsx
python data_loader.py --stats
```

---

## 6. Detailed Data Flow

### 6.1 System Initialization Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    SYSTEM STARTUP                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  1. Load Configuration (config.py)                          │
│     - Read .env file                                        │
│     - Validate API keys                                     │
│     - Set paths and parameters                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Initialize Databases                                    │
│     ├─ SQLite: Create tables and indexes                   │
│     └─ ChromaDB: Initialize collection                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Load Data (if not already loaded)                       │
│     - Check data_loading_status table                       │
│     - Load Excel files sequentially                         │
│     - Update loading status                                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Initialize Agents                                       │
│     ├─ Flight Agent                                         │
│     ├─ Weather Agent                                        │
│     ├─ Disaster Agent                                       │
│     ├─ Consensus Agent                                      │
│     └─ Orchestrator Agent (with context window)            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  5. Ready for Queries                                       │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Data Loading Flow

```
┌─────────────────────────────────────────────────────────────┐
│         EXCEL FILE DATA LOADING PIPELINE                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  1. File Discovery                                          │
│     - Scan Config.ADSB_DATA_PATHS                          │
│     - Check file existence                                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Duplicate Check                                         │
│     - Query data_loading_status table                       │
│     - If loaded and status='completed', skip                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Extract Month from Filename                             │
│     - Apply regex patterns                                  │
│     - Parse month name/number                               │
│     - Format as YYYY-MM                                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Open Excel File                                         │
│     - pd.ExcelFile(file_path)                              │
│     - Get all sheet names                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  5. Process Each Sheet (Loop)                               │
│     ┌──────────────────────────────────────────┐           │
│     │  a. Read sheet to DataFrame              │           │
│     │  b. Add metadata columns:                │           │
│     │     - _file_name                         │           │
│     │     - _month                             │           │
│     │     - _sheet                             │           │
│     │  c. Validate data types                  │           │
│     │  d. Handle missing values                │           │
│     │  e. Convert DataFrame to records         │           │
│     │  f. Batch insert to database (1000/batch)│           │
│     └──────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  6. Update Loading Status                                   │
│     - Record count                                          │
│     - Sheet count                                           │
│     - Duration                                              │
│     - Status = 'completed'                                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  7. Commit Transaction                                      │
└─────────────────────────────────────────────────────────────┘
```

### 6.3 Query Processing Flow

```
┌─────────────────────────────────────────────────────────────┐
│               USER QUERY PROCESSING FLOW                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  1. User Input                                              │
│     - Natural language query                                │
│     - "Show flights near Los Angeles in September 2025"     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Orchestrator Agent Receives Query                       │
│     - Retrieve 10-message context window                    │
│     - Add current query to context                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Intent Classification (LLM)                             │
│     - Determine relevant domain(s):                         │
│       ├─ Flight data                                        │
│       ├─ Weather data                                       │
│       ├─ Disaster data                                      │
│       └─ Combination                                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Agent Routing                                           │
│     - Route to appropriate specialist agent(s)              │
└─────────────────────────────────────────────────────────────┘
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │Flight Agent │  │Weather Agent│  │Disaster Agent│
    └─────────────┘  └─────────────┘  └─────────────┘
              │               │               │
              ▼               ▼               ▼
    ┌─────────────────────────────────────────────────┐
    │  5. Agent Processing (Parallel)                 │
    │                                                  │
    │  Flight Agent:                                  │
    │  ├─ Parse query parameters                      │
    │  ├─ Extract: location, date range, filters      │
    │  ├─ Call SQL tool methods                       │
    │  └─ Format results                              │
    │                                                  │
    │  Weather Agent:                                 │
    │  ├─ Check for location coordinates              │
    │  ├─ Query API for current weather               │
    │  ├─ Query DB for historical events              │
    │  └─ Correlate with time range                   │
    │                                                  │
    │  Disaster Agent:                                │
    │  ├─ Search vector DB for semantic match         │
    │  ├─ Query SQL DB for structured data            │
    │  └─ Rank by relevance                           │
    └─────────────────────────────────────────────────┘
              │               │               │
              └───────────────┼───────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  6. Collect Agent Results                                   │
│     - Flight data: 1,234 flights in area, 3 emergencies     │
│     - Weather data: 2 severe storms in Sep 2025             │
│     - Disaster data: 1 wildfire nearby                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  7. Consensus Agent Synthesis                               │
│     - Combine all agent outputs                             │
│     - Identify correlations                                 │
│     - Generate coherent narrative                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  8. Orchestrator Final Response                             │
│     - Format response with context                          │
│     - Store in 10-message window                            │
│     - Return to user                                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  9. User Response                                           │
│     - Rendered output with data, charts, insights           │
└─────────────────────────────────────────────────────────────┘
```

### 6.4 Context Window Management Flow

```
┌─────────────────────────────────────────────────────────────┐
│           10-MESSAGE CONTEXT WINDOW FLOW                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  New Query Arrives                                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  1. Retrieve Context Window (deque)                         │
│     - Check current size                                    │
│     - Max size: 10 messages                                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Check Window Size                                       │
│     ├─ If size < 10: Append new message                     │
│     └─ If size = 10: Remove oldest, append new              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Format Messages for LLM                                 │
│     [                                                       │
│       {"role": "system", "content": "..."},                │
│       {"role": "user", "content": "Query 1"},              │
│       {"role": "assistant", "content": "Response 1"},      │
│       ...                                                   │
│       {"role": "user", "content": "Current query"}         │
│     ]                                                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Send to LLM with Context                                │
│     - Full conversation history                             │
│     - System prompt with instructions                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  5. Receive LLM Response                                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  6. Store Response in Context Window                        │
│     - Append as assistant message                           │
│     - Update timestamp                                      │
│     - Apply eviction if size > 10                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  7. Optional: Persist to Disk                               │
│     - Save to JSON file (conversation_history.json)         │
│     - Enable session recovery                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Code Structure and Architecture

### 7.1 Directory Structure

```
disaster_rag_system/
│
├── config/
│   └── config.py                    # Configuration management
│
├── data/
│   ├── september_2025.xlsx          # Excel data files
│   ├── october_2025.xlsx
│   ├── november_2025.xlsx
│   ├── december_2025.xlsx
│   ├── january_2026.xlsx
│   ├── disaster_rag.db              # SQLite database
│   └── chromadb/                    # Vector database directory
│
├── utils/
│   ├── database.py                  # DatabaseManager class
│   ├── vector_db.py                 # VectorDB class
│   └── llm_client.py                # LLMClient class
│
├── tools/
│   ├── sql_tool.py                  # SQL query tools
│   └── api_tool.py                  # API client tools
│
├── agents/
│   ├── flight_agent.py              # Flight analysis agent
│   ├── weather_agent.py             # Weather analysis agent
│   ├── disaster_agent.py            # Disaster analysis agent
│   ├── consensus_agent.py           # Consensus synthesis agent
│   └── orchestrator_agent.py        # Main orchestrator (with context window)
│
├── scripts/
│   └── data_loader.py               # Standalone data loading script
│
├── docs/
│   ├── IMPLEMENTATION_GUIDE.md
│   ├── QUICK_START.md
│   └── API_REFERENCE.md
│
├── tests/
│   ├── test_database.py
│   ├── test_agents.py
│   └── test_context_window.py
│
├── main.py                          # Application entry point
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variables template
└── README.md                        # Project documentation
```

### 7.2 Class Hierarchy

```
┌────────────────────────────────────────────────────────────┐
│                    Core Components                          │
└────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐      ┌──────────────┐
│DatabaseManager│   │   VectorDB   │      │  LLMClient   │
└──────────────┘    └──────────────┘      └──────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌────────────────────────────────────────────────────────────┐
│                        Tools Layer                          │
├────────────────────────────────────────────────────────────┤
│  SQLTool, WeatherSQLTool, DisasterSQLTool                  │
│  WeatherAPITool, DisasterAPITool                           │
└────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────┐
│                      Agents Layer                           │
├────────────────────────────────────────────────────────────┤
│  BaseAgent (Abstract)                                       │
│    ├─ FlightAgent                                          │
│    ├─ WeatherAgent                                         │
│    ├─ DisasterAgent                                        │
│    └─ ConsensusAgent                                       │
└────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────┐
│                  Orchestrator Agent                         │
│  (Coordinates all agents + Context Window Management)       │
└────────────────────────────────────────────────────────────┘
```

### 7.3 Component Interaction Diagram

```
┌───────────────────────────────────────────────────────────────┐
│                          USER                                 │
└───────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌───────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR AGENT                         │
│  ┌─────────────────────────────────────────────────────┐     │
│  │           10-Message Context Window                  │     │
│  │  [Q1, A1, Q2, A2, ..., Q10, A10]                    │     │
│  └─────────────────────────────────────────────────────┘     │
└───────────────────────────────────────────────────────────────┘
       │                 │                 │                 │
       ▼                 ▼                 ▼                 ▼
┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐
│   Flight   │   │  Weather   │   │  Disaster  │   │ Consensus  │
│   Agent    │   │   Agent    │   │   Agent    │   │   Agent    │
└────────────┘   └────────────┘   └────────────┘   └────────────┘
       │                 │                 │                 │
       ▼                 ▼                 ▼                 ▼
┌───────────────────────────────────────────────────────────────┐
│                      TOOLS LAYER                              │
├───────────────────────────────────────────────────────────────┤
│  SQLTool  │  WeatherSQLTool  │  DisasterSQLTool  │  API Tools │
└───────────────────────────────────────────────────────────────┘
       │                 │                 │                 │
       └─────────────────┴─────────────────┴─────────────────┘
                               │
                               ▼
┌───────────────────────────────────────────────────────────────┐
│                       DATA LAYER                              │
├───────────────────────────────────────────────────────────────┤
│  SQLite Database  │  ChromaDB  │  External APIs               │
│  (aircraft,       │  (vector   │  (OpenWeather,               │
│   weather_events, │   search)  │   NASA EONET)                │
│   disaster_events)│            │                              │
└───────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌───────────────────────────────────────────────────────────────┐
│                    RAW DATA SOURCES                           │
├───────────────────────────────────────────────────────────────┤
│  Excel Files (Sept-Jan 2025-2026)  │  Real-time APIs          │
└───────────────────────────────────────────────────────────────┘
```

### 7.4 Sequence Diagram: Query with Context

```
User      Orchestrator    Context Window    LLM Client    Flight Agent    SQLTool    Database
 │             │                │               │              │            │           │
 │ Query       │                │               │              │            │           │
 ├────────────>│                │               │              │            │           │
 │             │ Get History    │               │              │            │           │
 │             ├───────────────>│               │              │            │           │
 │             │<───────────────┤               │              │            │           │
 │             │ [Q1-Q9, A1-A9] │               │              │            │           │
 │             │                │               │              │            │           │
 │             │ Add Q10        │               │              │            │           │
 │             ├───────────────>│               │              │            │           │
 │             │                │               │              │            │           │
 │             │ Classify Intent│               │              │            │           │
 │             ├────────────────┼──────────────>│              │            │           │
 │             │                │               │              │            │           │
 │             │ Route to Agent │               │              │            │           │
 │             ├────────────────┼───────────────┼─────────────>│            │           │
 │             │                │               │              │            │           │
 │             │                │               │              │ SQL Query  │           │
 │             │                │               │              ├───────────>│           │
 │             │                │               │              │            │ Execute   │
 │             │                │               │              │            ├──────────>│
 │             │                │               │              │            │<──────────┤
 │             │                │               │              │<───────────┤           │
 │             │                │               │              │            │           │
 │             │                │               │              │ Format     │           │
 │             │                │               │              ├───────────>│           │
 │             │<───────────────┼───────────────┼──────────────┤            │           │
 │             │                │               │              │            │           │
 │             │ Generate Response              │              │            │           │
 │             ├────────────────┼──────────────>│              │            │           │
 │             │<───────────────┼───────────────┤              │            │           │
 │             │                │               │              │            │           │
 │             │ Store A10      │               │              │            │           │
 │             ├───────────────>│               │              │            │           │
 │             │                │               │              │            │           │
 │<────────────┤                │               │              │            │           │
 │  Response   │                │               │              │            │           │
```

---

## 8. Context Window Implementation

### 8.1 Design Overview

The **10-message context window** is a critical feature that enables the system to maintain conversational coherence across multiple queries. It stores the most recent 5 question-answer pairs (10 messages total) to provide context for subsequent LLM calls.

### 8.2 Implementation Design

#### 8.2.1 Data Structure

We use Python's `collections.deque` with a maximum length of 10:

```python
from collections import deque
from typing import Dict, List
from datetime import datetime
import threading
import json

class ContextWindow:
    def __init__(self, max_size: int = 10, persist_path: str = None):
        """
        Initialize context window with maximum size.
        
        Args:
            max_size: Maximum number of messages to store (default 10)
            persist_path: Optional path to persist conversation history
        """
        self.max_size = max_size
        self.messages = deque(maxlen=max_size)
        self.persist_path = persist_path
        self.lock = threading.Lock()  # Thread-safety
        
        # Load persisted history if available
        if persist_path:
            self._load_from_disk()
    
    def add_message(self, role: str, content: str, metadata: dict = None):
        """
        Add a message to the context window.
        
        Args:
            role: 'user' or 'assistant'
            content: Message content
            metadata: Optional metadata (timestamp, tokens, etc.)
        """
        with self.lock:
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            self.messages.append(message)
            
            # Persist to disk if configured
            if self.persist_path:
                self._save_to_disk()
    
    def get_messages(self, include_system: bool = True) -> List[Dict]:
        """
        Get all messages formatted for LLM.
        
        Args:
            include_system: Whether to include system prompt
        
        Returns:
            List of message dictionaries
        """
        with self.lock:
            messages = list(self.messages)
            
            if include_system:
                system_prompt = {
                    "role": "system",
                    "content": self._get_system_prompt()
                }
                messages.insert(0, system_prompt)
            
            return messages
    
    def clear(self):
        """Clear all messages from context window."""
        with self.lock:
            self.messages.clear()
            if self.persist_path:
                self._save_to_disk()
    
    def get_summary(self) -> Dict:
        """Get summary statistics of context window."""
        with self.lock:
            return {
                "message_count": len(self.messages),
                "max_size": self.max_size,
                "oldest_message": self.messages[0]["timestamp"] if self.messages else None,
                "newest_message": self.messages[-1]["timestamp"] if self.messages else None,
                "user_messages": sum(1 for m in self.messages if m["role"] == "user"),
                "assistant_messages": sum(1 for m in self.messages if m["role"] == "assistant")
            }
    
    def _get_system_prompt(self) -> str:
        """Generate system prompt with instructions."""
        return """You are an intelligent assistant for a disaster management system.
        You have access to flight data, weather information, and disaster events.
        Provide accurate, contextual responses based on the conversation history."""
    
    def _save_to_disk(self):
        """Persist conversation to disk."""
        if not self.persist_path:
            return
        
        try:
            with open(self.persist_path, 'w') as f:
                json.dump(list(self.messages), f, indent=2)
        except Exception as e:
            print(f"Error saving context to disk: {e}")
    
    def _load_from_disk(self):
        """Load persisted conversation from disk."""
        if not self.persist_path:
            return
        
        try:
            with open(self.persist_path, 'r') as f:
                messages = json.load(f)
                self.messages.extend(messages[-self.max_size:])
        except FileNotFoundError:
            pass  # No existing history
        except Exception as e:
            print(f"Error loading context from disk: {e}")
```

#### 8.2.2 Integration with Orchestrator Agent

Update `orchestrator_agent.py`:

```python
from utils.context_window import ContextWindow

class OrchestratorAgent:
    def __init__(self, config, db_manager, vector_db, llm_client):
        self.config = config
        self.db_manager = db_manager
        self.vector_db = vector_db
        self.llm_client = llm_client
        
        # Initialize context window
        self.context_window = ContextWindow(
            max_size=10,
            persist_path="data/conversation_history.json"
        )
        
        # Initialize specialist agents
        self.flight_agent = FlightAgent(db_manager, llm_client)
        self.weather_agent = WeatherAgent(db_manager, llm_client)
        self.disaster_agent = DisasterAgent(db_manager, vector_db, llm_client)
        self.consensus_agent = ConsensusAgent(llm_client)
    
    def process_query(self, user_query: str) -> str:
        """
        Process user query with context awareness.
        
        Args:
            user_query: Natural language query from user
        
        Returns:
            Generated response with context
        """
        # Add user query to context
        self.context_window.add_message("user", user_query)
        
        # Get conversation history
        messages = self.context_window.get_messages(include_system=True)
        
        # Classify intent using LLM with context
        intent = self._classify_intent(messages)
        
        # Route to appropriate agents
        agent_results = self._route_to_agents(intent, user_query)
        
        # Synthesize response with consensus agent
        response = self.consensus_agent.synthesize(
            agent_results, 
            query=user_query,
            context=messages
        )
        
        # Add assistant response to context
        self.context_window.add_message("assistant", response)
        
        return response
    
    def _classify_intent(self, messages: List[Dict]) -> Dict:
        """
        Classify user intent with conversation context.
        
        Args:
            messages: Full conversation history
        
        Returns:
            Intent classification with confidence scores
        """
        classification_prompt = """
        Based on the conversation history, classify the user's current intent.
        Determine which domains are relevant:
        - flight: Aircraft tracking and flight data
        - weather: Meteorological events and conditions
        - disaster: Natural disasters and catastrophic events
        
        Return JSON format:
        {
            "primary_domain": "flight|weather|disaster|multi",
            "domains": ["flight", "weather", "disaster"],
            "confidence": 0.95,
            "requires_context": true
        }
        """
        
        # Add classification prompt
        messages_with_prompt = messages + [{
            "role": "user",
            "content": classification_prompt
        }]
        
        # Get LLM classification
        classification = self.llm_client.generate_response(
            messages_with_prompt,
            temperature=0.3  # Lower temperature for classification
        )
        
        return json.loads(classification)
    
    def _route_to_agents(self, intent: Dict, query: str) -> Dict:
        """
        Route query to relevant specialist agents.
        
        Args:
            intent: Classified intent with domains
            query: User query
        
        Returns:
            Dictionary of agent results
        """
        results = {}
        domains = intent.get("domains", [])
        
        # Execute agent queries in parallel (if multiple domains)
        if "flight" in domains:
            results["flight"] = self.flight_agent.analyze(query)
        
        if "weather" in domains:
            results["weather"] = self.weather_agent.analyze(query)
        
        if "disaster" in domains:
            results["disaster"] = self.disaster_agent.analyze(query)
        
        return results
    
    def get_context_summary(self) -> Dict:
        """Get summary of current context window."""
        return self.context_window.get_summary()
    
    def clear_context(self):
        """Clear conversation history."""
        self.context_window.clear()
```

#### 8.2.3 LLM Client Integration

Update `llm_client.py` to handle context:

```python
class LLMClient:
    def __init__(self, api_key: str, model: str = "llama3-70b-8192"):
        self.client = Groq(api_key=api_key)
        self.model = model
        self.default_temperature = 0.7
        self.default_max_tokens = 8000
    
    def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = None,
        max_tokens: int = None,
        stream: bool = False
    ) -> str:
        """
        Generate LLM response with conversation history.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream response
        
        Returns:
            Generated response text
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.default_temperature,
                max_tokens=max_tokens or self.default_max_tokens,
                stream=stream
            )
            
            if stream:
                return self._handle_stream(response)
            else:
                return response.choices[0].message.content
        
        except Exception as e:
            print(f"Error generating LLM response: {e}")
            return f"Error: {str(e)}"
    
    def _handle_stream(self, response):
        """Handle streaming response."""
        full_response = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                print(content, end="", flush=True)
        print()  # Newline after streaming
        return full_response
    
    def count_tokens(self, messages: List[Dict]) -> int:
        """
        Estimate token count for messages.
        
        Args:
            messages: List of message dictionaries
        
        Returns:
            Estimated token count
        """
        # Rough estimation: ~4 characters per token
        total_chars = sum(len(m.get("content", "")) for m in messages)
        return total_chars // 4
```

### 8.3 Key Design Decisions

#### 8.3.1 Window Size: 10 Messages

**Rationale:**
- 10 messages = 5 Q&A pairs
- Balances context depth with token limits
- Prevents context overflow in LLM (most models have 8K-32K token limits)
- Maintains recent conversation without excessive memory

**Alternative Considered:**
- Sliding window by tokens instead of message count
- Rejected because: harder to implement, less predictable, unnecessary complexity

#### 8.3.2 Eviction Policy: FIFO (First-In-First-Out)

**Rationale:**
- `deque(maxlen=10)` automatically removes oldest when full
- Simple, predictable behavior
- Most recent context is most relevant
- No need for complex scoring/ranking

**Alternative Considered:**
- Importance-based eviction (keep most relevant messages)
- Rejected because: requires semantic analysis, adds latency, marginal benefit

#### 8.3.3 Thread Safety

**Implementation:**
- `threading.Lock()` for concurrent access
- Protects `add_message`, `get_messages`, `clear` operations
- Necessary because multiple agents may query simultaneously

**Rationale:**
- Web servers are multi-threaded
- Prevents race conditions and data corruption
- Minimal performance overhead (<1ms per lock acquisition)

#### 8.3.4 Persistence Strategy

**Implementation:**
- Optional JSON file persistence (`conversation_history.json`)
- Saves on every message addition
- Loads on initialization

**Rationale:**
- Enables session recovery after crashes/restarts
- Useful for debugging and analysis
- Optional (can be disabled for ephemeral conversations)

**Alternatives Considered:**
- Database persistence (SQL/NoSQL)
  - Rejected: overkill for 10 messages, adds dependency
- No persistence
  - Rejected: loses context on restart, poor user experience

### 8.4 Integration Points

#### 8.4.1 Orchestrator Agent

**Entry Point:**

```python
def process_query(user_query: str) -> str:
    self.context_window.add_message("user", user_query)
    messages = self.context_window.get_messages()
    # ... process with context ...
    self.context_window.add_message("assistant", response)
    return response
```

**Exit Point:**
- After generating final response
- Store assistant message in context

#### 8.4.2 LLM Client

**Input:**
- Receives full message list including context

**Output:**
- Returns generated response
- No direct interaction with context window (separation of concerns)

#### 8.4.3 Specialist Agents

**Context Usage:**
- Agents receive context indirectly through orchestrator
- Can reference previous queries for continuity
- Example: "Show me more details" → agent retrieves previous query context

### 8.5 Example Usage

#### 8.5.1 Multi-Turn Conversation

```
User: "Show flights near Los Angeles in September 2025"
→ Context: [Q1]