"""Source-adapter interface and shared decoder-row normalisation.

A ``SkySource`` fetches raw rows and normalises them to canonical ``Aircraft``.
The normalisation here tolerates the field-name variance across dump1090-fa,
readsb and tar1090 so downstream code never sees decoder-specific shapes.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any, Optional

from ..models import Aircraft


@dataclass
class FetchResult:
    """Outcome of one source read."""

    rows: list[dict] = field(default_factory=list)
    ok: bool = False
    source_now: Optional[float] = None
    error: Optional[str] = None


def _first(row: dict, *keys: str) -> Any:
    for key in keys:
        if key in row and row[key] is not None:
            return row[key]
    return None


def _alt_to_ft(value: Any) -> Optional[float]:
    # dump1090 reports "ground" for on-ground aircraft.
    if value is None:
        return None
    if isinstance(value, str):
        if value.strip().lower() == "ground":
            return 0.0
        try:
            return float(value)
        except ValueError:
            return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalise_row(row: dict) -> Optional[Aircraft]:
    """Map one decoder row to an ``Aircraft``. Returns None if unusable (no hex)."""
    hex_id = _first(row, "hex", "icao", "addr")
    if not hex_id:
        return None
    flight = _first(row, "flight", "call", "callsign")
    if isinstance(flight, str):
        flight = flight.strip() or None

    return Aircraft(
        hex=str(hex_id).strip().lower(),
        flight=flight,
        lat=_first(row, "lat", "latitude"),
        lon=_first(row, "lon", "longitude"),
        alt_ft=_alt_to_ft(_first(row, "alt_baro", "altitude", "alt", "alt_geom")),
        speed_kt=_first(row, "gs", "speed", "ground_speed"),
        track_deg=_first(row, "track", "trak", "heading"),
        vertical_rate_fpm=_first(row, "baro_rate", "geom_rate", "vert_rate", "vrate"),
        squawk=(str(_first(row, "squawk")) if _first(row, "squawk") is not None else None),
        seen=_first(row, "seen"),
        seen_pos=_first(row, "seen_pos"),
        rssi=_first(row, "rssi"),
        type_code=(str(_first(row, "t", "type")).strip().upper() if _first(row, "t", "type") else None),
        registration=(str(_first(row, "r", "reg", "registration")).strip().upper() if _first(row, "r", "reg", "registration") else None),
    )


class SkySource(abc.ABC):
    """Fetches and normalises aircraft from some ADS-B source."""

    @abc.abstractmethod
    def fetch(self) -> FetchResult:
        """Read the source once. Never raises for expected I/O errors — returns
        ``FetchResult(ok=False, error=...)`` instead so the poll loop can't crash."""

    def normalise(self, result: FetchResult) -> list[Aircraft]:
        out: list[Aircraft] = []
        for row in result.rows:
            try:
                ac = normalise_row(row)
            except Exception:  # a single malformed row must not sink the batch
                ac = None
            if ac is not None:
                out.append(ac)
        return out

    @property
    @abc.abstractmethod
    def describe(self) -> str:
        """Human-readable source description for /m5/status."""
