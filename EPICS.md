# EPICS — SkyDial (flightview-api, the Pi back-end)

> The plan: epics → stories, story-pointed, in **MTP → MVP → MSP → MLP** tiers derived **directly
> from the STORYMAP release slices** (Walking Skeleton = MTP, R2 = MVP, R3 = MSP, ribs = MLP). Every
> tier is a **thin slice across the whole backbone**, never one activity built fully before the next.
> Re-evaluate before starting an epic and after finishing each one. Points are Fibonacci at the story
> level. Commit after every story (atomic, conventional-commit). **Stop between epics for eyeball QA.**

## Snapshot / tracker

| Epic | Title | Tier | Backbone | Points | Status |
| ---- | ----- | ---- | -------- | -----: | ------ |
| E01 | Source ingest & canonical model | MTP | A1 | 8 | ✅ Done |
| E02 | Geo & compute (distance/bearing/elevation/labels) | MTP | A3 | 8 | ✅ Done |
| E03 | `/m5/sky` MTP — one selected aircraft | MTP | A2·A4 | 5 | ✅ Done |
| E04 | Window profiles & cone filtering | MVP | A1·A3 | 8 | ✅ Done |
| E05 | Candidate scoring (best visible ≠ nearest) | MVP | A4 | 8 | ✅ Done |
| E06 | Multi-aircraft payload & `/m5/status` | MVP | A2·A5 | 5 | ✅ Done |
| E07 | Alert-state derivation in the API | MVP | A5 | 5 | ✅ Done |
| E08 | Multi-profile config & profile endpoints | MSP | A1 | 5 | ✅ Done |
| E09 | Debug web UI | MSP | A5 | 8 | ✅ Done |
| E10 | Enrichment — prefix map + cached route/model | MSP | A2 | 13 | 🟨 Prefix map done; route/model = seam/stub |
| E11 | Scoring reasons, quiet-mode, packaging & README | MSP | A4·A5·A1 | 8 | ✅ Done |
| E12 | Demo/replay mode | MLP | A5 | 5 | ✅ Done |
| E13 | Interesting-aircraft alerts & last-seen log | MLP | A5 | 5 | ⬜ Not started |
| E14 | 360 mode & RFID/NFC profile-switch support | MLP | A1 | 5 | 🟨 360 cone + switch endpoint done; tag reader is firmware |
| E15 | Companion & bridge surfaces (Cardputer / Meshtastic / compass) | MLP | cross | 8 | 🟨 Cardputer = same contract; Mesh/compass future |

**Legend:** ⬜ Not started · 🟨 In progress · ✅ Done · ⏸ Blocked. Tiers total — MTP 21 · MVP 26 · MSP 34 · MLP 23.

**Current position:** the **API side is built and verified** — MTP + MVP + MSP back-end complete
(E01–E09, E11) plus demo mode (E12); the service passes its pytest suite and serves live `/m5/*`
JSON + debug UI. Remaining: E10 route/model cached provider (offline prefix enrichment is live; the
external-lookup seam is stubbed), E13 interesting-aircraft alerts + last-seen log, and the E14/E15
firmware/hardware-side bits. MTP/MVP eyeball-QA now wants a run against a **real** decoder feed (see
PRD → Success Metrics); demo mode (`SKYDIAL_SOURCE_TYPE=demo`) validates the pipeline dry.

> **Non-atomic flags:** none within a tier — each epic below commits story-by-story in a runnable
> state. E03 depends on E01+E02; E05 depends on E04; E10's cache (Phase 3) may land behind Phase 2
> prefix mapping but each phase is independently shippable.

---

## MTP — Walking Skeleton (R1)
*Goal: Pi reads the sky → serves one sensible aircraft with rough direction → Dial shows it.*

### E01 — Source ingest & canonical model  ·  A1  ·  8 pts
**Value:** everything downstream speaks one vocabulary regardless of decoder.

- **S01.1** *(3)* — As **Mak**, I want the service to read the local decoder `aircraft.json`, so raw
  aircraft data is available to the service.
  - Given a reachable `aircraft.json` · When the service reads it · Then each entry with lat/lon is parsed and the rest skipped-and-counted.
- **S01.2** *(3)* — As a developer, I want raw rows mapped to a validated canonical `Aircraft`, so
  downstream code never touches decoder-specific shapes.
  - Given a raw row · When normalised · Then it yields a pydantic `Aircraft` with raw fields populated and computed/enriched fields left optional.
