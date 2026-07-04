"""Candidate filtering: staleness and window-cone visibility."""

from __future__ import annotations

from .geo import angular_diff
from .models import Aircraft, Profile


def is_fresh(ac: Aircraft, max_position_age_s: float) -> bool:
    """True if the aircraft's position is recent enough to trust."""
    age = ac.seen_pos if ac.seen_pos is not None else ac.seen
    if age is None:
        return True  # decoder didn't tell us; assume current
    return age <= max_position_age_s


def in_window(ac: Aircraft, profile: Profile) -> bool:
    """True if the aircraft is plausibly visible out of this window.

    Requires precomputed ``bearing_deg``/``distance_km``/``elevation_deg``.
    """
    if ac.distance_km is None or ac.distance_km > profile.max_distance_km:
        return False
    if ac.elevation_deg is not None and ac.elevation_deg < profile.min_elevation_deg:
        return False
    if profile.view_cone_deg < 360:
        if ac.bearing_deg is None:
            return False
        if angular_diff(ac.bearing_deg, profile.radar_up_deg) > profile.view_cone_deg / 2.0:
            return False
    return True
