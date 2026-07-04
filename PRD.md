# PRD.md — M5Dial ADS-B Window HUD

> **Scope of this repository:** `flightview-api` contains the **Raspberry Pi back-end service** — the "SkyDial Pi Service" described below. This is the code that runs on the Raspberry Pi to ingest ADS-B data, score and enrich aircraft, and serve the tiny JSON API that an **M5Dial** (and, in future, a **Cardputer**) connects to over Wi-Fi. The M5Dial firmware is the presentation layer and lives outside this repo; it is documented here only for context so the API contract stays coherent.

## 1. Product Name

**SkyDial**

*A window-sill aircraft radar that tells you what plane you're looking at.*

Working names:

* SkyDial
* Window Radar
* PlaneSpotter Dial
* ADS-B HUD
* "What's That Plane?"

## 2. Product Summary

SkyDial is a small, round, always-on aircraft heads-up display built using an **M5Dial** and a **Raspberry Pi ADS-B receiver**.

It sits next to a window and shows a radar-style ring of aircraft that are likely visible from that window. The centre of the display shows the currently selected aircraft: callsign, direction, distance, altitude, vertical movement, and eventually airline, route, and aircraft model.

The system should feel magical: someone looks out of the window, sees a plane, glances down at the Dial, and immediately knows what it is.

> "That plane out there? It's easyJet, Luton to Palma, Airbus A320neo, 6,800 feet, climbing."

The M5Dial is the presentation layer. The Raspberry Pi does the heavy lifting: ADS-B ingestion, filtering, scoring, enrichment, and serving a tiny UI-friendly API over Wi-Fi. **This repository is that Raspberry Pi service.**

## 3. Vision

Build a tiny physical object that makes the sky feel alive.

This should not feel like a geeky aircraft list squeezed onto a small screen. It should feel like a beautiful little dedicated instrument: a miniature radar/compass that happens to know what is flying outside your house.

The product should create a "massive wow" moment for people who see it:

1. They look out of a window and notice a plane.
2. The Dial chirps or highlights a blip.
3. The radar ring points towards the aircraft.
4. The centre shows the flight and route.
5. Rotating the Dial cycles through other visible aircraft.
6. It feels physical, immediate, and a bit magical.

## 4. Goals

### Primary Goals

* Show the most likely aircraft visible from a specific window.
* Use a circular radar-style UI that matches the M5Dial form factor.
* Make direction intuitive by allowing "up" on the radar to represent either north or the window-facing direction.
* Let the user rotate the Dial to browse other visible aircraft.
* Provide simple audible alerts when relevant aircraft enter the window view.
* Keep the M5Dial firmware simple by doing complex processing on the Pi.
* Make the system easy to demo and impressive to casual observers.

### Secondary Goals

* Support multiple window profiles.
* Support route/model/airline enrichment where possible.
* Provide a basic web/debug UI on the Pi.
* Allow future use with Cardputer Mesh Kit as a portable companion.
* Allow future Meshtastic or notification integrations.

### Non-Goals

* The M5Dial will not decode ADS-B directly.
* The M5Dial will not receive 1090 MHz aircraft signals.
* The first versions will not support true "point at aircraft" behaviour unless a compass/magnetometer is later added.
* The first versions will not depend on paid flight APIs.
* The product is not intended as a safety, navigation, or aviation-critical tool.
* The first version does not need to run away from home.

## 5. Hardware Architecture

### Required Hardware

* Raspberry Pi already running ADS-B stack.
* RTL-SDR or equivalent ADS-B receiver.
* 1090 MHz ADS-B antenna.
* M5Dial.
* USB-C power supply for M5Dial.
* Wi-Fi network shared by Pi and Dial.

### Optional Hardware

* M5Stack Cardputer Mesh Kit.
* M5Stack GPS/BDS Unit for portable Dial use.
* Magnetometer/compass module for true device-heading mode.
* NFC/RFID tags for window profile switching.
* ENV III or other sensors for extra dashboard modes.
* M5Stack C6L as separate Meshtastic node.