- **S01.3** *(2)* — As **Mak**, I want receiver coords and source location in top-of-file config, so
  I can point the service at my Pi without editing logic.
  - Given config values · When the service starts · Then it reads coords + source path from config, not literals.

### E02 — Geo & compute  ·  A3  ·  8 pts
**Value:** the Dial can stay dumb; the Pi owns all geometry.

- **S02.1** *(3)* — As **Skye**, I want each aircraft's distance and true bearing from the receiver,
  so I know how far and which way.
  - Given an aircraft lat/lon + receiver coords · When computed · Then `distance_km` (great-circle) and `bearing_deg` are correct within tolerance, plus a compass `bearing_label`.
- **S02.2** *(2)* — As **Skye**, I want the elevation angle, so overhead vs horizon is distinguishable.
  - Given distance + altitude · When computed · Then `elevation_deg` is populated.
- **S02.3** *(2)* — As a developer, I want `screen_angle_deg = bearing − radar_up_deg` precomputed,
  so the ring draws correctly for any orientation.
  - Given a profile `radar_up_deg` · When computed · Then `screen_angle_deg` is normalised to 0–359.
- **S02.4** *(1)* — As **Skye**, I want stale positions filtered out, so I never see ghosts.
  - Given `seen`/`seen_pos` beyond a config threshold · When filtering · Then the aircraft is excluded.

### E03 — `/m5/sky` MTP  ·  A2·A4  ·  5 pts
**Value:** the walking-skeleton payload the Dial renders.

- **S03.1** *(3)* — As **Skye**, I want `GET /m5/sky` to return the selected aircraft with
  callsign/hex, distance, and altitude, so the Dial can show what I'm looking at.
  - Given live aircraft · When I GET `/m5/sky` · Then I get `{ok, now, profile, selected, aircraft[]}` with the MTP fields populated.
- **S03.2** *(2)* — As **Skye**, I want auto-select to pick the nearest fresh aircraft (scoring
  stub), so there's always a sensible default.
  - Given ≥1 fresh aircraft · When selecting · Then `selected` indexes the nearest and the array is ordered.

**⏹ Eyeball QA (MTP):** run against a real feed — does `/m5/sky` show a live plane, distance/altitude
sane, `bearing_label` roughly matching the sky? Leave it running 30 min without crashing.

---

## MVP — Enhanced (R2)
*Goal: useful window-sill identifier — best-visible pick, cone filtering, alerts, status.*

### E04 — Window profiles & cone filtering  ·  A1·A3  ·  8 pts
- **S04.1** *(3)* — As **Mak**, I want a profile with `radar_up_deg`, `view_cone_deg`,
  `max_distance_km`, `min_elevation_deg`, so the radar matches my actual window.
- **S04.2** *(3)* — As **Skye**, I want candidates filtered to the window cone/distance/elevation, so
  I only see what's plausibly out this window.
- **S04.3** *(2)* — As **Mak**, I want the multi-decoder source adapter (`dump1090`/`readsb`/
  `tar1090`) behind one interface, so my decoder choice doesn't matter.

### E05 — Candidate scoring  ·  A4  ·  8 pts
- **S05.1** *(5)* — As **Skye**, I want the *best visible* aircraft auto-selected (not just nearest),
  so a jet ahead beats a chopper behind me.
  - Given candidates · When scored `freshness+window_alignment+elevation+distance+altitude_interest+vertical_rate` · Then `selected` is the max score, weights read from config.
- **S05.2** *(3)* — As a developer, I want scoring as a config-weighted strategy, so tuning needs no
  code change.

### E06 — Multi-aircraft payload & `/m5/status`  ·  A2·A5  ·  5 pts
- **S06.1** *(2)* — As **Skye**, I want up to 8–12 ordered candidates with a `selected` index and
  `score`, so I can browse the sky.
- **S06.2** *(1)* — As **Skye**, I want vertical-movement label + track arrow, so I see climb/descent
  and heading at a glance.
- **S06.3** *(2)* — As **Mak**, I want `GET /m5/status` (feed health, last fetch, raw vs filtered
  counts, state), so I can see the service is alive.

### E07 — Alert-state derivation  ·  A5  ·  5 pts
- **S07.1** *(3)* — As **Skye**, I want the API to flag transitions (new-in-cone, new-best-candidate,
  feed-lost/restored), so the Dial can chirp at the right moment.
  - Given two consecutive ticks · When they differ · Then the response names the alert event(s); the Dial owns the sound.
- **S07.2** *(2)* — As a developer, I want clean machine-readable states (connecting/quiet-sky/active/
  feed-lost), so every UI state maps to a value.

