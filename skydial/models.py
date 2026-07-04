"""Canonical data model — the single vocabulary shared across the service.

Raw + computed + enriched + decision fields on one ``Aircraft``. Enriched and
decision fields are always optional so any pipeline stage can be skipped and the
product still works (per the phased-enrichment design in ARCHITECTURE.md).
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class Aircraft(BaseModel):
    # --- raw (from the decoder) ---
    hex: str
    flight: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    alt_ft: Optional[float] = None
    speed_kt: Optional[float] = None
    track_deg: Optional[float] = None
    vertical_rate_fpm: Optional[float] = None
    squawk: Optional[str] = None
    seen: Optional[float] = None
    seen_pos: Optional[float] = None
    rssi: Optional[float] = None

    # --- computed (this service) ---
    bearing_deg: Optional[float] = None
    bearing_label: Optional[str] = None
    screen_angle_deg: Optional[float] = None
    distance_km: Optional[float] = None
    elevation_deg: Optional[float] = None
    track_arrow: Optional[str] = None
    vertical_label: Optional[str] = None

    # --- enriched (optional) ---
    airline: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    route: Optional[str] = None
    model: Optional[str] = None

    # --- decision (optional) ---
    score: Optional[float] = None
    selected_reason: Optional[str] = None
    score_factors: Optional[dict[str, float]] = None

    @property
    def has_position(self) -> bool:
        return self.lat is not None and self.lon is not None


class Profile(BaseModel):
    id: str
    name: str
    radar_up_deg: float = 0.0
    view_cone_deg: float = 360.0
    max_distance_km: float = 40.0
    min_elevation_deg: float = 0.0
    alert_enabled: bool = True
    quiet_mode: bool = False


# Machine-readable UI states the Dial renders (PRD → UX Design).
STATE_CONNECTING = "connecting"
STATE_QUIET_SKY = "quiet-sky"
STATE_ACTIVE = "active"
STATE_FEED_LOST = "feed-lost"


class SkyResponse(BaseModel):
    ok: bool
    now: int
    state: str
    profile: Profile
    selected: Optional[int] = None
    aircraft: list[Aircraft] = Field(default_factory=list)
    alerts: list[str] = Field(default_factory=list)


class StatusResponse(BaseModel):
    ok: bool
    now: int
    state: str
    version: str
    active_profile: str
    feed_ok: bool
    last_fetch_ts: Optional[int] = None
    last_fetch_age_s: Optional[float] = None
    raw_count: int = 0
    filtered_count: int = 0
    aircraft_count: int = 0
    source: str = ""
