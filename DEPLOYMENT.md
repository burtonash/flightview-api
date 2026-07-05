# DEPLOYMENT — flightview-api (SkyDial Pi back-end)

How to install and run the SkyDial Pi service on a Raspberry Pi alongside an existing ADS-B
decoder, as an always-on systemd appliance. For a laptop/dev run, see the Quick Start in
[`README.md`](README.md).

## Prerequisites

- A Raspberry Pi already running an ADS-B decoder that produces `aircraft.json`:
  **dump1090-fa**, **readsb**, or **tar1090** (any is fine — the source adapter normalises them).
- Python **3.11+** (`python3 --version`).
- The Pi and the M5Dial on the **same Wi-Fi / LAN**.
- Your receiver's **latitude/longitude** (decimal degrees).

Find your `aircraft.json` — it's usually one of:

| Decoder | Typical URL / path |
| ------- | ------------------ |
| tar1090 / readsb | `http://127.0.0.1:8080/data/aircraft.json` |
| dump1090-fa (web) | `http://127.0.0.1/dump1090-fa/data/aircraft.json` |
| dump1090-fa (file) | `/run/dump1090-fa/aircraft.json` |
| adsb.im / ultrafeeder (Docker) | `http://127.0.0.1:<mapped-port>/data/aircraft.json` |

> **adsb.im / ultrafeeder note:** the feeder image runs tar1090/readsb inside a Docker
> container whose web root (container port 80) is published on a **non-standard host
> port** — not 8080. Run `docker ps` and look at the `ultrafeeder` row's port mapping
> (e.g. `0.0.0.0:1090->80/tcp` means the feed is at `http://127.0.0.1:1090/data/aircraft.json`).
> The `:8754` feeder homepage gates `/data/` with a 403, so point at the mapped tar1090
> port, not 8754.

Confirm it responds:

```bash
curl -s http://127.0.0.1:8080/data/aircraft.json | head -c 200
```

## 1. Install the service

```bash
sudo mkdir -p /opt/flightview-api
sudo chown "$USER" /opt/flightview-api
git clone https://github.com/burtonash/flightview-api /opt/flightview-api
cd /opt/flightview-api

python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## 2. Configure

```bash
cp config.example.yaml config.yaml
nano config.yaml
```

Set at minimum:

- `receiver.lat` / `receiver.lon` — your real coordinates.
- `source.location` — your `aircraft.json` URL/path from the table above.
- `profiles` — one per window. `radar_up_deg` is the compass direction the window faces
  (0 = N, 90 = E, 180 = S, 270 = W); `view_cone_deg` is how wide a slice of sky it sees
  (start ~100°; 360 shows everything). Set `active_profile` to the one you want at boot.

`config.yaml` is git-ignored, so your coordinates never get committed.

## 3. Smoke-test by hand

```bash
.venv/bin/python -m skydial
```

From another device on the LAN, open `http://<pi-ip>:8090/` (debug UI) and
`http://<pi-ip>:8090/m5/sky`. You should see live aircraft. `Ctrl-C` to stop.

If the sky is quiet or you have no live feed yet, run against the bundled demo frames:

```bash
SKYDIAL_SOURCE_TYPE=demo .venv/bin/python -m skydial
```

## 4. Run as a systemd service

A unit file is provided at [`deploy/skydial-api.service`](deploy/skydial-api.service). It assumes
the install path `/opt/flightview-api`, the venv at `.venv`, and user `pi` — edit if yours differ.

> **Installing under `/home` instead of `/opt`?** The shipped unit sets
> `ProtectHome=true`, which makes systemd hide `/home` from the service — so a
> home-based `WorkingDirectory` becomes unreachable and the service won't start. If you
> install under your home directory, change `ProtectHome=true` to `ProtectHome=read-only`
> and set `ReadWritePaths=` to your install dir (the enrichment SQLite cache needs to
> write there). Also set `User=` to your own account and update every `/opt/flightview-api`
> path. Example for `~/scripts/flightview-api`:
>
> ```ini
> User=youruser
> WorkingDirectory=/home/youruser/scripts/flightview-api
> Environment=SKYDIAL_CONFIG=/home/youruser/scripts/flightview-api/config.yaml
> ExecStart=/home/youruser/scripts/flightview-api/.venv/bin/python -m skydial
> ProtectHome=read-only
> ReadWritePaths=/home/youruser/scripts/flightview-api
> ```

```bash
sudo cp deploy/skydial-api.service /etc/systemd/system/
# adjust User=/paths in the unit if needed:
sudo nano /etc/systemd/system/skydial-api.service

sudo systemctl daemon-reload
sudo systemctl enable --now skydial-api
systemctl status skydial-api
journalctl -u skydial-api -f      # follow logs
```

The service restarts on failure and self-heals across feed/Wi-Fi drops (it reports `feed-lost`
rather than crashing). To apply config changes: `sudo systemctl restart skydial-api`.

## 5. Point the M5Dial at it

Configure the Dial firmware to poll `http://<pi-ip>:8090/m5/sky` every 1–2 seconds. The Pi caches
the source read (~1s) so multiple Dials won't hammer the decoder.

## Updating

```bash
cd /opt/flightview-api && git pull
.venv/bin/pip install -r requirements.txt      # if deps changed
sudo systemctl restart skydial-api
```

## Security notes

- **Local network only.** The default bind is `0.0.0.0:8090` for LAN access — do **not** port-forward
  or expose it to the internet. Restrict with your firewall/router if needed.
- The service is **receive-only** and never transmits on aviation bands.
- Any future enrichment API keys belong in `config.yaml`/env-vars on the Pi — never in a payload to
  the Dial, never committed.

## Troubleshooting

| Symptom | Likely cause / fix |
| ------- | ------------------ |
| `state: feed-lost` | `source.location` wrong or decoder down — re-check the `curl` in Prerequisites. For an adsb.im/ultrafeeder box, confirm the mapped port via `docker ps` (it's not 8080). |
| `/m5/status` stuck at `connecting`, `feed_ok: false` | Expected if nothing has polled `/m5/sky` yet — the fetch/scoring cycle is driven by `/m5/sky` (what the Dial polls), and `/m5/status` only *reports* state. `curl .../m5/sky` once, then re-check status; it should flip to `active`. Not a fault. |
| `state: quiet-sky` always | Cone too narrow / distance too small, or genuinely no traffic. Widen `view_cone_deg`/`max_distance_km`, or test with `SKYDIAL_SOURCE_TYPE=demo`. |
| Direction looks wrong | Fix `radar_up_deg` for the window; verify against the debug UI radar preview. |
| Auto-pick feels off | Tune `scoring` weights in `config.yaml` using the per-factor columns in the debug UI. |
| Port already in use | Change `server.port` in `config.yaml`. |
