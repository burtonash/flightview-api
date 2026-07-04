# SkyDial — Product Requirements Document (PRD)

> **Scope of this repository:** `flightview-api` is the **Raspberry Pi back-end service** (the
> "SkyDial Pi Service"). It ingests ADS-B data, computes distance/bearing/elevation, filters and
> scores aircraft against window profiles, enriches them, and serves a tiny JSON API over Wi-Fi to
> an **M5Dial** (and, in future, a **Cardputer**) presentation layer. The Dial firmware lives
> outside this repo and is referenced here only so the API contract stays coherent.
>
> **Living document.** This PRD evolves with the project. The **Requirements** and **Out of Scope**
> tables are the single source of requirement truth and are **two views of one dataset** with
> `STORYMAP.md` — the `Action`/`Step` columns are the map's Activities/Steps, and the `Importance`
> lozenge moves an item between scope and out-of-scope. Importance ↔ delivery tier:
> **`ALPHA` = MTP (R1) · `BETA` = MVP (R2) · `GTM` = MSP (R3) · `Future` = MLP (ribs) / deferred.**
> Keep this table, `STORYMAP.md`, and `EPICS.md` in sync.

| **Planning Stage** | Concept → Ballpark → Initial Review → Initial Scoping → Estimation → Commercials → Sign-Off → Resourced → **In Flight** → Delivered → Launched |
| --- | --- |
| **Document owner** | @burtonash |
| **Business Sponsor** | Personal / maker project |
| **Product Owner** | @burtonash |
| **Project Manager** | @burtonash |
| **Technical Lead(s)** | @burtonash |
| **Team(s)** | SkyDial (Pi back-end + Dial firmware) |

## Overview

SkyDial is a small, round, always-on aircraft heads-up display: an **M5Dial** on a window sill,
fed by a **Raspberry Pi ADS-B receiver**. It shows a radar-style ring of the aircraft likely
visible from that window, with the best candidate selected in the centre — callsign, direction,
distance, altitude, and (later) airline, route and model. Someone glances out, sees a plane,
glances at the Dial, and instantly knows what it is. Winning looks like a stranger saying *"wait,
how does it know that?"* within twenty seconds. This repo is the **brain**: the Pi does all the
ingestion, maths, scoring and enrichment and serves a tiny precomputed JSON API; the Dial stays
dumb and just draws it.

## Customer Problem

You can see a plane out of the window but have no idea what it is. Existing answers — a phone app,
a laptop tab, a full tar1090 map — are heavyweight, require reaching for a device, and read like a
data table rather than a glanceable instrument. There's no *ambient, dedicated, delightful* object
that answers "what's that plane?" at a glance.

### Customer Pain Points

| Pain | Why it matters |
| --- | --- |
| "What's that plane?" needs a phone/laptop | Breaks the moment; kills the ambient magic of just looking up |
| ADS-B maps are dense and technical | Nearest ≠ what you can actually see out *this* window; no glance-value |
| Existing tools aren't a dedicated object | Nothing to leave on the sill that makes the sky feel alive |
| Home ADS-B receivers are underused | A working feed exists but delivers no everyday, delightful payoff |

## Strategic Value

* **Delight-led.** The bet is emotional, not analytical: a tiny physical instrument that produces a
  reliable "wow". That's what makes it worth building, keeping plugged in, and sharing.
* **Leverage existing assets.** A Pi ADS-B feed is already running; SkyDial turns that latent data
  into an everyday experience with a cheap presentation layer.
* **Shareable / community.** A clean, clonable maker build (README + config + demo mode) spreads
  organically and invites extension (Cardputer, Meshtastic, 360 mode).

## Value Proposition

|  | **Value to Customer** | **Value to Us** |
| --- | --- | --- |
| **New Business** | An ambient "what's that plane?" instrument that just works | A flagship, demoable maker project |
| **Existing Business** | Turns an existing ADS-B feed into daily delight | Reuse of the home receiver investment |
| **Partners** | A clonable, hackable, well-documented build | Community goodwill; contributions and extensions |

## Why now

