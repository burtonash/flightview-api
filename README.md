# flightview-api — SkyDial Pi back-end

The **Raspberry Pi back-end** for **SkyDial**, a window-sill ADS-B aircraft HUD. It ingests ADS-B
data from a local decoder, computes distance/bearing/elevation, filters and scores aircraft against
window profiles, enriches them, and serves a tiny precomputed JSON API over Wi-Fi to an **M5Dial**
(and, in future, a **Cardputer**).

The Dial stays dumb — this service does all the maths and hands over ready-to-draw JSON.

> Product spec: [`PRD.md`](PRD.md) · design: [`ARCHITECTURE.md`](ARCHITECTURE.md) · plan:
> [`EPICS.md`](EPICS.md) · install: [`DEPLOYMENT.md`](DEPLOYMENT.md)

## What it does

```
ADS-B decoder (dump1090-fa / readsb / tar1090)  →  aircraft.json
        │
        ▼
  flightview-api  ──  ingest → distance/bearing/elevation → cone-filter → score →
                      enrich → select → derive alert state  →  tiny /m5 JSON
        │  Wi-Fi
        ▼
  M5Dial  (radar ring + centre card + buzzer)
```

## Quick start (any machine, no receiver needed)

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

# Run against the bundled demo feed (recorded frames):
SKYDIAL_SOURCE_TYPE=demo python -m skydial
```

Then open the debug UI at <http://localhost:8090/> and the API at
<http://localhost:8090/m5/sky>.

To point at a real decoder, copy `config.example.yaml` to `config.yaml`, set your receiver
coordinates and `source.location`, then `python -m skydial`. Full install (systemd on a Pi) is in
[`DEPLOYMENT.md`](DEPLOYMENT.md).

## API

| Endpoint | Purpose |
| -------- | ------- |
| `GET /m5/sky` | Scored, ordered visible aircraft + `selected` index. `?profile=<id>` overrides. |
| `GET /m5/status` | Feed health, last-fetch age, raw vs filtered counts, service state. |
| `GET /m5/profiles` | List window profiles + the active one. |
| `POST /m5/profile` | Switch active profile — body `{"id": "front_bedroom"}`. |
| `GET /` or `/debug` | Responsive debug UI: radar preview + candidate table with per-factor scores. |

Example `GET /m5/sky` (trimmed):

```json
{
  "ok": true, "now": 1782475200, "state": "active", "selected": 0,
  "profile": {"id": "front_bedroom", "radar_up_deg": 0, "view_cone_deg": 100},
  "aircraft": [
    {"flight": "EZY82K", "hex": "407f35", "airline": "easyJet",
     "bearing_label": "NNE", "screen_angle_deg": 14.0, "distance_km": 2.29,
     "alt_ft": 6800, "vertical_label": "climbing", "score": 87.0,
     "selected_reason": "straight ahead and close"}
  ],
  "alerts": ["new_best_candidate"]
}
```

`state` is one of `connecting` · `quiet-sky` · `active` · `feed-lost`. `alerts` names discrete
transitions (`new_aircraft`, `new_best_candidate`, `feed_lost`, `feed_restored`) for the Dial's
buzzer — nothing fires on every refresh.

## Configuration

All config lives on the Pi (the Dial only *selects* a profile). Copy `config.example.yaml` →
`config.yaml`; the service reads `./config.yaml` or `$SKYDIAL_CONFIG`. Key knobs: `receiver` coords,
`source` (type + location), `scoring` weights (tune via the debug UI), and `profiles` (one per
window). `config.yaml` is git-ignored so real coordinates/keys never get committed.

## Development

```bash
pip install -r requirements.txt pytest
python -m pytest
```

Layout: `skydial/` (package) — `sources/` adapters, `geo.py`, `filters.py`, `scoring.py`,
`enrichment.py`, `profiles.py`, `alerts.py`, `pipeline.py` (orchestrator), `app.py` (FastAPI) +
`debug_ui.py`. Tests in `tests/`. See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the seams.

## Safety

Receive-only; never transmits. Bind to the local network only — do **not** expose to the internet.
Not an aviation-grade or navigation tool.
