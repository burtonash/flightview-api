"""Best-visible candidate scoring — a config-weighted strategy, not a hard-code.

``score_aircraft`` is a pure function of a canonical ``Aircraft`` + ``Profile`` +
weights. Each factor is normalised 0..1, weighted, summed and scaled to 0..100.
Tune the weights in config (and via the debug UI) — never edit this to re-tune.
"""

from __future__ import annotations

from .geo import angular_diff
from .models import Aircraft, Profile

FACTORS = (
    "freshness",
    "window_alignment",
    "elevation",
    "distance",
    "altitude_interest",
    "vertical_rate",
)

_REASONS = {
    "window_alignment": "straight ahead",
    "distance": "close",
    "elevation": "high overhead",
    "altitude_interest": "at eye-catching altitude",
    "vertical_rate": "climbing/descending",
    "freshness": "freshly seen",
}


def _clamp01(x: float) -> float:
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def compute_factors(
    ac: Aircraft, profile: Profile, scoring_cfg: dict, max_position_age_s: float
) -> dict[str, float]:
    """The six normalised 0..1 factors for one aircraft."""
    # freshness — decays with position age
    age = ac.seen_pos if ac.seen_pos is not None else (ac.seen or 0.0)
    freshness = _clamp01(1.0 - (age / max_position_age_s)) if max_position_age_s > 0 else 1.0

    # window alignment — 1 dead ahead, 0 at the cone edge (or beyond)
    if profile.view_cone_deg >= 360 or ac.bearing_deg is None:
        window_alignment = 1.0 if ac.bearing_deg is not None else 0.0
    else:
        half = max(profile.view_cone_deg / 2.0, 1e-6)
        window_alignment = _clamp01(1.0 - angular_diff(ac.bearing_deg, profile.radar_up_deg) / half)

    # elevation — higher above the horizon is more visually obvious
    elevation = _clamp01((ac.elevation_deg or 0.0) / 90.0)

    # distance — nearer is better, linear falloff
    falloff = max(float(scoring_cfg.get("distance_falloff_km", 40.0)), 1e-6)
    distance = _clamp01(1.0 - (ac.distance_km or falloff) / falloff)

    # altitude interest — peaks at a "most interesting" altitude
    peak = max(float(scoring_cfg.get("altitude_interest_peak_ft", 10000.0)), 1.0)
    altitude_interest = _clamp01(1.0 - abs((ac.alt_ft or 0.0) - peak) / peak)

    # vertical rate — movement is more interesting than level flight
    vertical_rate = _clamp01(abs(ac.vertical_rate_fpm or 0.0) / 1000.0)

    return {
        "freshness": freshness,
        "window_alignment": window_alignment,
        "elevation": elevation,
        "distance": distance,
        "altitude_interest": altitude_interest,
        "vertical_rate": vertical_rate,
    }


def score_aircraft(
    ac: Aircraft, profile: Profile, scoring_cfg: dict, max_position_age_s: float
) -> tuple[float, dict[str, float]]:
    """Return (score 0..100, raw factor dict)."""
    factors = compute_factors(ac, profile, scoring_cfg, max_position_age_s)
    total_w = sum(max(float(scoring_cfg.get(f, 0.0)), 0.0) for f in FACTORS)
    if total_w <= 0:
        return 0.0, factors
    weighted = sum(float(scoring_cfg.get(f, 0.0)) * factors[f] for f in FACTORS)
    return round(100.0 * weighted / total_w, 1), factors


def reason_for(factors: dict[str, float], scoring_cfg: dict) -> str:
    """A short 'why selected' phrase from the dominant weighted factor(s)."""
    contributions = {
        f: float(scoring_cfg.get(f, 0.0)) * factors.get(f, 0.0) for f in FACTORS
    }
    ranked = sorted(contributions, key=contributions.get, reverse=True)
    top = [f for f in ranked if contributions[f] > 0][:2]
    if not top:
        return "only candidate"
    return " and ".join(_REASONS[f] for f in top)
