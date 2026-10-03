/**
 * GeoAttend – Location-Based Attendance System
 * Main Application Logic (app.js)
 * 
 * Features:
 *  - GPS Geolocation API integration
 *  - Geofence zone management
 *  - Attendance Check-In / Check-Out
 *  - LocalStorage persistence
 *  - Chart.js analytics
 *  - CSV export
 *  - Dark/Light theme toggle
 */

'use strict';

/* ============================================================
   STATE & CONSTANTS
============================================================ */
const APP_KEY       = 'geoattend_v2';
const RECORDS_KEY   = `${APP_KEY}_records`;
const ZONES_KEY     = `${APP_KEY}_zones`;
const SETTINGS_KEY  = `${APP_KEY}_settings`;
const SESSION_KEY   = `${APP_KEY}_session`;

let state = {
  records: [],
  zones: [],
  settings: {
    startTime: '09:00',
    endTime: '18:00',
    lateThreshold: 15,   // minutes
    radius: 100,          // meters
    name: 'Admin User',
    role: 'Administrator',
    email: '',
    theme: 'dark'
  },
  session: null,          // active check-in session
  currentLocation: null,  // { lat, lng, accuracy }
  currentPage: 'dashboard',
  watchId: null,
  charts: {},
  editingZoneId: null,
  currentRecordPage: 1,
  recordsPerPage: 10,
  currentRecordId: null,
  filterDate: '',
  filterName: ''
};

