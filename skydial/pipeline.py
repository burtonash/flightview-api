"""The orchestrator: fetch → normalise → compute → filter → score → enrich →
select → derive alerts → build the response. Never throws to the caller; always
resolves to a machine-readable state so the poll loop can't crash the Dial.
"""

from __future__ import annotations

import time
from collections import OrderedDict
from typing import Optional

from . import __version__, geo
from .alerts import Snapshot, derive_alerts, interesting_reason
from .enrichment import Enricher, build_enricher
from .filters import in_window, is_fresh
from .models import (
    STATE_ACTIVE,
    STATE_CONNECTING,
    STATE_FEED_LOST,
    STATE_QUIET_SKY,
    Aircraft,
    Profile,
    Sighting,
    SkyResponse,
    StatusResponse,
)
from .profiles import ProfileStore
from .scoring import reason_for, score_aircraft
from .sources import SkySource, build_source


class SkyPipeline:
    def __init__(self, cfg: dict, source: SkySource | None = None, enricher: Enricher | None = None):
        self.cfg = cfg
        self.receiver = cfg["receiver"]
        self.source = source or build_source(cfg)
        self.profiles = ProfileStore.from_config(cfg)
        self.enricher = enricher or build_enricher(cfg)
        self.scoring_cfg = cfg["scoring"]
        self.max_age = float(cfg["max_position_age_s"])
        self.max_candidates = int(cfg["max_candidates"])
        self.cache_ttl = float(cfg["cache_ttl_s"])
        self.feed_lost_after = float(cfg["feed_lost_after_s"])
        self.log_size = int(cfg.get("log_size", 50))

        self._cache_result = None
        self._cache_ts = 0.0
        self._last_fetch_ts: Optional[float] = None
        self._last_success_ts: Optional[float] = None
        self._raw_count = 0
        self._last_filtered_count = 0
        self._last_aircraft_count = 0
        self._prev_snapshots: dict[str, Snapshot] = {}
        # last-seen log: hex -> Sighting, most-recent last
        self._log: "OrderedDict[str, Sighting]" = OrderedDict()

    # --- fetching -------------------------------------------------------- #
    def _fetch_cached(self, now: float):
        if self._cache_result is not None and (now - self._cache_ts) < self.cache_ttl:
            return self._cache_result
        result = self.source.fetch()
        self._cache_result = result
        self._cache_ts = now
        self._last_fetch_ts = now
        if result.ok:
            self._last_success_ts = now
            self._raw_count = len(result.rows)
        return result

    def _feed_ok(self, now: float) -> bool:
        if self._last_success_ts is None:
            return False
        return (now - self._last_success_ts) <= self.feed_lost_after

    # --- geometry -------------------------------------------------------- #
    def _compute(self, result, profile: Profile) -> list[Aircraft]:
        out: list[Aircraft] = []
        rlat, rlon = self.receiver["lat"], self.receiver["lon"]
        ralt = self.receiver.get("alt_m", 0.0)
        for ac in self.source.normalise(result):
            if not ac.has_position:
                continue
            dist = geo.haversine_km(rlat, rlon, ac.lat, ac.lon)
            brg = geo.bearing_deg(rlat, rlon, ac.lat, ac.lon)
            ac.distance_km = round(dist, 2)
            ac.bearing_deg = round(brg, 1)
            ac.bearing_label = geo.compass_label(brg)
            ac.screen_angle_deg = round(geo.screen_angle_deg(brg, profile.radar_up_deg), 1)
            elev = geo.elevation_deg(dist, ac.alt_ft, ralt)
            ac.elevation_deg = round(elev, 1) if elev is not None else None
            ac.track_arrow = geo.track_arrow(ac.track_deg)
            ac.vertical_label = geo.vertical_label(ac.vertical_rate_fpm)
            out.append(ac)
        return out

    # --- the main tick --------------------------------------------------- #
    def sky(self, profile_id: str | None = None) -> SkyResponse:
        now = time.time()
        profile = self.profiles.get(profile_id) if profile_id else self.profiles.active

        result = self._fetch_cached(now)
        feed_ok = self._feed_ok(now)

        computed = self._compute(result, profile) if result.ok else []
        fresh = [a for a in computed if is_fresh(a, self.max_age)]
        visible = [a for a in fresh if in_window(a, profile)]

        for ac in visible:
            ac.score, ac.score_factors = score_aircraft(
                ac, profile, self.scoring_cfg, self.max_age
            )
        visible.sort(key=lambda a: (-(a.score or 0.0), a.distance_km or 1e9))
        candidates = visible[: self.max_candidates]

        for ac in candidates:
            self.enricher.enrich(ac)
            ac.interesting_reason = interesting_reason(ac, self.cfg)
        selected = 0 if candidates else None
        if selected is not None:
            top = candidates[0]
            top.selected_reason = reason_for(top.score_factors or {}, self.scoring_cfg)

        self._record_sightings(candidates, int(now))
        interesting_hexes = {a.hex for a in candidates if a.interesting_reason}

        # state
        if self._last_success_ts is None:
            state = STATE_CONNECTING
        elif not feed_ok:
            state = STATE_FEED_LOST
        elif not candidates:
            state = STATE_QUIET_SKY
        else:
            state = STATE_ACTIVE

        # alerts
        cur_snap = Snapshot(
            feed_ok=feed_ok,
            in_view_hexes={a.hex for a in visible},
            selected_hex=candidates[0].hex if candidates else None,
            interesting_hexes=interesting_hexes,
        )
        alerts = derive_alerts(self._prev_snapshots.get(profile.id), cur_snap, profile)
        self._prev_snapshots[profile.id] = cur_snap

        self._last_filtered_count = len(visible)
        self._last_aircraft_count = len(candidates)

        return SkyResponse(
            ok=True,
            now=int(now),
            state=state,
            profile=profile,
            selected=selected,
            aircraft=candidates,
            alerts=alerts,
        )

    # --- last-seen log --------------------------------------------------- #
    def _record_sightings(self, candidates: list[Aircraft], now: int) -> None:
        for ac in candidates:
            self._log.pop(ac.hex, None)  # move-to-end on re-sighting
            self._log[ac.hex] = Sighting(
                hex=ac.hex,
                flight=ac.flight,
                airline=ac.airline,
                model=ac.model,
                bearing_label=ac.bearing_label,
                distance_km=ac.distance_km,
                alt_ft=ac.alt_ft,
                last_seen_ts=now,
            )
        while len(self._log) > self.log_size:
            self._log.popitem(last=False)

    def recent_log(self, limit: int = 20) -> list[Sighting]:
        """Most-recent sightings first."""
        items = list(self._log.values())[::-1]
        return items[: max(0, limit)]

    def status(self) -> StatusResponse:
        now = time.time()
        feed_ok = self._feed_ok(now)
        if self._last_success_ts is None:
            state = STATE_CONNECTING
        elif not feed_ok:
            state = STATE_FEED_LOST
        else:
            state = STATE_ACTIVE
        age = (now - self._last_fetch_ts) if self._last_fetch_ts else None
        return StatusResponse(
            ok=True,
            now=int(now),
            state=state,
            version=__version__,
            active_profile=self.profiles.active.id,
            feed_ok=feed_ok,
            last_fetch_ts=int(self._last_fetch_ts) if self._last_fetch_ts else None,
            last_fetch_age_s=round(age, 2) if age is not None else None,
            raw_count=self._raw_count,
            filtered_count=self._last_filtered_count,
            aircraft_count=self._last_aircraft_count,
            source=self.source.describe,
        )
