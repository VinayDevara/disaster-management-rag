"""
GPM IMERG ingestor — fetches recent satellite rainfall estimates
from the NASA PMM Publisher / OpenSearch API.

May optionally require NASA Earthdata credentials for expanded access;
supports env vars but does not hard-fail if absent.

Polling: every 60 min (configurable).
Strategy: append-only rainfall observations, deduplicated by
          (source_name, external_id, observation_time).
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from config.config import Config
from ingestion.base import BaseIngestor
from utils.database import DatabaseManager

logger = logging.getLogger(__name__)


class GPMIngestor(BaseIngestor):

    @property
    def source_name(self) -> str:
        return "gpm_imerg"

    def ingest(self) -> Dict:
        url = Config.GPM_PUBLISHER_URL
        started = datetime.utcnow().isoformat()

        # Build query for our region bounding box, last 6 hours
        bbox = Config.REGION_BBOX  # [south, north, west, east]
        now = datetime.utcnow()
        t_start = (now - timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%SZ")
        t_end = now.strftime("%Y-%m-%dT%H:%M:%SZ")

        params = {
            "bbox": f"{bbox[2]},{bbox[0]},{bbox[3]},{bbox[1]}",
            "startTime": t_start,
            "endTime": t_end,
            "limit": 50,
            "dataset": "GPM_3IMERGHH",
        }

        headers = {}
        if Config.EARTHDATA_TOKEN:
            headers["Authorization"] = f"Bearer {Config.EARTHDATA_TOKEN}"

        try:
            resp = self.fetch(url, headers=headers, params=params)
            resp.raise_for_status()
        except Exception as exc:
            self._log_fetch(url, started, "error", error=str(exc))
            logger.error("[gpm] fetch error: %s", exc)
            return {"source": self.source_name, "records_inserted": 0}

        if not resp.text or not resp.text.strip():
            logger.warning("[gpm] empty response body, skipping")
            self._log_fetch(url, started, "ok", http_status=resp.status_code, records=0)
            return {"source": self.source_name, "records_inserted": 0}

        raw_ref = self.payload_store.save(
            self.source_name, "opensearch_json", resp.text,
        )

        try:
            data = resp.json()
        except Exception as exc:
            logger.error("[gpm] JSON decode error: %s", exc)
            self._log_fetch(url, started, "error", error=str(exc))
            return {"source": self.source_name, "records_inserted": 0}
        items = _extract_items(data)
        count = 0
        for item in items:
            obs = _to_observation(item, raw_ref)
            if obs and self.db.append_rainfall_observation(obs):
                count += 1

        self._log_fetch(url, started, "ok", http_status=resp.status_code,
                        records=count)
        return {"source": self.source_name, "records_inserted": count}


# ======================================================================
# Parsing helpers  (kept modular so the rainfall provider can be swapped)
# ======================================================================

def _extract_items(data: dict) -> List[dict]:
    """Pull granule/item list from the OpenSearch response."""
    # PMM Publisher wraps items under 'items' or 'feed.entry'
    if "items" in data:
        return data["items"]
    feed = data.get("feed", data)
    entries = feed.get("entry", [])
    if isinstance(entries, dict):
        entries = [entries]
    return entries


def _to_observation(item: dict, raw_ref: int) -> Optional[dict]:
    """Normalize a single GPM granule into a rainfall_observations row."""
    try:
        ext_id = item.get("id") or item.get("granuleId") or item.get("title", "")
        obs_time = item.get("time_start") or item.get("startTime") or item.get("updated", "")

        # Try to extract a representative rainfall value from the metadata
        rainfall_mm = _extract_rainfall(item)

        # Coordinates — use center of bounding box if provided
        bbox = item.get("bbox") or item.get("georss:box") or ""
        lat, lon = _bbox_center(bbox)

        return {
            "source_name": "gpm_imerg",
            "external_id": str(ext_id),
            "location_name": Config.REGION_NAME,
            "district": "Dakshina Kannada",
            "latitude": lat or Config.MANGALORE_LAT,
            "longitude": lon or Config.MANGALORE_LON,
            "observation_time": obs_time,
            "rainfall_mm": rainfall_mm,
            "aggregation_window": "30min",
            "dataset_metadata": {
                "dataset": item.get("dataset", "GPM_3IMERGHH"),
                "title": item.get("title", ""),
            },
            "raw_payload_ref": raw_ref,
            "fetched_at": datetime.utcnow().isoformat(),
        }
    except Exception as exc:
        logger.warning("[gpm] parse error for item: %s", exc)
        return None


def _extract_rainfall(item: dict) -> Optional[float]:
    """Best-effort extraction of a rainfall value from granule metadata."""
    for key in ("precipitationCal", "precipitation", "rainfall_mm",
                "HQprecipitation", "precipitationUncal"):
        val = item.get(key)
        if val is not None:
            try:
                return float(val)
            except (ValueError, TypeError):
                pass
    return None


def _bbox_center(bbox):
    """Parse 'south west north east' or [s,w,n,e] into center (lat, lon)."""
    if isinstance(bbox, str) and bbox.strip():
        parts = bbox.strip().replace(",", " ").split()
        if len(parts) >= 4:
            s, w, n, e = [float(p) for p in parts[:4]]
            return (s + n) / 2, (w + e) / 2
    elif isinstance(bbox, (list, tuple)) and len(bbox) >= 4:
        s, w, n, e = [float(x) for x in bbox[:4]]
        return (s + n) / 2, (w + e) / 2
    return None, None
