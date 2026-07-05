# ARCHITECTURE — flightview-api (SkyDial Pi back-end)

> The architecture that supports the **end state and future states**, so we iterate towards it
> without re-factoring. Re-evaluate **before starting an epic and after finishing each one** —
> subtle updates automatically; a *major* shift gets flagged with why/impact/benefit. Kept current
> at all times. Derived from `PRD.md` and `STORYMAP.md`.

---

## 1. Design goals (what the architecture must protect)

1. **Thin, dumb clients.** The Dial (and future Cardputer) do *zero* aviation maths. The Pi
   precomputes every angle, label, and state. Presentation layers only draw JSON.
2. **One stable contract, many presenters.** `/m5/*` is a versioned, presentation-agnostic API.
   Adding the Cardputer must not touch the compute core.
3. **Source-independent.** Which decoder is running (`dump1090-fa` / `readsb` / `tar1090`) is an
   open question (PRD → Open Issues). A **source adapter** normalises all of them to one canonical model, so
   the answer can change without touching anything downstream.
4. **Enrichment is optional and phased.** The product is impressive with zero enrichment (R1) and
   gets richer (prefix map → cached API) without the core depending on any external service. Every
   enrichment path degrades gracefully.
5. **Scoring is a strategy, not a hard-code.** Candidate selection is a pure function of a canonical
   aircraft + profile + weights. Weights live in config and are tuned empirically via the debug UI.
6. **Profiles are data, not code.** Window behaviour (orientation, cone, distance, alerts) is
   config; adding a window never means a code change.
7. **Appliance-grade reliability.** Never crash the poll loop on bad source data; always answer with
   a clear machine-readable state (connecting / quiet-sky / active / feed-lost).

---

## 2. Component view

```text
                        ┌──────────────────────────── SkyDial Pi Service (this repo) ───────────────────────────┐
  ADS-B decoder         │                                                                                        │
  (dump1090/readsb/ ──► │  [1] Source Adapter ──► [2] Canonical Model ──► [3] Geo/Compute ──► [4] Filter+Score   │
   tar1090 JSON)        │        (pluggable)          (Aircraft)          (dist/brg/elev/     (cone, staleness,   │
                        │                                                  screen_angle)        weighted score)   │
                        │                                                        │                    │           │
                        │                                                        ▼                    ▼           │
                        │                                   [5] Enrichment ◄───────────────  [6] Selection +      │
                        │                                   (prefix map,                     Alert-state deriver  │
                        │                                    cached route/model, SQLite)             │            │
                        │                                                        │                    │           │
                        │   [7] Profile Store (config)  ─────────────────────────┴────────────────────┘          │
                        │            │                                           │                                │
                        │            ▼                                           ▼                                │
                        │   [8] API Layer (FastAPI)  ── /m5/sky /status /log /profiles /profile ──►  M5Dial/Cardputer│
                        │            │                                                                            │
                        │            └──►  [9] Debug Web UI  (candidate table, scores, radar preview)             │
                        └────────────────────────────────────────────────────────────────────────────────────────┘
```

### Component responsibilities

| # | Component | Responsibility | Key seam for the future |
| - | --------- | -------------- | ----------------------- |
| 1 | **Source Adapter** | Fetch/read raw decoder output; map to canonical `Aircraft`. One class per decoder behind a `SkySource` interface. | Swap decoder, or add MLAT/network feeds, without touching compute. |
| 2 | **Canonical Model** | `Aircraft`, `Profile`, `SkyResponse` as validated `pydantic` models — the single vocabulary. | New fields are additive; presenters ignore unknowns. |
| 3 | **Geo/Compute** | Great-circle distance, true bearing, elevation angle, `screen_angle_deg = bearing − radar_up_deg`, compass labels, track arrows. Pure functions. | Compass/magnetometer "true heading" later feeds `radar_up_deg` dynamically. |
| 4 | **Filter + Score** | Staleness filter; window-cone/distance/elevation filter; weighted scoring `f(aircraft, profile, weights)`. Strategy objects, config-driven weights. | New scoring factors = new weighted term; no caller changes. |
| 5 | **Enrichment** | Phase 1 none · Phase 2 static prefix map + type→model · Phase 3 cached route via SQLite (TTL + graceful fallback). `Enricher` chain. | Add a provider as a chain link; cache shields the API from rate limits/outages. |
| 6 | **Selection + Alert-state** | Pick `selected` index; diff against previous tick to derive alert-worthy transitions (new-in-cone, new-best, interesting, feed-lost/restored); apply rate-limit/quiet flags. | Firmware stays dumb — it just plays the sound the API names. |
| 7 | **Profile Store** | Load/validate window profiles from config; expose current + switch. | RFID/NFC and web-config just call the same switch. |
| 8 | **API Layer** | FastAPI app serving the `/m5/*` contract; precomputed, tiny payloads (≤8–12 aircraft); ~1s source cache. | Cardputer/other presenters consume the same endpoints. |
| 9 | **Debug Web UI** | Server-rendered page: current profile, candidate table with per-factor scores, raw vs filtered counts, last fetch/poll times, optional radar preview. | The tuning surface for scoring weights; responsive by default. |

