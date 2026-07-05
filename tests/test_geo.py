import math

from skydial import geo


def test_distance_zero():
    assert geo.haversine_km(51.5, -0.1, 51.5, -0.1) == 0.0


def test_distance_known():
    # ~111 km per degree of latitude near the equator
    d = geo.haversine_km(0, 0, 1, 0)
    assert 110 < d < 112


def test_bearing_cardinals():
    assert geo.bearing_deg(0, 0, 1, 0) == 0.0  # due north
    assert abs(geo.bearing_deg(0, 0, 0, 1) - 90) < 1e-6  # due east


def test_compass_label():
    assert geo.compass_label(0) == "N"
    assert geo.compass_label(90) == "E"
    assert geo.compass_label(45) == "NE"
    assert geo.compass_label(200) == "SSW"


def test_screen_angle_wraps():
    assert geo.screen_angle_deg(10, 270) == 100.0
    assert geo.screen_angle_deg(0, 0) == 0.0


def test_elevation_45deg():
    # 1 km up at 1 km ground range -> 45°
    elev = geo.elevation_deg(1.0, 3280.84, 0.0)
    assert abs(elev - 45.0) < 0.5


def test_elevation_none_without_alt():
    assert geo.elevation_deg(5.0, None) is None


def test_track_arrow():
    assert geo.track_arrow(0) == "↑"
    assert geo.track_arrow(90) == "→"
    assert geo.track_arrow(None) is None


def test_vertical_label():
    assert geo.vertical_label(900) == "climbing"
    assert geo.vertical_label(-900) == "descending"
    assert geo.vertical_label(0) == "level"
    assert geo.vertical_label(None) is None


def test_angular_diff():
    assert geo.angular_diff(350, 10) == 20
    assert geo.angular_diff(0, 180) == 180
