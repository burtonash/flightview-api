import copy
import pathlib

import pytest

from skydial.config import DEFAULTS

REPO = pathlib.Path(__file__).resolve().parent.parent


@pytest.fixture
def demo_cfg():
    cfg = copy.deepcopy(DEFAULTS)
    cfg["source"] = {
        "type": "demo",
        "demo_frames": str(REPO / "sample_data" / "demo_frames.json"),
    }
    cfg["receiver"] = {"lat": 51.5074, "lon": -0.1278, "alt_m": 0.0}
    cfg["enrichment"] = {
        "static_routes": True,
        "route_cache_enabled": True,
        "route_cache_path": ":memory:",
        "route_cache_ttl_s": 3600.0,
    }
    return cfg
