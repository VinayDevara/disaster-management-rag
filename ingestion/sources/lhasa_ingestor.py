"""
NASA LHASA ingestor — fetches landslide nowcast / risk / exposure data
for the Dakshina Karnataka region.

Primary source: NASA NCCS ArcGIS MapServer.
Fallback: rainfall-based risk estimation using Open-Meteo precipitation
data when the NASA server is unreachable.

Polling: every 6 hours (configurable).
Strategy: replace region snapshot (landslide_snapshot_current).
"""
import json
import logging
import requests as _requests
from datetime import datetime
from typing import Dict, List, Optional

from config.config import Config
from ingestion.base import BaseIngestor
from utils.database import DatabaseManager

logger = logging.getLogger(__name__)


class LHASAIngestor(BaseIngestor):

    @property
    def source_name(self) -> str:
        return "lhasa"

    def ingest(self) -> Dict:
        url = Config.LHASA_SERVICE_URL
        started = datetime.utcnow().isoformat()

        bbox = Config.REGION_BBOX  # [south, north, west, east]
        params = {
            "f": "json",
            "geometry": f"{bbox[2]},{bbox[0]},{bbox[3]},{bbox[1]}",
            "geometryType": "esriGeometryEnvelope",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "*",
            "returnGeometry": "true",
        }
        # Append /0/query for ArcGIS REST pattern
        query_url = url.rstrip("/") + "/0/query"

        headers = {}
        if Config.EARTHDATA_TOKEN:
            headers["Authorization"] = f"Bearer {Config.EARTHDATA_TOKEN}"

        try:
            resp = self.fetch(query_url, headers=headers, params=params,
                              timeout=15)
            resp.raise_for_status()
        except Exception as exc:
            self._log_fetch(query_url, started, "error", error=str(exc))
            logger.warning("[lhasa] NASA NCCS unreachable (%s); using rainfall fallback", exc)
            return self._rainfall_fallback()

        raw_ref = self.payload_store.save(
            self.source_name, "arcgis_json", resp.text,
        )

        data = resp.json()
        rows = _parse_features(data, raw_ref)
        count = self.db.replace_landslide_snapshot(self.source_name, rows)

        self._log_fetch(query_url, started, "ok",
                        http_status=resp.status_code, records=count)
        return {"source": self.source_name, "records_inserted": count}

    # ------------------------------------------------------------------
    # Fallback: estimate risk from Open-Meteo precipitation
    # ------------------------------------------------------------------

    def _rainfall_fallback(self) -> Dict:
        """Generate landslide risk snapshot from current rainfall data."""
        locations = [
            {"name": "Mangalore", "district": "Dakshina Kannada",
             "lat": Config.MANGALORE_LAT, "lon": Config.MANGALORE_LON},
            {"name": "Udupi", "district": "Udupi",
             "lat": Config.UDUPI_LAT, "lon": Config.UDUPI_LON},
        ]
        now_str = datetime.utcnow().isoformat()
        rows: List[dict] = []

        for loc in locations:
            try:
                resp = _requests.get(
                    Config.OPENMETEO_BASE_URL,
                    params={
                        "latitude": loc["lat"],
                        "longitude": loc["lon"],
                        "hourly": "precipitation,rain,showers",
                        "forecast_days": 1,
                        "past_days": 1,
                        "timezone": "Asia/Kolkata",
                    },
                    timeout=10,
                )
                resp.raise_for_status()
                data = resp.json()
                hourly = data.get("hourly", {})
                precip = hourly.get("precipitation", [])
                # Sum last 24 h of actual + forecast precipitation
                total_mm = sum(p for p in precip if p is not None)
                prob = _precip_to_probability(total_mm)
                risk = _risk_from_prob(prob)
            except Exception as exc:
                logger.error("[lhasa] rainfall fallback error for %s: %s",
                             loc["name"], exc)
                prob, risk, total_mm = 0.1, "low", 0.0

            rows.append({
                "region_name": Config.REGION_NAME,
                "district": loc["district"],
                "snapshot_time": now_str,
                "latitude": loc["lat"],
                "longitude": loc["lon"],
                "probability": prob,
                "risk_level": risk,
                "exposure_population": None,
                "exposure_roads": None,
                "metadata": {"source": "rainfall_estimate",
                             "total_precip_mm_24h": total_mm,
                             "location": loc["name"]},
                "raw_payload_ref": None,
                "fetched_at": now_str,
            })

        count = self.db.replace_landslide_snapshot(self.source_name, rows)
        logger.info("[lhasa] rainfall fallback inserted %d rows", count)
        return {"source": self.source_name, "records_inserted": count,
                "fallback": True}


