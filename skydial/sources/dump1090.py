"""dump1090-family source: reads aircraft.json from a file path or http(s) URL.

Compatible with dump1090-fa, readsb and tar1090 (all expose an ``aircraft.json``
with a top-level ``aircraft`` list and a ``now`` timestamp).
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx

from .base import FetchResult, SkySource


class Dump1090Source(SkySource):
    def __init__(self, location: str, timeout_s: float = 2.0):
        self.location = location
        self.timeout_s = timeout_s
        self._is_url = location.startswith(("http://", "https://"))

    @property
    def describe(self) -> str:
        return f"dump1090 @ {self.location}"

    def fetch(self) -> FetchResult:
        try:
            payload = self._read()
        except (httpx.HTTPError, OSError, json.JSONDecodeError) as exc:
            return FetchResult(ok=False, error=f"{type(exc).__name__}: {exc}")

        if not isinstance(payload, dict):
            return FetchResult(ok=False, error="aircraft.json is not a JSON object")

        rows = payload.get("aircraft")
        if not isinstance(rows, list):
            return FetchResult(ok=False, error="aircraft.json missing 'aircraft' list")

        return FetchResult(rows=rows, ok=True, source_now=payload.get("now"))

    def _read(self) -> object:
        if self._is_url:
            resp = httpx.get(self.location, timeout=self.timeout_s)
            resp.raise_for_status()
            return resp.json()
        text = Path(self.location).read_text(encoding="utf-8")
        return json.loads(text)
