"""Server-hosted debug UI — the scoring/orientation tuning surface.

Self-contained HTML (no external assets). Polls /m5/sky and /m5/status, renders
the radar preview, the candidate table with per-factor scores, and feed health.
Responsive by default.
"""

DEBUG_HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SkyDial · debug</title>
<style>
  :root { color-scheme: light dark; --bg:#0f1420; --panel:#182031; --ink:#e7edf7; --mut:#8a97ad; --acc:#4ea1ff; --sel:#ffcc44; --line:#26304a; }
  @media (prefers-color-scheme: light){ :root{ --bg:#f4f6fb; --panel:#fff; --ink:#101725; --mut:#5a6577; --acc:#1668d8; --sel:#c8860a; --line:#e2e7f0; } }
  * { box-sizing: border-box; }
  body { margin:0; font:14px/1.4 system-ui,-apple-system,Segoe UI,Roboto,sans-serif; background:var(--bg); color:var(--ink); }
  header { padding:16px 20px; border-bottom:1px solid var(--line); display:flex; gap:16px; align-items:baseline; flex-wrap:wrap; }
  h1 { font-size:18px; margin:0; letter-spacing:.3px; }
  .state { font-weight:600; padding:2px 10px; border-radius:999px; background:var(--panel); border:1px solid var(--line); }
  .state.active{ color:#2ec27e; } .state.feed-lost{ color:#ff6b6b; } .state.quiet-sky{ color:var(--mut); } .state.connecting{ color:var(--acc); }
  main { display:grid; grid-template-columns: 320px 1fr; gap:20px; padding:20px; align-items:start; }
  @media (max-width:820px){ main{ grid-template-columns:1fr; } }
  .panel { background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:16px; }
  canvas { width:100%; height:auto; display:block; }
  .kv { display:flex; justify-content:space-between; padding:3px 0; color:var(--mut); }
  .kv b { color:var(--ink); font-weight:600; }
  .scroll { overflow-x:auto; }
  table { border-collapse:collapse; width:100%; font-variant-numeric:tabular-nums; }
  th,td { text-align:right; padding:6px 8px; border-bottom:1px solid var(--line); white-space:nowrap; }
  th:first-child, td:first-child { text-align:left; }
  tr.sel td { background:color-mix(in srgb, var(--sel) 16%, transparent); }
  .flt { color:var(--mut); }
  .alerts { min-height:20px; color:var(--sel); font-weight:600; }
  select { background:var(--bg); color:var(--ink); border:1px solid var(--line); border-radius:8px; padding:4px 8px; }
  .foot { padding:0 20px 24px; color:var(--mut); font-size:12px; }
</style>
</head>
<body>
<header>
  <h1>SkyDial · debug</h1>
  <span id="state" class="state">…</span>
  <span id="prof-wrap">profile <select id="profile"></select></span>
  <span id="alerts" class="alerts"></span>
</header>
<main>
  <section class="panel">
    <canvas id="radar" width="320" height="320" aria-label="radar preview"></canvas>
    <div id="meta" style="margin-top:12px"></div>
  </section>
  <section class="panel scroll">
    <table id="tbl">
      <thead><tr>
        <th>#</th><th>Flight</th><th>Airline</th><th>Dir</th><th>Dist km</th><th>Alt ft</th>
        <th>Elev°</th><th>V</th><th>Score</th>
        <th>fresh</th><th>align</th><th>elev</th><th>dist</th><th>alt</th><th>vrt</th><th>reason</th>
      </tr></thead>
      <tbody></tbody>
    </table>
  </section>
</main>
<div class="foot" id="statusline"></div>
<script>
const $ = s => document.querySelector(s);
let currentProfile = null;

function fnum(x, d=0){ return (x==null) ? "–" : Number(x).toFixed(d); }

async function loadProfiles(){
  const r = await fetch('/m5/profiles'); const j = await r.json();
  const sel = $('#profile'); sel.innerHTML='';
  for(const p of j.profiles){ const o=document.createElement('option'); o.value=p.id; o.textContent=p.name+' ('+p.radar_up_deg+'°/'+p.view_cone_deg+'°)'; sel.appendChild(o); }
  sel.value = j.active; currentProfile = j.active;
  sel.onchange = async () => { await fetch('/m5/profile',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({id:sel.value})}); currentProfile=sel.value; tick(); };
}

function drawRadar(sky){
  const c = $('#radar'), g = c.getContext('2d'); const W=c.width, H=c.height, cx=W/2, cy=H/2, R=Math.min(cx,cy)-10;
  g.clearRect(0,0,W,H);
  const line = getComputedStyle(document.body).getPropertyValue('--line');
  const mut = getComputedStyle(document.body).getPropertyValue('--mut');
  const acc = getComputedStyle(document.body).getPropertyValue('--acc');
  const sel = getComputedStyle(document.body).getPropertyValue('--sel');
  g.strokeStyle=line; for(const f of [1,0.66,0.33]){ g.beginPath(); g.arc(cx,cy,R*f,0,7); g.stroke(); }
  g.beginPath(); g.moveTo(cx,cy-R); g.lineTo(cx,cy+R); g.moveTo(cx-R,cy); g.lineTo(cx+R,cy); g.stroke();
  g.fillStyle=mut; g.font='11px system-ui'; g.textAlign='center'; g.fillText('▲ up', cx, cy-R-2);
  const maxd = Math.max(1, ...(sky.aircraft||[]).map(a=>a.distance_km||0));
  (sky.aircraft||[]).forEach((a,i)=>{
    if(a.screen_angle_deg==null) return;
    const ang=(a.screen_angle_deg-90)*Math.PI/180; const rr=R*Math.min(1,(a.distance_km||0)/maxd);
    const x=cx+rr*Math.cos(ang), y=cy+rr*Math.sin(ang); const isSel=(i===sky.selected);
    g.beginPath(); g.arc(x,y,isSel?7:4,0,7); g.fillStyle=isSel?sel:acc; g.fill();
    if(isSel){ g.strokeStyle=sel; g.beginPath(); g.arc(x,y,11,0,7); g.stroke(); }
  });
}

function fillTable(sky){
  const tb = $('#tbl tbody'); tb.innerHTML='';
  (sky.aircraft||[]).forEach((a,i)=>{
    const f=a.score_factors||{}; const tr=document.createElement('tr'); if(i===sky.selected) tr.className='sel';
    tr.innerHTML = `<td>${i}</td><td>${a.flight||a.hex}</td><td class="flt">${a.airline||'–'}</td>
      <td>${a.bearing_label||'–'}</td><td>${fnum(a.distance_km,1)}</td><td>${fnum(a.alt_ft)}</td>
      <td>${fnum(a.elevation_deg,0)}</td><td>${a.track_arrow||''}${a.vertical_label==='climbing'?'↑':a.vertical_label==='descending'?'↓':''}</td>
      <td><b>${fnum(a.score,1)}</b></td>
      <td class="flt">${fnum(f.freshness,2)}</td><td class="flt">${fnum(f.window_alignment,2)}</td>
      <td class="flt">${fnum(f.elevation,2)}</td><td class="flt">${fnum(f.distance,2)}</td>
      <td class="flt">${fnum(f.altitude_interest,2)}</td><td class="flt">${fnum(f.vertical_rate,2)}</td>
      <td class="flt" style="text-align:left">${a.selected_reason||''}</td>`;
    tb.appendChild(tr);
  });
}

async function tick(){
  try{
    const sky = await (await fetch('/m5/sky')).json();
    const st  = await (await fetch('/m5/status')).json();
    $('#state').textContent = sky.state; $('#state').className = 'state '+sky.state;
    $('#alerts').textContent = (sky.alerts||[]).join('  ·  ');
    const p = sky.profile;
    $('#meta').innerHTML = `<div class="kv"><span>Profile</span><b>${p.name}</b></div>
      <div class="kv"><span>Up / cone</span><b>${p.radar_up_deg}° / ${p.view_cone_deg}°</b></div>
      <div class="kv"><span>Max dist / min elev</span><b>${p.max_distance_km} km / ${p.min_elevation_deg}°</b></div>
      <div class="kv"><span>Selected</span><b>${sky.selected==null?'–':(sky.aircraft[sky.selected].flight||sky.aircraft[sky.selected].hex)}</b></div>`;
    drawRadar(sky); fillTable(sky);
    $('#statusline').textContent = `source: ${st.source} · feed ${st.feed_ok?'OK':'LOST'} · raw ${st.raw_count} → in-view ${st.filtered_count} → shown ${st.aircraft_count} · last fetch ${st.last_fetch_age_s==null?'–':st.last_fetch_age_s+'s'} ago · v${st.version}`;
  }catch(e){ $('#statusline').textContent = 'error: '+e; }
}

loadProfiles().then(tick); setInterval(tick, 2000);
</script>
</body>
</html>"""
