"""
IBTrACS ingestor — historical tropical cyclone tracks from NOAA.

Downloads the North Indian Ocean (NI) basin CSV from IBTrACS,
parses tracks, and batch-inserts into historical_cyclones.

Polling: weekly (configurable).
Strategy: INSERT OR IGNORE (append-only, idempotent).
"""
import csv
import io
import logging
from datetime import datetime
from typing import Dict, List, Optional

from config.config import Config
from ingestion.base import BaseIngestor
from utils.database import DatabaseManager

logger = logging.getLogger(__name__)

# The IBTrACS CSV has metadata header lines starting with these
_SKIP_PREFIXES = ("IBTrACS", "SEASON", "Year")


class IBTrACSIngestor(BaseIngestor):

    @property
    def source_name(self) -> str:
        return "ibtracs"

    def ingest(self) -> Dict:
        url = Config.IBTRACS_SOURCE_URL
        started = datetime.utcnow().isoformat()

        try:
            resp = self.fetch(url)
            resp.raise_for_status()
        except Exception as exc:
            self._log_fetch(url, started, "error", error=str(exc))
            logger.error("[ibtracs] fetch error: %s", exc)
            return {"source": self.source_name, "records_inserted": 0}

        raw_ref = self.payload_store.save(
            self.source_name, "csv", resp.text,
        )

        rows = _parse_csv(resp.text, raw_ref)
        count = self.db.batch_insert_historical_cyclones(rows)

        self._log_fetch(url, started, "ok",
                        http_status=resp.status_code, records=count)
        logger.info("[ibtracs] inserted %d cyclone records", count)
        return {"source": self.source_name, "records_inserted": count}


# ======================================================================
# Parsing
# ======================================================================

def _parse_csv(text: str, raw_ref: int) -> List[dict]:
    """Parse IBTrACS CSV (v04 format) into row dicts for historical_cyclones."""
    rows: List[dict] = []

    reader = csv.DictReader(io.StringIO(text))
    for record in reader:
        # Skip the second header / units row
        sid = (record.get("SID") or "").strip()
        if not sid or sid.startswith("SID"):
            continue

        lat = _to_float(record.get("LAT"))
        lon = _to_float(record.get("LON"))
        if lat is None or lon is None:
            continue

        # Filter to region bbox
        bbox = Config.REGION_BBOX  # [south, north, west, east]
        # Also accept wider basin tracks (North Indian Ocean = "NI")
        basin = (record.get("BASIN") or "").strip()

        iso_time = (record.get("ISO_TIME") or "").strip()
        name = (record.get("NAME") or "").strip()
        wind_kt = _to_float(record.get("USA_WIND") or record.get("WMO_WIND"))
        pressure_mb = _to_float(record.get("USA_PRES") or record.get("WMO_PRES"))
        category = (record.get("USA_SSHS") or record.get("STORM_TYPE") or "").strip()

        rows.append({
            "storm_id": sid,
            "name": name if name and name != "NOT_NAMED" else None,
            "basin": basin,
            "iso_time": iso_time,
            "lat": lat,
            "lon": lon,
            "wind_kt": wind_kt,
            "pressure_mb": pressure_mb,
            "category": category,
            "metadata": None,
            "raw_payload_ref": raw_ref,
            "fetched_at": datetime.utcnow().isoformat(),
        })

    return rows


def _to_float(v) -> Optional[float]:
    if v is None:
        return None
    v = str(v).strip()
    if not v or v in (" ", ""):
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None
