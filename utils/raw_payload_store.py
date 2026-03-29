"""
Raw payload archive helper.
Writes fetched payloads to disk (compressed where appropriate) and stores
a reference row in the raw_payload_store table via DatabaseManager.
"""
import gzip
import hashlib
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from config.config import Config
from utils.database import DatabaseManager

logger = logging.getLogger(__name__)


class RawPayloadStore:
    """Write raw payloads to disk and register them in the database."""

    def __init__(self, db: DatabaseManager):
        self.db = db
        self.base_dir = Path(Config.RAW_PAYLOAD_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def save(
        self,
        source_name: str,
        payload_type: str,
        content: str,
        external_id: str = None,
        compress: bool = True,
    ) -> int:
        """
        Persist a raw payload to disk + DB.

        Returns:
            raw_payload_store.id (the DB row id), or -1 on failure.
        """
        now = datetime.utcnow()
        payload_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        # Build path: raw_payloads/{source}/{YYYY}/{MM}/{hash}.json.gz
        rel_dir = Path(source_name) / now.strftime("%Y") / now.strftime("%m")
        abs_dir = self.base_dir / rel_dir
        abs_dir.mkdir(parents=True, exist_ok=True)

        ext = ".json.gz" if compress else ".json"
        filename = f"{payload_hash[:16]}_{now.strftime('%Y%m%dT%H%M%S')}{ext}"
        file_path = abs_dir / filename

        try:
            if compress:
                with gzip.open(file_path, "wt", encoding="utf-8") as f:
                    f.write(content)
            else:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
        except OSError as exc:
            logger.error("Failed to write payload file %s: %s", file_path, exc)
            return -1

        # Try to parse as JSON for the payload_json column
        payload_json = None
        try:
            payload_json = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            pass

        row_id = self.db.store_raw_payload(
            source_name=source_name,
            payload_type=payload_type,
            external_id=external_id,
            payload_hash=payload_hash,
            payload_text=None,          # text stored on disk, not in DB
            payload_json=payload_json,  # small payloads also kept inline
            file_path=str(file_path),
            fetched_at=now.isoformat(),
        )

        logger.debug("Saved raw payload %s → %s (row %d)", source_name, file_path, row_id)
        return row_id
