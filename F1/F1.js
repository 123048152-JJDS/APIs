/* ── F1 EXPLORER · JAVASCRIPT ────────────────────────────────────────── */

const BASE = 'https://api.openf1.org/v1';

// ── API helper ──────────────────────────────────────────────────────────
async function apiFetch(endpoint, params = {}) {
  const q = new URLSearchParams(params).toString();
  const url = `${BASE}/${endpoint}${q ? '?' + q : ''}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// ── Panel navigation ────────────────────────────────────────────────────
function showPanel(id) {
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('panel-' + id).classList.add('active');
  document.getElementById('nav-' + id).classList.add('active');
  if (id === 'meetings' && !meetingsLoaded) loadMeetings();
}

// ── Utils ───────────────────────────────────────────────────────────────
function fmtTime(sec) {
  if (sec == null) return '–';
  const m = Math.floor(sec / 60);
  const s = (sec % 60).toFixed(3).padStart(6, '0');
  return m > 0 ? `${m}:${s}` : `${s}`;
}

function posBadge(pos) {
  if (pos == null) return '<span class="pos-badge dnf">DNF</span>';
  if (pos === 1)   return '<span class="pos-badge p1">1</span>';
  if (pos === 2)   return '<span class="pos-badge p2">2</span>';
  if (pos === 3)   return '<span class="pos-badge p3">3</span>';
  return `<span class="pos-badge">${pos}</span>`;
}

function loader(id, show) {
  document.getElementById('loader-' + id).classList.toggle('show', show);
}

function showErr(id, msg) {
  const el = document.getElementById('err-' + id);
  el.textContent = msg;
  el.classList.toggle('show', !!msg);
}

// ── Team colours ────────────────────────────────────────────────────────
const TEAM_COLORS = {
  'Mercedes':        '#00d2be',
  'Ferrari':         '#e8002d',
  'Red Bull Racing': '#3671c6',
  'McLaren':         '#ff8000',
  'Aston Martin':    '#358c75',
  'Alpine':          '#0093cc',
  'Williams':        '#64c4ff',
  'Racing Bulls':    '#6692ff',
  'Haas F1 Team':    '#b6babd',
  'Audi':            '#e5e5e5',
  'Cadillac':        '#ffffff',
};

function teamBar(team) {
  const c = TEAM_COLORS[team] || '#555';
  return `<span class="team-bar" style="background:${c}"></span>`;
}

// ── MEETINGS ────────────────────────────────────────────────────────────
let meetingsLoaded = false;
let allMeetings = [];

async function loadMeetings() {
  meetingsLoaded = true;
  loader('meetings', true);
  showErr('meetings', '');
  try {
    allMeetings = await apiFetch('meetings');
    allMeetings.sort((a, b) => (b.year - a.year) || (a.meeting_key - b.meeting_key));

    const years = [...new Set(allMeetings.map(m => m.year))].sort((a, b) => b - a);
    const tabsEl = document.getElementById('year-tabs');
    tabsEl.innerHTML = years.map((y, i) =>
      `<button class="year-tab ${i === 0 ? 'active' : ''}" onclick="filterYear(${y}, this)">${y}</button>`
    ).join('');

    filterYear(years[0], tabsEl.querySelector('.active'));
  } catch (e) {
    showErr('meetings', 'Error al cargar GPs: ' + e.message);
  }
  loader('meetings', false);
}

function filterYear(year, btn) {
  document.querySelectorAll('.year-tab').forEach(t => t.classList.remove('active'));
  btn.classList.add('active');
  renderMeetings(allMeetings.filter(m => m.year === year));
}

function renderMeetings(list) {
  document.getElementById('meetings-grid').innerHTML = list.map(m => `
    <div class="meeting-card" onclick="selectMeeting(${m.meeting_key}, '${(m.meeting_name || '?').replace(/'/g, "\\'")}')">
      <div class="meeting-key-tag">#${m.meeting_key}</div>
      <div class="meeting-year">${m.year} · Ronda ${m.meeting_official_name?.match(/\d+/)?.[0] || ''}</div>
      <div class="meeting-name">${m.meeting_name || '?'}</div>
      <div class="meeting-circuit">📍 ${m.circuit_short_name || '?'}, ${m.country_name || '?'}</div>
    </div>
  `).join('');
}

function selectMeeting(key, name) {
  ['res-meeting', 'laps-meeting', 'champ-meeting', 'pits-meeting', 'wx-meeting']
    .forEach(id => { document.getElementById(id).value = key; });

  const notice = document.createElement('div');
  notice.style.cssText = 'position:fixed;bottom:1.5rem;right:1.5rem;background:#1a1a1a;border:1px solid var(--red);color:#fff;font-family:var(--head);font-size:0.9rem;font-weight:700;padding:0.8rem 1.4rem;border-radius:4px;z-index:999;letter-spacing:0.05em;text-transform:uppercase;';
  notice.textContent = `🏁 ${name} seleccionado`;
  document.body.appendChild(notice);
  setTimeout(() => notice.remove(), 2500);
}

// ── RESULTS ─────────────────────────────────────────────────────────────
async function loadResults() {
  const mk = document.getElementById('res-meeting').value.trim() || 'latest';
  loader('results', true);
  showErr('results', '');
  document.getElementById('results-table').innerHTML = '';
  document.getElementById('results-info').textContent = '';
  try {
    const [sessions, meetings] = await Promise.all([
      apiFetch('sessions', { meeting_key: mk, session_name: 'Race' }),
      apiFetch('meetings', { meeting_key: mk }),
    ]);
    if (!sessions.length) throw new Error('No se encontró sesión de carrera para ese meeting_key');
    const sk = sessions[0].session_key;
    const gpName = meetings[0]?.meeting_name || '?';
    const date = (sessions[0].date_start || '').slice(0, 10);

    document.getElementById('results-info').textContent =
      `🏁 ${gpName}  ·  Race  ·  ${date}  ·  session_key: ${sk}`;

    const [results, drivers] = await Promise.all([
      apiFetch('session_result', { session_key: sk }),
      apiFetch('drivers', { session_key: sk }),
    ]);

    const dMap = {};
    drivers.forEach(d => dMap[d.driver_number] = d);
    results.sort((a, b) => (a.position || 999) - (b.position || 999));

    document.getElementById('results-table').innerHTML = `
      <thead><tr>
        <th>Pos</th><th>N°</th><th>Piloto</th><th>Equipo</th>
      </tr></thead>
      <tbody>
        ${results.map(r => {
          const num  = r.driver_number;
          const d    = dMap[num] || {};
          const team = d.team_name || '–';
          const pos_s = r.position != null ? r.position : null;
          const num_s = num != null ? String(num) : '?';
          return `<tr>
            <td>${posBadge(pos_s)}</td>
            <td><span class="drv-num">${num_s}</span></td>
            <td>${teamBar(team)}${d.full_name || '#' + num}</td>
            <td style="color:var(--dim)">${team}</td>
          </tr>`;
        }).join('')}
      </tbody>`;
  } catch (e) {
    showErr('results', e.message);
  }
  loader('results', false);
}

// ── LAPS ─────────────────────────────────────────────────────────────────
async function loadLapSessions() {
  const mk = document.getElementById('laps-meeting').value.trim() || 'latest';
  showErr('laps', '');
  const sel = document.getElementById('laps-session');
  sel.innerHTML = '<option>Cargando…</option>';
  document.getElementById('laps-driver-row').style.display = 'none';
  try {
    const sessions = await apiFetch('sessions', { meeting_key: mk });
    if (!sessions.length) throw new Error('Sin sesiones para ese meeting_key');
    sel.innerHTML = sessions.map(s =>
      `<option value="${s.session_key}">${s.session_name} (${(s.date_start || '').slice(0, 10)})</option>`
    ).join('');
    document.getElementById('laps-driver-row').style.display = 'flex';
    await loadLapDrivers();
    sel.onchange = loadLapDrivers;
  } catch (e) {
    showErr('laps', e.message);
    sel.innerHTML = '<option value="">— error —</option>';
  }
}

async function loadLapDrivers() {
  const sk = document.getElementById('laps-session').value;
  if (!sk) return;
  const dSel = document.getElementById('laps-driver');
  dSel.innerHTML = '<option>Cargando…</option>';
  try {
    const drivers = await apiFetch('drivers', { session_key: sk });
    drivers.sort((a, b) => a.driver_number - b.driver_number);
    dSel.innerHTML = drivers.map(d =>
      `<option value="${d.driver_number}">${d.driver_number} – ${d.full_name || '?'} (${d.team_name || '?'})</option>`
    ).join('');
  } catch (e) {
    dSel.innerHTML = '<option value="">— error —</option>';
  }
}

async function loadLaps() {
  const sk = document.getElementById('laps-session').value;
  const dn = document.getElementById('laps-driver').value;
  if (!sk || !dn) return;
  loader('laps', true);
  showErr('laps', '');
  document.getElementById('laps-table').innerHTML = '';
  document.getElementById('laps-info').textContent = '';
  try {
    const [laps, drivers] = await Promise.all([
      apiFetch('laps',    { session_key: sk, driver_number: dn }),
      apiFetch('drivers', { session_key: sk, driver_number: dn }),
    ]);
    const drv = drivers[0] || {};
    laps.sort((a, b) => a.lap_number - b.lap_number);

    const times = laps.map(l => l.lap_duration).filter(t => t != null);
    const best  = times.length ? Math.min(...times) : null;

    document.getElementById('laps-info').textContent =
      `${drv.full_name || '#' + dn}  ·  ${drv.team_name || ''}  ·  ${laps.length} vueltas`;

    document.getElementById('laps-table').innerHTML = `
      <thead><tr>
        <th class="num">Vlt</th>
        <th class="num">Tiempo</th>
        <th class="num">S1</th>
        <th class="num">S2</th>
        <th class="num">S3</th>
        <th>Compuesto</th>
      </tr></thead>
      <tbody>
        ${laps.map(l => {
          const isBest = l.lap_duration != null && l.lap_duration === best;
          const tc = isBest ? ' class="fast"' : '';
          return `<tr>
            <td class="num">${l.lap_number ?? '–'}</td>
            <td class="num"${tc}>${fmtTime(l.lap_duration)}</td>
            <td class="num">${fmtTime(l.duration_sector_1)}</td>
            <td class="num">${fmtTime(l.duration_sector_2)}</td>
            <td class="num">${fmtTime(l.duration_sector_3)}</td>
            <td style="color:var(--dim);font-family:var(--mono);font-size:0.75rem">${l.compound || '–'}</td>
          </tr>`;
        }).join('')}
      </tbody>`;
  } catch (e) {
    showErr('laps', e.message);
  }
  loader('laps', false);
}

// ── CHAMPIONSHIP ─────────────────────────────────────────────────────────
async function loadChampionship() {
  const mk = document.getElementById('champ-meeting').value.trim() || 'latest';
  loader('champ', true);
  showErr('champ', '');
  document.getElementById('champ-table').innerHTML = '';
  try {
    const sessions = await apiFetch('sessions', { meeting_key: mk, session_name: 'Race' });
    if (!sessions.length) throw new Error('Sin sesión de carrera para ese meeting_key');
    const sk = sessions[0].session_key;

    const [standings, drivers] = await Promise.all([
      apiFetch('championship_drivers', { session_key: sk }),
      apiFetch('drivers',              { session_key: sk }),
    ]);
    if (!standings.length) throw new Error('Sin datos de campeonato para esa sesión (puede ser muy reciente)');

    const dMap = {};
    drivers.forEach(d => dMap[d.driver_number] = d);
    standings.sort((a, b) => (a.position_current || 999) - (b.position_current || 999));
    const maxPts = standings[0]?.points_current || 1;

    document.getElementById('champ-table').innerHTML = `
      <thead><tr>
        <th>Pos</th><th>Piloto</th><th>Equipo</th>
        <th class="num">Puntos</th><th class="num">+Ronda</th>
        <th style="min-width:140px"></th>
      </tr></thead>
      <tbody>
        ${standings.map(s => {
          const d      = dMap[s.driver_number] || {};
          const team   = d.team_name || '–';
          const gained = (s.points_current || 0) - (s.points_start || s.points_current || 0);
          const pct    = ((s.points_current || 0) / maxPts * 100).toFixed(1);
          const color  = TEAM_COLORS[team] || 'var(--red)';
          const gainedStr = (gained > 0 ? '+' : '') + gained;
          const gainColor = gained > 0 ? '#4caf50' : gained < 0 ? '#f44336' : 'var(--dim)';
          return `<tr>
            <td>${posBadge(s.position_current)}</td>
            <td>${teamBar(team)}${d.full_name || '#' + s.driver_number}</td>
            <td style="color:var(--dim)">${team}</td>
            <td class="num" style="font-weight:700">${s.points_current ?? '–'}</td>
            <td class="num" style="color:${gainColor}">${gainedStr}</td>
            <td>
              <div class="pts-bar-wrap">
                <div class="pts-bar-bg">
                  <div class="pts-bar-fill" style="width:${pct}%;background:${color}"></div>
                </div>
              </div>
            </td>
          </tr>`;
        }).join('')}
      </tbody>`;
  } catch (e) {
    showErr('champ', e.message);
  }
  loader('champ', false);
}

// ── PITS ──────────────────────────────────────────────────────────────────
async function loadPits() {
  const mk = document.getElementById('pits-meeting').value.trim() || 'latest';
  loader('pits', true);
  showErr('pits', '');
  document.getElementById('pits-table').innerHTML = '';
  try {
    const sessions = await apiFetch('sessions', { meeting_key: mk, session_name: 'Race' });
    if (!sessions.length) throw new Error('Sin sesión de carrera para ese meeting_key');
    const sk = sessions[0].session_key;

    const [pits, drivers] = await Promise.all([
      apiFetch('pit',     { session_key: sk }),
      apiFetch('drivers', { session_key: sk }),
    ]);
    if (!pits.length) throw new Error('Sin datos de pits');

    const dMap = {};
    drivers.forEach(d => dMap[d.driver_number] = d);
    pits.sort((a, b) =>
      (a.lap_number || 0) - (b.lap_number || 0) ||
      (a.driver_number || 0) - (b.driver_number || 0)
    );

    document.getElementById('pits-table').innerHTML = `
      <thead><tr>
        <th class="num">Vuelta</th><th>Piloto</th><th>Equipo</th>
        <th class="num">Parada (s)</th><th class="num">Carril (s)</th>
      </tr></thead>
      <tbody>
        ${pits.map(p => {
          const d    = dMap[p.driver_number] || {};
          const team = d.team_name || '–';
          const stop = p.stop_duration;
          const lane = p.lane_duration;
          return `<tr>
            <td class="num">${p.lap_number ?? '–'}</td>
            <td>${teamBar(team)}${d.full_name || '#' + p.driver_number}</td>
            <td style="color:var(--dim)">${team}</td>
            <td class="num">${stop != null ? stop.toFixed(2) + 's' : '–'}</td>
            <td class="num">${lane != null ? lane.toFixed(2) + 's' : '–'}</td>
          </tr>`;
        }).join('')}
      </tbody>`;
  } catch (e) {
    showErr('pits', e.message);
  }
  loader('pits', false);
}

// ── WEATHER ──────────────────────────────────────────────────────────────
async function loadWeatherSessions() {
  const mk  = document.getElementById('wx-meeting').value.trim() || 'latest';
  const sel = document.getElementById('wx-session');
  showErr('wx', '');
  sel.innerHTML = '<option>Cargando…</option>';
  document.getElementById('wx-go-btn').style.display = 'none';
  try {
    const sessions = await apiFetch('sessions', { meeting_key: mk });
    if (!sessions.length) throw new Error('Sin sesiones');
    sel.innerHTML = sessions.map(s =>
      `<option value="${s.session_key}">${s.session_name} (${(s.date_start || '').slice(0, 10)})</option>`
    ).join('');
    document.getElementById('wx-go-btn').style.display = 'flex';
  } catch (e) {
    showErr('wx', e.message);
    sel.innerHTML = '<option value="">— error —</option>';
  }
}

async function loadWeather() {
  const sk = document.getElementById('wx-session').value;
  if (!sk) return;
  loader('wx', true);
  showErr('wx', '');
  document.getElementById('wx-cards').innerHTML = '';
  document.getElementById('wx-table').innerHTML = '';
  try {
    const weather = await apiFetch('weather', { session_key: sk });
    if (!weather.length) throw new Error('Sin datos meteorológicos');

    const pick = k  => weather.map(w => w[k]).filter(v => v != null);
    const avg  = arr => arr.reduce((a, b) => a + b, 0) / arr.length;

    const stats = [
      { label: 'Temp. Aire',  key: 'air_temperature',   unit: '°C'   },
      { label: 'Temp. Pista', key: 'track_temperature',  unit: '°C'   },
      { label: 'Humedad',     key: 'humidity',            unit: '%'    },
      { label: 'Presión',     key: 'pressure',            unit: 'mbar' },
      { label: 'Vel. Viento', key: 'wind_speed',          unit: 'm/s'  },
    ];

    const cards = document.getElementById('wx-cards');
    cards.innerHTML = stats.map(s => {
      const arr = pick(s.key);
      if (!arr.length) return '';
      return `<div class="stat-card">
        <div class="stat-label">${s.label}</div>
        <div class="stat-value">${avg(arr).toFixed(1)}<span class="stat-unit">${s.unit}</span></div>
        <div class="stat-range">↓ ${Math.min(...arr).toFixed(1)} · ↑ ${Math.max(...arr).toFixed(1)}</div>
      </div>`;
    }).join('');

    const rain = weather.some(w => w.rainfall);
    cards.innerHTML += `<div class="stat-card">
      <div class="stat-label">Lluvia</div>
      <div class="stat-value" style="font-size:2rem">${rain ? '🌧️' : '☀️'}</div>
      <div class="stat-range">${rain ? 'Detectada' : 'No detectada'}</div>
    </div>`;

    const sampled = weather.filter((_, i) =>
      i % Math.max(1, Math.floor(weather.length / 30)) === 0
    );
    document.getElementById('wx-table').innerHTML = `
      <thead><tr>
        <th>Hora (UTC)</th>
        <th class="num">Aire °C</th><th class="num">Pista °C</th>
        <th class="num">Hum %</th><th class="num">Viento m/s</th><th>Lluvia</th>
      </tr></thead>
      <tbody>
        ${sampled.map(w => `<tr>
          <td style="font-family:var(--mono);font-size:0.75rem;color:var(--dim)">${(w.date || '').slice(11, 19)}</td>
          <td class="num">${w.air_temperature   ?? '–'}</td>
          <td class="num">${w.track_temperature ?? '–'}</td>
          <td class="num">${w.humidity          ?? '–'}</td>
          <td class="num">${w.wind_speed        ?? '–'}</td>
          <td>${w.rainfall ? '🌧️' : '–'}</td>
        </tr>`).join('')}
      </tbody>`;
  } catch (e) {
    showErr('wx', e.message);
  }
  loader('wx', false);
}