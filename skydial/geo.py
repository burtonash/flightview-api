"""Pure geometry helpers. The Pi owns all of this so the Dial stays dumb.

All angles in degrees, distances in km, altitudes in feet unless noted.
"""

from __future__ import annotations

import math

EARTH_RADIUS_KM = 6371.0088
_FT_PER_KM = 3280.84

_COMPASS_16 = [
    "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
]
# Arrows in 45° steps starting at North (up).
_ARROWS_8 = ["↑", "↗", "→", "↘", "↓", "↙", "←", "↖"]


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two lat/lon points, in km."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(a)))


def bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Initial true compass bearing from point 1 to point 2, 0..360 (0 = N)."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlmb = math.radians(lon2 - lon1)
    y = math.sin(dlmb) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dlmb)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


def compass_label(bearing: float) -> str:
    """16-point compass label for a bearing."""
    idx = int((bearing % 360.0) / 22.5 + 0.5) % 16
    return _COMPASS_16[idx]


def track_arrow(track: float | None) -> str | None:
    """Unicode arrow for a ground track (heading of travel)."""
    if track is None:
        return None
    idx = int((track % 360.0) / 45.0 + 0.5) % 8
    return _ARROWS_8[idx]


def elevation_deg(distance_km: float, alt_ft: float | None, receiver_alt_m: float = 0.0) -> float | None:
    """Angle above the horizon of an aircraft at ``distance_km`` slant-ground.

    Ignores Earth curvature (fine at these ranges). Returns None without altitude.
    """
    if alt_ft is None:
        return None
    height_km = (alt_ft / _FT_PER_KM) - (receiver_alt_m / 1000.0)
    if distance_km <= 0:
        return 90.0 if height_km > 0 else 0.0
    return math.degrees(math.atan2(height_km, distance_km))


def screen_angle_deg(bearing: float, radar_up_deg: float) -> float:
    """Bearing rotated into the Dial's frame: 0 = top of the ring."""
    return (bearing - radar_up_deg) % 360.0


def angular_diff(a: float, b: float) -> float:
    """Smallest absolute difference between two bearings, 0..180."""
    d = abs((a - b) % 360.0)
    return min(d, 360.0 - d)


def vertical_label(vertical_rate_fpm: float | None, level_threshold: float = 100.0) -> str | None:
    """climbing / descending / level from a vertical rate (fpm)."""
    if vertical_rate_fpm is None:
        return None
    if vertical_rate_fpm > level_threshold:
        return "climbing"
    if vertical_rate_fpm < -level_threshold:
        return "descending"
    return "level"
