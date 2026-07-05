"""Alert-state derivation: discrete transitions only, so nothing fires every refresh.

The Pi decides *what* happened (new aircraft, new best pick, feed lost/restored,
something interesting appeared); the Dial owns the actual sound. Quiet-mode /
alerts-disabled suppress here.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .data.aircraft_types import is_rotorcraft
from .models import Aircraft, Profile

# Event names the Dial maps to sounds (PRD → Alerts).
NEW_AIRCRAFT = "new_aircraft"
NEW_BEST_CANDIDATE = "new_best_candidate"
FEED_LOST = "feed_lost"
FEED_RESTORED = "feed_restored"
INTERESTING_AIRCRAFT = "interesting_aircraft"

_EMERGENCY_SQUAWKS = {"7500", "7600", "7700"}


def interesting_reason(ac: Aircraft, cfg: dict) -> str | None:
    """Why this aircraft is noteworthy (emergency / low+close / rotorcraft), else None."""
    icfg = cfg.get("interesting", {})
    squawks = {str(s) for s in icfg.get("emergency_squawks", [7500, 7600, 7700])}
    if ac.squawk and ac.squawk in (squawks or _EMERGENCY_SQUAWKS):
        return f"emergency squawk {ac.squawk}"
    if is_rotorcraft(ac.type_code):
        return "helicopter"
    low_alt = float(icfg.get("low_alt_ft", 4000))
    near_km = float(icfg.get("near_km", 8))
    if (ac.alt_ft is not None and ac.alt_ft <= low_alt
            and ac.distance_km is not None and ac.distance_km <= near_km):
        return "low and close"
    return None


@dataclass
class Snapshot:
    feed_ok: bool = False
    in_view_hexes: set[str] = field(default_factory=set)
    selected_hex: str | None = None
    interesting_hexes: set[str] = field(default_factory=set)


def derive_alerts(prev: Snapshot | None, cur: Snapshot, profile: Profile) -> list[str]:
    """Alert events for this tick. Empty on the first tick (no baseline)."""
    if not profile.alert_enabled or profile.quiet_mode:
        return []
    if prev is None:
        return []

    alerts: list[str] = []
    if prev.feed_ok and not cur.feed_ok:
        alerts.append(FEED_LOST)
    elif not prev.feed_ok and cur.feed_ok:
        alerts.append(FEED_RESTORED)

    if cur.feed_ok:
        if cur.in_view_hexes - prev.in_view_hexes:
            alerts.append(NEW_AIRCRAFT)
        if cur.selected_hex and cur.selected_hex != prev.selected_hex:
            alerts.append(NEW_BEST_CANDIDATE)
        if cur.interesting_hexes - prev.interesting_hexes:
            alerts.append(INTERESTING_AIRCRAFT)
    return alerts