### Market / maker pull
Affordable round smart displays (M5Dial) + mature local ADS-B decoders (dump1090/readsb/tar1090)
make a dedicated glanceable instrument cheap and buildable today.

### Capability pull
Home ADS-B is common and reliable; the raw data is sitting there precomputed-adjacent — only the
scoring, enrichment and a tiny API stand between it and delight.

### Internal / personal pull
An existing running receiver, a clear wow-driven vision, and appetite to ship a lovable object.

## Objectives

1. **Nail the glance.** Serve the *most likely visible* aircraft for a given window (not merely the
   nearest) with correct direction, so a look-down instantly answers "what's that?".
2. **Keep the Dial dumb.** Precompute every angle, label, and state server-side; ship tiny JSON.
3. **Be impressive with zero enrichment, magical with it.** Core value from direction + matching;
   airline/route/model enriches the wow without becoming a dependency.
4. **Run as an appliance.** Always-on, self-healing across feed/Wi-Fi loss, never a crashed board.
5. **Be clonable.** Another maker can rebuild it from the README with a demo mode to prove it.

## Constraints & Dependencies

**Delivery constraints**
1. **M5Dial resources.** Small round screen, limited RAM/CPU → payloads must be tiny (≤8–12 aircraft) and pre-labelled.
2. **Poll cadence.** Dial polls every 1–2s → the Pi must answer fast and cache the source read (~1s).

**Internal dependencies**
3. **Running ADS-B decoder.** Requires a local `dump1090-fa`/`readsb`/`tar1090` producing `aircraft.json`.
4. **Shared Wi-Fi.** Pi and Dial on the same LAN.

**Vendor and partner dependencies**
5. **Enrichment sources.** Optional route/model lookups; must degrade gracefully and be cached — never a hard dependency.

**Regulatory dependencies**
6. **Receive-only posture.** Nothing transmits on aviation bands; not presented as safety/nav-grade.

## Assumptions

### Platform and architecture
1. A local decoder exposes `aircraft.json` in a dump1090-compatible shape (or adaptable to it).
2. Receiver coordinates are known and fixed per install.

### Vendor and commercial
3. Free/offline enrichment (airline-prefix map, static hex DB) covers most of the wow; paid APIs are optional polish.

### Market and customer
4. The primary user watches from a fixed window; portable/360 use is a later delight, not day-one.

## Risks

### Product risks
1. **Selection feels wrong.** The auto-pick doesn't match what the eye sees. _Mitigation:_ config-weighted scoring tuned empirically via the debug UI; expose per-factor reasons.
2. **Alert fatigue.** Chirps on every refresh become annoying. _Mitigation:_ API derives discrete transitions only; rate-limit + quiet-mode.

### Delivery risks
3. **Decoder variance.** Field names differ across dump1090/readsb/tar1090. _Mitigation:_ source-adapter seam normalising to one canonical model.
4. **Feed/Wi-Fi flakiness.** Drops make the device look broken. _Mitigation:_ explicit machine-readable states + self-healing poll loop with last-good timestamps.

## Persona

| **Organization** | **Type** | **Persona** | **Involvement** | **Primary Value Sought** |
| --- | --- | --- | --- | --- |
| **Household** | `USER` | Skye — Window-Watcher | Lives with the Dial on the sill | Instantly know what plane is overhead, at a glance |
| **Household** | `INFLUENCER` | Guest — Observer | Sees it, spreads the "wow" | Delight: "how does it *know* that?" |
| **Maker** | `SIGN-OFF` / `DELIVERY` | Mak — Maker/Builder (you) | Builds, aims, tunes, runs, shares | A magical, reliable, shareable build |
| **Community** | `IN-LIFE SERVICE` | Fellow makers | Rebuild from README, extend | A clonable, hackable project |

## Core Motions