**⏹ Eyeball QA (MVP):** at the real window — sensible auto-pick, cone hides behind-you traffic,
alerts fire on arrivals not every refresh, status reflects reality. Demoable to family.

---

## MSP — Polish (R3)
*Goal: polished, shareable — profiles, enrichment, debug UI, packaging.*

### E08 — Multi-profile config & endpoints  ·  A1  ·  5 pts
- **S08.1** *(3)* — As **Mak**, I want multiple named profiles in config + `GET /m5/profiles`, so I
  can move the Dial around the house.
- **S08.2** *(2)* — As **Skye**, I want `POST /m5/profile` to switch the active profile, so the Dial
  (or web) can change window.

### E09 — Debug web UI  ·  A5  ·  8 pts
- **S09.1** *(5)* — As **Mak**, I want a Pi-hosted page showing current profile, candidate table with
  per-factor scores, bearing/elevation/distance, raw vs filtered counts, last fetch/poll times, so I
  can tune without reflashing. *(Responsive by default.)*
- **S09.2** *(3)* — As **Mak**, I want an optional browser radar preview, so I can verify orientation
  visually.

### E10 — Enrichment  ·  A2  ·  13 pts
- **S10.1** *(3)* — As **Skye**, I want static airline-prefix → name mapping (`EZY→easyJet`), so the
  card names the airline offline.
- **S10.2** *(2)* — As **Skye**, I want an aircraft hex/type static lookup where available, so I see
  the model without a network call.
- **S10.3** *(5)* — As **Skye**, I want cached route/model lookup (SQLite, TTL) with graceful
  fallback, so enrichment feels instant and never breaks the core when offline.
- **S10.4** *(3)* — As **Skye**, I want a `selected_reason` string ("ahead and visible"), so the card
  explains why this plane.

### E11 — Scoring reasons, quiet-mode, packaging  ·  A4·A5·A1  ·  8 pts
- **S11.1** *(2)* — As **Mak**, I want per-factor scoring reasons exposed, so tuning is data-driven.
- **S11.2** *(2)* — As **Skye**, I want rate-limiting + quiet-mode in the profile, so it never chirps
  every refresh and can go silent.
- **S11.3** *(1)* — As **Mak**, I want the ~1s source cache + clean decoder/Wi-Fi recovery, so many
  Dials don't hammer the decoder and outages self-heal.
- **S11.4** *(3)* — As **Mak**, I want a systemd unit + config examples + clear README/installer
  notes, so another maker can build it.

**⏹ Eyeball QA (MSP):** film-able in <20s; a stranger can build from the README; debug UI looks
intentional; the wow demo (chirp → route/model → look-WNW) lands.

---

## MLP — Ribs (delight)
*Goal: a beautiful always-on appliance.*

### E12 — Demo/replay mode  ·  A5  ·  5 pts
- **S12.1** *(5)* — As **Mak**, I want a `SkySource` that replays recorded ADS-B frames, so I can demo
  with no live traffic.

### E13 — Interesting-aircraft alerts & last-seen log  ·  A5  ·  5 pts
- **S13.1** *(3)* — As **Skye**, I want alerts for low/close or unusual aircraft, so standout moments
  get flagged.
- **S13.2** *(2)* — As **Skye**, I want a "last seen" mini-log, so I can glance back at recent traffic.

### E14 — 360 mode & RFID/NFC support  ·  A1  ·  5 pts
- **S14.1** *(2)* — As **Skye**, I want a full-360 / window-HUD profile mode, so a portable/omni view
  works.
- **S14.2** *(3)* — As **Skye**, I want the API to accept RFID/NFC-driven profile switches (same
  `POST /m5/profile`), so tapping a window tag changes profile.

### E15 — Companion & bridge surfaces  ·  cross  ·  8 pts
- **S15.1** *(3)* — As **Skye**, I want the Cardputer to consume the same `/m5/*` contract, so a
  companion view needs no back-end change.
- **S15.2** *(3)* — As **Skye**, I want an optional Meshtastic notification bridge subscribing to
  alert-state events, so notable aircraft can notify off-device.
- **S15.3** *(2)* — As **Skye**, I want optional compass/magnetometer heading to feed `radar_up_deg`,
  so true "point-at-aircraft" mode is possible.

---

## Backlog hygiene

- Bugs/small betterments → `SNAGGING.md` (not here).
- Brand-new feature → add an Epic row + section here; re-cut the STORYMAP slice.
- When the backlog passes ~12 *active* epics, split detail into `EPIC-NN.md` and keep a one-line
  teaser in the tracker.
