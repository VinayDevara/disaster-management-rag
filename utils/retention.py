"""
Data retention manager — moves data through the 3-tier lifecycle:

  HOT (< 24 h)  →  WARM (1-30 days)  →  COLD (compressed archive files)

Called periodically by the ingestion scheduler.
"""

import gzip
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict

from config.config import Config
from utils.database import DatabaseManager

logger = logging.getLogger(__name__)


class RetentionManager:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def run(self) -> Dict:
        """Execute all retention steps and return summary counts."""
        results: Dict[str, int] = {}

        results["forecasts_moved_to_warm"] = self._hot_to_warm_forecasts()
        results["old_records_archived"] = self._archive_old_records()
        results["cold_files_written"] = self._warm_to_cold()

        logger.info("[retention] cycle complete: %s", results)
        return results

    # ──────────────────────────────────────────────────────────────────
    # HOT → WARM  (forecast signals)
    # ──────────────────────────────────────────────────────────────────

    def _hot_to_warm_forecasts(self) -> int:
        """Move forecast rows older than HOT_RETENTION_HOURS to warm table."""
        return self.db.move_hot_forecasts_to_warm(int(Config.HOT_RETENTION_HOURS))

    # ──────────────────────────────────────────────────────────────────
    # WARM → removal of records past WARM_RETENTION_DAYS
    # ──────────────────────────────────────────────────────────────────

    def _archive_old_records(self) -> int:
        """Delete rows beyond warm retention window."""
        days = int(Config.WARM_RETENTION_DAYS)
        total = 0
        for table, time_col in [
            ("forecast_signals_warm", "forecast_time"),
            ("weather_events", "start_time"),
            ("external_events", "fetched_at"),
            ("rainfall_observations", "observation_time"),
        ]:
            total += self.db.archive_old_records(table, time_col, days)
        return total

    # ──────────────────────────────────────────────────────────────────
    # WARM → COLD  (export to compressed JSON files)
    # ──────────────────────────────────────────────────────────────────

    def _warm_to_cold(self) -> int:
        """Export warm forecast rows older than WARM_RETENTION_DAYS to gzip files."""
        cutoff = datetime.utcnow() - timedelta(days=int(Config.WARM_RETENTION_DAYS))
        cutoff_str = cutoff.isoformat()

        conn = self.db.connect()
        try:
            cursor = conn.execute(
                "SELECT * FROM forecast_signals_warm WHERE fetched_at < ?",
                (cutoff_str,),
            )
            cols = [d[0] for d in cursor.description] if cursor.description else []
            rows = [dict(zip(cols, r)) for r in cursor.fetchall()]
        finally:
            conn.close()

        if not rows:
            return 0

        archive_dir = Config.COLD_ARCHIVE_DIR
        os.makedirs(archive_dir, exist_ok=True)

        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        path = os.path.join(archive_dir, f"warm_forecasts_{ts}.json.gz")

        with gzip.open(path, "wt", encoding="utf-8") as f:
            json.dump(rows, f, default=str)

        # Remove exported rows
        conn = self.db.connect()
        try:
            conn.execute(
                "DELETE FROM forecast_signals_warm WHERE fetched_at < ?",
                (cutoff_str,),
            )
            conn.commit()
        finally:
            conn.close()

        logger.info("[retention] archived %d warm rows to %s", len(rows), path)
        return 1