| **Use Case** | **Description** | **Primary Personas** |
| --- | --- | --- |
| **Ingest** | Read + normalise the decoder feed to a canonical model | Mak |
| **Compute** | Distance, bearing, elevation, screen-angle, labels | Skye |
| **Filter & Score** | Window-cone/staleness filtering; best-visible scoring | Skye |
| **Enrich** | Airline/route/model, cached + graceful fallback | Skye |
| **Serve** | Tiny precomputed `/m5/*` JSON to the Dial | Skye |
| **Configure** | Window profiles as data; switch active profile | Mak / Skye |
| **Alert** | Derive discrete alert transitions for the buzzer | Skye |
| **Tune / Debug** | Pi-hosted debug UI to tune scoring/orientation | Mak |

## Spectrum of Use Cases

| **Use Case** | **Description** |
| --- | --- |
| Single-window identify | Fixed sill, one profile — the core daily motion |
| Multi-window roaming | Named profiles; move the Dial around the house |
| Portable / 360 | Omni cone for garden/travel (later delight) |
| Demo mode | Replay recorded ADS-B for filming with no live traffic |
| Community rebuild | Another maker clones from README + config examples |

### Notes on Go to Market
Not a commercial launch — GTM is a shareable build: a <20s film of the wow, a clean README, and a
demo mode so it lands even when the sky is quiet.

## Requirements

> 8-column story-mapping table, one block per **Activity** (matches `STORYMAP.md` backbone
> A1–A5). `Importance` uses phase lozenges (see tier mapping at top). `Ticket` links to the
> `EPICS.md` epic/story. Firmware-side rows are marked `_(Dial)_` in Notes and tracked here only for
> contract coherence.

### A1 — Aim it at my window

| **Requirement (stub)** | **User Story** | Importance | **Persona** | **Action** | **Step** | Ticket | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Read decoder JSON → canonical model | As Mak, I want the service to read the local `aircraft.json` and normalise it, so downstream code speaks one vocabulary. | `ALPHA` | Mak | A1 | 1.1 | E01/S01.1–2 | Source-adapter seam |
| Config: receiver coords + source path | As Mak, I want coords and source in top-of-file config, so I can point it at my Pi without editing logic. | `ALPHA` | Mak | A1 | 1.1 | E01/S01.3 | |
| Multi-decoder source adapter | As Mak, I want dump1090/readsb/tar1090 tolerated behind one interface, so decoder choice doesn't matter. | `BETA` | Mak | A1 | 1.1 | E04/S04.3 | |
| systemd packaging + config file | As Mak, I want a systemd unit + config, so it runs as an appliance. | `GTM` | Mak | A1 | 1.1 | E11/S11.4 | |
| Hard-coded north-up profile | As Mak, I want one north-up profile to start, so the skeleton works. | `ALPHA` | Mak | A1 | 1.2 | E01/E03 | |
| Window profile fields | As Mak, I want `radar_up_deg`/`view_cone_deg`/`max_distance_km`/`min_elevation_deg`, so the radar matches my window. | `BETA` | Mak | A1 | 1.2 | E04/S04.1 | |
| Multi named profiles + endpoints | As Skye, I want named profiles + `GET /m5/profiles` + `POST /m5/profile`, so I can move the Dial around. | `GTM` | Skye/Mak | A1 | 1.2 | E08 | |
| RFID/NFC profile switch (API) | As Skye, I want the API to accept tag-driven profile switches, so tapping a window tag changes profile. | `Future` | Skye | A1 | 1.2 | E14/S14.2 | |

### A2 — See what I'm looking at

| **Requirement (stub)** | **User Story** | Importance | **Persona** | **Action** | **Step** | Ticket | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `/m5/sky` selected card fields | As Skye, I want `GET /m5/sky` to return callsign/hex, distance, altitude, so the Dial shows what I'm looking at. | `ALPHA` | Skye | A2 | 2.1 | E03/S03.1 | |
| Vertical label + track arrow | As Skye, I want climb/descend + heading arrow, so I read movement at a glance. | `BETA` | Skye | A2 | 2.1 | E06/S06.2 | |
| Render centre card | As Skye, I want the centre card drawn, so I can read the selected aircraft. | `ALPHA` | Skye | A2 | 2.1 | firmware | _(Dial)_ |
| Airline-prefix enrichment | As Skye, I want `EZY→easyJet` offline mapping, so the card names the airline. | `GTM` | Skye | A2 | 2.2 | E10/S10.1 | |
| Cached route/model lookup | As Skye, I want cached route+model with fallback, so enrichment feels instant and never breaks offline. | `GTM` | Skye | A2 | 2.2 | E10/S10.3 | SQLite, TTL |
| `selected_reason` hint | As Skye, I want a "why this plane" line, so the pick is explained. | `GTM` | Skye | A2 | 2.2 | E10/S10.4 | |
| Operator/silhouette/phase | As Skye, I want operator abbrev, silhouette class and flight phase, so the card feels premium. | `Future` | Skye | A2 | 2.2 | E13+ | |

