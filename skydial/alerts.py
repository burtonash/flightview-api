"""Alert-state derivation: discrete transitions only, so nothing fires every refresh.

The Pi decides *what* happened (new aircraft, new best pick, feed lost/restored);
the Dial owns the actual sound. Quiet-mode / alerts-disabled suppress here.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import Profile

# Event names the Dial maps to sounds (PRD → Alerts).
NEW_AIRCRAFT = "new_aircraft"
NEW_BEST_CANDIDATE = "new_best_candidate"
FEED_LOST = "feed_lost"
FEED_RESTORED = "feed_restored"


@dataclass
class Snapshot:
    feed_ok: bool = False
    in_view_hexes: set[str] = field(default_factory=set)
    selected_hex: str | None = None


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
    return alerts
