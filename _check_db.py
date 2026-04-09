"""Quick DB health check — shows row counts and sample data for all tables."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.database import DatabaseManager

db = DatabaseManager()

print("=" * 60)
print("  DisasterRAG — Database Status")
print("=" * 60)

rows = db.execute_query("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
total = 0
for r in rows:
    name = r["name"]
    cnt = db.execute_query(f"SELECT COUNT(*) as cnt FROM [{name}]")
    count = cnt[0]["cnt"] if cnt else 0
    total += count
    icon = "✅" if count > 0 else "⚠️"
    print(f"  {icon} {name:35s} {count:>8,}")

print(f"\n  {'Total rows':35s} {total:>8,}")
print("=" * 60)

# Show ingestion source summary
print("\n  Ingestion Source Log (last 10):")
logs = db.execute_query(
    "SELECT source_name, fetch_url, status, http_status, records_processed, error_message, fetch_completed_at "
    "FROM source_fetch_log ORDER BY fetch_completed_at DESC LIMIT 10"
)
if logs:
    for log in logs:
        src = log.get("source_name", "?")
        status = log.get("status", "?")
        records = log.get("records_processed", 0)
        err = log.get("error_message", "")
        ts = log.get("fetch_completed_at", "")
        err_short = (err[:50] + "..") if err and len(err) > 50 else (err or "")
        print(f"    [{ts}] {src:15s} {status:5s} records={records} {err_short}")
else:
    print("    (no fetch logs found)")

# Show vector DB collections if chromadb available
try:
    from utils.vector_db import VectorDatabase
    vdb = VectorDatabase()
    print("\n  Vector DB Collections:")
    for name in ["flights", "weather", "disasters", "documents"]:
        try:
            col = vdb.client.get_collection(name)
            print(f"    ✅ {name:20s} {col.count():>6,} docs")
        except Exception:
            print(f"    ⚠️ {name:20s} not found")
except ImportError:
    print("\n  (chromadb not available — skip vector DB check)")

print()
