"""ADS-B source adapters — the seam that makes the service decoder-independent."""

from __future__ import annotations

from typing import Any

from .base import FetchResult, SkySource
from .demo import DemoSource
from .dump1090 import Dump1090Source


def build_source(cfg: dict[str, Any]) -> SkySource:
    """Construct the configured source. Raises ValueError on unknown type."""
    src = cfg.get("source", {})
    kind = src.get("type", "dump1090")
    if kind == "dump1090":
        return Dump1090Source(location=src["location"], timeout_s=src.get("timeout_s", 2.0))
    if kind == "demo":
        return DemoSource(frames_path=src.get("demo_frames", "sample_data/demo_frames.json"))
    raise ValueError(f"Unknown source type: {kind!r} (expected 'dump1090' or 'demo')")


__all__ = ["FetchResult", "SkySource", "Dump1090Source", "DemoSource", "build_source"]