### A3 — Know where to look

| **Requirement (stub)** | **User Story** | Importance | **Persona** | **Action** | **Step** | Ticket | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| True bearing + label + screen-angle | As Skye, I want `bearing_deg`/`bearing_label`/`screen_angle_deg` precomputed, so the ring points correctly for any orientation. | `ALPHA` | Skye | A3 | 3.1 | E02 | |
| Elevation + stale filter | As Skye, I want elevation angle and stale positions dropped, so overhead vs horizon is clear and no ghosts. | `ALPHA` | Skye | A3 | 3.1 | E02 | |
| Ring + one blip | As Skye, I want a ring + blip roughly in the right direction, so I know where to look. | `ALPHA` | Skye | A3 | 3.1 | firmware | _(Dial)_ |
| Window-cone filtering | As Skye, I want candidates filtered to the cone/distance/elevation, so I only see what's out this window. | `BETA` | Skye | A3 | 3.2 | E04/S04.2 | |
| Off-view hints + cone arc | As Skye, I want edge hints + cone arc data, so near-edge traffic is indicated. | `GTM` | Skye | A3 | 3.2 | E09+ | |
| Full radar ring, multi-blip | As Skye, I want multiple blips with the selected highlighted, so I see the whole sky. | `BETA` | Skye | A3 | 3.2 | firmware | _(Dial)_ |

### A4 — Explore the sky

| **Requirement (stub)** | **User Story** | Importance | **Persona** | **Action** | **Step** | Ticket | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Best-visible candidate scoring | As Skye, I want the best *visible* aircraft auto-selected (not nearest), so a jet ahead beats a chopper behind. | `BETA` | Skye | A4 | 4.1 | E05/S05.1 | Config-weighted |
| Ordered candidates + selected index | As Skye, I want up to 8–12 ordered candidates + `selected` + `score`, so I can browse. | `BETA` | Skye | A4 | 4.1 | E06/S06.1 | |
| Per-factor scoring reasons | As Mak, I want per-factor score breakdown, so tuning is data-driven. | `GTM` | Mak | A4 | 4.1 | E11/S11.1 | |
| Stable ordering for rotary | As Skye, I want stable ordering across polls, so rotary next/prev is coherent. | `BETA` | Skye | A4 | 4.2 | E05/E06 | |
| Rotary browse / lock / timeout | As Skye, I want to rotate to cycle, press to lock, and auto-return to auto. | `BETA` | Skye | A4 | 4.2 | firmware | _(Dial)_ |

### A5 — Feel it come alive

| **Requirement (stub)** | **User Story** | Importance | **Persona** | **Action** | **Step** | Ticket | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Alert-state transitions in API | As Skye, I want the API to flag new-in-cone/new-best/feed-lost transitions, so the Dial chirps at the right moment. | `BETA` | Skye | A5 | 5.1 | E07/S07.1 | Dial owns the sound |
| Rate-limit + quiet-mode flags | As Skye, I want rate-limiting + quiet-mode, so it never chirps every refresh and can go silent. | `GTM` | Skye | A5 | 5.1 | E11/S11.2 | |
| Interesting-aircraft alerts | As Skye, I want low/close/unusual flagged, so standout moments get noticed. | `Future` | Skye | A5 | 5.1 | E13/S13.1 | |
| `/m5/status` feed health | As Mak, I want feed health/last-fetch/counts/state, so I can see the service is alive. | `BETA` | Mak | A5 | 5.2 | E06/S06.3 | |
| Machine-readable states | As Skye, I want connecting/quiet-sky/active/feed-lost, so every UI state maps to a value. | `BETA` | Skye | A5 | 5.2 | E07/S07.2 | |
| ~1s cache + clean recovery | As Mak, I want a source cache and self-healing loop, so many Dials don't hammer the decoder and outages recover. | `GTM` | Mak | A5 | 5.2 | E11/S11.3 | |
| Last-seen log + demo mode | As Mak, I want a last-seen log and recorded-frame replay, so I can review traffic and demo dry. | `Future` | Mak | A5 | 5.2 | E12/E13 | |

