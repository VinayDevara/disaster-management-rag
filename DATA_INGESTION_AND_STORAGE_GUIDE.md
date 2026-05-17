# DisasterRAG Data Ingestion and Storage Guide

This document explains the complete data flow in the current implementation:

1. Which data sources exist
2. What raw payloads look like
3. How each source is polled
4. How data is normalized and stored
5. How raw payload archival works
6. Which SQLite tables are used
7. When the vector database is used
8. Which API calls hit SQL only vs SQL + vector paths

---

## 1) End-to-End Data Pipeline

### Runtime ingestion path (background)

1. FastAPI startup calls scheduler start.
2. Scheduler creates one async polling loop per source.
3. Each ingestor fetches remote data using shared retry logic.
4. Raw response is written to disk under `data/raw_payloads/...` and logged in `raw_payload_store`.
5. Ingestor parses and normalizes payload fields.
6. DatabaseManager writes normalized rows using source-specific strategy (upsert/replace/append).
7. Fetch execution metadata is written to `source_fetch_log`.

### Query-time path (on-demand)

1. Client calls `/api/query`.
2. Orchestrator classifies and routes to flight/weather/disaster agents.
3. Agents call SQL tools, external APIs, and optionally vector-search tools.
4. Results are synthesized and returned.

---

## 2) Source Catalog

## Scheduled ingestion sources

| Source | Polling | Raw payload stored | Main table(s) | Write strategy |
|---|---:|---|---|---|
| Open-Meteo | every 30 min | yes | `forecast_signals_hot` | replace rolling window per location |
| SACHET / NDMA | every 10 min | yes | `official_alerts` | upsert on `(source_name, external_id)` |
| GDACS | every 15 min | yes | `external_events` | upsert on `(source_name, external_id)` |
| GPM IMERG | every 60 min | yes | `rainfall_observations` | append with dedupe (`INSERT OR IGNORE`) |
| NASA LHASA | every 6 h | yes when API path works | `landslide_snapshot_current` | replace source snapshot |
| IBTrACS | every 7 days | yes | `historical_cyclones` | append with dedupe (`INSERT OR IGNORE`) |

## On-demand sources (agent tool calls)

| Source | Trigger | Persisted automatically? | Notes |
|---|---|---|---|
| OpenWeatherMap | weather tool calls in `/api/query` | no (response returned to agent flow only) | used for live weather and forecast |
| NASA EONET | disaster tool calls in `/api/query` | no (unless manually inserted in loader path) | used for active events and category filters |
| ADS-B Excel files | manual data load flow | yes (`aircraft`) | primary flight structured store |

---

## 3) Polling and Scheduling Details

Scheduler launches loops for:

- Open-Meteo: `POLL_MINUTES_OPENMETEO * 60`
- SACHET: `POLL_MINUTES_SACHET * 60`
- GDACS: `POLL_MINUTES_GDACS * 60`
- GPM: `POLL_MINUTES_GPM * 60`
- LHASA: `POLL_HOURS_LHASA * 3600`
- IBTrACS: `POLL_DAYS_IBTRACS * 86400`
- Retention manager: `HOT_RETENTION_HOURS * 3600`

Execution behavior:

- Non-blocking async loops, source jobs run via `run_in_executor`.
- HTTP retries and backoff configured in `BaseIngestor`.
- Source fetch status and errors always logged to `source_fetch_log`.

---

## 4) Raw Payload Archival

Raw payload write flow:

1. Ingestor receives HTTP payload text.
2. `RawPayloadStore.save(...)` computes SHA-256 hash.
3. Payload is compressed (`.json.gz` by default) and written to:

`data/raw_payloads/{source_name}/{YYYY}/{MM}/{hash_prefix}_{timestamp}.json.gz`

4. A DB row is written to `raw_payload_store` with:

- `source_name`
- `payload_type`
- `payload_hash`
- `payload_json` (when JSON parse succeeds)
- `file_path`
- `fetched_at`

### Example raw_payload_store row

```json
{
  "id": 716,
  "source_name": "sachet",
  "payload_type": "json_feed",
  "payload_hash": "a707b9ecf9b3f6e5cc88ffa32d9cb279c166886abcd753ac2f7e99f2f642d41e",
  "file_path": ".../data/raw_payloads/sachet/2026/04/a707b9ecf9b3f6e5_20260422T221505.json.gz",
  "fetched_at": "2026-04-22T22:15:05.646066"
}
```

---

## 5) What Data Looks Like Per Source