## 6. System Architecture

```text
ADS-B Antenna
    ↓
RTL-SDR
    ↓
Raspberry Pi
    ↓
dump1090 / readsb / tar1090
    ↓
SkyDial Pi Service   ← THIS REPOSITORY (flightview-api)
    - aircraft parsing
    - distance/bearing/elevation calculations
    - window filtering
    - scoring
    - route/model enrichment
    - profile management
    - tiny JSON API
    ↓ Wi-Fi
M5Dial   (separate firmware repo; Cardputer in future)
    - radar ring
    - selected aircraft display
    - rotary selection
    - buzzer alerts
    - window profile UI
```

## 7. Core User Experience

### Default Experience

The Dial sits next to a window.

The display shows:

* Outer circular radar ring.
* Aircraft blips positioned around the ring.
* Highlighted selected aircraft.
* Centre aircraft info.
* Small indication of current orientation, e.g. `↑ N`, `↑ WSW`, or `Kitchen`.

When an aircraft enters the configured window view:

* The Dial makes a small chirp.
* The new aircraft appears as a blip.
* If it is the best visible candidate, it becomes selected.
* The centre updates with its information.

### Example Display

```text
       ↑ N
      EZY82K
    LTN → PMI
    A320neo
  3.1 km NNE
  6,800 ft ↑
```

Outer ring:

* Selected aircraft: larger/pulsing blip.
* Other visible aircraft: smaller blips.
* Optional window cone arc.
* Optional compass ticks.

## 8. User Stories

### Core Stories

#### US1 — See the likely aircraft out of the window

As a user looking out of a window,
I want the Dial to show the most likely visible aircraft,
so that I can identify what I am seeing without opening a phone or laptop.

#### US2 — Understand where to look

As a user,
I want the radar ring to show the aircraft direction relative to the window,
so that I know whether to look left, right, straight ahead, or behind.

#### US3 — Browse other aircraft

As a user,
I want to rotate the Dial to cycle through other visible aircraft,
so that I can inspect more than just the auto-selected one.

#### US4 — Configure window direction

As a user,
I want to set the window-facing direction as "up" on the display,
so that the radar ring matches what I see through that window.

#### US5 — Get notified when a new aircraft appears

As a user,
I want a small sound when a relevant aircraft enters the window view,
so that the device feels alive and draws attention at the right moment.

### Advanced Stories

#### US6 — See route and aircraft type

As a user,
I want to see airline, origin, destination, and aircraft model,
so that the device feels like a proper plane-spotting instrument.

#### US7 — Switch between windows

As a user,
I want named profiles for different windows,
so that I can move the Dial around the house and preserve useful orientation settings.

#### US8 — Use RFID/NFC profile switching

As a user,
I want to tap the Dial against a window tag,
so that it automatically switches to the right window profile.

#### US9 — Debug from a browser

As a builder,
I want a Pi-hosted debug page showing what the Dial is receiving,
so that I can tune scoring and visibility rules without repeatedly flashing firmware.

## 9. Feature Set

## 9.1 Radar Ring

The radar ring is the hero UI.

### Requirements

* Render a circular outer ring.
* Plot aircraft blips by relative screen angle.
* Support orientation offset via `radar_up_deg`.
* Highlight selected aircraft.
* Show non-selected visible aircraft as smaller or dimmer blips.
* Support optional visible window cone arc.
* Support optional compass labels/ticks.

### Bearing Transform

Aircraft bearing is calculated as true compass bearing from receiver location to aircraft.

Display angle is calculated as:

```text
screen_angle_deg = aircraft_bearing_deg - radar_up_deg
```

Where:

* `radar_up_deg = 0` means north is up.
* `radar_up_deg = 270` means west is up.
* `radar_up_deg = 180` means south is up.