> **Implementation map** (`skydial/`): [1] `sources/` · [2] `models.py` · [3] `geo.py` ·
> [4] `filters.py` + `scoring.py` · [5] `enrichment.py` + `cache.py` (+ `data/airlines.py`,
> `data/aircraft_types.py`, `data/routes.py`) · [6] `pipeline.py` + `alerts.py` · [7] `profiles.py` ·
> [8] `app.py` · [9] `debug_ui.py`. Config in `config.py`; entrypoint `__main__.py`.

---

## 3. Data model (canonical)

Authoritative shapes live in `PRD.md` → Architecture & Technical Considerations → Data model. Architecturally:

- **`Aircraft`** — raw ADS-B fields (hex, flight, lat/lon, alt, speed, track, vertical_rate, seen,
  rssi, type_code, registration) + **computed** (bearing_deg, bearing_label, screen_angle_deg,
  distance_km, elevation_deg, track_arrow, vertical_label) + **enriched** (airline, origin,
  destination, route, model) + **decision** (score, selected_reason, interesting_reason).
  Enriched/decision fields are always optional so any stage can be skipped.
- **`Profile`** — id, name, radar_up_deg, view_cone_deg, max_distance_km, min_elevation_deg,
  alert_enabled, quiet_mode.
- **`SkyResponse`** — ok, now, profile, selected (index), aircraft[]. Plus alert/state hints for the
  Dial. **`Sighting`** — the last-seen log entry served by `/m5/log`.

Everything the Dial needs is precomputed server-side; the client never derives geometry.

---

## 4. API contract (`/m5/*`)

| Endpoint | Purpose | Tier |
| -------- | ------- | ---- |
| `GET /m5/sky` | Current scored, ordered candidates + selected index. `?profile=` overrides active profile. | MTP→ |
| `GET /m5/status` | Feed health, last fetch time, raw vs filtered counts, service state. | MVP |
| `GET /m5/log` | Recent last-seen sightings (rolling log). | MSP |
| `GET /m5/profiles` | List available window profiles. | MSP |
| `POST /m5/profile` | Switch active profile (used by long-press, web config, and future RFID/NFC). | MSP |

Contract rules: additive-only evolution; presentation-agnostic; small payloads; stable field names.
If a breaking change is ever needed, version the prefix (`/m5/v2/…`) rather than mutate `/m5`.

---

## 5. Runtime & poll loop

- **Stack (recommended, to confirm against PRD → Open Issues):** Python 3.11+, FastAPI + uvicorn, pydantic
  models, `httpx`/file-read for source ingest, SQLite (stdlib) for the enrichment cache, PyYAML/JSON
  config, `pytest` for tests. Rationale: matches the PRD's recommended stack, async-friendly for the
  1–2s Dial poll cadence, zero heavyweight deps on the Pi.
- **Cadence:** Dial polls every 1–2s; the service caches the raw source read ~1s so N Dials don't
  hammer the decoder. Selection/alert-state diffing is per-tick against the previous snapshot.
- **Config at the top:** receiver coords, source URL/path, profile set, and scoring weights are
  user-customisable config (per CLAUDE.md engineering defaults), not literals buried in code.
- **Failure posture:** the loop never throws to the client. Bad/absent source → `feed-lost` state
  with last-good timestamp; empty cone → `quiet-sky`; malformed aircraft rows are skipped and
  counted (raw vs filtered), not fatal.

---

## 6. Security & safety (from PRD → Architecture & Technical Considerations)

- Receive-only; the service never transmits on aviation bands.
- Bind to the **local network only** by default; no public exposure.
- Enrichment API keys (if ever used) stay on the Pi in env-vars/secret config, **never** in a
  payload to the Dial, never committed. Placeholders only in the repo.
- Nothing presents as aviation-grade / navigation-safe.

---

## 7. Future states (supported without refactor)

| Future capability | How the current design absorbs it |
| ----------------- | --------------------------------- |
| **Cardputer companion** | Another presenter on the same `/m5/*` contract. No core change. |
| **RFID/NFC profile switch** | Trigger that calls `POST /m5/profile`. Profile Store unchanged. |
| **Full-360 / window-HUD modes** | A profile variant (wide/omni cone); pure data. |
| **Compass/magnetometer true heading** | Feeds `radar_up_deg` dynamically into Geo/Compute; transform already parameterised. |
| **Meshtastic / notification bridge** | New subscriber to the Alert-state deriver's events. |
| **Live route/model provider** | Drop a provider into `enrichment.py`; the SQLite cache already sits in front. |
| **Extra ADS-B sources / MLAT** | New `SkySource` adapter; canonical model absorbs it. |
| **Demo/replay mode** | A `SkySource` that reads recorded JSON frames — same interface. |

---

## 8. Open architectural questions (track, don't block)

Mirrors PRD → Open Issues where it bites the architecture:
1. Which decoder + exact JSON endpoint? → isolated behind the Source Adapter; pick a default, keep the seam.
2. systemd from the start? → yes, target packaging at MSP; keep the app a plain ASGI process so it's trivial to wrap.
3. Config on Pi vs Dial? → **all config on the Pi** (profiles are data here); the Dial only selects.
4. Default view cone (70/90/100/120°)? → config default (start 100°), tuned via the debug UI.