Below are payload-level and normalized-storage examples.

## 5.1 Open-Meteo (scheduled)

### Raw payload top keys (observed)

```json
{
  "latitude": 12.9141,
  "longitude": 74.856,
  "timezone": "Asia/Kolkata",
  "hourly_units": {"time": "iso8601", "precipitation": "mm"},
  "hourly": {
    "time": ["2026-04-23T00:00", "..."],
    "precipitation": [0.0, 0.1],
    "precipitation_probability": [3, 8],
    "showers": [0.0, 0.0],
    "rain": [0.0, 0.1],
    "wind_gusts_10m": [15.5, 17.2],
    "weather_code": [2, 3],
    "cape": [3910.0, 4020.0],
    "cloud_cover": [90, 93]
  }
}
```

### Stored row example (`forecast_signals_hot`)

```json
{
  "source_name": "openmeteo",
  "location_name": "Udupi",
  "district": "Udupi",
  "forecast_time": "2026-04-23T00:00",
  "precipitation": 0.0,
  "precipitation_probability": 3.0,
  "wind_gusts_10m": 15.5,
  "weather_code": 2,
  "raw_payload_ref": 711,
  "fetched_at": "2026-04-22T22:04:58.931689"
}
```

## 5.2 SACHET / NDMA (scheduled)

### Raw payload item keys (observed)

```json
{
  "severity": "ALERT",
  "identifier": 1776875919515019,
  "effective_start_time": "Wed Apr 22 22:06:00 IST 2026",
  "effective_end_time": "Thu Apr 23 01:06:00 IST 2026",
  "disaster_type": "Thunderstorm with Lightning",
  "area_description": "Bidar,Kalaburagi,Vijayapura districts of Karnataka",
  "severity_level": "Likely",
  "warning_message": "...",
  "disseminated": "true"
}
```

### Stored row example (`official_alerts`)

```json
{
  "source_name": "sachet",
  "external_id": "1776875919515019",
  "alert_type": "Thunderstorm with Lightning",
  "severity": "WATCH",
  "urgency": "Likely",
  "certainty": "Likely",
  "state": "Karnataka",
  "latitude": 17.9500230109718,
  "longitude": 77.22535765623813,
  "onset": "2026-04-22T22:06:00",
  "expires": "2026-04-23T01:06:00",
  "status": "Actual",
  "raw_payload_ref": 652,
  "fetched_at": "2026-04-22T19:34:49.472684"
}
```

## 5.3 GDACS (scheduled)