/* ============================================================
   UTILITY FUNCTIONS
============================================================ */
const uid = () => `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;

const fmt = (date, type = 'datetime') => {
  if (!date) return '--';
  const d = new Date(date);
  if (type === 'date') return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
  if (type === 'time') return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true });
  return d.toLocaleString('en-IN', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit', hour12: true });
};

const calcDuration = (start, end) => {
  if (!start || !end) return '--';
  const ms = new Date(end) - new Date(start);
  if (ms < 0) return '--';
  const h = Math.floor(ms / 3600000);
  const m = Math.floor((ms % 3600000) / 60000);
  return `${h}h ${m}m`;
};

const distance = (lat1, lon1, lat2, lon2) => {
  const R = 6371000; // Earth radius in metres
  const φ1 = lat1 * Math.PI / 180;
  const φ2 = lat2 * Math.PI / 180;
  const Δφ = (lat2 - lat1) * Math.PI / 180;
  const Δλ = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(Δφ / 2) ** 2 + Math.cos(φ1) * Math.cos(φ2) * Math.sin(Δλ / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
};

const getZoneTypeIcon = t => ({ office: '🏢', field: '🌾', remote: '🏠', client: '🤝' }[t] || '📍');

/* ============================================================
   PERSISTENCE
============================================================ */
const save = () => {
  try {
    localStorage.setItem(RECORDS_KEY,  JSON.stringify(state.records));
    localStorage.setItem(ZONES_KEY,    JSON.stringify(state.zones));
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(state.settings));
    if (state.session) localStorage.setItem(SESSION_KEY, JSON.stringify(state.session));
    else localStorage.removeItem(SESSION_KEY);
  } catch (e) { console.error('Save failed:', e); }
};

const load = () => {
  try {
    state.records  = JSON.parse(localStorage.getItem(RECORDS_KEY))  || [];
    state.zones    = JSON.parse(localStorage.getItem(ZONES_KEY))     || [];
    const saved    = JSON.parse(localStorage.getItem(SETTINGS_KEY))  || {};
    state.settings = { ...state.settings, ...saved };
    state.session  = JSON.parse(localStorage.getItem(SESSION_KEY))   || null;
  } catch (e) { console.error('Load failed:', e); }
};

/* ============================================================
   GEOLOCATION
============================================================ */
const startLocationWatch = () => {
  if (!navigator.geolocation) {
    showToast('⚠️ Geolocation not supported by this browser', 'warning');
    updateLocationUI(null, 'unsupported');
    return;
  }
  const opts = { enableHighAccuracy: true, timeout: 15000, maximumAge: 5000 };
  state.watchId = navigator.geolocation.watchPosition(
    pos => {
      state.currentLocation = { lat: pos.coords.latitude, lng: pos.coords.longitude, accuracy: pos.coords.accuracy };
      updateLocationUI(state.currentLocation, 'success');
    },
    err => {
      let msg = 'Location access denied.';
      if (err.code === 2) msg = 'Location unavailable.';
      if (err.code === 3) msg = 'Location request timed out.';
      updateLocationUI(null, 'error', msg);
    },
    opts
  );
};

const refreshLocation = () => {
  if (state.watchId !== null) {
    navigator.geolocation.clearWatch(state.watchId);
    state.watchId = null;
  }
  updateLocationUI(null, 'loading');
  setTimeout(startLocationWatch, 300);
};

const updateLocationUI = (loc, status, errMsg = '') => {
  // Dashboard location status
  const dashEl = document.getElementById('dashLocationStatus');
  // Check-in GPS badge
  const gpsBadge = document.getElementById('gpsBadge');
  const latEl = document.getElementById('latDisplay');
  const lngEl = document.getElementById('lngDisplay');
  const accEl = document.getElementById('accDisplay');

  if (status === 'success' && loc) {
    if (dashEl) dashEl.innerHTML = `<div class="location-icon">✅</div><p>Location detected · <strong>${loc.accuracy.toFixed(0)}m</strong> accuracy</p>`;
    if (gpsBadge) { gpsBadge.textContent = 'Active'; gpsBadge.className = 'badge badge-success'; }
    if (latEl) latEl.textContent = loc.lat.toFixed(5) + '°';
    if (lngEl) lngEl.textContent = loc.lng.toFixed(5) + '°';
    if (accEl) accEl.textContent = loc.accuracy.toFixed(0) + ' m';
    checkZoneMatch();
    updateUserPin();
  } else if (status === 'loading') {
    if (dashEl) dashEl.innerHTML = `<div class="location-icon">📡</div><p>Fetching your location...</p>`;
    if (gpsBadge) { gpsBadge.textContent = 'Detecting...'; gpsBadge.className = 'badge'; }
  } else {
    if (dashEl) dashEl.innerHTML = `<div class="location-icon">❌</div><p>${errMsg || 'Location unavailable'}</p>`;
    if (gpsBadge) { gpsBadge.textContent = 'Error'; gpsBadge.className = 'badge badge-danger'; }
    if (latEl) latEl.textContent = '--°';
    if (lngEl) lngEl.textContent = '--°';
    if (accEl) accEl.textContent = '-- m';
  }
};

const checkZoneMatch = () => {
  const zoneMatchEl = document.getElementById('zoneMatch');
  const zoneMatchText = document.getElementById('zoneMatchText');
  const zoneSelect = document.getElementById('zoneSelect');
  if (!zoneMatchEl || !state.currentLocation) return;
  const loc = state.currentLocation;
  const matched = state.zones.find(z => distance(loc.lat, loc.lng, z.lat, z.lng) <= z.radius);
  if (matched) {
    zoneMatchEl.className = 'zone-match matched';
    zoneMatchEl.querySelector('.zone-icon').textContent = '✅';
    if (zoneMatchText) zoneMatchText.textContent = `Inside zone: ${matched.name}`;
    if (zoneSelect) zoneSelect.value = matched.id;
  } else {
    zoneMatchEl.className = 'zone-match no-match';
    zoneMatchEl.querySelector('.zone-icon').textContent = '⚠️';
    if (zoneMatchText) zoneMatchText.textContent = 'Not inside any registered zone';
  }
};

const updateUserPin = () => {
  const pin = document.getElementById('userPin');
  if (!pin || !state.currentLocation || state.zones.length === 0) return;
  const lats = state.zones.map(z => z.lat);
  const lngs = state.zones.map(z => z.lng);
  const minLat = Math.min(...lats) - 0.005;
  const maxLat = Math.max(...lats) + 0.005;
  const minLng = Math.min(...lngs) - 0.005;
  const maxLng = Math.max(...lngs) + 0.005;
  const x = ((state.currentLocation.lng - minLng) / (maxLng - minLng)) * 100;
  const y = (1 - (state.currentLocation.lat - minLat) / (maxLat - minLat)) * 100;
  if (x >= 0 && x <= 100 && y >= 0 && y <= 100) {
    pin.style.display = 'block';
    pin.style.left = `${x}%`;
    pin.style.top  = `${y}%`;
  }
};

/* ============================================================
   NAVIGATION
============================================================ */
const navigateTo = (page) => {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  const pageEl = document.getElementById(`page-${page}`);
  const navEl  = document.getElementById(`nav-${page}`);
  if (pageEl) pageEl.classList.add('active');
  if (navEl)  navEl.classList.add('active');
  state.currentPage = page;
  if (page === 'records')   renderRecords();
  if (page === 'locations') renderZones();
  if (page === 'reports')   renderReports();
  if (page === 'checkin')   { populateZoneSelect(); renderMapZones(); }
  if (page === 'dashboard') { updateDashStats(); renderActivityFeed(); renderMonthlyChart(); }
};

/* ============================================================
   CHECK-IN / CHECK-OUT
============================================================ */
const getAttendanceStatus = (checkInTime) => {
  const d = new Date(checkInTime);
  const [sh, sm] = state.settings.startTime.split(':').map(Number);
  const threshold = sh * 60 + sm + state.settings.lateThreshold;
  const actual = d.getHours() * 60 + d.getMinutes();
  return actual <= threshold ? 'present' : 'late';
};

const checkIn = () => {
  const name = document.getElementById('empName').value.trim();
  const id   = document.getElementById('empId').value.trim();
  const dept = document.getElementById('empDept').value;
  const zone = document.getElementById('zoneSelect').value;
  const notes= document.getElementById('empNotes').value.trim();
  if (!name || !id) { showToast('❌ Please fill in Name and Employee ID', 'error'); return; }
  if (!state.currentLocation) { showToast('⚠️ Location not detected yet', 'warning'); return; }
  if (state.session) { showToast('⚠️ Already checked in', 'warning'); return; }

  const now = new Date();
  const status = getAttendanceStatus(now);
  const zoneName = zone ? (state.zones.find(z => z.id === zone)?.name || 'Unknown') : 'Manual';

  const record = {
    id: uid(),
    name, empId: id, dept, zoneName, zoneId: zone, notes,
    checkIn: now.toISOString(),
    checkOut: null, duration: null,
    lat: state.currentLocation.lat,
    lng: state.currentLocation.lng,
    accuracy: state.currentLocation.accuracy,
    status
  };

  state.session = { recordId: record.id, startTime: record.checkIn };
  state.records.unshift(record);
  save();

  // Update UI
  document.getElementById('checkInBtn').style.display = 'none';
  document.getElementById('checkOutBtn').style.display = 'flex';
  document.getElementById('quickCheckInBtn').style.display = 'none';
  document.getElementById('quickCheckOutBtn').style.display = 'flex';
  document.getElementById('sessionInfo').style.display = 'block';
  document.getElementById('sessionStart').textContent = fmt(record.checkIn, 'time');
  startSessionTimer();

  showToast(`✅ Checked in successfully${status === 'late' ? ' (Late)' : ''}`, status === 'late' ? 'warning' : 'success');
  addActivity({ type: 'checkin', name, zone: zoneName, time: now.toISOString() });
};

const checkOut = () => {
  if (!state.session) { showToast('⚠️ No active session', 'warning'); return; }
  const now = new Date();
  const record = state.records.find(r => r.id === state.session.recordId);
  if (record) {
    record.checkOut = now.toISOString();
    record.duration = calcDuration(record.checkIn, record.checkOut);
  }
  const name = record?.name || 'User';
  const zone = record?.zoneName || '--';
  state.session = null;
  save();

  document.getElementById('checkInBtn').style.display = 'flex';
  document.getElementById('checkOutBtn').style.display = 'none';
  document.getElementById('quickCheckInBtn').style.display = 'flex';
  document.getElementById('quickCheckOutBtn').style.display = 'none';
  document.getElementById('sessionInfo').style.display = 'none';
  showToast('🔴 Checked out successfully', 'info');
  addActivity({ type: 'checkout', name, zone, time: now.toISOString() });
};

const quickCheckIn = () => { navigateTo('checkin'); setTimeout(checkIn, 200); };
const quickCheckOut = () => checkOut();

/* Session duration timer */
let sessionTimerInterval = null;
const startSessionTimer = () => {
  if (sessionTimerInterval) clearInterval(sessionTimerInterval);
  sessionTimerInterval = setInterval(() => {
    if (!state.session) { clearInterval(sessionTimerInterval); return; }
    const dur = calcDuration(state.session.startTime, new Date().toISOString());
    const el = document.getElementById('sessionDuration');
    if (el) el.textContent = dur;
  }, 30000);
  const el = document.getElementById('sessionDuration');
  if (el) el.textContent = calcDuration(state.session.startTime, new Date().toISOString());
};

/* ============================================================
   ACTIVITY FEED
============================================================ */
const todayActivities = [];

const addActivity = ({ type, name, zone, time }) => {
  todayActivities.unshift({ type, name, zone, time });
  renderActivityFeed();
  const el = document.getElementById('activityCount');
  if (el) el.textContent = `${todayActivities.length} events`;
};

const renderActivityFeed = () => {
  const feed = document.getElementById('activityFeed');
  if (!feed) return;
  if (todayActivities.length === 0) {
    feed.innerHTML = `<div class="empty-state"><div class="empty-icon">📭</div><p>No activity yet today</p></div>`;
    return;
  }
  feed.innerHTML = todayActivities.map(a => `
    <div class="activity-item">
      <div class="activity-dot ${a.type}"></div>
      <div>
        <div class="activity-text"><strong>${a.name}</strong> ${a.type === 'checkin' ? 'checked in' : 'checked out'} · ${a.zone}</div>
        <div class="activity-time">${fmt(a.time, 'time')}</div>
      </div>
    </div>
  `).join('');
};

/* ============================================================
   DASHBOARD STATS
============================================================ */
const updateDashStats = () => {
  const today = new Date().toDateString();
  const todayRecords = state.records.filter(r => new Date(r.checkIn).toDateString() === today);
  const present  = todayRecords.filter(r => r.status === 'present').length;
  const late     = todayRecords.filter(r => r.status === 'late').length;
  const absent   = 0; // In a real app this would come from expected attendees
  const zones    = state.zones.length;

  document.getElementById('statPresent').textContent   = present;
  document.getElementById('statAbsent').textContent    = absent;
  document.getElementById('statLate').textContent      = late;
  document.getElementById('statLocations').textContent = zones;
  document.getElementById('trendPresent').textContent  = `+${present + late} today`;
  document.getElementById('trendZones').textContent    = zones > 0 ? 'Active' : 'None set';

  const dateStr = new Date().toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
  document.getElementById('dashboardDate').textContent = dateStr;
};

/* ============================================================
   RECORDS PAGE
============================================================ */
const renderRecords = () => {
  const fd = document.getElementById('filterDate').value;
  const fn = document.getElementById('filterName').value.toLowerCase();
  state.filterDate = fd;
  state.filterName = fn;

  let filtered = state.records.filter(r => {
    const dateOk = !fd || new Date(r.checkIn).toISOString().slice(0, 10) === fd;
    const nameOk = !fn || r.name.toLowerCase().includes(fn) || r.empId.toLowerCase().includes(fn);
    return dateOk && nameOk;
  });

  const total = filtered.length;
  const pages = Math.ceil(total / state.recordsPerPage);
  const start = (state.currentRecordPage - 1) * state.recordsPerPage;
  const slice = filtered.slice(start, start + state.recordsPerPage);

  const tbody = document.getElementById('recordsBody');
  if (!tbody) return;

  if (slice.length === 0) {
    tbody.innerHTML = `<tr><td colspan="10" class="empty-row">No records found</td></tr>`;
  } else {
    tbody.innerHTML = slice.map((r, i) => `
      <tr>
        <td>${start + i + 1}</td>
        <td><strong>${r.name}</strong></td>
        <td>${r.empId}</td>
        <td>${r.dept || '--'}</td>
        <td>${fmt(r.checkIn, 'time')}<br/><small style="color:var(--text-muted)">${fmt(r.checkIn, 'date')}</small></td>
        <td>${r.checkOut ? fmt(r.checkOut, 'time') : '<span class="badge badge-info">Active</span>'}</td>
        <td>${r.duration || (state.session?.recordId === r.id ? '⏳ Ongoing' : '--')}</td>
        <td>${r.zoneName || '--'}</td>
        <td><span class="status-badge status-${r.status}">${r.status}</span></td>
        <td>
          <button class="btn btn-outline" style="padding:4px 10px;font-size:12px" onclick="viewRecord('${r.id}')">View</button>
        </td>
      </tr>
    `).join('');
  }

  document.getElementById('recordCount').textContent = `${total} record${total !== 1 ? 's' : ''}`;
  renderPagination(pages);
};

const renderPagination = (pages) => {
  const pg = document.getElementById('pagination');
  if (!pg) return;
  pg.innerHTML = '';
  for (let i = 1; i <= pages; i++) {
    const btn = document.createElement('button');
    btn.className = `page-btn${i === state.currentRecordPage ? ' active' : ''}`;
    btn.textContent = i;
    btn.onclick = () => { state.currentRecordPage = i; renderRecords(); };
    pg.appendChild(btn);
  }
};

document.addEventListener('change', (e) => {
  if (e.target.id === 'filterDate' || e.target.id === 'filterName') {
    state.currentRecordPage = 1;
    renderRecords();
  }
});
document.addEventListener('input', (e) => {
  if (e.target.id === 'filterName') {
    state.currentRecordPage = 1;
    renderRecords();
  }
});

const viewRecord = (id) => {
  const r = state.records.find(rec => rec.id === id);
  if (!r) return;
  state.currentRecordId = id;
  document.getElementById('recordModalBody').innerHTML = `
    <div class="form-group"><div class="form-label">Employee</div><strong>${r.name}</strong> (${r.empId})</div>
    <div class="form-group"><div class="form-label">Department</div>${r.dept || '--'}</div>
    <div class="form-group"><div class="form-label">Check In</div>${fmt(r.checkIn)}</div>
    <div class="form-group"><div class="form-label">Check Out</div>${r.checkOut ? fmt(r.checkOut) : 'Not yet'}</div>
    <div class="form-group"><div class="form-label">Duration</div>${r.duration || '--'}</div>
    <div class="form-group"><div class="form-label">Zone</div>${r.zoneName || '--'}</div>
    <div class="form-group"><div class="form-label">Status</div><span class="status-badge status-${r.status}">${r.status}</span></div>
    <div class="form-group"><div class="form-label">Coordinates</div>${r.lat?.toFixed(5)}°, ${r.lng?.toFixed(5)}° (±${r.accuracy?.toFixed(0)}m)</div>
    ${r.notes ? `<div class="form-group"><div class="form-label">Notes</div>${r.notes}</div>` : ''}
  `;
  document.getElementById('recordModal').classList.add('open');
};

const closeRecordModal = () => { document.getElementById('recordModal').classList.remove('open'); };

const deleteCurrentRecord = () => {
  if (!state.currentRecordId) return;
  state.records = state.records.filter(r => r.id !== state.currentRecordId);
  save();
  closeRecordModal();
  renderRecords();
  showToast('🗑️ Record deleted', 'info');
};

/* ============================================================
   ZONES / LOCATIONS
============================================================ */
const populateZoneSelect = () => {
  const sel = document.getElementById('zoneSelect');
  if (!sel) return;
  sel.innerHTML = '<option value="">-- Select Zone --</option>' +
    state.zones.map(z => `<option value="${z.id}">${getZoneTypeIcon(z.type)} ${z.name}</option>`).join('');
  const cnt = document.getElementById('mapZoneCount');
  if (cnt) cnt.textContent = `${state.zones.length} zone${state.zones.length !== 1 ? 's' : ''}`;
};

const renderZones = () => {
  const grid = document.getElementById('zonesGrid');
  if (!grid) return;
  if (state.zones.length === 0) {
    grid.innerHTML = `
      <div class="zone-empty">
        <div class="zone-empty-icon">📍</div>
        <p>No zones configured yet</p>
        <p style="font-size:13px;margin-top:6px">Add a zone to start tracking attendance</p>
      </div>`;
    return;
  }
  grid.innerHTML = state.zones.map(z => `
    <div class="zone-card ${z.type}" id="zcard-${z.id}">
      <div class="zone-card-header">
        <div class="zone-type-icon">${getZoneTypeIcon(z.type)}</div>
        <div class="zone-card-actions">
          <button class="btn btn-outline" style="padding:4px 10px;font-size:12px" onclick="editZone('${z.id}')">✏️</button>
          <button class="btn btn-danger-outline" style="padding:4px 10px;font-size:12px" onclick="deleteZone('${z.id}')">🗑️</button>
        </div>
      </div>
      <div class="zone-card-body">
        <div class="zone-name">${z.name}</div>
        <div class="zone-address">${z.address || 'No address provided'}</div>
        <div class="zone-meta">
          <div class="zone-meta-item">📍 <strong>${z.lat.toFixed(4)}°</strong></div>
          <div class="zone-meta-item">📍 <strong>${z.lng.toFixed(4)}°</strong></div>
          <div class="zone-meta-item">⭕ <strong>${z.radius}m</strong> radius</div>
        </div>
      </div>
    </div>
  `).join('');
};

const openZoneModal = (id = null) => {
  state.editingZoneId = id;
  const modal = document.getElementById('zoneModal');
  if (id) {
    const z = state.zones.find(z => z.id === id);
    if (!z) return;
    document.getElementById('modalTitle').textContent = 'Edit Location Zone';
    document.getElementById('zoneName').value    = z.name;
    document.getElementById('zoneAddress').value = z.address || '';
    document.getElementById('zoneLat').value     = z.lat;
    document.getElementById('zoneLng').value     = z.lng;
    document.getElementById('zoneRadius').value  = z.radius;
    document.getElementById('zoneType').value    = z.type;
  } else {
    document.getElementById('modalTitle').textContent = 'Add Location Zone';
    document.getElementById('zoneName').value    = '';
    document.getElementById('zoneAddress').value = '';
    document.getElementById('zoneLat').value     = '';
    document.getElementById('zoneLng').value     = '';
    document.getElementById('zoneRadius').value  = '100';
    document.getElementById('zoneType').value    = 'office';
  }
  modal.classList.add('open');
};

const closeZoneModal = () => { document.getElementById('zoneModal').classList.remove('open'); state.editingZoneId = null; };

const saveZone = () => {
  const name   = document.getElementById('zoneName').value.trim();
  const addr   = document.getElementById('zoneAddress').value.trim();
  const lat    = parseFloat(document.getElementById('zoneLat').value);
  const lng    = parseFloat(document.getElementById('zoneLng').value);
  const radius = parseInt(document.getElementById('zoneRadius').value);
  const type   = document.getElementById('zoneType').value;

  if (!name) { showToast('❌ Zone name is required', 'error'); return; }
  if (isNaN(lat) || isNaN(lng)) { showToast('❌ Valid latitude and longitude are required', 'error'); return; }
  if (isNaN(radius) || radius < 10) { showToast('❌ Radius must be at least 10m', 'error'); return; }

  if (state.editingZoneId) {
    const z = state.zones.find(z => z.id === state.editingZoneId);
    if (z) Object.assign(z, { name, address: addr, lat, lng, radius, type });
  } else {
    state.zones.push({ id: uid(), name, address: addr, lat, lng, radius, type, createdAt: new Date().toISOString() });
  }

  save();
  closeZoneModal();
  renderZones();
  populateZoneSelect();
  renderMapZones();
  document.getElementById('statLocations').textContent = state.zones.length;
  showToast(`✅ Zone ${state.editingZoneId ? 'updated' : 'created'} successfully`, 'success');
};

const editZone   = (id) => openZoneModal(id);
const deleteZone = (id) => {
  state.zones = state.zones.filter(z => z.id !== id);
  save();
  renderZones();
  populateZoneSelect();
  renderMapZones();
  showToast('🗑️ Zone deleted', 'info');
};

const useCurrentLocation = () => {
  if (!state.currentLocation) { showToast('⚠️ Location not available yet', 'warning'); return; }
  document.getElementById('zoneLat').value = state.currentLocation.lat.toFixed(6);
  document.getElementById('zoneLng').value = state.currentLocation.lng.toFixed(6);
  showToast('📍 Current coordinates filled in', 'success');
};

/* ============================================================
   MAP VISUALIZATION
============================================================ */
const renderMapZones = () => {
  const container = document.getElementById('mapZonesDisplay');
  if (!container || state.zones.length === 0) return;

  const lats = state.zones.map(z => z.lat);
  const lngs = state.zones.map(z => z.lng);
  const minLat = Math.min(...lats) - 0.005;
  const maxLat = Math.max(...lats) + 0.005;
  const minLng = Math.min(...lngs) - 0.005;
  const maxLng = Math.max(...lngs) + 0.005;
  const latRange = maxLat - minLat || 0.01;
  const lngRange = maxLng - minLng || 0.01;

  const colors = { office: '#6366f1', field: '#22c55e', remote: '#3b82f6', client: '#f59e0b' };

  container.innerHTML = state.zones.map(z => {
    const x = ((z.lng - minLng) / lngRange) * 100;
    const y = (1 - (z.lat - minLat) / latRange) * 100;
    const size = Math.max(40, Math.min(100, z.radius / 2));
    const color = colors[z.type] || '#6366f1';
    return `
      <div class="map-zone-circle" style="
        left:${x}%; top:${y}%;
        width:${size}px; height:${size}px;
        border-color:${color};
        color:${color};
        background:${color}22;
      " title="${z.name}">
        ${getZoneTypeIcon(z.type)}
      </div>`;
  }).join('');

  updateUserPin();
};

/* ============================================================
   CHARTS
============================================================ */
const chartDefaults = {
  color: '#8b92b3',
  grid: { color: 'rgba(255,255,255,0.05)' }
};

const destroyChart = (key) => { if (state.charts[key]) { state.charts[key].destroy(); delete state.charts[key]; } };

const renderMonthlyChart = () => {
  const canvas = document.getElementById('monthlyChart');
  if (!canvas) return;
  destroyChart('monthly');

  const days = 30;
  const labels = [];
  const present = [], absent = [], late = [];

  for (let i = days - 1; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    const dStr = d.toDateString();
    labels.push(d.getDate());
    const dayRecs = state.records.filter(r => new Date(r.checkIn).toDateString() === dStr);
    present.push(dayRecs.filter(r => r.status === 'present').length);
    late.push(dayRecs.filter(r => r.status === 'late').length);
    absent.push(dayRecs.filter(r => r.status === 'absent').length);
  }

  state.charts['monthly'] = new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        { label: 'Present', data: present, backgroundColor: 'rgba(34,197,94,0.7)', borderRadius: 4 },
        { label: 'Late',    data: late,    backgroundColor: 'rgba(245,158,11,0.7)', borderRadius: 4 },
        { label: 'Absent',  data: absent,  backgroundColor: 'rgba(239,68,68,0.7)',  borderRadius: 4 }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { mode: 'index' } },
      scales: {
        x: { stacked: true, grid: chartDefaults.grid, ticks: { color: chartDefaults.color, font: { size: 11 } } },
        y: { stacked: true, grid: chartDefaults.grid, ticks: { color: chartDefaults.color, stepSize: 1 } }
      }
    }
  });
};

const renderReports = () => {
  const period = parseInt(document.getElementById('reportPeriod')?.value || 30);
  const cutoff = new Date(Date.now() - period * 24 * 3600 * 1000);
  const filtered = state.records.filter(r => new Date(r.checkIn) >= cutoff);

  const totalDays = period;
  const avgRate = totalDays > 0 ? Math.round((filtered.length / (totalDays * Math.max(1, state.zones.length || 1))) * 100) : 0;
  const totalMs = filtered.reduce((s, r) => {
    if (!r.checkOut) return s;
    return s + (new Date(r.checkOut) - new Date(r.checkIn));
  }, 0);
  const avgHrs = filtered.filter(r => r.checkOut).length > 0
    ? (totalMs / filtered.filter(r => r.checkOut).length / 3600000).toFixed(1)
    : 0;
  const lateCount = filtered.filter(r => r.status === 'late').length;

  const depts = {};
  filtered.forEach(r => { if (r.dept) depts[r.dept] = (depts[r.dept] || 0) + 1; });
  const topDept = Object.entries(depts).sort((a, b) => b[1] - a[1])[0]?.[0] || '--';

  document.getElementById('rptAvgRate').textContent  = `${Math.min(100, avgRate)}%`;
  document.getElementById('rptAvgHours').textContent = `${avgHrs}h`;
  document.getElementById('rptTopDept').textContent  = topDept;
  document.getElementById('rptLateCount').textContent = lateCount;

  renderTrendChart(filtered, period);
  renderDeptChart(depts);
  renderZoneChart(filtered);
};

const renderTrendChart = (records, period) => {
  const canvas = document.getElementById('trendChart');
  if (!canvas) return;
  destroyChart('trend');
  const labels = [], data = [];
  for (let i = period - 1; i >= 0; i--) {
    const d = new Date(); d.setDate(d.getDate() - i);
    labels.push(d.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' }));
    data.push(records.filter(r => new Date(r.checkIn).toDateString() === d.toDateString()).length);
  }
  state.charts['trend'] = new Chart(canvas, {
    type: 'line',
    data: {
      labels,
      datasets: [{ label: 'Attendance', data, fill: true,
        backgroundColor: 'rgba(99,102,241,0.1)', borderColor: '#6366f1',
        tension: 0.4, pointBackgroundColor: '#818cf8', pointRadius: 3 }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: chartDefaults.grid, ticks: { color: chartDefaults.color, font: { size: 10 }, maxTicksLimit: 10 } },
        y: { grid: chartDefaults.grid, ticks: { color: chartDefaults.color, stepSize: 1 } }
      }
    }
  });
};

const renderDeptChart = (depts) => {
  const canvas = document.getElementById('deptChart');
  if (!canvas) return;
  destroyChart('dept');
  const labels = Object.keys(depts);
  const data   = Object.values(depts);
  const colors = ['#6366f1','#22c55e','#f59e0b','#ef4444','#3b82f6','#8b5cf6'];
  state.charts['dept'] = new Chart(canvas, {
    type: 'doughnut',
    data: { labels, datasets: [{ data, backgroundColor: colors, borderWidth: 0 }] },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { position: 'right', labels: { color: '#8b92b3', padding: 14, font: { size: 12 } } }
      }
    }
  });
};

const renderZoneChart = (records) => {
  const canvas = document.getElementById('zoneChart');
  if (!canvas) return;
  destroyChart('zone');
  const zoneCounts = {};
  records.forEach(r => { zoneCounts[r.zoneName || 'Unknown'] = (zoneCounts[r.zoneName || 'Unknown'] || 0) + 1; });
  const labels = Object.keys(zoneCounts);
  const data   = Object.values(zoneCounts);
  state.charts['zone'] = new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [{ label: 'Check-ins', data, backgroundColor: 'rgba(99,102,241,0.7)', borderRadius: 6 }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: chartDefaults.grid, ticks: { color: chartDefaults.color } },
        y: { grid: chartDefaults.grid, ticks: { color: chartDefaults.color, stepSize: 1 } }
      }
    }
  });
};

/* ============================================================
   SETTINGS
============================================================ */
const saveSettings = () => {
  state.settings.startTime      = document.getElementById('settingStartTime').value;
  state.settings.endTime        = document.getElementById('settingEndTime').value;
  state.settings.lateThreshold  = parseInt(document.getElementById('settingLateThreshold').value);
  state.settings.radius         = parseInt(document.getElementById('settingRadius').value);
  save();
  showToast('✅ Settings saved', 'success');
};

const saveProfile = () => {
  state.settings.name  = document.getElementById('settingName').value.trim() || 'Admin User';
  state.settings.role  = document.getElementById('settingRole').value.trim() || 'Administrator';
  state.settings.email = document.getElementById('settingEmail').value.trim();
  save();
  updateProfileUI();
  showToast('✅ Profile saved', 'success');
};

const updateProfileUI = () => {
  const initials = state.settings.name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
  document.getElementById('userAvatar').textContent     = initials;
  document.getElementById('sidebarAvatar').textContent  = initials;
  document.getElementById('sidebarName').textContent    = state.settings.name;
  document.getElementById('sidebarRole').textContent    = state.settings.role;
};

const loadSettings = () => {
  document.getElementById('settingStartTime').value     = state.settings.startTime;
  document.getElementById('settingEndTime').value       = state.settings.endTime;
  document.getElementById('settingLateThreshold').value = state.settings.lateThreshold;
  document.getElementById('settingRadius').value        = state.settings.radius;
  document.getElementById('settingName').value          = state.settings.name;
  document.getElementById('settingRole').value          = state.settings.role;
  document.getElementById('settingEmail').value         = state.settings.email;
  updateProfileUI();
};

/* ============================================================
   THEME TOGGLE
============================================================ */
const toggleTheme = () => {
  const isLight = document.body.classList.toggle('light-theme');
  state.settings.theme = isLight ? 'light' : 'dark';
  document.getElementById('themeToggle').textContent = isLight ? '☀️' : '🌙';
  save();
};

/* ============================================================
   EXPORT CSV
============================================================ */
const exportCSV = () => {
  if (state.records.length === 0) { showToast('⚠️ No records to export', 'warning'); return; }
  const headers = ['#', 'Name', 'Employee ID', 'Department', 'Check In', 'Check Out', 'Duration', 'Zone', 'Status', 'Latitude', 'Longitude'];
  const rows = state.records.map((r, i) => [
    i + 1, r.name, r.empId, r.dept || '', fmt(r.checkIn), r.checkOut ? fmt(r.checkOut) : '',
    r.duration || '', r.zoneName || '', r.status, r.lat || '', r.lng || ''
  ]);
  const csv = [headers, ...rows].map(row => row.map(v => `"${String(v).replace(/"/g, '""')}"`).join(',')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href = url; a.download = `geoattend_export_${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
  showToast('📥 CSV exported successfully', 'success');
};

