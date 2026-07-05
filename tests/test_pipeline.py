from skydial.models import STATE_ACTIVE
from skydial.pipeline import SkyPipeline


def test_sky_returns_scored_candidates(demo_cfg):
    pipe = SkyPipeline(demo_cfg)
    resp = pipe.sky()
    assert resp.ok
    assert resp.state == STATE_ACTIVE
    assert resp.selected == 0
    assert resp.aircraft
    # ordered by score descending
    scores = [a.score for a in resp.aircraft]
    assert scores == sorted(scores, reverse=True)
    # selected carries a reason
    assert resp.aircraft[0].selected_reason


def test_stale_aircraft_excluded(demo_cfg):
    pipe = SkyPipeline(demo_cfg)
    resp = pipe.sky()
    hexes = {a.hex for a in resp.aircraft}
    assert "51ab00" not in hexes  # STALE99, seen 40s > 30s threshold


def test_enrichment_airline(demo_cfg):
    pipe = SkyPipeline(demo_cfg)
    resp = pipe.sky()
    by_hex = {a.hex: a for a in resp.aircraft}
    assert by_hex["400a1b"].airline == "British Airways"  # BAW117
    assert by_hex["407f35"].airline == "easyJet"  # EZY82K


def test_route_and_model_enriched(demo_cfg):
    pipe = SkyPipeline(demo_cfg)
    resp = pipe.sky()
    by_hex = {a.hex: a for a in resp.aircraft}
    ezy = by_hex["407f35"]
    assert ezy.model == "Airbus A320neo"  # from type code A20N
    assert ezy.route == "LTN → PMI"  # from static route table
    assert ezy.registration == "G-UZHA"


def test_interesting_helicopter_flagged(demo_cfg):
    pipe = SkyPipeline(demo_cfg)
    resp = pipe.sky()
    by_hex = {a.hex: a for a in resp.aircraft}
    assert by_hex["43c2e9"].interesting_reason == "helicopter"  # GXTRA / EC35


def test_last_seen_log(demo_cfg):
    pipe = SkyPipeline(demo_cfg)
    pipe.sky()
    log = pipe.recent_log(limit=10)
    assert log
    assert all(s.last_seen_ts > 0 for s in log)
    hexes = {s.hex for s in log}
    assert "407f35" in hexes


def test_status_reports_feed_ok(demo_cfg):
    pipe = SkyPipeline(demo_cfg)
    pipe.sky()
    st = pipe.status()
    assert st.ok
    assert st.feed_ok
    assert st.raw_count >= 1
    assert st.aircraft_count >= 1


def test_cone_filtering_changes_visibility(demo_cfg):
    # north_up (360 cone) sees the eastbound DLH; a narrow north window shouldn't.
    demo_cfg["profiles"] = [
        {"id": "north_up", "name": "North Up", "radar_up_deg": 0, "view_cone_deg": 360,
         "max_distance_km": 40, "min_elevation_deg": 0},
        {"id": "narrow_n", "name": "Narrow North", "radar_up_deg": 0, "view_cone_deg": 60,
         "max_distance_km": 40, "min_elevation_deg": 0},
    ]
    pipe = SkyPipeline(demo_cfg)
    wide = {a.hex for a in pipe.sky(profile_id="north_up").aircraft}
    narrow = {a.hex for a in pipe.sky(profile_id="narrow_n").aircraft}
    assert "3c6dd2" in wide  # DLH to the east
    assert "3c6dd2" not in narrow
