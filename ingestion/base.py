"""
Base ingestor: shared HTTP fetch with retry, timeout, logging,
raw-payload storage, and source_fetch_log helper.
All concrete ingestors inherit from this.
"""
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.config import Config
from utils.database import DatabaseManager
from utils.raw_payload_store import RawPayloadStore

logger = logging.getLogger(__name__)


class BaseIngestor(ABC):
    """
    Abstract base for all data-source ingestors.

    Subclasses must implement:
        source_name  (str property)
        ingest()     (the actual fetch → parse → store cycle)
    """

    def __init__(self, db: DatabaseManager):
        self.db = db
        self.payload_store = RawPayloadStore(db)
        self._session: Optional[requests.Session] = None

    # ------------------------------------------------------------------
    # Properties subclasses must define
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def source_name(self) -> str:
        ...

    @abstractmethod
    def ingest(self) -> Dict:
        """Run one fetch-parse-store cycle. Return a summary dict."""
        ...

    # ------------------------------------------------------------------
    # Shared HTTP helper
    # ------------------------------------------------------------------

    def _get_session(self) -> requests.Session:
        if self._session is None:
            s = requests.Session()
            retries = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["GET", "HEAD"],
            )
            adapter = HTTPAdapter(max_retries=retries)
            s.mount("https://", adapter)
            s.mount("http://", adapter)
            self._session = s
        return self._session

    def fetch(self, url: str, headers: Dict = None,
              params: Dict = None, timeout: int = 30) -> requests.Response:
        """GET with retry + timeout. Raises on hard failures."""
        session = self._get_session()
        resp = session.get(url, headers=headers or {},
                           params=params or {}, timeout=timeout)
        return resp

    # ------------------------------------------------------------------
    # Fetch-log convenience
    # ------------------------------------------------------------------

    def _log_fetch(self, url: str, started: str, status: str,
                   http_status: int = None, etag_sent: str = None,
                   etag_received: str = None, records: int = 0,
                   error: str = None, meta: dict = None):
        completed = datetime.utcnow().isoformat()
        self.db.log_source_fetch(
            source_name=self.source_name,
            fetch_url=url,
            fetch_started_at=started,
            fetch_completed_at=completed,
            status=status,
            http_status=http_status,
            etag_sent=etag_sent,
            etag_received=etag_received,
            records_processed=records,
            error_message=error,
            metadata=meta,
        )