/* ============================================================
   DEMO DATA
============================================================ */
const importDemo = () => {
  if (!confirm('Load demo data? This will add sample zones and attendance records.')) return;

  // Demo zones
  state.zones = [
    { id: uid(), name: 'Main Office', address: 'Tech Park, Pune', lat: 18.5204, lng: 73.8567, radius: 150, type: 'office', createdAt: new Date().toISOString() },
    { id: uid(), name: 'Satellite Office', address: 'Baner, Pune', lat: 18.5600, lng: 73.7898, radius: 100, type: 'office', createdAt: new Date().toISOString() },
    { id: uid(), name: 'Client Site - Infosys', address: 'Hinjewadi, Pune', lat: 18.5912, lng: 73.7385, radius: 200, type: 'client', createdAt: new Date().toISOString() },
    { id: uid(), name: 'Work From Home', address: 'Virtual Zone', lat: 18.4088, lng: 73.8547, radius: 50, type: 'remote', createdAt: new Date().toISOString() }
  ];

  const names = ['Rahul Sharma', 'Priya Patel', 'Amit Kumar', 'Sneha Joshi', 'Vikram Singh', 'Anjali Mehta'];
  const depts = ['Engineering', 'Design', 'Marketing', 'HR', 'Finance', 'Operations'];
  const records = [];
  for (let d = 6; d >= 0; d--) {
    names.forEach((name, idx) => {
      const date = new Date();
      date.setDate(date.getDate() - d);
      if (Math.random() < 0.85) {
        const h = 8 + Math.floor(Math.random() * 2);
        const m = Math.floor(Math.random() * 60);
        date.setHours(h, m, 0);
        const zone = state.zones[Math.floor(Math.random() * state.zones.length)];
        const co = new Date(date);
        co.setHours(co.getHours() + 8 + Math.floor(Math.random() * 2));
        const status = h < 9 || (h === 9 && m <= 15) ? 'present' : 'late';
        records.push({
          id: uid(), name, empId: `EMP-00${idx + 1}`, dept: depts[idx],
          zoneName: zone.name, zoneId: zone.id, notes: '',
          checkIn: date.toISOString(), checkOut: co.toISOString(),
          duration: calcDuration(date.toISOString(), co.toISOString()),
          lat: zone.lat + (Math.random() - 0.5) * 0.001,
          lng: zone.lng + (Math.random() - 0.5) * 0.001,
          accuracy: 10 + Math.random() * 20, status
        });
      }
    });
  }
  state.records = records;
  save();
  navigateTo('dashboard');
  updateDashStats();
  showToast('✅ Demo data loaded successfully', 'success');
};

