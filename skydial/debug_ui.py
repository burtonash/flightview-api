"""Server-hosted test harness — the SkyDial v2 "Pi Web Harness" surface.

Self-contained HTML (system-font fallback; Google Fonts as progressive
enhancement so it still renders offline on the LAN). Polls the live /m5
contract and renders:

  * the round **DIAL render** — a faithful port of the M5Dial sector-dial
    (16 bearing wedges, proximity glow, selected-aircraft detail card,
    overhead flash) driven by real /m5/sky data;
  * the **flights-on-screen** table (click a row to select on the dial);
  * a **test controls** panel wired to real endpoints only — profile switch
    (POST /m5/profile), colour-by, poll-rate, pause/refresh, quiet, and the
    /m5/log recent-sightings panel.

The dial is the shippable render; the table + controls are harness-only dev
affordances, never shown on the device. Responsive by default.
"""

DEBUG_HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SkyDial · Pi Test Harness</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root{
    --font: 'Space Grotesk', system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    --mono: 'IBM Plex Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
    --dial:#4f7cff;
    --text:#eef0ff; --sub:#9aa2d8; --acc:#8a9bff; --ring:#343a72; --tick:#7a82c4;
    --surface:rgba(255,255,255,.06); --edge:rgba(255,255,255,.14);
    --screen-bg: radial-gradient(circle at 50% 36%,#1d2452 0%,#141838 58%,#0c0f24 100%);
  }
  *{box-sizing:border-box}
  html,body{margin:0;padding:0}
  body{
    font-family:var(--font); color:#e7ecf3;
    background:radial-gradient(1200px 700px at 50% -10%,#1a2230 0%,#0e1116 55%,#090b0f 100%);
    -webkit-font-smoothing:antialiased; min-height:100vh; padding:26px 18px 48px;
  }
  @keyframes sd-secflash{0%,100%{opacity:.55}50%{opacity:1}}
  @keyframes sd-toast{0%{transform:translateX(14px);opacity:0}12%{transform:translateX(0);opacity:1}82%{opacity:1}100%{opacity:0}}
  .wrap{max-width:1120px;margin:0 auto}

  /* header */
  .head{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
  .logo{width:30px;height:30px;border-radius:8px;background:linear-gradient(145deg,#39435a,#1d2230);border:1px solid #2c3442;box-shadow:inset 0 1px 1px rgba(255,255,255,.1)}
  .brand{font-size:23px;font-weight:700;letter-spacing:-.02em}
  .pill{font-family:var(--mono);font-size:11px;letter-spacing:.12em;text-transform:uppercase;padding:4px 9px;border:1px solid #262b34;border-radius:999px;color:#7d8696}
  .tag{margin-top:9px;color:#8b94a3;font-size:13.5px;max-width:520px;line-height:1.5}

  /* harness shell */
  .shell{margin-top:22px;border-radius:18px;overflow:hidden;border:1px solid #20262f;box-shadow:0 30px 70px -30px rgba(0,0,0,.8)}
  .chrome{display:flex;align-items:center;gap:10px;padding:10px 14px;background:#191d24;border-bottom:1px solid #0c0f14}
  .dots{display:flex;gap:7px}
  .dots i{width:11px;height:11px;border-radius:50%;display:block}
  .url{flex:1;display:flex;align-items:center;gap:8px;background:#0c0f14;border:1px solid #262d38;border-radius:8px;padding:6px 12px;max-width:420px;margin:0 auto;font-family:var(--mono);font-size:12px;color:#aeb7c4}
  .url .lock{color:#4f9a6a;font-size:11px}
  .url .host{margin-left:auto;font-size:10px;color:#5f6773}
  .clock{font-family:var(--mono);font-size:11px;color:#7d8696}

  .legend{display:flex;align-items:center;gap:12px;flex-wrap:wrap;padding:12px 16px;background:#0e1218;border-bottom:1px solid #1c222b}
  .legend .ttl{font-size:13px;font-weight:700;color:#e7ecf3}
  .legend .sp{flex:1;min-width:12px}
  .badge{display:inline-flex;align-items:center;gap:7px;padding:5px 11px;border-radius:9px;font-size:10.5px;font-weight:700}
  .badge.dial{border:1.5px solid var(--dial);background:rgba(79,124,255,.12);color:#dfe6f2}
  .badge.dial .g{color:var(--dial);font-size:12px}
  .badge.harn{border:1.5px dashed #6b7688;color:#aeb7c4}
  .badge.harn .g{color:#8b94a3;font-size:12px}

  .body{padding:20px;background:#070a0e}
  .row{display:flex;gap:20px;flex-wrap:wrap;align-items:flex-start}

  /* dial box */
  .dialbox{flex:0 0 auto;border:1.5px solid var(--dial);border-radius:16px;background:#080b10;padding:16px;position:relative}
  .cap-dial{position:absolute;top:-11px;left:16px;background:var(--dial);color:#05070c;font-family:var(--mono);font-size:9.5px;font-weight:700;letter-spacing:.08em;padding:3px 9px;border-radius:6px}
  .screen{position:relative;width:min(340px,84vw);aspect-ratio:1;border-radius:50%;overflow:hidden;cursor:pointer;background:var(--screen-bg);box-shadow:inset 0 0 20px rgba(0,0,0,.9),0 0 0 4px #050608}
  .screen svg#dial{position:absolute;inset:0;width:100%;height:100%}
  .glare{position:absolute;inset:0;border-radius:50%;background:linear-gradient(150deg,rgba(255,255,255,.10) 0%,rgba(255,255,255,0) 32%);pointer-events:none}
  .card{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:0 44px;pointer-events:none}
  .cap-note{text-align:center;font-family:var(--mono);font-size:9.5px;color:#5f6773;margin-top:11px;line-height:1.55}

  /* table box */
  .tablebox{flex:1 1 380px;min-width:320px;border:1.5px dashed #6b7688;border-radius:16px;background:#0a0d12;padding:16px 14px 12px;position:relative}
  .cap-harn{position:absolute;top:-11px;left:16px;background:#0a0d12;color:#aeb7c4;font-family:var(--mono);font-size:9.5px;font-weight:700;letter-spacing:.08em;padding:3px 9px;border-radius:6px;border:1px dashed #6b7688}
  .strip{display:flex;gap:16px;flex-wrap:wrap;font-family:var(--mono);font-size:10.5px;color:#7d8696;margin:2px 0 10px}
  .strip b{color:#cfd6e0}
  .scroll{overflow-x:auto}
  table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums}
  th{font-family:var(--mono);font-size:9px;letter-spacing:.08em;color:#6b7482;text-transform:uppercase;padding:7px 9px;border-bottom:1px solid #222833;white-space:nowrap;text-align:right}
  th:nth-child(1),th:nth-child(2),th:nth-child(4),th:nth-child(5){text-align:left}
  td{font-family:var(--mono);font-size:11.5px;color:#cfd6e0;padding:7px 9px;white-space:nowrap;border-bottom:1px solid #171c24;text-align:right}
  td:nth-child(1),td:nth-child(2),td:nth-child(4),td:nth-child(5){text-align:left}
  tbody tr{cursor:pointer}
  .rowdot{width:9px;height:9px;border-radius:50%;border:1px solid #3a4250}
  .empty{font-family:var(--mono);font-size:12px;color:#5f6773;padding:26px 0;text-align:center}
  .foot{font-family:var(--mono);font-size:9.5px;color:#4e5663;margin-top:10px;line-height:1.5}

  /* controls */
  .controls{margin-top:18px;border:1.5px dashed #6b7688;border-radius:16px;background:#0a0d12;padding:16px;position:relative}
  .ctl-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px}
  .ctl h4{margin:0 0 7px;font-family:var(--mono);font-size:9.5px;letter-spacing:.1em;text-transform:uppercase;color:#7d8696;font-weight:600}
  .segm{display:flex;flex-wrap:wrap;gap:6px}
  .segm button{cursor:pointer;font-family:var(--mono);font-size:11px;padding:6px 10px;border-radius:8px;border:1px solid #242b35;background:#12161d;color:#aeb7c4;transition:all .15s}
  .segm button:hover{border-color:#39435a}
  .segm button.on{background:#e7ecf3;color:#0e1116;border-color:#e7ecf3;font-weight:700}
  .logpanel{margin-top:14px}
  .logpanel .logrow{display:flex;gap:12px;flex-wrap:wrap;font-family:var(--mono);font-size:10.5px;color:#8b94a3;padding:5px 0;border-bottom:1px solid #141a22}
  .logpanel .logrow b{color:#cfd6e0}

  /* toasts */
  .toasts{position:fixed;right:18px;bottom:18px;display:flex;flex-direction:column;gap:8px;z-index:50}
  .toast{font-family:var(--mono);font-size:12px;padding:9px 13px;border-radius:10px;background:#12161d;border:1px solid #2a3346;color:#e7ecf3;box-shadow:0 10px 30px -10px rgba(0,0,0,.7);animation:sd-toast 3.6s ease forwards}
</style>
</head>
<body>
<div class="wrap">
  <div class="head">
    <div class="logo"></div>
    <div class="brand">SkyDial</div>
    <div class="pill">M5Dial · ADS-B Window HUD</div>
  </div>
  <div class="tag">Pi test harness — the round screen is the shippable dial render; the table and controls around it are dev-only affordances served over Wi-Fi.</div>

  <div class="shell">
    <div class="chrome">
      <div class="dots"><i style="background:#ff5f57"></i><i style="background:#febc2e"></i><i style="background:#28c840"></i></div>
      <div class="url"><span class="lock">●</span><span id="urlhost">http://skydial.local</span><span class="host">Pi Zero 2 W</span></div>
      <div class="clock" id="clock">--:--:--</div>
    </div>
    <div class="legend">
      <div class="ttl">SkyDial — Pi Test Harness</div>
      <div class="sp"></div>
      <div class="badge dial"><span class="g">◉</span><span>DIAL — device firmware</span></div>
      <div class="badge harn"><span class="g">▤</span><span>HARNESS — Pi web, dev only</span></div>
    </div>

    <div class="body">
      <div class="row">
        <!-- DIAL RENDER -->
        <div class="dialbox">
          <div class="cap-dial">◉ DIAL RENDER · SHIPS TO DEVICE</div>
          <div class="screen" id="screen" onclick="cycleSelect(1)">
            <svg id="dial" viewBox="0 0 340 340" aria-label="sector dial"></svg>
            <div class="card" id="card"></div>
            <div class="glare"></div>
          </div>
          <div class="cap-note">240×240 round · identical render to the M5Dial<br>click the screen to step the selection</div>
        </div>

        <!-- FLIGHTS TABLE -->
        <div class="tablebox">
          <div class="cap-harn">▤ FLIGHTS ON SCREEN · HARNESS TABLE</div>
          <div class="strip" id="strip"></div>
          <div class="scroll">
            <table id="tbl">
              <thead><tr>
                <th></th><th>Flight</th><th>Op</th><th>Route</th><th>Type</th>
                <th>Brg</th><th>Dist</th><th>Alt</th><th>Elev</th><th>Score</th>
              </tr></thead>
              <tbody></tbody>
            </table>
          </div>
          <div class="empty" id="empty" style="display:none"></div>
          <div class="foot">click a row to select it on the dial · this table is a harness affordance, NOT rendered on the device</div>
        </div>
      </div>

      <!-- TEST CONTROLS -->
      <div class="controls">
        <div class="cap-harn">▤ TEST CONTROLS · HARNESS</div>
        <div class="ctl-grid" style="margin-top:6px">
          <div class="ctl"><h4>Window profile</h4><div class="segm" id="c-profile"></div></div>
          <div class="ctl"><h4>Colour by</h4><div class="segm" id="c-colorby">
            <button data-v="airline" class="on">airline</button>
            <button data-v="type">type</button>
            <button data-v="altitude">altitude</button>
          </div></div>
          <div class="ctl"><h4>Poll rate</h4><div class="segm" id="c-poll">
            <button data-v="1000">1s</button>
            <button data-v="2000" class="on">2s</button>
            <button data-v="5000">5s</button>
          </div></div>
          <div class="ctl"><h4>Stream</h4><div class="segm" id="c-stream">
            <button data-v="pause" id="btn-pause">⏸ pause</button>
            <button data-v="refresh">↻ refresh</button>
          </div></div>
          <div class="ctl"><h4>Harness alerts</h4><div class="segm" id="c-quiet">
            <button data-v="on" class="on">🔔 toasts on</button>
          </div></div>
        </div>
        <div class="logpanel">
          <h4 style="margin:0 0 7px;font-family:var(--mono);font-size:9.5px;letter-spacing:.1em;text-transform:uppercase;color:#7d8696;font-weight:600">Recent sightings · /m5/log</h4>
          <div id="log"></div>
        </div>
      </div>
    </div>
  </div>
</div>
<div class="toasts" id="toasts"></div>

<script>
"use strict";
const $ = s => document.querySelector(s);

// ---- theme / palettes (aurora dark, matching the v2 design) ----
const TH = {text:'#eef0ff', sub:'#9aa2d8', acc:'#8a9bff', ring:'#343a72', tick:'#7a82c4',
            surface:'rgba(255,255,255,.06)', edge:'rgba(255,255,255,.14)'};
const CAT = {narrow:'#5b8cff', wide:'#b07cff', cargo:'#ff9f43', light:'#2dd4bf', heli:'#ffd23f'};
const CAT_LABEL = {narrow:'Narrow', wide:'Wide', cargo:'Cargo', light:'Light', heli:'Heli'};
const AIRLINE_PAL = ['#ff6a13','#2f6fd0','#1d52b8','#d21ba0','#1e63a8','#e23139','#1aa3df','#ff5a5f','#f2b50a','#5ec5b8','#22c55e'];
const COMPASS = ['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW','SW','WSW','W','WNW','NW','NNW'];

// ---- config / runtime state ----
let pollMs = 2000, paused = false, colorBy = 'airline', quietToasts = false;
let profiles = [], activeProfile = null;
let lastSky = null, lastStatus = null, lastSelKey = null, pollTimer = null;

// ---- helpers ----
const wrap360 = d => ((d % 360) + 360) % 360;
const wrap180 = d => { d = wrap360(d); return d > 180 ? d - 360 : d; };
const compass = b => COMPASS[Math.round(wrap360(b) / 22.5) % 16];
const fnum = (x, d = 0) => (x == null ? '–' : Number(x).toFixed(d));

function rgba(hex, a){
  const n = parseInt(hex.slice(1), 16);
  return `rgba(${(n>>16)&255},${(n>>8)&255},${n&255},${a})`;
}
function hashIdx(str, len){ let h = 0; for (const ch of (str||'')) h = (h + ch.charCodeAt(0)) % len; return h; }

function classifyCat(ac){
  const m = ((ac.model||'') + ' ' + (ac.type_code||'')).toLowerCase();
  if (/heli|h145|h135|ec13|ec14|as35|r44|r22|bell|s-?76|aw13|aw16|puma|h175/.test(m)) return 'heli';
  if (/cessna|piper|pa-?\d|c1[0-9]{2}|diamond|cirrus|sr2|tbm|da4|light|glider/.test(m)) return 'light';
  if (/freighter|cargo|-?\d{2,3}f\b|77l|74[78].*f/.test(m) || /\b(dhl|fedex|ups|cargolux)\b/.test((ac.airline||'').toLowerCase())) return 'cargo';
  if (/a3[35][05]|a380|a340|b?7[4678]7|777|787|767|350|330|340|380/.test(m)) return 'wide';
  return 'narrow';
}
const altColor = a => a == null ? TH.acc : a < 10000 ? '#2dd4bf' : a < 25000 ? '#5b8cff' : a < 35000 ? '#b07cff' : '#ff6ad5';
function colorFor(ac){
  const cat = classifyCat(ac);
  if (colorBy === 'type') return CAT[cat] || TH.acc;
  if (colorBy === 'altitude') return altColor(ac.alt_ft);
  return AIRLINE_PAL[hashIdx(ac.airline || ac.hex, AIRLINE_PAL.length)];
}
function flightPhase(ac){
  const vr = ac.vertical_rate_fpm || 0, alt = ac.alt_ft || 0, cat = classifyCat(ac);
  if (cat === 'heli') return 'hover';
  if (alt < 4500 && vr > 150) return 'climb';
  if (vr < -200 && alt < 9000) return 'approach';
  if (vr < -200) return 'descent';
  return 'cruise';
}
function opCode(ac){
  if (!ac.flight) return '';
  const m = ac.flight.trim().match(/^[A-Z]{2,3}/);
  return m ? m[0] : '';
}
function selKey(sky){
  if (sky.selected == null || !sky.aircraft[sky.selected]) return null;
  const a = sky.aircraft[sky.selected]; return a.hex || a.flight;
}

// ---- sector-dial geometry (port of v2 renderSectors) ----
const C = 170, OUTER = 150, BAND_IN = OUTER - 9, GAP = 2.6, OVERHEAD_ELEV = 52;
function sectorIdx(screenAngle){ return Math.floor((wrap360(screenAngle) + 11.25) / 22.5) % 16; }
function wedge(a0, a1, ri, ro){
  const p = (a, r) => [C + r * Math.sin(a*Math.PI/180), C - r * Math.cos(a*Math.PI/180)];
  const o0=p(a0,ro), o1=p(a1,ro), i1=p(a1,ri), i0=p(a0,ri);
  return `M${o0[0].toFixed(2)} ${o0[1].toFixed(2)} A${ro} ${ro} 0 0 1 ${o1[0].toFixed(2)} ${o1[1].toFixed(2)} L${i1[0].toFixed(2)} ${i1[1].toFixed(2)} A${ri} ${ri} 0 0 0 ${i0[0].toFixed(2)} ${i0[1].toFixed(2)} Z`;
}
function shapeIcon(cat, color, s){
  s = s || 24;
  const open = `<svg width="${s}" height="${s}" viewBox="0 0 24 24" style="display:block;flex:0 0 auto">`;
  if (cat === 'heli') return open +
    `<line x1="3" y1="6.5" x2="21" y2="6.5" stroke="${color}" stroke-width="1.7" stroke-linecap="round"/>` +
    `<rect x="8.5" y="8" width="6.5" height="9" rx="3" fill="${color}"/>` +
    `<rect x="14" y="11.2" width="7" height="1.7" rx="0.8" fill="${color}"/>` +
    `<line x1="20" y1="9.5" x2="20" y2="14" stroke="${color}" stroke-width="1.7" stroke-linecap="round"/></svg>`;
  if (cat === 'light') return open +
    `<path d="M12 3.2c.7 0 1.1 1 1.1 2.6L21 9.4v1.5l-7.9-1.5.1 4.7 2.5 1.7v1.3L12 16.3 8.2 17.1v-1.3l2.5-1.7.1-4.7L3 10.9V9.4l7.9-3.6c0-1.6.4-2.6 1.1-2.6Z" fill="${color}"/>` +
    `<circle cx="12" cy="3.4" r="1" fill="${color}"/></svg>`;
  return open +
    `<path d="M12 2c.9 0 1.4 1.5 1.4 3.7L21 11v1.9l-7.6-2-.2 5.6 2.6 1.9v1.5L12 20.3l-3.8.6v-1.5l2.6-1.9-.2-5.6L3 12.9V11l7.6-5.3C10.6 3.5 11.1 2 12 2Z" fill="${color}"/></svg>`;
}

function drawDial(sky){
  const svg = $('#dial'), card = $('#card');
  const pr = sky.profile || {};
  const upDeg = pr.radar_up_deg || 0;
  const maxd = pr.max_distance_km || 40;
  const vis = sky.aircraft || [];
  const sel = (sky.selected != null) ? vis[sky.selected] : null;

  // group aircraft into sectors by on-screen angle
  const sectors = {};
  vis.forEach(ac => {
    if (ac.screen_angle_deg == null) return;
    const i = sectorIdx(ac.screen_angle_deg);
    (sectors[i] = sectors[i] || []).push(ac);
  });
  const overheadAc = vis.filter(ac => (ac.elevation_deg || 0) >= OVERHEAD_ELEV);
  const anyOverhead = overheadAc.length > 0;
  const oc = anyOverhead ? colorFor(overheadAc.reduce((m, a) => (a.distance_km||99) < (m.distance_km||99) ? a : m, overheadAc[0])) : null;

  let out = '';
  // hollow ring — every sector at constant thickness (flashes when overhead)
  for (let i = 0; i < 16; i++){
    const ci = i * 22.5, a0 = ci - (11.25 - GAP), a1 = ci + (11.25 - GAP);
    const style = anyOverhead ? ` style="animation:sd-secflash .45s ease-in-out ${(i%4)*0.04}s infinite;filter:drop-shadow(0 0 5px ${oc})"` : '';
    out += `<path d="${wedge(a0,a1,BAND_IN,OUTER)}" fill="${anyOverhead?rgba(oc,0.35):'none'}" stroke="${anyOverhead?oc:TH.ring}" stroke-width="${anyOverhead?2.2:1.6}" stroke-linejoin="round"${style}/>`;
  }
  // occupied sectors — fill intensity + glow by proximity
  Object.keys(sectors).map(Number).forEach(i => {
    const list = sectors[i];
    const closest = list.reduce((m, a) => (a.distance_km||99) < (m.distance_km||99) ? a : m, list[0]);
    const isSel = sel && list.some(a => (a.hex||a.flight) === (sel.hex||sel.flight));
    const rep = (sel && list.find(a => (a.hex||a.flight) === (sel.hex||sel.flight))) || closest;
    const color = colorFor(rep);
    const prox = 1 - Math.min(1, (closest.distance_km || 0) / maxd);
    const overhead = (closest.elevation_deg || 0) >= OVERHEAD_ELEV;
    const op = (isSel ? 0.42 : 0.30) + prox * (isSel ? 0.58 : 0.62);
    const glowR = (prox * 7 + (isSel ? 4 : 0));
    const ci = i * 22.5, a0 = ci - (11.25 - GAP), a1 = ci + (11.25 - GAP);
    let style = '';
    if (glowR > 0.5) style += `filter:drop-shadow(0 0 ${glowR.toFixed(1)}px ${rgba(color,0.85)});`;
    if (overhead) style += 'animation:sd-secflash .5s ease-in-out infinite;';
    out += `<path d="${wedge(a0,a1,BAND_IN,OUTER)}" fill="${rgba(color,op)}" stroke="${color}" stroke-width="${isSel?2.4:1.4}" stroke-linejoin="round"${style?` style="${style}"`:''}/>`;
    if (prox > 0.35)
      out += `<path d="${wedge(a0,a1,BAND_IN,BAND_IN+1.6+prox*2.2)}" fill="${overhead?'#ffffff':rgba(color,Math.min(1,0.4+prox))}"/>`;
    if (list.length > 1){
      const px = C + (OUTER-5)*Math.sin(ci*Math.PI/180), py = C - (OUTER-5)*Math.cos(ci*Math.PI/180);
      out += `<text x="${px.toFixed(1)}" y="${(py+3).toFixed(1)}" fill="#fff" font-size="8.5" font-family="var(--mono)" text-anchor="middle" font-weight="700">${list.length}</text>`;
    }
  });
  // N/E/S/W compass ticks (rotated by radar-up)
  ['N','E','S','W'].forEach((lab, k) => {
    const ang = wrap180(k*90 - upDeg);
    const px = C + (OUTER+13)*Math.sin(ang*Math.PI/180), py = C - (OUTER+13)*Math.cos(ang*Math.PI/180);
    out += `<text x="${px.toFixed(1)}" y="${(py+3.5).toFixed(1)}" fill="${TH.tick}" font-size="10" font-family="var(--mono)" text-anchor="middle" opacity="0.9">${lab}</text>`;
  });
  // up marker
  out += `<path d="M${C} ${C-OUTER-1} l5 8 l-10 0 Z" fill="${TH.acc}"/>`;
  svg.innerHTML = out;

  card.innerHTML = buildCard(sky, sel, anyOverhead && sel && (sel.elevation_deg||0) >= OVERHEAD_ELEV);
}

function buildCard(sky, sel, overhead){
  const st = lastStatus || {};
  if (st.feed_ok === false)
    return `<div style="font-size:20px;font-weight:600;color:#ff8f6a">ADS-B feed lost</div>
            <div style="font-size:12px;color:${TH.sub};margin-top:6px">no data from the decoder</div>`;
  if (!sel)
    return `<div style="font-size:21px;font-weight:600;color:${TH.text}">Quiet sky</div>
            <div style="font-size:12px;color:${TH.sub};margin-top:6px">nothing in the window right now</div>`;

  const accent = colorFor(sel);
  const cat = classifyCat(sel);
  const dir = sel.bearing_label || compass(sel.bearing_deg || 0);
  const dist = fnum(sel.distance_km, 1);
  const alt = sel.alt_ft != null ? (sel.alt_ft/1000).toFixed(1) : '–';
  const vLab = sel.vertical_label || 'level';
  const vc = vLab === 'climbing' ? '#5fcf8a' : vLab === 'descending' ? '#ff8f6a' : TH.sub;
  const codes = opCode(sel);
  let h = '';

  if (overhead)
    h += `<div style="display:inline-flex;align-items:center;gap:6px;font-family:var(--mono);font-size:10px;font-weight:700;letter-spacing:.16em;color:#fff;background:${accent};padding:3px 10px;border-radius:6px;margin-bottom:9px;animation:sd-secflash .5s ease-in-out infinite;box-shadow:0 0 12px ${rgba(accent,0.6)}">▲ OVERHEAD · LOOK UP</div>`;

  // airline chip
  h += `<div style="display:flex;align-items:center;gap:7px;margin-bottom:8px">${shapeIcon(cat, accent, 22)}
        <div style="display:flex;align-items:center;gap:6px;background:${rgba(accent,0.18)};border:1px solid ${rgba(accent,0.5)};border-radius:7px;padding:3px 9px">
          ${codes ? `<span style="font-family:var(--mono);font-size:11px;font-weight:700;color:${accent};letter-spacing:.04em">${codes}</span>` : ''}
          <span style="font-size:11.5px;font-weight:600;color:${TH.text}">${sel.airline || 'Unknown airline'}</span>
        </div></div>`;

  // callsign
  const flight = sel.flight || sel.hex;
  h += `<div style="font-family:var(--mono);font-size:${flight.length>6?24:27}px;font-weight:700;color:${TH.text};line-height:1">${flight}</div>`;

  if (sel.origin || sel.route)
    h += `<div style="font-family:var(--mono);font-size:14px;color:${accent};margin-top:5px;font-weight:600;letter-spacing:.03em">${sel.route || (sel.origin + ' ▸ ' + (sel.destination||'?'))}</div>`;
  if (sel.model)
    h += `<div style="font-size:12px;color:${TH.sub};margin-top:3px">${sel.model}</div>`;

  // phase chip
  h += `<div style="display:inline-block;font-family:var(--mono);font-size:9px;letter-spacing:.14em;text-transform:uppercase;color:#fff;background:${accent};padding:2px 8px;border-radius:5px;margin-top:8px">${flightPhase(sel)}</div>`;

  // dist / alt / vertical pills
  const pill = (lab, val, col) => `<div style="display:flex;flex-direction:column;align-items:center;gap:1px;background:${TH.surface};border:1px solid ${TH.edge};border-radius:9px;padding:6px 9px;min-width:50px">
      <div style="font-family:var(--mono);font-size:13px;font-weight:700;color:${col||TH.text}">${val}</div>
      <div style="font-family:var(--mono);font-size:7.5px;letter-spacing:.1em;color:${TH.sub};text-transform:uppercase">${lab}</div></div>`;
  const vArrow = vLab === 'climbing' ? '↑' : vLab === 'descending' ? '↓' : '–';
  h += `<div style="display:flex;gap:6px;margin-top:11px">
        ${pill('dir', dir)}${pill('dist', dist+'km')}${pill('alt', alt+'k')}${pill('vert', vArrow, vc)}</div>`;

  if (sel.selected_reason)
    h += `<div style="font-family:var(--mono);font-size:9.5px;color:${TH.sub};margin-top:9px;max-width:210px;line-height:1.4">↳ ${sel.selected_reason}</div>`;
  return h;
}

// ---- flights table ----
function fillTable(sky){
  const tb = $('#tbl tbody'), empty = $('#empty');
  const vis = sky.aircraft || [];
  const sel = (sky.selected != null) ? vis[sky.selected] : null;
  tb.innerHTML = '';
  if (!vis.length){
    $('#tbl').style.display = 'none';
    empty.style.display = 'block';
    empty.textContent = (lastStatus && lastStatus.feed_ok === false) ? 'ADS-B feed lost' : 'no aircraft in view';
    return;
  }
  $('#tbl').style.display = ''; empty.style.display = 'none';
  vis.forEach((ac, i) => {
    const isSel = sel && (ac.hex||ac.flight) === (sel.hex||sel.flight);
    const color = colorFor(ac);
    const cat = classifyCat(ac);
    const tr = document.createElement('tr');
    tr.style.background = isSel ? rgba('#4f7cff', 0.16) : 'transparent';
    tr.onclick = () => selectByIndex(i);
    tr.innerHTML =
      `<td><div class="rowdot" style="${isSel?'background:#4f7cff;border:none':''}"></div></td>`+
      `<td style="color:#fff;font-weight:700">${ac.flight || ac.hex}</td>`+
      `<td style="color:${color};font-weight:700">${opCode(ac) || '—'}</td>`+
      `<td>${ac.route || (ac.origin ? ac.origin+'→'+(ac.destination||'?') : '—')}</td>`+
      `<td style="color:#8b94a3">${CAT_LABEL[cat]}</td>`+
      `<td>${ac.bearing_label || compass(ac.bearing_deg||0)}</td>`+
      `<td>${fnum(ac.distance_km,1)}</td>`+
      `<td>${ac.alt_ft!=null?Math.round(ac.alt_ft).toLocaleString():'–'}</td>`+
      `<td>${fnum(ac.elevation_deg,0)}°</td>`+
      `<td style="color:${isSel?'#4f7cff':'#8b94a3'};font-weight:700">${fnum(ac.score,0)}</td>`;
    tb.appendChild(tr);
  });
}

function statusStrip(sky, st){
  const pr = sky.profile || {};
  const feed = st.feed_ok !== false;
  $('#strip').innerHTML =
    `<span>profile <b>${pr.name||'–'}</b></span>`+
    `<span>state <b>${sky.state||'–'}</b></span>`+
    `<span>feed <b style="color:${feed?'#5fcf8a':'#ff8f6a'}">${feed?'LIVE':'LOST'}</b></span>`+
    `<span><b>${(sky.aircraft||[]).length}</b> on screen · <b>${st.raw_count||0}</b> rx · <b>${st.filtered_count||0}</b> in-view</span>`+
    `<span>fetch <b>${st.last_fetch_age_s==null?'–':st.last_fetch_age_s+'s'}</b> ago</span>`;
}

// ---- selection (manual, client-side; the API auto-selects) ----
let manualSelHex = null;
function selectByIndex(i){
  const vis = (lastSky && lastSky.aircraft) || [];
  if (!vis[i]) return;
  manualSelHex = vis[i].hex || vis[i].flight;
  applyManualSel(); render();
}
function cycleSelect(dir){
  const vis = (lastSky && lastSky.aircraft) || [];
  if (!vis.length) return;
  let idx = lastSky.selected != null ? lastSky.selected : 0;
  idx = (idx + dir + vis.length) % vis.length;
  manualSelHex = vis[idx].hex || vis[idx].flight;
  applyManualSel(); render();
}
function applyManualSel(){
  if (!lastSky || manualSelHex == null) return;
  const idx = (lastSky.aircraft||[]).findIndex(a => (a.hex||a.flight) === manualSelHex);
  if (idx >= 0) lastSky.selected = idx; else manualSelHex = null;
}

// ---- toasts ----
function toast(msg){
  if (quietToasts) return;
  const t = document.createElement('div');
  t.className = 'toast'; t.textContent = msg;
  $('#toasts').appendChild(t);
  setTimeout(() => t.remove(), 3700);
}

// ---- render + poll ----
function render(){
  if (!lastSky) return;
  drawDial(lastSky);
  fillTable(lastSky);
  statusStrip(lastSky, lastStatus || {});
}

async function tick(){
  try{
    const q = activeProfile ? ('?profile=' + encodeURIComponent(activeProfile)) : '';
    const [sky, st] = await Promise.all([
      fetch('/m5/sky' + q).then(r => r.json()),
      fetch('/m5/status').then(r => r.json())
    ]);
    lastSky = sky; lastStatus = st;
    applyManualSel();
    // new-best alert
    const key = selKey(sky);
    if (key && key !== lastSelKey && manualSelHex == null){
      const a = sky.aircraft[sky.selected];
      toast('New best · ' + (a.flight || a.hex));
    }
    lastSelKey = key;
    render();
  }catch(e){
    $('#strip').innerHTML = '<span style="color:#ff8f6a">error: ' + e + '</span>';
  }
}

function schedulePoll(){
  if (pollTimer) clearInterval(pollTimer);
  if (!paused) pollTimer = setInterval(tick, pollMs);
}

// ---- profiles + controls ----
async function loadProfiles(){
  const j = await fetch('/m5/profiles').then(r => r.json());
  profiles = j.profiles || []; activeProfile = j.active;
  const box = $('#c-profile'); box.innerHTML = '';
  profiles.forEach(p => {
    const b = document.createElement('button');
    b.textContent = p.name;
    b.className = (p.id === activeProfile) ? 'on' : '';
    b.title = `up ${p.radar_up_deg}° · cone ${p.view_cone_deg}° · ${p.max_distance_km}km`;
    b.onclick = async () => {
      await fetch('/m5/profile', {method:'POST', headers:{'content-type':'application/json'}, body:JSON.stringify({id:p.id})});
      activeProfile = p.id; manualSelHex = null;
      [...box.children].forEach(c => c.className = (c === b) ? 'on' : '');
      toast('Profile · ' + p.name);
      tick();
    };
    box.appendChild(b);
  });
}

function segmGroup(sel, onPick){
  const box = $(sel);
  box.querySelectorAll('button').forEach(b => {
    b.onclick = () => {
      [...box.children].forEach(c => c.classList.remove('on'));
      b.classList.add('on');
      onPick(b.dataset.v, b);
    };
  });
}

async function loadLog(){
  try{
    const j = await fetch('/m5/log?limit=10').then(r => r.json());
    const rows = (j.sightings || []).map(s =>
      `<div class="logrow"><b>${s.flight||s.hex}</b>
        <span>${s.airline||'—'}</span>
        <span>${s.bearing_label||'–'} · ${fnum(s.distance_km,1)}km · ${s.alt_ft!=null?Math.round(s.alt_ft).toLocaleString()+'ft':'–'}</span>
        <span style="margin-left:auto">${s.model||''}</span></div>`).join('');
    $('#log').innerHTML = rows || '<div class="logrow">no recent sightings</div>';
  }catch(e){ $('#log').innerHTML = '<div class="logrow">log unavailable</div>'; }
}

function initControls(){
  segmGroup('#c-colorby', v => { colorBy = v; render(); });
  segmGroup('#c-poll', v => { pollMs = +v; schedulePoll(); });
  segmGroup('#c-quiet', (v, b) => { quietToasts = !quietToasts; b.textContent = quietToasts ? '🔕 toasts off' : '🔔 toasts on'; });
  $('#c-stream').querySelectorAll('button').forEach(b => {
    b.onclick = () => {
      if (b.dataset.v === 'pause'){
        paused = !paused;
        b.classList.toggle('on', paused);
        b.textContent = paused ? '▶ resume' : '⏸ pause';
        schedulePoll();
      } else {
        tick(); loadLog();
      }
    };
  });
}

function clockTick(){ $('#clock').textContent = new Date().toLocaleTimeString('en-GB'); }

// ---- boot ----
$('#urlhost').textContent = 'http://' + location.host;
clockTick(); setInterval(clockTick, 1000);
initControls();
loadProfiles().then(tick).then(loadLog);
schedulePoll();
setInterval(loadLog, 15000);
</script>
</body>
</html>"""
