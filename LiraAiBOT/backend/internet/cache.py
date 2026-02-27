import os
import sqlite3
import time
from pathlib import Path
from typing import Optional


class WebCache:
    def __init__(self, db_path: Optional[str] = None):
        root = Path(__file__).resolve().parents[2]
        default_path = root / 'data' / 'web_cache.db'
        self.db_path = Path(db_path) if db_path else default_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS web_cache (
                  cache_key TEXT PRIMARY KEY,
                  value TEXT NOT NULL,
                  expires_at INTEGER NOT NULL
                );
                """
            )
            conn.commit()

    def get(self, cache_key: str) -> Optional[str]:
        now = int(time.time())
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT value FROM web_cache WHERE cache_key = ? AND expires_at > ?",
                (cache_key, now),
            ).fetchone()
        return row[0] if row else None

    def set(self, cache_key: str, value: str, ttl_sec: int) -> None:
        expires_at = int(time.time()) + max(0, int(ttl_sec))
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "REPLACE INTO web_cache (cache_key, value, expires_at) VALUES (?, ?, ?)",
                (cache_key, value, expires_at),
            )
            conn.commit()