/* ============================================================
   CLEAR DATA
============================================================ */
const clearAllData = () => {
  if (!confirm('⚠️ This will permanently delete ALL attendance records. Are you sure?')) return;
  if (!confirm('This action cannot be undone. Confirm?')) return;
  state.records = [];
  state.session = null;
  save();
  renderRecords();
  updateDashStats();
  showToast('🗑️ All records cleared', 'info');
};

/* ============================================================
   TOAST NOTIFICATIONS
============================================================ */
const showToast = (message, type = 'info', duration = 3500) => {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
  toast.innerHTML = `<span>${icons[type] || 'ℹ️'}</span><span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.classList.add('toast-fade');
    setTimeout(() => toast.remove(), 300);
  }, duration);
};

/* ============================================================
   CLOCK
============================================================ */
const startClock = () => {
  const update = () => {
    const el = document.getElementById('navTime');
    if (el) el.textContent = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true });
  };
  update();
  setInterval(update, 1000);
};

/* ============================================================
   NAVIGATION EVENT BINDING
============================================================ */
const bindNavigation = () => {
  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      navigateTo(item.dataset.page);
    });
  });
  document.getElementById('themeToggle').addEventListener('click', toggleTheme);

  // Close modals on overlay click
  document.getElementById('zoneModal').addEventListener('click', (e) => {
    if (e.target.id === 'zoneModal') closeZoneModal();
  });
  document.getElementById('recordModal').addEventListener('click', (e) => {
    if (e.target.id === 'recordModal') closeRecordModal();
  });
};

/* ============================================================
   RESTORE SESSION
============================================================ */
const restoreSession = () => {
  if (!state.session) return;
  const record = state.records.find(r => r.id === state.session.recordId);
  if (!record) { state.session = null; save(); return; }
  document.getElementById('checkInBtn').style.display   = 'none';
  document.getElementById('checkOutBtn').style.display  = 'flex';
  document.getElementById('quickCheckInBtn').style.display  = 'none';
  document.getElementById('quickCheckOutBtn').style.display = 'flex';
  document.getElementById('sessionInfo').style.display  = 'block';
  document.getElementById('sessionStart').textContent   = fmt(record.checkIn, 'time');
  document.getElementById('empName').value  = record.name;
  document.getElementById('empId').value    = record.empId;
  document.getElementById('empDept').value  = record.dept;
  startSessionTimer();
  showToast('🔄 Active session restored', 'info');
};

/* ============================================================
   INIT
============================================================ */
const init = () => {
  load();
  startClock();
  bindNavigation();

  // Apply saved theme
  if (state.settings.theme === 'light') {
    document.body.classList.add('light-theme');
    document.getElementById('themeToggle').textContent = '☀️';
  }

  loadSettings();
  updateDashStats();
  renderActivityFeed();
  populateZoneSelect();
  renderMapZones();
  restoreSession();
  renderMonthlyChart();

  // Start GPS
  setTimeout(startLocationWatch, 500);

  // Show welcome toast
  showToast('👋 Welcome to GeoAttend!', 'info');
};

// Bootstrap when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