### Raw payload top keys (observed)

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {"type": "Point", "coordinates": [163.8, -23.6]},
      "properties": {
        "eventid": "1001266",
        "name": "Tropical Cyclone TWENTYEIGHT-26",
        "alertlevel": "Green"
      }
    }
  ],
  "bbox": ["..."]
}
```

### Stored row example (`external_events`)

```json
{
  "source_name": "gdacs",
  "external_id": "1001266",
  "event_type": "cyclone",
  "title": "Tropical Cyclone TWENTYEIGHT-26",
  "severity": "Green",
  "country": "New Caledonia",
  "latitude": -23.6,
  "longitude": 163.8,
  "start_time": "2026-03-23T00:00:00",
  "end_time": "2026-03-24T00:00:00",
  "source_url": "https://www.gdacs.org/report.aspx?...",
  "raw_payload_ref": 714,
  "fetched_at": "2026-04-22T22:05:07.494250"
}
```

## 5.4 GPM IMERG (scheduled)

### Raw payload currently observed

Current latest payload file in this environment is HTML (not JSON), so parse yields no observations.

```text
<!DOCTYPE html> ...
```

### Expected normalized row shape (`rainfall_observations`)

```json
{
  "source_name": "gpm_imerg",
  "external_id": "granule_or_item_id",
  "location_name": "Mangalore-Udupi",
  "district": "Dakshina Kannada",
  "latitude": 12.9,
  "longitude": 74.8,
  "observation_time": "2026-04-22T20:30:00Z",
  "rainfall_mm": 7.8,
  "aggregation_window": "30min",
  "dataset_metadata": {"dataset": "GPM_3IMERGHH"},
  "raw_payload_ref": 123,
  "fetched_at": "2026-04-22T20:35:00"
}
```

## 5.5 NASA LHASA (scheduled)

### Source behavior

- Primary mode: ArcGIS nowcast query.
- Fallback mode: rainfall-derived risk estimate when NASA endpoint is unreachable.

In this environment, fallback rows exist and show the expected schema.

### Stored row example (`landslide_snapshot_current`)

```json
{
  "source_name": "lhasa",
  "region_name": "Mangalore-Udupi",
  "district": "Dakshina Kannada",
  "snapshot_time": "2026-04-22T20:13:01.953109",
  "latitude": 12.9141,
  "longitude": 74.856,
  "probability": 0.05,
  "risk_level": "low",
  "metadata": {
    "source": "rainfall_estimate",
    "total_precip_mm_24h": 4.4,
    "location": "Mangalore"
  },
  "raw_payload_ref": null,
  "fetched_at": "2026-04-22T20:13:01.953109"
}
```

## 5.6 IBTrACS (scheduled)

### Raw payload prefix (observed)

```text
SID,SEASON,NUMBER,BASIN,SUBBASIN,NAME,ISO_TIME,NATURE,LAT,LON,WMO_WIND,...
```

### Stored row example (`historical_cyclones`)

```json
{
  "source_name": "ibtracs",
  "storm_id": "2014202N22087",
  "basin": "NI",
  "category": "-5",
  "raw_payload_ref": 686,
  "created_at": "2026-04-22 20:12:11"
}
```

Note: current stored rows show many nulls in cyclone detail columns, indicating mapper-to-table field mismatch in the current code path.

## 5.7 ADS-B flight source (batch-loaded)

### Stored row example (`aircraft`)

```json
{
  "aircraft__hex": "485f84",
  "aircraft__flight": "KLM879",
  "aircraft__alt_baro": 35000,
  "aircraft__gs": 552.9,
  "aircraft__lat": 15.543699,
  "aircraft__lon": 72.739841,
  "aircraft__emergency": "none",
  "aircraft__squawk": 1645,
  "now": 1769020325.3
}
```

## 5.8 On-demand APIs (used in query-time tools)

### OpenWeather normalized response shape

```json
{
  "location": "Mangalore",
  "coordinates": {"lat": 12.91, "lon": 74.85},
  "temperature": 29.7,
  "humidity": 73,
  "wind_speed": 3.1,
  "weather": "Clouds",
  "description": "scattered clouds",
  "timestamp": 1769095200
}
```

### EONET normalized event shape

```json
{
  "event_id": "EONET_1234",
  "title": "Wildfire - Region X",
  "event_type": "wildfires",
  "lat": 11.23,
  "lon": 76.45,
  "start_date": "2026-04-20T00:00:00Z",
  "sources": ["https://..."]
}
```

---

## 6) SQLite Tables and Purpose

## Core domain tables

- `aircraft`: ADS-B flight snapshots
- `weather_events`: weather events
- `disaster_events`: disaster events
- `correlations`: cross-entity relationship scoring

## Ingestion and observability tables

- `source_fetch_log`: per-poll status, HTTP code, records processed, errors
- `raw_payload_store`: payload hash/path/JSON reference

## External-source normalized tables

- `official_alerts`: SACHET/NDMA warnings
- `forecast_signals_hot`: latest forecast window (hot storage)
- `forecast_signals_warm`: aged forecast rows (warm storage)
- `rainfall_observations`: GPM rainfall history
- `landslide_snapshot_current`: LHASA latest risk snapshot
- `external_events`: GDACS flood/cyclone events
- `historical_cyclones`: IBTrACS history

---

## 7) Storage Strategy by Source/Table

- SACHET -> `official_alerts`: upsert (latest by external ID)
- GDACS -> `external_events`: upsert (latest by external ID)
- Open-Meteo -> `forecast_signals_hot`: replace rolling location window
- GPM -> `rainfall_observations`: append, dedupe with unique key
- LHASA -> `landslide_snapshot_current`: replace current snapshot
- IBTrACS -> `historical_cyclones`: append, dedupe via `INSERT OR IGNORE`
- Fetch telemetry -> `source_fetch_log`: append-only logs
- Payload archive metadata -> `raw_payload_store`: append-only references

---

## 8) Retention and Lifecycle Policy

Current lifecycle:

HOT (< `HOT_RETENTION_HOURS`) -> WARM (up to `WARM_RETENTION_DAYS`) -> COLD archive files

Retention manager actions:

1. Move old hot forecasts to warm table.
2. Delete rows older than warm retention window from selected tables.
3. Export old warm forecast rows to compressed JSON in cold archive directory.

### How this is implemented in this codebase

The lifecycle is implemented by `RetentionManager` and is run by the ingestion scheduler.

- Scheduler registration: retention is scheduled as a periodic callable job.
- Trigger interval: every `HOT_RETENTION_HOURS * 3600` seconds.
- Startup hook: scheduler starts from FastAPI startup, so retention begins automatically when backend starts.

### HOT tier implementation

- Primary hot table: `forecast_signals_hot`.
- Movement function: `DatabaseManager.move_hot_forecasts_to_warm(...)`.
- Cutoff logic: rows where `forecast_time` is older than `now - HOT_RETENTION_HOURS` are moved.
- SQL pattern:
  - Insert matching rows from `forecast_signals_hot` into `forecast_signals_warm`.
  - Delete those moved rows from `forecast_signals_hot`.

### WARM tier implementation

Warm data currently has two different outcomes in the implementation:

1. Forecast warm table path:
   - Table: `forecast_signals_warm`.
   - This table is used as an intermediate tier before cold archival.

2. Non-forecast warm retention cleanup path:
   - Tables cleaned by age-based delete when older than `WARM_RETENTION_DAYS`:
     - `weather_events` (using `start_time`)
     - `external_events` (using `fetched_at`)
     - `rainfall_observations` (using `observation_time`)
   - These are deleted directly by `archive_old_records(...)` and are not currently exported to cold files.

### COLD tier implementation

- Export source: rows from `forecast_signals_warm` older than `WARM_RETENTION_DAYS`.
- File format: gzip-compressed JSON (`.json.gz`).
- Destination directory: `Config.COLD_ARCHIVE_DIR` (default under `data/archive`).
- File naming pattern: `warm_forecasts_YYYYMMDDTHHMMSS.json.gz`.
- After successful file write, exported rows are deleted from `forecast_signals_warm`.

### Lifecycle summary by table

| Table | Tier path | Current behavior |
|---|---|---|
| `forecast_signals_hot` | HOT -> WARM | moved by age cutoff |
| `forecast_signals_warm` | WARM -> COLD | archived to gzip JSON then deleted |
| `weather_events` | HOT/WARM logical | deleted when older than warm retention window |
| `external_events` | HOT/WARM logical | deleted when older than warm retention window |
| `rainfall_observations` | HOT/WARM logical | deleted when older than warm retention window |

### Important practical notes

1. Cold archival currently covers forecast warm rows only (`forecast_signals_warm`).
2. Raw payload files under `data/raw_payloads/...` are separate from this hot/warm/cold forecast lifecycle.
3. If scheduler is not running, automatic tier movement does not occur.
4. Time columns used for cutoff checks differ by table (`forecast_time`, `fetched_at`, `observation_time`, `start_time`).

### Do we really have Hot/Warm/Cold here? (direct answer)

Yes, but only fully for forecast data.

- Full 3-tier path exists for forecasts:
  - `forecast_signals_hot` -> `forecast_signals_warm` -> gzip files in cold archive dir
- Other ingestion tables do not currently implement full 3-tier archival-to-file:
  - `weather_events`, `external_events`, `rainfall_observations` are age-deleted when past warm retention cutoff.

So the architecture is "hybrid tiered":

1. Full HOT/WARM/COLD for forecast signals
2. HOT/WARM-like retention + delete for selected non-forecast tables

### Durations and intervals (current defaults)

- `HOT_RETENTION_HOURS`: default `24`
- `WARM_RETENTION_DAYS`: default `30`
- Retention job schedule interval: `HOT_RETENTION_HOURS * 3600` seconds
  - With defaults, this means once every 24 hours

### Exact function inventory for tiering

#### Scheduler wiring

1. `IngestionScheduler.start()`
  - registers retention by calling `_schedule_callable(RetentionManager(self.db), Config.HOT_RETENTION_HOURS * 3600)`
2. `IngestionScheduler._schedule_callable(obj, interval_seconds)`
3. `IngestionScheduler._poll_loop_callable(obj, interval)`
  - repeatedly executes `obj.run()` on interval

#### Retention lifecycle functions

1. `RetentionManager.run()`
  - orchestrates all retention steps
2. `RetentionManager._hot_to_warm_forecasts()`
  - calls `DatabaseManager.move_hot_forecasts_to_warm(...)`
3. `RetentionManager._archive_old_records()`
  - calls `DatabaseManager.archive_old_records(...)` for:
    - `forecast_signals_warm` by `forecast_time`
    - `weather_events` by `start_time`
    - `external_events` by `fetched_at`
    - `rainfall_observations` by `observation_time`
4. `RetentionManager._warm_to_cold()`
  - exports old `forecast_signals_warm` rows to gzip JSON
  - deletes exported rows from `forecast_signals_warm`

#### Database functions used by retention

1. `DatabaseManager.replace_forecast_window(source_name, location_name, rows)`
  - writes/refreshes HOT forecast rows
2. `DatabaseManager.move_hot_forecasts_to_warm(older_than_hours=None)`
  - SQL insert-select from HOT to WARM and delete from HOT
3. `DatabaseManager.archive_old_records(table, time_col, older_than_days)`
  - age-based delete helper for configured tables

### Tier-related table schemas (exact)

#### `forecast_signals_hot`

```sql
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
```

#### `forecast_signals_warm`

```sql
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
```

#### `weather_events` (deleted by warm cutoff)

```sql
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
```

#### `external_events` (deleted by warm cutoff)

```sql
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
```

#### `rainfall_observations` (deleted by warm cutoff)

```sql
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
```

### Cold archive artifact format

Cold archive is file-based (not a SQL table):

- Directory: `Config.COLD_ARCHIVE_DIR` (default `data/archive`)
- File name: `warm_forecasts_YYYYMMDDTHHMMSS.json.gz`
- Payload: JSON array of full rows exported from `forecast_signals_warm`

---

## 9) Vector Database Details

## Backend and model

- Store: Chroma persistent client
- Path: `data/chromadb`
- Embedding model: `all-MiniLM-L6-v2`
- Embedding size: 384

### Example generated embedding (first 8 values)

```json
[0.052233, 0.035882, 0.020844, 0.098957, 0.093044, 0.01616, 0.05688, 0.042095]
```

## Collections

- `flights`
- `weather`
- `disasters`
- `knowledge`

Observed collection counts in this environment:

```json
{"flights": 700, "weather": 0, "disasters": 149, "knowledge": 0}
```

---

## 10) When Vector Store Is Used, and Under Which API Calls

Vector DB is used primarily in query-time agent logic and fallback paths.

## API route mapping

- `/api/query`: can use vector store (via agent tools `vector_search_flights`, `vector_search_weather`, `vector_search_disasters`)
- `/api/alerts/latest`: SQL only
- `/api/forecast/latest`: SQL only
- `/api/rainfall/latest`: SQL only
- `/api/landslide/latest`: SQL only
- `/api/events/latest`: SQL only
- `/api/ingestion/status`: SQL only
- `/api/health`: no DB query

## Concrete query example where vector was used

From benchmark runs:

- Query: "What is the current temperature in Mangalore?"
- Tools called included: `vector_search_weather`
- Category: A

Another observed example:

- Query: "What is the capital of France?"
- Tools called included: `vector_search_flights`

This confirms vector tools are active in `/api/query` orchestration paths.

---

## 11) How Database Is Invoked

## Ingestion-time DB invocation

Ingestors call DatabaseManager methods such as:

- `upsert_official_alert`
- `replace_forecast_window`
- `append_rainfall_observation`
- `replace_landslide_snapshot`
- `upsert_external_event`
- `batch_insert_historical_cyclones`
- `store_raw_payload`
- `log_source_fetch`

## API-time DB invocation

Read endpoints call:

- `get_latest_alerts`
- `get_latest_forecasts`
- `get_latest_rainfall`
- `get_latest_landslide_snapshot`
- `get_latest_external_events`
- `get_ingestion_status`

## Agent tool DB invocation

Agents use SQL tool classes for domain-specific queries against SQLite, then LLM synthesizes outputs.

---

## 12) Practical Notes

1. Raw payload files are the source-of-truth forensic trace for each poll cycle.
2. `raw_payload_ref` links normalized rows back to their archived raw payload.
3. Vector search participates only in conversational query processing (`/api/query`), not in inspection endpoints.
4. If a source returns malformed or non-JSON payload (observed for some GPM payloads), rows may not populate target tables.

---

## 13) Quick Reference: Current Important Paths

- Scheduler and polling loops: `ingestion/scheduler.py`
- Source ingestors: `ingestion/sources/*.py`
- Shared fetch + retry: `ingestion/base.py`
- Raw payload writer: `utils/raw_payload_store.py`
- Retention lifecycle: `utils/retention.py`
- SQLite schema + writes: `utils/database.py`
- Vector embeddings + search: `utils/vector_db.py`
- Query orchestration: `agents/orchestrator_agent.py`
- API routes: `main.py`
