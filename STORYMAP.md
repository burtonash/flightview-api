# STORYMAP — SkyDial (flightview-api, the Pi back-end)

> Jeff Patton user story map. **Two views of one dataset:** this map and the PRD Requirements
> table — keep them in sync (the table's `Action`/`Step` columns are this map's Activities/Steps;
> `Importance` lozenges track the release slices). Re-cut whenever scope shifts. This map
> **drives the EPICS tiers** (Walking Skeleton = MTP, R2 = MVP, R3 = MSP, ribs = MLP).
>
> **Scope note:** this repo is the **Pi back-end**. The map is the whole-product user journey, but
> every task below is annotated with what *this service* must do to enable it. Firmware-only tasks
> are marked _(Dial)_ and tracked here only so the API contract stays coherent.

**Narrative (the one-sentence JTBD goal above the backbone):**
_As **Skye** (window-watcher), I glance at a little dial and instantly know what plane I'm looking
at, so the sky outside my window feels alive._

**Personas**
- **Skye — Window-Watcher** `USER`. Looks out of a window, wants to identify what's up there without reaching for a phone.
- **Mak — Maker/Builder** `DELIVERY` / `IN-LIFE SERVICE`. Installs, aims, tunes, and shares the build; keeps it running as an appliance.
- **Guest — Observer** `INFLUENCER`. The person who sees it on the sill and says "wait, how does it know that?" — the wow test.

---

## The map

Backbone (Activities — user *behaviours*, left→right in journey order):
**A1 Aim it at my window → A2 See what I'm looking at → A3 Know where to look → A4 Explore the sky → A5 Feel it come alive**

Under each activity: Steps, then Tasks. Every task tagged with its release slice **(R1/R2/R3/rib)**.
Priority descends vertically.

### A1 — Aim it at my window  *(Mak sets it up; Skye lives with it)*
- **Step 1.1 — Stand up the service & read the sky**
  - Read local `aircraft.json` from the decoder, normalise to a canonical aircraft model (R1)
  - Source adapter tolerates `dump1090` / `readsb` / `tar1090` shapes (R2)
  - Package as a systemd service with a config file (R3)
- **Step 1.2 — Tell it where "here" and "the window" are**
  - Hard-coded receiver coords + one north-up profile (`radar_up_deg=0`) (R1)
  - Window profile fields: `radar_up_deg`, `view_cone_deg`, `max_distance_km`, `min_elevation_deg` (R2)
  - Multiple named profiles in config + `GET /m5/profiles`, `POST /m5/profile` (R3)
  - RFID/NFC-driven profile switch supported by the API (rib)

### A2 — See what I'm looking at  *(the centre aircraft card)*
- **Step 2.1 — Identify the aircraft**
  - `GET /m5/sky` returns the selected aircraft with callsign/hex, distance, altitude (R1)
  - Add vertical-movement label + track arrow (R2)
  - _(Dial)_ Render the centre card (R1)
- **Step 2.2 — Make it feel like a real instrument (enrichment)**
  - Static airline-prefix mapping (`BAW→British Airways`, `EZY→easyJet`) (R3)
  - Cached route + aircraft-model lookup with SQLite + graceful fallback (R3)
  - `selected_reason` / "why selected" hint (R3)
  - Operator abbreviation / silhouette category / flight phase (rib)

### A3 — Know where to look  *(the radar ring & direction)*
- **Step 3.1 — Point me the right way**
  - Compute true bearing + `bearing_label`; precompute `screen_angle_deg = bearing − radar_up_deg` (R1)
  - Compute elevation angle; filter stale positions (R1)
  - _(Dial)_ Draw outer ring + one blip roughly in the right direction (R1)
- **Step 3.2 — Only show what's actually out this window**
  - Filter candidates to the window cone / max distance / min elevation (R2)
  - Off-view hint markers + view-cone arc data for aircraft near the edge (R3)
  - _(Dial)_ Full radar ring with multiple blips, selected highlighted (R2)

