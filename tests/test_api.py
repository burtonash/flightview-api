from fastapi.testclient import TestClient

from skydial.app import create_app


def _client(demo_cfg):
    return TestClient(create_app(demo_cfg))


def test_sky_endpoint(demo_cfg):
    c = _client(demo_cfg)
    j = c.get("/m5/sky").json()
    assert j["ok"] is True
    assert "aircraft" in j
    assert j["selected"] == 0


def test_status_endpoint(demo_cfg):
    c = _client(demo_cfg)
    c.get("/m5/sky")
    j = c.get("/m5/status").json()
    assert j["ok"] is True
    assert j["feed_ok"] is True


def test_profiles_and_switch(demo_cfg):
    demo_cfg["profiles"] = [
        {"id": "north_up", "name": "North Up", "radar_up_deg": 0, "view_cone_deg": 360,
         "max_distance_km": 40, "min_elevation_deg": 0},
        {"id": "kitchen", "name": "Kitchen", "radar_up_deg": 270, "view_cone_deg": 100,
         "max_distance_km": 30, "min_elevation_deg": 5},
    ]
    c = _client(demo_cfg)
    profs = c.get("/m5/profiles").json()
    assert {p["id"] for p in profs["profiles"]} == {"north_up", "kitchen"}

    r = c.post("/m5/profile", json={"id": "kitchen"})
    assert r.status_code == 200
    assert r.json()["active"] == "kitchen"
    assert c.get("/m5/profiles").json()["active"] == "kitchen"


def test_unknown_profile_404(demo_cfg):
    c = _client(demo_cfg)
    assert c.post("/m5/profile", json={"id": "nope"}).status_code == 404
    assert c.get("/m5/sky?profile=nope").status_code == 404


def test_debug_ui_served(demo_cfg):
    c = _client(demo_cfg)
    html = c.get("/").text
    assert "SkyDial" in html
    assert "<canvas" in html