## Out of Scope

> Set `Importance = Future` for deferred items (they can move into scope by changing the lozenge).
> Rows noted **permanent** are hard non-goals, not deferrals.

| **Requirement (stub)** | **User Story** | Importance | **Persona** | **Action** | **Step** | Ticket | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Dial decodes ADS-B directly | As Skye, I do *not* want the Dial to decode 1090 MHz — the Pi does all decoding. | `Future` | Skye | A1 | — | — | **Permanent non-goal** |
| True point-at-aircraft | As Skye, I want the device heading to drive the ring. | `Future` | Skye | A3 | 3.1 | E15/S15.3 | Needs compass/magnetometer |
| Paid flight-API dependency | As Skye, I want route/model even offline. | `Future` | Skye | A2 | 2.2 | — | **Permanent:** enrichment must degrade gracefully |
| Safety / navigation use | — | `Future` | — | — | — | — | **Permanent non-goal**; receive-only, not aviation-grade |
| Public / remote exposure | As Mak, I want it internet-exposed. | `Future` | Mak | A1 | — | — | **Permanent:** local-network only by default |
| Cardputer companion | As Skye, I want a Cardputer view on the same API. | `Future` | Skye | cross | — | E15/S15.1 | Same `/m5/*` contract |
| Meshtastic notification bridge | As Skye, I want notable aircraft to notify off-device. | `Future` | Skye | A5 | 5.1 | E15/S15.2 | |
| Portable GPS / hotspot mode | As Skye, I want portable use away from home. | `Future` | Skye | A1 | — | — | |

## UX Design

The Dial is the presentation layer (firmware, separate repo); this service precomputes everything it
draws. Reference UX the API must support:

- **Active view** — outer radar ring, blips by `screen_angle_deg`, selected blip highlighted; centre
  card: callsign · direction label · distance · altitude · vertical state; small orientation hint
  (`↑ N` / `Kitchen`).
- **States the API names** (so the Dial can render each): `connecting` · `quiet-sky` (no aircraft in
  cone) · `active` · `feed-lost` (with last-seen age) · `config`.
- **Example centre card (MSP):** `EZY82K` / `LTN → PMI` / `A320neo` / `Look NNE` / `3.1 km` /
  `6,800 ft ↑`.

Full state list and example displays are preserved in `git` history and mirrored by the firmware
repo; this service's job is to make every one of them renderable from JSON alone.

## Architecture & Technical Considerations

Full design is in **`ARCHITECTURE.md`** (component view, seams, future-state absorption). Key
considerations:

1. **Thin client / fat Pi** — the Dial does zero geometry; the Pi precomputes angles, labels, states.
2. **Source-adapter seam** — normalise dump1090/readsb/tar1090 to one canonical model.
3. **Config-weighted scoring strategy** — tune weights, not code.
4. **Phased, graceful enrichment** — none → prefix map → cached API (SQLite), never a hard dependency.
5. **Versioned `/m5/*` contract** — additive-only; endpoints in `ARCHITECTURE.md → API contract`.
6. **Appliance reliability** — poll loop never throws to the client; explicit states.

**Data model (canonical).** The authoritative shapes live here and are consumed by
`ARCHITECTURE.md`:

- **`Aircraft`** — raw ADS-B (`hex`, `flight`, `lat`, `lon`, `alt_ft`, `speed_kt`, `track_deg`,
  `vertical_rate_fpm`, `squawk`, `seen`, `seen_pos`, `rssi`) + **computed** (`bearing_deg`,
  `bearing_label`, `screen_angle_deg`, `distance_km`, `elevation_deg`, `track_arrow`,
  `vertical_label`) + **enriched** (`airline`, `origin`, `destination`, `route`, `model`) +
  **decision** (`score`, `selected_reason`). Enriched/decision fields are always optional.
