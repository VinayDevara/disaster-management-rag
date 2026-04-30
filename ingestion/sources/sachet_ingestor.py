"""
SACHET / NDMA ingestor — polls official Indian disaster warning feeds.
No dedicated API key expected; configure feed URLs in Config.

Polling: every 5–10 min (configurable).
Strategy: upsert alerts, ETag caching, district filtering.
"""
import json
import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from config.config import Config
from ingestion.base import BaseIngestor
from utils.database import DatabaseManager

logger = logging.getLogger(__name__)

# CAP XML namespaces
_CAP_NS = {"cap": "urn:oasis:names:tc:emergency:cap:1.2"}


class SachetIngestor(BaseIngestor):

    def __init__(self, db: DatabaseManager):
        super().__init__(db)
        # Per-URL ETag cache (in-memory; resets on restart)
        self._etags: Dict[str, str] = {}

    @property
    def source_name(self) -> str:
        return "sachet"

    def ingest(self) -> Dict:
        total = 0
        # Try JSON feed first, then CAP XML feeds
        for url in Config.SACHET_FEED_URLS:
            count = self._fetch_json_feed(url.strip())
            total += count
        for url in Config.SACHET_CAP_URLS:
            count = self._fetch_cap_feed(url.strip())
            total += count
        return {"source": self.source_name, "records_upserted": total}

    # ------------------------------------------------------------------
    # JSON feed (SACHET REST endpoint)
    # ------------------------------------------------------------------

    def _fetch_json_feed(self, url: str) -> int:
        started = datetime.utcnow().isoformat()
        headers: Dict[str, str] = {}
        etag_sent = self._etags.get(url)
        if etag_sent:
            headers["If-None-Match"] = etag_sent

        try:
            resp = self.fetch(url, headers=headers)
        except Exception as exc:
            self._log_fetch(url, started, "error", error=str(exc))
            logger.error("[sachet] JSON fetch error: %s", exc)
            return 0

        if resp.status_code == 304:
            self._log_fetch(url, started, "not_modified", http_status=304,
                            etag_sent=etag_sent)
            logger.debug("[sachet] 304 Not Modified for %s", url)
            return 0

        if not resp.ok:
            self._log_fetch(url, started, "http_error", http_status=resp.status_code)
            return 0

        etag_recv = resp.headers.get("ETag")
        if etag_recv:
            self._etags[url] = etag_recv

        raw_ref = self.payload_store.save(
            self.source_name, "json_feed", resp.text
        )

        try:
            payload = resp.json()
        except Exception:
            payload = []

        alerts = payload if isinstance(payload, list) else payload.get("alerts", payload.get("data", []))
        count = 0
        district_matched = []
        state_matched = []
        for item in alerts:
            alert = _normalize_json_alert(item)
            if _matches_district(alert):
                district_matched.append(alert)
            elif _matches_state(alert):
                state_matched.append(alert)

        # Use district-matched alerts; fall back to state-level if none
        chosen = district_matched if district_matched else state_matched
        for alert in chosen:
            alert["raw_payload_ref"] = raw_ref
            alert["fetched_at"] = datetime.utcnow().isoformat()
            if self.db.upsert_official_alert(alert):
                count += 1

        self._log_fetch(url, started, "ok", http_status=resp.status_code,
                        etag_sent=etag_sent, etag_received=etag_recv,
                        records=count)
        return count

    # ------------------------------------------------------------------
    # CAP XML feed
    # ------------------------------------------------------------------

    def _fetch_cap_feed(self, url: str) -> int:
        started = datetime.utcnow().isoformat()
        headers: Dict[str, str] = {}
        etag_sent = self._etags.get(url)
        if etag_sent:
            headers["If-None-Match"] = etag_sent

        try:
            resp = self.fetch(url, headers=headers)
        except Exception as exc:
            self._log_fetch(url, started, "error", error=str(exc))
            return 0

        if resp.status_code == 304:
            self._log_fetch(url, started, "not_modified", http_status=304,
                            etag_sent=etag_sent)
            return 0

        if not resp.ok:
            self._log_fetch(url, started, "http_error", http_status=resp.status_code)
            return 0

        etag_recv = resp.headers.get("ETag")
        if etag_recv:
            self._etags[url] = etag_recv

        raw_ref = self.payload_store.save(
            self.source_name, "cap_xml", resp.text
        )

        count = 0
        try:
            alerts = _parse_cap_xml(resp.text)
        except Exception as exc:
            logger.error("[sachet] CAP parse error: %s", exc)
            alerts = []

        for alert in alerts:
            if not _matches_district(alert):
                continue
            alert["raw_payload_ref"] = raw_ref
            alert["fetched_at"] = datetime.utcnow().isoformat()
            if self.db.upsert_official_alert(alert):
                count += 1

        self._log_fetch(url, started, "ok", http_status=resp.status_code,
                        etag_sent=etag_sent, etag_received=etag_recv,
                        records=count)
        return count


# ======================================================================
# Parsing helpers
# ======================================================================