> **Back-end note:** the Pi service is responsible for computing `screen_angle_deg` from `bearing_deg` and the active profile's `radar_up_deg`, so the Dial firmware never has to do the trigonometry.

### Behaviour

* Top of ring means "straight out of this window" when using a window profile.
* Aircraft outside the current window cone may be hidden, dimmed, or shown as off-view hints depending on mode.

## 9.2 Centre Aircraft Card

The centre of the display shows the selected aircraft.

### MTP Fields

* Callsign or ICAO hex.
* Direction label, e.g. `NNE`, `WSW`.
* Distance in km.
* Altitude in feet.

### MVP Fields

* Callsign.
* Direction label.
* Distance.
* Altitude.
* Vertical movement indicator: climbing, descending, level.
* Track arrow.

### MSP Fields

* Airline.
* Route: origin → destination.
* Aircraft type/model.
* Friendly status line, e.g. `Look WNW`.

### MLP Fields

* Airline logo or stylised operator abbreviation.
* Aircraft silhouette category.
* Flight phase: climb, cruise, descent, approach-ish.
* "Why selected" hint, e.g. `closest in window`, `low and ahead`.

## 9.3 Auto-Selection

The system should auto-select the most likely aircraft the user can see.

### Candidate Scoring Inputs

* Fresh position data.
* Inside current window cone.
* Distance.
* Elevation angle.
* Altitude.
* Vertical rate.
* Bearing closeness to window centre.
* Signal age.
* Optional RSSI.
* Optional route/airport relevance.

### Desired Behaviour

The selected aircraft should be the best visible match, not always the nearest.

Example:

* A helicopter 2 km behind the user should not beat a jet 7 km directly in front of the configured window.
* A high aircraft directly overhead may beat a lower aircraft near the horizon if it is more visually obvious.
* Very stale aircraft positions should be ignored.

### Suggested Initial Formula

```text
score =
  freshness_score
  + window_alignment_score
  + elevation_score
  + distance_score
  + altitude_interest_score
  + vertical_rate_score
```

This should be tuned empirically using the Pi debug view.

## 9.4 Manual Selection

The rotary encoder allows browsing aircraft. (Firmware-side; the Pi supports it by returning a stable, ordered aircraft array with a `selected` index.)

### Controls

| Action               | Behaviour                                    |
| -------------------- | -------------------------------------------- |
| Rotate clockwise     | Next aircraft                                |
| Rotate anticlockwise | Previous aircraft                            |
| Short press          | Lock/unlock selected aircraft                |
| Long press           | Open config                                  |
| No input timeout     | Return to auto-selection                     |
| Touch centre         | Detail view                                  |
| Touch ring           | Future: select aircraft near touched bearing |

### Manual Mode

When the user rotates:

* Device enters manual selection mode.
* Auto-selection pauses.
* Selected aircraft follows rotary input.
* After configurable timeout, device returns to auto mode unless locked.

### Lock Mode

When locked:

* Selection remains on the chosen aircraft while it remains valid.
* If the aircraft disappears or goes stale, lock expires.
* Press again unlocks.

## 9.5 Window Profiles

Window profiles define how the radar behaves in a location.

### Profile Fields

```json
{
  "id": "front_bedroom",
  "name": "Front Bedroom",
  "radar_up_deg": 0,
  "view_cone_deg": 100,
  "max_distance_km": 35,
  "min_elevation_deg": 5,
  "alert_enabled": true
}
```

### Required Profiles

* Default North-Up.
* At least one configurable window profile.

### Desired Profiles

* Front bedroom.
* Kitchen.
* Garden.
* Portable / full 360 mode.

### Profile Selection Methods

#### MTP

Hard-coded profile in Pi config.

#### MVP

Long-press Dial to select profile.

#### MSP

Pi-hosted web config page.

#### MLP

RFID/NFC tags attached near windows. Tapping the Dial to a tag switches to that window profile.

## 9.6 Alerts

