from skydial.config import DEFAULTS
from skydial.filters import in_window
from skydial.models import Aircraft, Profile
from skydial.scoring import score_aircraft

SCORING = DEFAULTS["scoring"]


def _ac(**kw):
    base = dict(hex="x", lat=51.6, lon=-0.1, seen_pos=0.5)
    base.update(kw)
    return Aircraft(**base)


def test_factors_bounded():
    ac = _ac(bearing_deg=0, distance_km=5, elevation_deg=30, alt_ft=10000, vertical_rate_fpm=900)
    profile = Profile(id="p", name="p", radar_up_deg=0, view_cone_deg=360)
    score, factors = score_aircraft(ac, profile, SCORING, 30.0)
    assert 0 <= score <= 100
    for v in factors.values():
        assert 0.0 <= v <= 1.0


def test_alignment_prefers_ahead():
    profile = Profile(id="p", name="p", radar_up_deg=0, view_cone_deg=100)
    ahead = _ac(bearing_deg=0, distance_km=7, elevation_deg=20, alt_ft=9000)
    edge = _ac(bearing_deg=45, distance_km=7, elevation_deg=20, alt_ft=9000)
    s_ahead, _ = score_aircraft(ahead, profile, SCORING, 30.0)
    s_edge, _ = score_aircraft(edge, profile, SCORING, 30.0)
    assert s_ahead > s_edge


def test_best_visible_beats_nearer_but_behind():
    # A jet ahead (in cone) should beat a nearer aircraft behind (out of cone).
    profile = Profile(id="p", name="p", radar_up_deg=0, view_cone_deg=100, max_distance_km=40)
    jet = _ac(bearing_deg=5, distance_km=7, elevation_deg=15, alt_ft=8000)
    heli = _ac(bearing_deg=180, distance_km=2, elevation_deg=8, alt_ft=1200)
    assert in_window(jet, profile) is True
    assert in_window(heli, profile) is False  # behind the window


def test_stale_freshness_low():
    fresh = _ac(bearing_deg=0, distance_km=5, seen_pos=0.5)
    stale = _ac(bearing_deg=0, distance_km=5, seen_pos=25.0)
    profile = Profile(id="p", name="p", radar_up_deg=0, view_cone_deg=360)
    _, ff = score_aircraft(fresh, profile, SCORING, 30.0)
    _, sf = score_aircraft(stale, profile, SCORING, 30.0)
    assert ff["freshness"] > sf["freshness"]
