from skydial.alerts import interesting_reason
from skydial.config import DEFAULTS
from skydial.models import Aircraft

CFG = {"interesting": DEFAULTS["interesting"]}


def test_emergency_squawk():
    ac = Aircraft(hex="x", squawk="7700", alt_ft=30000, distance_km=20)
    assert "emergency" in interesting_reason(ac, CFG)


def test_helicopter():
    ac = Aircraft(hex="x", type_code="EC35", alt_ft=20000, distance_km=20)
    assert interesting_reason(ac, CFG) == "helicopter"


def test_low_and_close():
    ac = Aircraft(hex="x", alt_ft=1500, distance_km=5, type_code="A320")
    assert interesting_reason(ac, CFG) == "low and close"


def test_boring_airliner_not_interesting():
    ac = Aircraft(hex="x", alt_ft=35000, distance_km=30, type_code="A320", squawk="1000")
    assert interesting_reason(ac, CFG) is None
