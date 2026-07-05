import pathlib

from skydial.sources import DemoSource
from skydial.sources.base import normalise_row

REPO = pathlib.Path(__file__).resolve().parent.parent
DEMO = str(REPO / "sample_data" / "demo_frames.json")


def test_normalise_readsb_variants():
    row = {
        "hex": "ABC123",
        "flight": "BAW117  ",
        "lat": 51.5,
        "lon": -0.1,
        "alt_baro": 10000,
        "gs": 300,
        "track": 90,
        "baro_rate": -500,
        "squawk": "6142",
        "seen": 0.5,
        "seen_pos": 0.6,
    }
    ac = normalise_row(row)
    assert ac.hex == "abc123"  # lowercased
    assert ac.flight == "BAW117"  # stripped
    assert ac.alt_ft == 10000
    assert ac.speed_kt == 300
    assert ac.track_deg == 90
    assert ac.vertical_rate_fpm == -500


def test_normalise_ground_altitude():
    ac = normalise_row({"hex": "abc", "alt_baro": "ground", "lat": 1, "lon": 2})
    assert ac.alt_ft == 0.0


def test_normalise_no_hex_returns_none():
    assert normalise_row({"flight": "NOPE", "lat": 1, "lon": 2}) is None


def test_demo_source_cycles():
    src = DemoSource(DEMO)
    r1 = src.fetch()
    r2 = src.fetch()
    assert r1.ok and r2.ok
    assert r1.rows and r2.rows
    assert r1.source_now != r2.source_now  # advanced to next frame


def test_demo_missing_file_no_crash():
    src = DemoSource("/does/not/exist.json")
    res = src.fetch()
    assert res.ok is False
    assert res.error