# ======================================================================
# Parsing
# ======================================================================

def _parse_features(data: dict, raw_ref: int) -> List[dict]:
    features = data.get("features", [])
    now_str = datetime.utcnow().isoformat()
    rows: List[dict] = []

    for feat in features:
        attrs = feat.get("attributes", {})
        geom = feat.get("geometry", {})

        lat = geom.get("y") or geom.get("latitude")
        lon = geom.get("x") or geom.get("longitude")

        # Handle rings (polygon) — take centroid of first ring
        if lat is None and "rings" in geom:
            lat, lon = _polygon_centroid(geom["rings"])

        probability = (
            attrs.get("nowcast") or attrs.get("probability")
            or attrs.get("Nowcast_Probability")
        )
        risk_level = (
            attrs.get("risk_level") or attrs.get("hazard_level")
            or _risk_from_prob(probability)
        )
        exposure_pop = attrs.get("exposure_population") or attrs.get("PopExposure")
        exposure_roads = attrs.get("exposure_roads") or attrs.get("RoadExposure")

        district = _guess_district(attrs)

        rows.append({
            "region_name": Config.REGION_NAME,
            "district": district,
            "snapshot_time": now_str,
            "latitude": _to_float(lat),
            "longitude": _to_float(lon),
            "probability": _to_float(probability),
            "risk_level": str(risk_level) if risk_level else None,
            "exposure_population": _to_int(exposure_pop),
            "exposure_roads": _to_float(exposure_roads),
            "metadata": {k: v for k, v in attrs.items()},
            "raw_payload_ref": raw_ref,
            "fetched_at": now_str,
        })

    return rows


def _polygon_centroid(rings):
    """Simple centroid of the first ring."""
    if not rings or not rings[0]:
        return None, None
    pts = rings[0]
    avg_x = sum(p[0] for p in pts) / len(pts)
    avg_y = sum(p[1] for p in pts) / len(pts)
    return avg_y, avg_x  # lat, lon


def _risk_from_prob(p) -> Optional[str]:
    if p is None:
        return None
    try:
        p = float(p)
    except (ValueError, TypeError):
        return None
    if p >= 0.7:
        return "high"
    if p >= 0.4:
        return "moderate"
    return "low"


def _guess_district(attrs: dict) -> str:
    for key in ("district", "District", "admin2", "NAME_2"):
        val = attrs.get(key, "")
        if val:
            return str(val)
    return "Dakshina Kannada"


def _to_float(v) -> Optional[float]:
    if v is None:
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def _to_int(v) -> Optional[int]:
    if v is None:
        return None
    try:
        return int(float(v))
    except (ValueError, TypeError):
        return None


def _precip_to_probability(total_mm: float) -> float:
    """Map 24h precipitation total to a rough landslide probability.

    Based on empirical thresholds for Western Ghats terrain:
      <10 mm  → 0.05,  10-30 → 0.15,  30-60 → 0.35,
      60-100 → 0.55,  100-150 → 0.70,  >150 → 0.85
    """
    if total_mm < 10:
        return 0.05
    if total_mm < 30:
        return 0.15
    if total_mm < 60:
        return 0.35
    if total_mm < 100:
        return 0.55
    if total_mm < 150:
        return 0.70
    return 0.85