def _normalize_json_alert(item: dict) -> dict:
    """Map a SACHET JSON alert object to our official_alerts schema."""
    # Parse centroid "lon,lat" string for coordinates
    lat, lon = None, None
    centroid = item.get("centroid", "")
    if centroid and "," in str(centroid):
        parts = str(centroid).split(",")
        if len(parts) >= 2:
            lon = _to_float(parts[0])
            lat = _to_float(parts[1])

    # Detect state from alert_source or area_description
    state = ""
    for field in ("alert_source", "area_description", "warning_message"):
        val = item.get(field, "")
        if "Karnataka" in val:
            state = "Karnataka"
            break

    return {
        "source_name": "sachet",
        "external_id": str(item.get("identifier") or item.get("alert_id_sdma_autoinc", "")),
        "alert_type": item.get("disaster_type", ""),
        "title": item.get("disaster_type", ""),
        "description": item.get("warning_message", ""),
        "severity": item.get("severity", ""),
        "urgency": item.get("severity_level", ""),
        "certainty": item.get("severity_level", ""),
        "area_desc": item.get("area_description", ""),
        "district": "",
        "state": state,
        "latitude": lat,
        "longitude": lon,
        "onset": _parse_sachet_date(item.get("effective_start_time", "")),
        "expires": _parse_sachet_date(item.get("effective_end_time", "")),
        "status": "Actual" if item.get("disseminated") == "true" else "",
        "source_url": "",
        # Keep original fields for district matching
        "_warning_message": item.get("warning_message", ""),
        "_alert_source": item.get("alert_source", ""),
    }


def _parse_cap_xml(xml_text: str) -> List[dict]:
    """Parse CAP 1.2 XML into a list of normalized alert dicts."""
    alerts: List[dict] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return alerts

    # Handle both single <alert> and <feed>/<alerts> wrapper
    alert_elements = root.findall(".//cap:alert", _CAP_NS)
    if not alert_elements:
        # Try without namespace
        alert_elements = root.findall(".//alert")
    if not alert_elements:
        # The root itself may be <alert>
        if root.tag.endswith("alert") or root.tag == "alert":
            alert_elements = [root]

    for alert_el in alert_elements:
        a = _parse_single_cap(alert_el)
        if a:
            alerts.append(a)
    return alerts


def _parse_single_cap(el: ET.Element) -> Optional[dict]:
    """Extract fields from a single CAP <alert> element."""
    def _t(tag):
        # Try with namespace then without
        node = el.find(f"cap:{tag}", _CAP_NS)
        if node is None:
            node = el.find(tag)
        return node.text.strip() if node is not None and node.text else ""

    info = el.find("cap:info", _CAP_NS)
    if info is None:
        info = el.find("info")
    if info is None:
        info = el  # fallback

    def _i(tag):
        node = info.find(f"cap:{tag}", _CAP_NS)
        if node is None:
            node = info.find(tag)
        return node.text.strip() if node is not None and node.text else ""

    area = info.find("cap:area", _CAP_NS)
    if area is None:
        area = info.find("area")

    area_desc = ""
    lat, lon = None, None
    if area is not None:
        ad = area.find("cap:areaDesc", _CAP_NS)
        if ad is None:
            ad = area.find("areaDesc")
        area_desc = ad.text.strip() if ad is not None and ad.text else ""

        circle = area.find("cap:circle", _CAP_NS)
        if circle is None:
            circle = area.find("circle")
        if circle is not None and circle.text:
            parts = circle.text.strip().split()
            if parts:
                coords = parts[0].split(",")
                if len(coords) >= 2:
                    lat = _to_float(coords[0])
                    lon = _to_float(coords[1])

    return {
        "source_name": "sachet",
        "external_id": _t("identifier") or _i("identifier"),
        "alert_type": _i("msgType") or _i("event"),
        "title": _i("headline") or _i("event"),
        "description": _i("description"),
        "severity": _i("severity"),
        "urgency": _i("urgency"),
        "certainty": _i("certainty"),
        "area_desc": area_desc,
        "district": _extract_district(area_desc),
        "state": "Karnataka",
        "latitude": lat,
        "longitude": lon,
        "onset": _i("onset") or _i("effective"),
        "expires": _i("expires"),
        "status": _t("status"),
        "source_url": "",
    }


def _extract_district(area_desc: str) -> str:
    """Try to detect a known district name inside area_desc."""
    for d in Config.DISTRICT_FILTERS:
        if d.strip().lower() in area_desc.lower():
            return d.strip()
    return ""


def _matches_district(alert: dict) -> bool:
    """Return True if alert is relevant to our target districts."""
    filters = [d.strip().lower() for d in Config.DISTRICT_FILTERS]
    for field in ("district", "area_desc", "description", "title",
                  "_warning_message", "_alert_source"):
        val = (alert.get(field) or "").lower()
        for f in filters:
            if f in val:
                return True
    return False


def _matches_state(alert: dict) -> bool:
    """Return True if alert belongs to our target state (Karnataka)."""
    state = Config.REGION_STATE.lower()
    for field in ("state", "area_desc", "description", "_warning_message",
                  "_alert_source"):
        val = (alert.get(field) or "").lower()
        if state in val:
            return True
    return False


def _parse_sachet_date(date_str: str) -> str:
    """Parse SACHET date format like 'Sun Mar 29 06:23:00 IST 2026' to ISO."""
    if not date_str:
        return ""
    # Remove timezone abbreviation (IST etc.) for parsing
    cleaned = re.sub(r'\b[A-Z]{2,4}\b', '', date_str).strip()
    # Collapse extra spaces
    cleaned = re.sub(r'\s+', ' ', cleaned)
    for fmt in ("%a %b %d %H:%M:%S %Y", "%b %d %H:%M:%S %Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(cleaned, fmt).isoformat()
        except ValueError:
            continue
    return date_str


def _to_float(v) -> Optional[float]:
    if v is None:
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None
