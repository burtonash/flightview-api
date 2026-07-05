"""SQLite-backed key/value cache with TTL for enrichment lookups.

Shields any external provider from repeated calls and keeps enrichment instant.
Fully graceful: any DB error degrades to a no-op (get→None, set→ignored) so the
cache can never break the core. An in-memory ``:memory:`` path works for tests.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from typing import Any, Optional


class SqliteCache:
    def __init__(self, path: str, default_ttl_s: float = 86400.0):
        self.path = path
        self.default_ttl_s = default_ttl_s
        self._lock = threading.Lock()
        self._conn: Optional[sqlite3.Connection] = None
        try:
            self._conn = sqlite3.connect(path, check_same_thread=False)
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS cache (k TEXT PRIMARY KEY, v TEXT, expires REAL)"
            )
            self._conn.commit()
        except sqlite3.Error:
            self._conn = None  # degrade to no-op

    def get(self, key: str) -> Optional[Any]:
        if self._conn is None:
            return None
        try:
            with self._lock:
                row = self._conn.execute(
                    "SELECT v, expires FROM cache WHERE k = ?", (key,)
                ).fetchone()
            if row is None:
                return None
            value, expires = row
            if expires is not None and expires < time.time():
                return None
            return json.loads(value)
        except (sqlite3.Error, json.JSONDecodeError):
            return None

    def set(self, key: str, value: Any, ttl_s: Optional[float] = None) -> None:
        if self._conn is None:
            return
        ttl = self.default_ttl_s if ttl_s is None else ttl_s
        if ttl is not None and ttl <= 0:
            return  # non-positive TTL: don't cache
        expires = time.time() + ttl if ttl is not None else None
        try:
            with self._lock:
                self._conn.execute(
                    "INSERT OR REPLACE INTO cache (k, v, expires) VALUES (?, ?, ?)",
                    (key, json.dumps(value), expires),
                )
                self._conn.commit()
        except (sqlite3.Error, TypeError):
            return
