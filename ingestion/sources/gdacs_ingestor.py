"""
GDACS ingestor — polls flood and cyclone events via the GDACS JSON API.
No API key expected.

The former RSS/XML feeds (rss_fl.xml, rss_tc.xml) now return HTML pages,
so we use the GeoJSON search API instead.

Polling: every 10–15 min (configurable).
Strategy: upsert events by (source_name, external_id).
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from config.config import Config
from ingestion.base import BaseIngestor

logger = logging.getLogger(__name__)

# JSON API base — returns GeoJSON FeatureCollections
_API_BASE = "https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH"


class GDACSIngestor(BaseIngestor):

    @property
    def source_name(self) -> str:
        return "gdacs"

    def ingest(self) -> Dict:
        total = 0
        for event_code, event_type in [("FL", "flood"), ("TC", "cyclone")]:
            count = self._fetch_events(event_code, event_type)
            total += count
        return {"source": self.source_name, "records_upserted": total}

    def _fetch_events(self, event_code: str, event_type: str) -> int:
        started = datetime.utcnow().isoformat()
        now = datetime.utcnow()
        from_date = (now - timedelta(days=30)).strftime("%Y-%m-%d")
        to_date = now.strftime("%Y-%m-%d")

        url = (
            f"{_API_BASE}?eventlist={event_code}"
            f"&fromDate={from_date}&toDate={to_date}"
            f"&alertlevel=Green;Orange;Red"
        )

        try:
            resp = self.fetch(url)
            resp.raise_for_status()
        except Exception as exc:
            self._log_fetch(url, started, "error", error=str(exc))
            logger.error("[gdacs] fetch error %s: %s", event_type, exc)
            return 0

        raw_ref = self.payload_store.save(
            self.source_name, f"json_{event_type}", resp.text,
        )

        try:
            data = resp.json()
        except Exception as exc:
            self._log_fetch(url, started, "error", error=f"JSON decode: {exc}")
            logger.error("[gdacs] JSON decode error %s: %s", event_type, exc)
            return 0

        features = data.get("features", [])
        count = 0
        for feature in features:
            ev = _feature_to_event(feature, event_type)
            if ev:
                ev["raw_payload_ref"] = raw_ref
                ev["fetched_at"] = datetime.utcnow().isoformat()
                if self.db.upsert_external_event(ev):
                    count += 1

        self._log_fetch(url, started, "ok", http_status=resp.status_code,
                        records=count)
        return count


# ======================================================================
# GeoJSON feature → event dict
# ======================================================================

def _feature_to_event(feature: dict, event_type: str) -> Optional[dict]:
    props = feature.get("properties", {})
    geom = feature.get("geometry", {})

    event_id = props.get("eventid")
    if not event_id:
        return None

    coords = geom.get("coordinates", [])
    lon = coords[0] if len(coords) >= 1 else None
    lat = coords[1] if len(coords) >= 2 else None

    # url can be a dict in the JSON API — extract the report link or serialize
    raw_url = props.get("url", "")
    if isinstance(raw_url, dict):
        raw_url = raw_url.get("report", raw_url.get("details", str(raw_url)))

    return {
        "source_name": "gdacs",
        "external_id": str(event_id),
        "event_type": event_type,
        "title": props.get("name", ""),
        "description": props.get("description", ""),
        "severity": props.get("alertlevel", ""),
        "country": props.get("country", ""),
        "region": "",
        "latitude": lat,
        "longitude": lon,
        "start_time": props.get("fromdate", ""),
        "end_time": props.get("todate"),
        "source_url": str(raw_url),
    }
