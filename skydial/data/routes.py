"""Tiny offline route table keyed by callsign — the default route provider.

Real route data needs an external source; this offline stub gives the demo (and
any known regular flights you add) a genuine origin→destination without any
network dependency. Extend it, or wire a live provider in ``enrichment.py`` and
let the SQLite cache sit in front of it. Airports are IATA codes.
"""

from __future__ import annotations

# callsign -> (origin, destination)
ROUTES: dict[str, tuple[str, str]] = {
    "EZY82K": ("LTN", "PMI"),
    "BAW117": ("LHR", "BCN"),
    "DLH4AB": ("FRA", "LHR"),
    "RYR1AB": ("STN", "DUB"),
}


def route_for_callsign(flight: str | None) -> dict | None:
    """Return {'origin', 'destination'} for a known callsign, else None."""
    if not flight:
        return None
    hit = ROUTES.get(flight.strip().upper())
    if not hit:
        return None
    return {"origin": hit[0], "destination": hit[1]}