- **`Profile`** — `id`, `name`, `radar_up_deg`, `view_cone_deg`, `max_distance_km`,
  `min_elevation_deg`, `alert_enabled`, `quiet_mode`.
- **`SkyResponse`** — `ok`, `now`, `profile`, `selected` (index), `aircraft[]`, plus state/alert hints.

**Security & safety.** Receive-only (never transmits on aviation bands); binds to the **local network
only** by default; any enrichment API keys stay on the Pi in env-vars/secret config, **never** sent to
the Dial or committed; nothing presents as aviation-grade or navigation-safe.

**Recommended stack** (confirm against Open Issues): Python 3.11+, FastAPI + uvicorn, pydantic,
SQLite (stdlib) for the enrichment cache, pytest.

## Success Metrics

- **Glance test:** a fixed-window user identifies visible aircraft from the Dial without a phone.
- **Selection quality:** the auto-pick matches what the eye sees in the majority of arrivals (tuned via debug UI).
- **Alert quality:** chirps fire on genuine arrivals/best-changes, never every refresh.
- **Reliability:** runs 30+ min unattended without crashing; recovers cleanly from feed/Wi-Fi loss.
- **Wow test:** a non-technical observer "gets it" in <5s and says "that's cool" in <20s.
- **Clonability:** another maker rebuilds it from the README (demo mode proves it dry).

**Acceptance tests** (retained from the original spec):
- *MVP:* aircraft enters cone → Dial chirps once → blip in correct relative direction → centre shows
  callsign/direction/distance/altitude → rotary selects others → press returns to auto → empty cone shows "quiet sky".
- *Wow:* a stranger understands the object in five seconds and is delighted in twenty.

## GTM Approach

Shareable build, not a commercial launch: a short film of the wow, a clean README + config examples,
and a demo mode. Community distribution (maker forums, socials) and openness to extension.

## Open Issues

1. Which decoder is running — `dump1090-fa` / `readsb` / `tar1090`? (Isolated behind the source adapter; pick a default.)
2. Exact local `aircraft.json` endpoint/path?
3. Actual receiver coordinates?
4. First target window + its compass direction?
5. Default view cone — 70/90/100/120°? (Start 100°, tune via debug UI.)
6. Aircraft behind the user — hidden or dimmed?
7. First enrichment source?
8. systemd from the start? (Target packaging at MSP; app is a plain ASGI process.)
9. Config on Pi vs Dial? (Decision: **all config on the Pi**; the Dial only selects.)

## Q&A

| **Asked by** | **Date** | **Question** | **Answer** | **Answered By** | **Accepted By** | **Close Date** |
| --- | --- | --- | --- | --- | --- | --- |
| @burtonash | 2026-07-04 | Where does config live — Pi or Dial? | On the Pi; profiles are data, the Dial only selects. | @burtonash | @burtonash | 2026-07-04 |

## Feature Timeline and Phasing

Phasing is driven by the `STORYMAP.md` release slices and delivered via `EPICS.md`. Tier ↔ lozenge:

| Tier | Slice | Lozenge | Outcome |
| --- | --- | --- | --- |
| **MTP** | R1 Walking Skeleton | `ALPHA` | Pi serves one sensible aircraft with rough direction; Dial shows it |
| **MVP** | R2 Enhanced | `BETA` | Best-visible pick, cone filtering, alerts, `/m5/status`; demo-able |
| **MSP** | R3 Polish | `GTM` | Multi-profile, enrichment, debug UI, packaging; shareable |
| **MLP** | Ribs | `Future` | Demo mode, interesting alerts, 360/RFID, companion/bridge; delight |

Every tier is a **thin slice across the whole backbone** (A1–A5), never one activity built fully
before the next. See `EPICS.md` for the epic/story breakdown and per-tier eyeball-QA gates.
