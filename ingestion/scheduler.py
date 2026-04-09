"""
Ingestion scheduler — runs background polling jobs inside the FastAPI event loop.
Uses asyncio tasks so the main thread is never blocked.
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List

from config.config import Config
from utils.database import DatabaseManager

logger = logging.getLogger(__name__)


class IngestionScheduler:
    """
    Central scheduler for periodic source ingestion.
    Call start() on FastAPI startup and stop() on shutdown.
    """

    def __init__(self, db: DatabaseManager):
        self.db = db
        self._tasks: List[asyncio.Task] = []
        self._running = False

    # ------------------------------------------------------------------
    # Public lifecycle
    # ------------------------------------------------------------------

    async def start(self):
        """Register and launch all polling loops."""
        if self._running:
            return
        self._running = True
        logger.info("IngestionScheduler starting …")

        # Phase 1 sources
        from ingestion.sources.openmeteo_ingestor import OpenMeteoIngestor
        from ingestion.sources.sachet_ingestor import SachetIngestor
        from ingestion.sources.gdacs_ingestor import GDACSIngestor

        self._schedule(OpenMeteoIngestor(self.db), Config.POLL_MINUTES_OPENMETEO * 60)
        self._schedule(SachetIngestor(self.db), Config.POLL_MINUTES_SACHET * 60)
        self._schedule(GDACSIngestor(self.db), Config.POLL_MINUTES_GDACS * 60)

        # Phase 2 sources (import-guarded so missing files don't block Phase 1)
        try:
            from ingestion.sources.gpm_ingestor import GPMIngestor
            self._schedule(GPMIngestor(self.db), Config.POLL_MINUTES_GPM * 60)
        except ImportError:
            logger.info("GPMIngestor not available yet — skipping")

        try:
            from ingestion.sources.lhasa_ingestor import LHASAIngestor
            self._schedule(LHASAIngestor(self.db), Config.POLL_HOURS_LHASA * 3600)
        except ImportError:
            logger.info("LHASAIngestor not available yet — skipping")

        # Phase 3: IBTrACS — very infrequent, only once per run
        try:
            from ingestion.sources.ibtracs_ingestor import IBTrACSIngestor
            self._schedule(IBTrACSIngestor(self.db), Config.POLL_DAYS_IBTRACS * 86400)
        except ImportError:
            logger.info("IBTrACSIngestor not available yet — skipping")

        # Retention cycle — run every 6 hours
        try:
            from utils.retention import RetentionManager
            self._schedule_callable(
                RetentionManager(self.db), Config.HOT_RETENTION_HOURS * 3600
            )
        except ImportError:
            logger.info("RetentionManager not available yet — skipping")

        logger.info("IngestionScheduler started with %d jobs", len(self._tasks))

    async def stop(self):
        """Cancel all background tasks."""
        self._running = False
        for t in self._tasks:
            t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        logger.info("IngestionScheduler stopped")

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _schedule(self, ingestor, interval_seconds: float):
        """Wrap an ingestor.ingest() call in an async polling loop."""
        task = asyncio.create_task(
            self._poll_loop(ingestor, interval_seconds)
        )
        self._tasks.append(task)

    def _schedule_callable(self, obj, interval_seconds: float):
        """Wrap an object with a .run() method in an async polling loop."""
        task = asyncio.create_task(
            self._poll_loop_callable(obj, interval_seconds)
        )
        self._tasks.append(task)

    async def _poll_loop(self, ingestor, interval: float):
        """Run ingestor.ingest() in a thread, sleep, repeat."""
        name = ingestor.source_name
        # Small initial stagger so sources don't all fire at once
        await asyncio.sleep(2)
        while self._running:
            try:
                logger.info("[%s] ingestion cycle starting", name)
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(None, ingestor.ingest)
                logger.info("[%s] ingestion done — %s", name, result)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("[%s] ingestion error", name)
            await asyncio.sleep(interval)

    async def _poll_loop_callable(self, obj, interval: float):
        """Run obj.run() in a thread, sleep, repeat."""
        name = getattr(obj, "__class__", type(obj)).__name__
        await asyncio.sleep(5)
        while self._running:
            try:
                logger.info("[%s] cycle starting", name)
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(None, obj.run)
                logger.info("[%s] cycle done — %s", name, result)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("[%s] cycle error", name)
            await asyncio.sleep(interval)
