"""ICAO airline (telephony) prefix → operator name. Offline, extend freely.

The 3-letter prefix of an ADS-B callsign identifies the operator (e.g. ``EZY82K``
→ ``EZY`` → easyJet). This is a starter set of common operators; it is not
exhaustive and never a dependency — unknown prefixes just leave ``airline`` unset.
"""

from __future__ import annotations

AIRLINE_PREFIXES: dict[str, str] = {
    "BAW": "British Airways",
    "EZY": "easyJet",
    "EJU": "easyJet Europe",
    "RYR": "Ryanair",
    "RUK": "Ryanair UK",
    "TOM": "TUI Airways",
    "EXS": "Jet2",
    "VIR": "Virgin Atlantic",
    "DLH": "Lufthansa",
    "AFR": "Air France",
    "KLM": "KLM",
    "IBE": "Iberia",
    "VLG": "Vueling",
    "SWR": "Swiss",
    "AUA": "Austrian",
    "TAP": "TAP Air Portugal",
    "SAS": "SAS",
    "FIN": "Finnair",
    "NAX": "Norwegian",
    "WZZ": "Wizz Air",
    "WUK": "Wizz Air UK",
    "AAL": "American Airlines",
    "UAL": "United Airlines",
    "DAL": "Delta Air Lines",
    "ACA": "Air Canada",
    "UAE": "Emirates",
    "QTR": "Qatar Airways",
    "ETD": "Etihad",
    "THY": "Turkish Airlines",
    "SIA": "Singapore Airlines",
    "QFA": "Qantas",
    "ANA": "All Nippon Airways",
    "JAL": "Japan Airlines",
    "CPA": "Cathay Pacific",
    "UPS": "UPS Airlines",
    "FDX": "FedEx Express",
    "DHK": "DHL Air UK",
    "BCS": "DHL (European Air Transport)",
    "NPT": "West Atlantic UK",
    "CFE": "BA CityFlyer",
    "LOG": "Loganair",
    "EIN": "Aer Lingus",
    "ELY": "El Al",
    "ICE": "Icelandair",
    "AEE": "Aegean",
    "ROT": "TAROM",
    "LOT": "LOT Polish Airlines",
    "CSA": "Czech Airlines",
    "AFL": "Aeroflot",
    "GFA": "Gulf Air",
    "MSR": "EgyptAir",
    "RAM": "Royal Air Maroc",
    "ETH": "Ethiopian Airlines",
    "KQA": "Kenya Airways",
    "SAA": "South African Airways",
    "AIC": "Air India",
    "AXB": "Air India Express",
}


def airline_for_callsign(flight: str | None) -> str | None:
    """Map a callsign to an operator name via its 3-letter ICAO prefix."""
    if not flight:
        return None
    prefix = flight.strip()[:3].upper()
    return AIRLINE_PREFIXES.get(prefix)
