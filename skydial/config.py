"""Configuration for the SkyDial Pi service.

Config resolution order (later wins):
  1. DEFAULTS below (safe, runnable out of the box against a demo feed).
  2. A YAML file — path from ``SKYDIAL_CONFIG`` env var, else ``./config.yaml``.
  3. A small set of environment-variable overrides (see ``_ENV_OVERRIDES``).

Everything user-tunable lives here or in the YAML — never buried as literals in
logic (per the project engineering defaults). See ``config.example.yaml``.
"""

from __future__ import annotations

import os
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

# --------------------------------------------------------------------------- #
# DEFAULTS — override via config.yaml rather than editing these.
# --------------------------------------------------------------------------- #
DEFAULTS: dict[str, Any] = {
    # Where the receiver is. REPLACE with your real coordinates.
    "receiver": {"lat": 51.5074, "lon": -0.1278, "alt_m": 0.0},
    # ADS-B source. type: dump1090 | demo
    #   dump1090 covers dump1090-fa / readsb / tar1090 (compatible aircraft.json).
    #   location may be a file path or an http(s) URL.
    "source": {
        "type": "dump1090",
        "location": "http://127.0.0.1:8080/data/aircraft.json",
        "timeout_s": 2.0,
        # demo source only:
        "demo_frames": "sample_data/demo_frames.json",
    },
    # Cache the raw source read for this long so many Dials don't hammer the decoder.
    "cache_ttl_s": 1.0,
    # Drop aircraft whose position is older than this (seconds).
    "max_position_age_s": 30.0,
    # Feed is considered lost if no successful fetch within this window (seconds).
    "feed_lost_after_s": 15.0,
    # Cap the aircraft array returned to the Dial.
    "max_candidates": 10,
    # Last-seen log size (entries kept for GET /m5/log).
    "log_size": 50,
    # Enrichment: offline by default. Cached route lookup sits in front of a
    # provider (default = static offline route table). No external dependency.
    "enrichment": {
        "static_routes": True,
        "route_cache_enabled": True,
        "route_cache_path": "skydial_cache.sqlite",
        "route_cache_ttl_s": 86400.0,
    },
    # What counts as an "interesting" aircraft (for interesting_reason + alerts).
    "interesting": {
        "low_alt_ft": 4000,
        "near_km": 8,
        "emergency_squawks": [7500, 7600, 7700],
    },
    # Scoring weights (0..1 factors, weighted then summed and scaled to 0..100).
    "scoring": {
        "freshness": 1.0,
        "window_alignment": 2.0,
        "elevation": 1.0,
        "distance": 1.5,
        "altitude_interest": 0.5,
        "vertical_rate": 0.5,
        # Distance (km) at which the distance factor decays to ~0.
        "distance_falloff_km": 40.0,
        # Altitude (ft) treated as "most visually interesting" peak.
        "altitude_interest_peak_ft": 10000.0,
    },
    # Which profile is active at boot; profiles are data, not code.
    "active_profile": "north_up",
    "profiles": [
        {
            "id": "north_up",
            "name": "North Up",
            "radar_up_deg": 0,
            "view_cone_deg": 360,
            "max_distance_km": 40,
            "min_elevation_deg": 0,
            "alert_enabled": True,
            "quiet_mode": False,
        }
    ],
    # HTTP server bind. Local network only by default (do not expose publicly).
    "server": {"host": "0.0.0.0", "port": 8090},
}

# env var -> (dotted config path, caster)
_ENV_OVERRIDES: dict[str, tuple[str, Any]] = {
    "SKYDIAL_RECEIVER_LAT": ("receiver.lat", float),
    "SKYDIAL_RECEIVER_LON": ("receiver.lon", float),
    "SKYDIAL_SOURCE_TYPE": ("source.type", str),
    "SKYDIAL_SOURCE_LOCATION": ("source.location", str),
    "SKYDIAL_ACTIVE_PROFILE": ("active_profile", str),
    "SKYDIAL_PORT": ("server.port", int),
    "SKYDIAL_HOST": ("server.host", str),
}


def _deep_merge(base: dict, override: dict) -> dict:
    out = deepcopy(base)
    for key, val in override.items():
        if isinstance(val, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], val)
        else:
            out[key] = deepcopy(val)
    return out


def _set_dotted(cfg: dict, path: str, value: Any) -> None:
    keys = path.split(".")
    node = cfg
    for key in keys[:-1]:
        node = node.setdefault(key, {})
    node[keys[-1]] = value


def load_config(path: str | os.PathLike[str] | None = None) -> dict[str, Any]:
    """Load merged configuration.

    Raises ``ConfigError`` if a supplied YAML path is unreadable or malformed;
    a *missing* default ``config.yaml`` is fine (we fall back to DEFAULTS).
    """
    cfg = deepcopy(DEFAULTS)

    yaml_path = Path(path) if path else Path(os.environ.get("SKYDIAL_CONFIG", "config.yaml"))
    explicit = path is not None or "SKYDIAL_CONFIG" in os.environ
    if yaml_path.exists():
        try:
            loaded = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError) as exc:
            raise ConfigError(f"Could not read config {yaml_path}: {exc}") from exc
        if not isinstance(loaded, dict):
            raise ConfigError(f"Config {yaml_path} must be a mapping, got {type(loaded).__name__}")
        cfg = _deep_merge(cfg, loaded)
    elif explicit:
        raise ConfigError(f"Config file not found: {yaml_path}")

    for env_key, (dotted, caster) in _ENV_OVERRIDES.items():
        if env_key in os.environ:
            try:
                _set_dotted(cfg, dotted, caster(os.environ[env_key]))
            except (TypeError, ValueError) as exc:
                raise ConfigError(f"Bad value for {env_key}: {exc}") from exc

    return cfg


class ConfigError(Exception):
    """Raised when configuration is present but invalid."""
