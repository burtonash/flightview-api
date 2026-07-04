"""Phased, graceful enrichment. Impressive with none; richer with each phase.

Phase 2 (here): offline airline-prefix mapping.
Phase 3 (seam): cached route/model lookup — ``RouteModelEnricher`` is the hook;
it returns nothing until a provider is wired in, and must always degrade
gracefully (never a hard dependency, never blocks the core).
"""

from __future__ import annotations

import abc

from .data.airlines import airline_for_callsign
from .models import Aircraft


class Enricher(abc.ABC):
    @abc.abstractmethod
    def enrich(self, ac: Aircraft) -> None:
        """Mutate ``ac`` in place, filling any fields it can. Must not raise."""


class AirlinePrefixEnricher(Enricher):
    def enrich(self, ac: Aircraft) -> None:
        if ac.airline is None:
            ac.airline = airline_for_callsign(ac.flight)


class RouteModelEnricher(Enricher):
    """Seam for cached route/model lookup (SQLite-backed provider goes here).

    Ships as a no-op so there is zero external dependency by default. When a
    provider is added it should read/write the cache and fall back silently.
    """

    def __init__(self, provider=None):
        self.provider = provider

    def enrich(self, ac: Aircraft) -> None:
        if self.provider is None:
            return
        try:
            info = self.provider(ac)  # {origin, destination, model} or None
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


def default_chain() -> EnricherChain:
    return EnricherChain([AirlinePrefixEnricher(), RouteModelEnricher()])
