"""
Open-Meteo ingestor — fetches hourly forecast data for Mangalore and Udupi.
No API key needed for free non-commercial use.

Polling: every 30 min (configurable).
Strategy: replace rolling next-24h hot forecast window per location.
"""
import json
import logging
from datetime import datetime
from typing import Dict, List

from config.config import Config
from ingestion.base import BaseIngestor
from utils.database import DatabaseManager

logger = logging.getLogger(__name__)

# Variables requested per the spec
_HOURLY_VARS = (
    "precipitation,precipitation_probability,showers,rain,"
    "wind_gusts_10m,weather_code,cape,cloud_cover"
)

# Locations to fetch
_LOCATIONS = [
    {
        "name": "Mangalore",
        "district": "Dakshina Kannada",
        "lat": Config.MANGALORE_LAT,
        "lon": Config.MANGALORE_LON,
    },
    {
        "name": "Udupi",
        "district": "Udupi",
        "lat": Config.UDUPI_LAT,
        "lon": Config.UDUPI_LON,
    },
]


class OpenMeteoIngestor(BaseIngestor):

    @property
    def source_name(self) -> str:
        return "openmeteo"

    def ingest(self) -> Dict:
        total = 0
        for loc in _LOCATIONS:
            count = self._fetch_location(loc)
            total += count
        return {"source": self.source_name, "records_inserted": total}

    # ------------------------------------------------------------------

    def _fetch_location(self, loc: dict) -> int:
        url = Config.OPENMETEO_BASE_URL
        params = {
            "latitude": loc["lat"],
            "longitude": loc["lon"],
            "hourly": _HOURLY_VARS,
            "forecast_days": 1,
            "timezone": "Asia/Kolkata",
        }

        started = datetime.utcnow().isoformat()
        try:
            resp = self.fetch(url, params=params)
            resp.raise_for_status()
        except Exception as exc:
            self._log_fetch(url, started, "error", error=str(exc))
            logger.error("[openmeteo] fetch failed for %s: %s", loc["name"], exc)
            return 0

        data = resp.json()
        raw_ref = self.payload_store.save(
            source_name=self.source_name,
            payload_type="forecast_json",
            content=resp.text,
            external_id=f"{loc['name']}_{datetime.utcnow().strftime('%Y%m%dT%H')}",
        )

        rows = self._parse_hourly(data, loc, raw_ref)
        count = self.db.replace_forecast_window(
            source_name=self.source_name,
            location_name=loc["name"],
            rows=rows,
        )

        self._log_fetch(
            url, started, "ok",
            http_status=resp.status_code,
            records=count,
        )
        return count

    # ------------------------------------------------------------------

    @staticmethod
    def _parse_hourly(data: dict, loc: dict, raw_ref: int) -> List[dict]:
        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        rows: List[dict] = []
        now_str = datetime.utcnow().isoformat()

        for i, t in enumerate(times):
            rows.append({
                "district": loc["district"],
                "latitude": loc["lat"],
                "longitude": loc["lon"],
                "forecast_time": t,
                "precipitation": _safe_idx(hourly.get("precipitation"), i),
                "precipitation_probability": _safe_idx(hourly.get("precipitation_probability"), i),
                "showers": _safe_idx(hourly.get("showers"), i),
                "rain": _safe_idx(hourly.get("rain"), i),
                "wind_gusts_10m": _safe_idx(hourly.get("wind_gusts_10m"), i),
                "weather_code": _safe_idx(hourly.get("weather_code"), i),
                "cape": _safe_idx(hourly.get("cape"), i),
                "cloud_cover": _safe_idx(hourly.get("cloud_cover"), i),
                "risk_score": None,
                "raw_payload_ref": raw_ref,
                "fetched_at": now_str,
            })
        return rows


def _safe_idx(lst, idx):
    """Return lst[idx] if possible, else None."""
    if lst is None:
        return None
    try:
        return lst[idx]
    except (IndexError, TypeError):
        return None