The Dial includes a buzzer and should make small, tasteful alerts. The Pi is responsible for the *decisions* that trigger alerts (new aircraft in cone, best-candidate change, feed lost) by exposing enough state in the API; the buzzer itself is firmware.

### Alert Events

* New aircraft enters the current window cone.
* Auto-selected aircraft changes.
* Aircraft becomes almost straight ahead.
* Low/close aircraft appears.
* Data feed lost.
* Wi-Fi reconnected.

### Alert Patterns

| Event                | Sound              |
| -------------------- | ------------------ |
| New visible aircraft | Single soft chirp  |
| New best candidate   | Double chirp       |
| Aircraft leaves view | Low soft tone      |
| Feed lost            | Short warning buzz |
| Feed restored        | Positive chirp     |

### Alert Principles

* Alerts should feel charming, not annoying.
* Quiet mode must be available.
* Repeated alerts should be rate-limited.
* No sound should play on every refresh.

## 9.7 Pi Service

The Pi service is the core product brain **and the subject of this repository.**

### Responsibilities

* Fetch raw aircraft JSON from local ADS-B decoder.
* Normalise data across `dump1090`, `readsb`, or `tar1090`.
* Calculate distance from receiver.
* Calculate true bearing.
* Calculate elevation angle.
* Filter stale aircraft.
* Filter based on selected profile.
* Score candidates.
* Enrich aircraft data where possible.
* Serve M5-friendly JSON.
* Serve optional debug web UI.

### Initial Endpoints

```text
GET /m5/sky
GET /m5/sky?profile=front_bedroom
GET /m5/status
GET /m5/profiles
POST /m5/profile
```

### Example `/m5/sky` Response

```json
{
  "ok": true,
  "now": 1782475200,
  "profile": {
    "id": "front_bedroom",
    "name": "Front Bedroom",
    "radar_up_deg": 0,
    "view_cone_deg": 100
  },
  "selected": 0,
  "aircraft": [
    {
      "flight": "EZY82K",
      "hex": "407F35",
      "airline": "easyJet",
      "route": "LTN → PMI",
      "model": "Airbus A320neo",
      "bearing_deg": 18,
      "bearing_label": "NNE",
      "screen_angle_deg": 18,
      "distance_km": 3.1,
      "alt_ft": 6800,
      "speed_kt": 245,
      "track_deg": 152,
      "track_arrow": "↘",
      "vertical_rate_fpm": 900,
      "vertical_label": "climbing",
      "elevation_deg": 24,
      "seen": 0.8,
      "score": 91,
      "selected_reason": "ahead and visible"
    }
  ]
}
```

## 9.8 Data Enrichment

### Raw ADS-B Fields

Expected from decoder:

* ICAO hex.
* Callsign.
* Latitude.
* Longitude.
* Altitude.
* Ground speed.
* Track.
* Vertical rate.
* Squawk.
* Seen age.
* RSSI if available.

### Enriched Fields

Nice-to-have:

* Airline name.
* Origin.
* Destination.
* Aircraft model.
* Aircraft manufacturer.
* Registration.
* Wake category or aircraft size class.

### Enrichment Strategy

#### Phase 1

No external enrichment. Show:

* callsign
* direction
* distance
* altitude

#### Phase 2

Local static mapping:

* airline prefix mapping, e.g. `BAW = British Airways`, `EZY = easyJet`
* aircraft hex database if available

#### Phase 3

Cached route/model lookup:

* API-backed lookup where available
* local cache to avoid repeated API calls
* graceful fallback when data unavailable

### Enrichment Principle

The product must still be impressive without route/model data. Route/model enriches the wow, but the core magic is direction + visible aircraft matching.

## 9.9 Debug Web UI

