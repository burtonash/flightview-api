from skydial.cache import SqliteCache
from skydial.enrichment import (
    AircraftTypeEnricher,
    AirlinePrefixEnricher,
    RouteEnricher,
    build_enricher,
)
from skydial.models import Aircraft


def test_airline_prefix():
    ac = Aircraft(hex="x", flight="EZY82K")
    AirlinePrefixEnricher().enrich(ac)
    assert ac.airline == "easyJet"


def test_type_to_model():
    ac = Aircraft(hex="x", type_code="A20N")
    AircraftTypeEnricher().enrich(ac)
    assert ac.model == "Airbus A320neo"


def test_route_enricher_builds_route():
    ac = Aircraft(hex="x", flight="EZY82K")
    RouteEnricher().enrich(ac)  # default static provider
    assert ac.origin == "LTN"
    assert ac.destination == "PMI"
    assert ac.route == "LTN → PMI"


def test_route_enricher_unknown_callsign_noop():
    ac = Aircraft(hex="x", flight="ZZZ999")
    RouteEnricher().enrich(ac)
    assert ac.route is None


def test_cache_hit_avoids_second_provider_call():
    calls = {"n": 0}

    def provider(ac):
        calls["n"] += 1
        return {"origin": "AAA", "destination": "BBB"}

    cache = SqliteCache(":memory:")
    enr = RouteEnricher(provider=provider, cache=cache)
    a1 = Aircraft(hex="1", flight="TEST1")
    a2 = Aircraft(hex="2", flight="TEST1")  # same callsign -> cache hit
    enr.enrich(a1)
    enr.enrich(a2)
    assert calls["n"] == 1
    assert a2.route == "AAA → BBB"


def test_cache_ttl_expiry():
    cache = SqliteCache(":memory:", default_ttl_s=1.0)
    cache.set("k", {"v": 1}, ttl_s=-1)  # already expired
    assert cache.get("k") is None


def test_build_enricher_full_chain():
    chain = build_enricher({"enrichment": {"route_cache_path": ":memory:"}})
    ac = Aircraft(hex="x", flight="BAW117", type_code="A21N")
    chain.enrich(ac)
    assert ac.airline == "British Airways"
    assert ac.model == "Airbus A321neo"
    assert ac.route == "LHR → BCN"
