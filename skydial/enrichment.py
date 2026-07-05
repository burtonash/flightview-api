"""Phased, graceful enrichment. Impressive with none; richer with each phase.

Phase 2: offline airline-prefix mapping + aircraft-type → model (from the feed's
         ``t`` field).
Phase 3: cached route lookup via a pluggable provider, with a SQLite cache in
         front. The default provider is an offline static route table; swap in a
         live provider without touching callers. Every path degrades gracefully
         (never a hard dependency, never blocks the core).
"""

from __future__ import annotations

import abc
from typing import Callable, Optional

from .cache import SqliteCache
from .data.aircraft_types import model_for_type
from .data.airlines import airline_for_callsign
from .data.routes import route_for_callsign
from .models import Aircraft

# A route provider maps an Aircraft to {"origin", "destination", "model"} or None.
RouteProvider = Callable[[Aircraft], Optional[dict]]


class Enricher(abc.ABC):
    @abc.abstractmethod
    def enrich(self, ac: Aircraft) -> None:
        """Mutate ``ac`` in place, filling any fields it can. Must not raise."""


class AirlinePrefixEnricher(Enricher):
    def enrich(self, ac: Aircraft) -> None:
        if ac.airline is None:
            ac.airline = airline_for_callsign(ac.flight)


class AircraftTypeEnricher(Enricher):
    """Offline model name from the feed's ICAO type code."""

    def enrich(self, ac: Aircraft) -> None:
        if ac.model is None and ac.type_code:
            ac.model = model_for_type(ac.type_code)


def static_route_provider(ac: Aircraft) -> Optional[dict]:
    """Default offline provider: the static route table keyed by callsign."""
    return route_for_callsign(ac.flight)


_DEFAULT_PROVIDER = object()  # sentinel: "not passed" (use static) vs explicit None (disable)


class RouteEnricher(Enricher):
    """Cached route lookup: cache → provider → cache-store, all fail-soft."""

    def __init__(self, provider=_DEFAULT_PROVIDER, cache: Optional[SqliteCache] = None,
                 ttl_s: float = 86400.0):
        self.provider = static_route_provider if provider is _DEFAULT_PROVIDER else provider
        self.cache = cache
        self.ttl_s = ttl_s

    def enrich(self, ac: Aircraft) -> None:
        if self.provider is None or not ac.flight:
            return
        key = f"route:{ac.flight.strip().upper()}"
        info = None
        try:
            if self.cache is not None:
                info = self.cache.get(key)
            if info is None:
                info = self.provider(ac)
                if info is not None and self.cache is not None:
                    self.cache.set(key, info, self.ttl_s)
        except Exception:
            return
        if not info:
            return
        ac.origin = ac.origin or info.get("origin")
        ac.destination = ac.destination or info.get("destination")
        ac.model = ac.model or info.get("model")
        if ac.origin and ac.destination and not ac.route:
            ac.route = f"{ac.origin} → {ac.destination}"


class EnricherChain(Enricher):
    def __init__(self, enrichers: list[Enricher]):
        self.enrichers = enrichers

    def enrich(self, ac: Aircraft) -> None:
        for enr in self.enrichers:
            try:
                enr.enrich(ac)
            except Exception:
                continue


def build_enricher(cfg: dict) -> EnricherChain:
    """Assemble the enricher chain from config.

    Offline by default: airline prefix + type→model + static route table, with a
    SQLite cache in front of the route provider.
    """
    enr_cfg = cfg.get("enrichment", {})
    cache = None
    cache_path = enr_cfg.get("route_cache_path")
    if enr_cfg.get("route_cache_enabled", True) and cache_path:
        cache = SqliteCache(cache_path, float(enr_cfg.get("route_cache_ttl_s", 86400.0)))
    provider: Optional[RouteProvider] = static_route_provider if enr_cfg.get("static_routes", True) else None
    return EnricherChain(
        [
            AirlinePrefixEnricher(),
            AircraftTypeEnricher(),
            RouteEnricher(provider=provider, cache=cache,
                          ttl_s=float(enr_cfg.get("route_cache_ttl_s", 86400.0))),
        ]
    )


def default_chain() -> EnricherChain:
    """Zero-config offline chain (no route cache)."""
    return EnricherChain(
        [AirlinePrefixEnricher(), AircraftTypeEnricher(), RouteEnricher(provider=static_route_provider)]
    )