A simple Pi-hosted page should show what the Dial sees. (Served by this repository's service.)

### Purpose

* Tune visibility scoring.
* Verify window direction.
* See candidate aircraft.
* Debug stale data.
* Preview M5Dial payload.

### Features

* Current profile.
* Current selected aircraft.
* List of candidate aircraft with scores.
* Bearing/elevation/distance table.
* Raw vs filtered count.
* Last ADS-B fetch time.
* Last M5Dial poll time.
* Optional browser radar preview.

## 10. Phasing

## 10.1 Minimum Testable Product — MTP

### Objective

Prove the core loop:

> Pi reads aircraft → filters candidates → Dial displays one selected aircraft.

### Must Have

#### Pi

* Read local `aircraft.json`.
* Parse aircraft with lat/lon.
* Calculate distance and bearing.
* Return top nearest aircraft via `/m5/sky`.
* Hard-coded home receiver coordinates.
* Hard-coded profile with `radar_up_deg = 0`.

#### Dial

* Connect to Wi-Fi.
* Poll `/m5/sky`.
* Display selected callsign/hex.
* Display direction label.
* Display distance.
* Display altitude.
* Draw simple outer circle.
* Draw one blip for selected aircraft.

### Does Not Need

* Route/model enrichment.
* Multiple profiles.
* Alerts.
* Manual rotary selection.
* Fancy radar ring.
* Window cone filtering.
* Debug UI.

### Success Criteria

* Dial updates every 1–2 seconds.
* Dial shows a real live aircraft from the Pi.
* The displayed direction broadly matches where the aircraft is.
* The device can sit powered by a window for 30 minutes without crashing.

### MTP Example Display

```text
EZY82K
NNE
3.1 km
6800 ft
```

## 10.2 Minimum Viable Product — MVP

### Objective

Make it useful as a window-sill aircraft identifier.

### Must Have

#### Pi

* Window profile with:
  * `radar_up_deg`
  * `view_cone_deg`
  * `max_distance_km`
  * `min_elevation_deg`
* Candidate filtering by window cone.
* Basic scoring.
* `/m5/sky` returns up to 8 visible aircraft.
* Selected aircraft is best candidate, not simply nearest.
* Basic status endpoint.

#### Dial

* Full radar ring with multiple aircraft blips.
* Selected blip highlighted.
* Centre aircraft display.
* Rotary selection.
* Auto-selection timeout.
* Press to return to auto.
* Buzzer alert for new best candidate.
* Simple config for current profile or hard-coded profile selection.

### Success Criteria

* Someone looking out of the configured window can use the Dial to identify likely visible aircraft.
* Turning the Dial cycles through other aircraft.
* Auto-selection feels broadly sensible.
* Alerts happen at useful moments, not constantly.
* The product is demoable to family/friends.

### MVP Example Display

```text
↑ N
EZY82K
Look NNE
3.1 km
6,800 ft ↑
```

## 10.3 Minimum Shareable Product — MSP

### Objective

Make it polished enough to show online or share with other makers.

### Must Have

#### Pi

* Config file for multiple profiles.
* Pi-hosted debug web UI.
* Better scoring with visible reasons.
* Airline prefix enrichment.
* Optional local aircraft model database.
* Caching layer for enrichment.
* Installer/setup notes.
* Clear README.

#### Dial

* Polished radar ring.
* Smooth redraw.
* Distinct states:
  * connecting
  * no aircraft
  * active
  * feed lost
  * config
* Named profile selection.
* Better alert patterns.
* Quiet mode.
* Detail view.
* Attractive typography/layout within M5Dial constraints.

### Nice to Have

* RFID/NFC profile switching.
* Browser preview of radar ring.
* Simple OTA or easy firmware update route.
* Demo mode using recorded ADS-B data.

### Success Criteria

* Project can be filmed and understood in under 20 seconds.
* Another technically capable person can build it from the README.
* The UI looks intentional rather than like a debug display.
* It has a clear "wow" demo:
  * point at window
  * Dial chirps
  * route/model appears
  * aircraft blip matches real sky position

### MSP Demo Script

1. Show the Dial next to the window.
2. Show an aircraft outside.
3. Dial chirps.
4. Camera moves to Dial.
5. It shows:
   * `BAW217`
   * `Heathrow → Barcelona`
   * `A320neo`
   * `Look WNW`
6. Rotate the Dial to show other aircraft around the sky.

## 10.4 Maximum Lovable Product — MLP

### Objective

Make it feel like a beautiful dedicated consumer object.

### Must Have

#### Experience

* Feels alive even when idle.
* Subtle sweep/radar animation.
* Soft pulsing selected blip.
* Beautiful alert sounds within buzzer limitations.
* Route/model/operator enrichment feels instant due to caching.
* Window profiles feel effortless.
* Device recovers cleanly from Wi-Fi/feed loss.
* Works reliably as an always-on appliance.

#### Advanced Features

* RFID/NFC window profile tags.
* Full 360 mode and window HUD mode.
* Interesting aircraft alerts.
* Aircraft trails.
* Day/night display mode.
* Brightness control.
* Quiet hours.
* Historical "last seen" mini log.
* Optional Cardputer companion view.
* Optional Meshtastic notification bridge.
* Optional portable mode using GPS and phone hotspot.
* Optional compass/magnetometer support for true heading.

#### Visual Polish

* Radar ring has:
  * outer compass ticks
  * view cone arc
  * selected aircraft pulse
  * aircraft travel direction tick
  * off-view hint markers
* Centre card has:
  * callsign
  * airline/route/model
  * direction/distance/altitude
  * vertical state
* Loading and error states are charming.

### Success Criteria

* People immediately ask, "Wait, how does it know that?"
* It becomes something worth leaving plugged in permanently.
* It feels more like a tiny aviation instrument than a dev board project.
* The maker community would recognise it as a polished, desirable build.

## 11. UI States

### 11.1 Boot

```text
SkyDial
Connecting...
```

### 11.2 Wi-Fi Connected, Feed Connecting

```text
SkyDial
Wi-Fi OK
Waiting for Pi...
```

### 11.3 No Aircraft

```text
Quiet sky
No visible aircraft
```

### 11.4 Active

Shows radar ring and selected aircraft.

### 11.5 Manual Selection

Small indicator:

```text
MANUAL
```

Auto-selection paused.

### 11.6 Locked Selection

Small indicator:

```text
LOCKED
```

### 11.7 Feed Lost

```text
ADS-B feed lost
Last seen 42s ago
```

### 11.8 Config

```text
Profile
Front Bedroom
↑ N
Cone 100°
```

## 12. Data Model

### Aircraft Object

```json
{
  "flight": "EZY82K",
  "hex": "407F35",
  "airline": "easyJet",
  "origin": "LTN",
  "destination": "PMI",
  "route": "LTN → PMI",
  "model": "Airbus A320neo",
  "lat": 51.9,
  "lon": -0.2,
  "bearing_deg": 18,
  "bearing_label": "NNE",
  "screen_angle_deg": 18,
  "distance_km": 3.1,
  "alt_ft": 6800,
  "speed_kt": 245,
  "track_deg": 152,
  "track_arrow": "↘",
  "vertical_rate_fpm": 900,
  "vertical_label": "climbing",
  "elevation_deg": 24,
  "seen": 0.8,
  "seen_pos": 1.1,
  "rssi": -12.4,
  "score": 91,
  "selected_reason": "ahead and visible"
}
```

### Profile Object

```json
{
  "id": "front_bedroom",
  "name": "Front Bedroom",
  "radar_up_deg": 0,
  "view_cone_deg": 100,
  "max_distance_km": 35,
  "min_elevation_deg": 5,
  "alert_enabled": true,
  "quiet_mode": false
}
```

## 13. Technical Design Notes

### Pi Language

Recommended:

* Python.
* Flask or FastAPI.
* Requests or direct file read for ADS-B JSON.
* Optional SQLite cache for enrichment.

### Dial Firmware

Recommended:

* Arduino IDE or PlatformIO.
* M5Dial / M5Unified / M5GFX.
* WiFi.
* HTTPClient.
* ArduinoJson.

### Polling

Suggested:

* Dial polls Pi every 1–2 seconds.
* Pi may cache ADS-B source response for 1 second.
* Dial should handle stale response gracefully.

### Performance Constraints

* Dial should receive small JSON only.
* Limit aircraft array to 8–12 candidates.
* Avoid parsing full raw ADS-B feed on M5Dial.
* Pi should precompute angles and labels.

### Reliability

* If Pi unavailable, show clear "feed lost" state.
* If Wi-Fi unavailable, retry with friendly state.
* If no aircraft in cone, show "quiet sky".
* If selected aircraft disappears, auto-select next best.

## 14. Security and Safety

* Device is receive-only from an aviation perspective.
* It must not transmit ADS-B or aviation-band data.
* Pi service should be local network only by default.
* No public exposure required.
* API keys, if used for enrichment, must remain on the Pi, never on the Dial.
* The product must not present itself as aviation-grade, safety-critical, or suitable for navigation.

## 15. Open Questions

1. Which ADS-B stack is running on the Pi: `dump1090-fa`, `readsb`, `tar1090`, or other?
2. What exact local aircraft JSON endpoint is available?
3. What are the actual receiver coordinates?
4. Which window should be the first target profile?
5. What is the window's approximate compass direction?
6. What should the default view cone be: 70°, 90°, 100°, 120°?
7. Should aircraft behind the user be hidden or shown dimmed?
8. Which enrichment source should be used first?
9. Should the Pi service be packaged as a systemd service from the start?
10. Should the Dial support config locally, or should all config live on the Pi?

## 16. Suggested Build Order

### Step 1 — Pi Data Probe

* Confirm ADS-B JSON endpoint.
* Write script to fetch aircraft.
* Print nearest aircraft with distance/bearing.

### Step 2 — Pi API MTP

* Create `/m5/sky`.
* Return one selected aircraft.
* Add receiver coordinates.
* Add bearing/distance/elevation.

### Step 3 — Dial MTP

* Connect to Wi-Fi.
* Fetch `/m5/sky`.
* Display callsign/distance/altitude.
* Draw simple circle and one blip.

### Step 4 — Multi-Aircraft Radar

* Return up to 8 candidates.
* Draw multiple blips.
* Highlight selected.

### Step 5 — Window Profile

* Add `radar_up_deg`.
* Add `view_cone_deg`.
* Filter/score by window.

### Step 6 — Rotary Interaction

* Rotate to cycle aircraft.
* Press to return to auto.
* Add manual timeout.

### Step 7 — Alerts

* Chirp when best candidate changes.
* Add quiet mode/rate limiting.

### Step 8 — Polish

* Improve radar ring.
* Add centre card.
* Add error/loading states.
* Add debug web UI.

### Step 9 — Enrichment

* Add airline prefix mapping.
* Add route/model cache.
* Display route/model when available.

### Step 10 — Shareable Package

* README.
* Wiring/power notes.
* Config examples.
* Demo mode.
* Screenshots/video.

## 17. MVP Acceptance Test

Given:

* The Pi is receiving ADS-B aircraft.
* The M5Dial is powered and connected to Wi-Fi.
* A window profile is configured.

When:

* An aircraft enters the configured view cone.

Then:

* The Dial chirps once.
* The aircraft appears on the outer radar ring in the correct relative direction.
* The centre shows callsign, direction, distance, and altitude.
* Rotating the Dial selects other aircraft.
* Pressing the Dial returns to auto-selection.
* If no aircraft are visible, the Dial shows a calm "quiet sky" state.

## 18. Wow Acceptance Test

A non-technical person should be able to look at the device and understand it within five seconds.

They should be able to say:

> "Oh, the dots are planes around us, and the middle is the plane we're probably looking at."

Within twenty seconds, they should say something like:

> "That's actually really cool."

The product succeeds when it feels like a tiny, delightful aviation instrument rather than a development board project.
