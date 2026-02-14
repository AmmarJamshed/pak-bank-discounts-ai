"""Scrape-in-progress state for maintenance banner (cleared after ~1 hour max)."""

import logging
import threading
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_scraping = False
_scrape_started_at: datetime | None = None
_last_scrape_inserted: int = 0
_last_scrape_completed_at: datetime | None = None
_lock = threading.Lock()
MAX_MAINTENANCE_HOURS = 1.0


def set_scraping(value: bool, inserted: int = -1) -> None:
    with _lock:
        global _scraping, _scrape_started_at, _last_scrape_inserted, _last_scrape_completed_at
        _scraping = value
        _scrape_started_at = datetime.now(timezone.utc) if value else None
        if not value and inserted >= 0:
            _last_scrape_inserted = inserted
            _last_scrape_completed_at = datetime.now(timezone.utc)


def get_last_scrape_result() -> tuple[int, datetime | None]:
    with _lock:
        return _last_scrape_inserted, _last_scrape_completed_at


def is_maintenance() -> tuple[bool, str | None]:
    """Returns (in_maintenance, message). Auto-clears after 1 hour."""
    with _lock:
        if not _scraping:
            return False, None
        if _scrape_started_at:
            elapsed = (datetime.now(timezone.utc) - _scrape_started_at).total_seconds() / 3600
            if elapsed >= MAX_MAINTENANCE_HOURS:
                _scraping = False
                _scrape_started_at = None
                logger.warning("Scrape maintenance flag auto-cleared after 1h")
                return False, None
        return True, "Website in weekly maintenance. Deals refresh in under an hour."