### A4 — Explore the sky  *(browse beyond the auto-pick)*
- **Step 4.1 — Auto-pick the best visible plane, not just the nearest**
  - Candidate scoring: freshness + window-alignment + elevation + distance + altitude-interest + vertical-rate (R2)
  - Return up to 8–12 ordered candidates with a `selected` index + `score` (R2)
  - Expose per-factor scoring reasons for tuning (R3)
- **Step 4.2 — Let me cycle and lock**
  - Stable ordering so rotary next/prev is coherent across polls (R2)
  - _(Dial)_ Rotary browse, press-to-lock, auto-timeout back to auto (R2)

### A5 — Feel it come alive  *(alerts, states, reliability, delight)*
- **Step 5.1 — Nudge me at the right moment**
  - Derive alert-worthy transitions in the API (new-in-cone, new-best-candidate, feed-lost/restored) (R2)
  - Rate-limit + quiet-mode flags in the profile so the Dial doesn't chirp every refresh (R3)
  - Interesting-aircraft alerts (low/close, unusual type) (rib)
- **Step 5.2 — Never look broken**
  - `GET /m5/status`: feed health, last fetch time, raw vs filtered counts (R2)
  - Clear machine-readable states: connecting / quiet-sky / active / feed-lost (R2)
  - Cache source response ~1s; recover cleanly from decoder/Wi-Fi loss (R3)
  - "Last seen" mini-log; demo mode replaying recorded ADS-B (rib)

---

## Release slices (the horizontal cuts → EPICS tiers)

Every slice is a **thin slice across the whole backbone** — never one activity built fully before
the next.

### R1 · Walking Skeleton → **MTP**
The thinnest end-to-end journey: the Pi reads the sky and serves *one* sensible aircraft with a
rough direction; the Dial shows it. Browse/alerts intentionally absent — the journey is still
complete (see a real plane, roughly where it is).
- A1: read `aircraft.json` → canonical model; hard-coded coords + north-up profile
- A2: `GET /m5/sky` → selected callsign, distance, altitude
- A3: true bearing + label + `screen_angle_deg`, elevation, stale-filter; one blip
- A4: auto-select = nearest fresh aircraft (scoring stub)
- A5: — (implicitly "here's the one plane")

### R2 · Enhanced → **MVP** (demo-able)
- A1: full window-profile fields; multi-decoder source adapter
- A2: vertical label + track arrow
- A3: window-cone / distance / elevation filtering; up to 8 candidates
- A4: real candidate scoring (best visible ≠ nearest); ordered array + `selected` index
- A5: alert-state transitions in the API; `GET /m5/status`; connecting/quiet/active/feed-lost states

### R3 · Polish → **MSP** (sellable/shareable)
- A1: multi-profile config + `GET /m5/profiles` + `POST /m5/profile`; systemd packaging
- A2: airline-prefix enrichment; cached route/model (SQLite) with fallback; `selected_reason`
- A3: off-view hints + view-cone arc data
- A4: per-factor scoring reasons for tuning
- A5: rate-limit + quiet-mode; ~1s source cache; clean recovery; **debug web UI**; README/installer

### Below the line · Ribs → **MLP** (delight)
- A1: RFID/NFC profile switching; full-360 profile mode
- A2: operator abbrev / silhouette / flight-phase enrichment
- A5: interesting-aircraft alerts; last-seen log; demo/replay mode
- Cross-cutting: Cardputer companion API; Meshtastic notification bridge; compass/magnetometer true-heading; portable GPS mode

---

## From map to backlog

Each Task above slices into INVEST-sized user stories:
- Validate INVEST-minus-Small first; if a slice isn't *Valuable*, recombine rather than split; always
  **vertical** slices delivering observable user value — never horizontal splits.
- Write each story in Mike Cohn "As a / I want / so that" + Gherkin Given/When/Then form.
- Story-point at the story level; the slices become the EPICS.md tiers.

> **Sync note:** `PRD.md` currently expresses requirements as narrative user stories (US1–US9) plus
> the §10 phasing, rather than the 8-column Requirements table. This map is derived from those. When
> the PRD is next refreshed to the master template, populate the Requirements table from this map so
> the two views share one dataset.
