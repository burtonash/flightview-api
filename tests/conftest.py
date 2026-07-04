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
    return cfg
