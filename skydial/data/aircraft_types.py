"""ICAO aircraft type designator → friendly model name. Offline, extend freely.

readsb/tar1090 ``aircraft.json`` carries a ``t`` field (ICAO type code, e.g.
``A20N``). This maps it to a human name (``Airbus A320neo``). Not exhaustive;
unknown codes simply leave ``model`` unset.
"""

from __future__ import annotations

AIRCRAFT_TYPES: dict[str, str] = {
    # Airbus narrowbody
    "A318": "Airbus A318",
    "A319": "Airbus A319",
    "A320": "Airbus A320",
    "A321": "Airbus A321",
    "A19N": "Airbus A319neo",
    "A20N": "Airbus A320neo",
    "A21N": "Airbus A321neo",
    # Airbus widebody
    "A306": "Airbus A300-600",
    "A310": "Airbus A310",
    "A332": "Airbus A330-200",
    "A333": "Airbus A330-300",
    "A338": "Airbus A330-800neo",
    "A339": "Airbus A330-900neo",
    "A342": "Airbus A340-200",
    "A343": "Airbus A340-300",
    "A345": "Airbus A340-500",
    "A346": "Airbus A340-600",
    "A359": "Airbus A350-900",
    "A35K": "Airbus A350-1000",
    "A388": "Airbus A380-800",
    # Boeing 737
    "B733": "Boeing 737-300",
    "B734": "Boeing 737-400",
    "B735": "Boeing 737-500",
    "B736": "Boeing 737-600",
    "B737": "Boeing 737-700",
    "B738": "Boeing 737-800",
    "B739": "Boeing 737-900",
    "B37M": "Boeing 737 MAX 7",
    "B38M": "Boeing 737 MAX 8",
    "B39M": "Boeing 737 MAX 9",
    "B3XM": "Boeing 737 MAX 10",
    # Boeing widebody
    "B742": "Boeing 747-200",
    "B744": "Boeing 747-400",
    "B748": "Boeing 747-8",
    "B752": "Boeing 757-200",
    "B753": "Boeing 757-300",
    "B762": "Boeing 767-200",
    "B763": "Boeing 767-300",
    "B764": "Boeing 767-400",
    "B772": "Boeing 777-200",
    "B77L": "Boeing 777-200LR",
    "B773": "Boeing 777-300",
    "B77W": "Boeing 777-300ER",
    "B788": "Boeing 787-8 Dreamliner",
    "B789": "Boeing 787-9 Dreamliner",
    "B78X": "Boeing 787-10 Dreamliner",
    # Embraer / regional
    "E170": "Embraer E170",
    "E75L": "Embraer E175",
    "E75S": "Embraer E175",
    "E190": "Embraer E190",
    "E195": "Embraer E195",
    "E290": "Embraer E190-E2",
    "E295": "Embraer E195-E2",
    "AT72": "ATR 72",
    "AT76": "ATR 72-600",
    "AT45": "ATR 42",
    "DH8D": "Bombardier Dash 8 Q400",
    "CRJ2": "Bombardier CRJ200",
    "CRJ7": "Bombardier CRJ700",
    "CRJ9": "Bombardier CRJ900",
    "BCS1": "Airbus A220-100",
    "BCS3": "Airbus A220-300",
    # GA / rotary / other
    "C172": "Cessna 172",
    "C25A": "Cessna Citation",
    "PC12": "Pilatus PC-12",
    "SR22": "Cirrus SR22",
    "EC35": "Airbus H135 (helicopter)",
    "EC45": "Airbus H145 (helicopter)",
    "A139": "AgustaWestland AW139 (helicopter)",
    "R44": "Robinson R44 (helicopter)",
    "H500": "MD 500 (helicopter)",
}

# Type prefixes that indicate a rotorcraft (for "interesting"/silhouette hints).
HELICOPTER_PREFIXES = ("EC", "H", "R44", "R22", "A109", "A139", "S76", "B06", "B47")


def model_for_type(type_code: str | None) -> str | None:
    """Friendly model name for an ICAO type designator."""
    if not type_code:
        return None
    return AIRCRAFT_TYPES.get(type_code.strip().upper())


def is_rotorcraft(type_code: str | None) -> bool:
    if not type_code:
        return False
    code = type_code.strip().upper()
    return code.startswith(HELICOPTER_PREFIXES)
