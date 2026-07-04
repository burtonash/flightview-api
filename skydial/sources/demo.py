"""Demo source: loop over recorded ADS-B frames so the build works with no receiver.

The frames file is a JSON list of dump1090-shaped payloads:
    [ {"now": 1782..., "aircraft": [ {...}, ... ]}, ... ]
Each ``fetch()`` advances to the next frame (wrapping around).
"""

from __future__ import annotations

import json
from pathlib import Path

from .base import FetchResult, SkySource


class DemoSource(SkySource):
    def __init__(self, frames_path: str):
        self.frames_path = frames_path
        self._frames: list[dict] | None = None
        self._idx = 0

    @property
    def describe(self) -> str:
        return f"demo @ {self.frames_path}"

    def _load(self) -> list[dict]:
        if self._frames is None:
            data = json.loads(Path(self.frames_path).read_text(encoding="utf-8"))
            if isinstance(data, dict):  # allow a single frame too
                data = [data]
            self._frames = [f for f in data if isinstance(f, dict)]
        return self._frames

    def fetch(self) -> FetchResult:
        try:
            frames = self._load()
        except (OSError, json.JSONDecodeError) as exc:
            return FetchResult(ok=False, error=f"{type(exc).__name__}: {exc}")
        if not frames:
            return FetchResult(ok=True, rows=[], source_now=None)

        frame = frames[self._idx % len(frames)]
        self._idx += 1
        rows = frame.get("aircraft", [])
        return FetchResult(rows=list(rows), ok=True, source_now=frame.get("now"))
