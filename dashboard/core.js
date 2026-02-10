/* ============================================================
   Core Module - Data processing, filters, utilities
   ============================================================ */

// ---- GLOBAL STATE ----
const RAW_DATA = {{DATA_PLACEHOLDER}};
let filteredData = [];
let globalFilters = {
  users: [],
  modules: [],
  campuses: [],
  status: 'all',
  validatedOnly: false,
  dateStart: '',
  dateEnd: '',
  scoreMin: 0,
  scoreMax: 100,
  hourMin: 0
};

// ---- PLOTLY DEFAULTS ----
const PLOTLY_LAYOUT_DEFAULTS = {
  paper_bgcolor: 'rgba(0,0,0,0)',
  plot_bgcolor: 'rgba(0,0,0,0)',
  font: { color: '#8e8e8e', family: '-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif', size: 11 },
  margin: { t: 30, r: 20, b: 40, l: 50 },
  xaxis: { gridcolor: '#2c3038', zerolinecolor: '#2c3038' },
  yaxis: { gridcolor: '#2c3038', zerolinecolor: '#2c3038' },
  colorway: ['#33a2e5','#73bf69','#ff9830','#f2495c','#b877d9','#fade2a','#5794f2','#ff6384','#36a2eb','#cc65fe'],
  hoverlabel: { bgcolor: '#1a1d23', bordercolor: '#3a3f4a', font: { color: '#e0e0e0', size: 11 } }
};

const PLOTLY_CONFIG = {
  displayModeBar: true,
  displaylogo: false,
  modeBarButtonsToRemove: ['lasso2d','select2d'],
  responsive: true
};

// ---- COLOR PALETTES ----
const COLORS = {
  primary: '#33a2e5',
  green: '#73bf69',
  orange: '#ff9830',
  red: '#f2495c',
  purple: '#b877d9',
  yellow: '#fade2a',
  cyan: '#5794f2',
  palette: ['#33a2e5','#73bf69','#ff9830','#f2495c','#b877d9','#fade2a','#5794f2','#ff6384','#36a2eb','#cc65fe',
            '#4dc9f6','#f67019','#f53794','#537bc4','#acc236','#166a8f','#00a950','#58595b','#8549ba','#e6194b']
};

const STATUS_COLORS = {
  finished: '#73bf69',
  in_progress: '#5794f2',
  waiting: '#ff9830',
  unknown: '#8e8e8e'
};

// ---- NEW COMMON CORE MODULE SLUGS ----
const NEW_COMMON_CORE_SLUGS = [
  'python-0-starting',
  'python-1-base',
  'python-2-datascience',
  'python-3-oop',
  'python-module-00',
  'python-module-01',
  'python-module-02',
  'python-module-03',
  'python-module-04',
  'piscine-python',
  'piscine-python-datascience',
  'django-0-starting',
  'django-1-base-django',
  'django-2-sql',
  'django-3-advanced',
  'django-4-final',
];

function isNewCommonCoreProject(project) {
  const slug = (project.project_slug || '').toLowerCase();
  const name = (project.project_name || '').toLowerCase();
  return NEW_COMMON_CORE_SLUGS.some(m => slug.includes(m) || name.includes(m));
}

function getNewCommonCoreModules() {
  const modules = new Set();
  RAW_DATA.forEach(u => u.python_projects.forEach(p => {
    if (isNewCommonCoreProject(p)) modules.add(p.project_name);
  }));
  return [...modules].sort();
}

function isNewCommonCoreUser(user) {
  return user.python_projects.some(p => isNewCommonCoreProject(p));
}

function getCompletionDays(project) {
  if (!project.start_date || !project.end_date) return null;
  const start = new Date(project.start_date);
  const end = new Date(project.end_date);
  const days = (end - start) / (1000 * 60 * 60 * 24);
  return days > 0 ? days : null;
}

// ---- UTILITY FUNCTIONS ----
function getAllUsers() {
  return [...new Set(RAW_DATA.map(u => u.login))].sort();
}

function getAllModules() {
  const modules = new Set();
  RAW_DATA.forEach(u => u.python_projects.forEach(p => modules.add(p.project_name)));
  return [...modules].sort();
}

function getAllStatuses() {
  const statuses = new Set();
  RAW_DATA.forEach(u => u.python_projects.forEach(p => statuses.add(p.status)));
  return [...statuses].sort();
}

function getAllCampuses() {
  const campuses = new Set();
  RAW_DATA.forEach(u => { if (u.campus_name) campuses.add(u.campus_name); });
  return [...campuses].sort();
}

function flattenProjects(data) {
  const rows = [];
  data.forEach(user => {
    user.python_projects.forEach(proj => {
      rows.push({ ...proj, login: user.login, user_id: user.user_id, total_python_hours: user.total_python_hours });
    });
  });
  return rows;
}

function formatHours(h) {
  return h < 1 ? h.toFixed(1) + 'h' : Math.round(h) + 'h';
}

function formatNumber(n) {
  return n.toLocaleString(undefined, { maximumFractionDigits: 1 });
}

function percentile(arr, p) {
  const sorted = [...arr].sort((a, b) => a - b);
  const idx = (p / 100) * (sorted.length - 1);
  const lo = Math.floor(idx);
  const hi = Math.ceil(idx);
  if (lo === hi) return sorted[lo];
  return sorted[lo] + (sorted[hi] - sorted[lo]) * (idx - lo);
}

function mean(arr) { return arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0; }
function median(arr) { return arr.length ? percentile(arr, 50) : 0; }
function stddev(arr) { if (arr.length < 2) return 0; const m = mean(arr); return Math.sqrt(arr.reduce((s, x) => s + (x - m) ** 2, 0) / arr.length); }
function sum(arr) { return arr.reduce((a, b) => a + b, 0); }

function dateStr(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toISOString().split('T')[0];
}

// ---- APPLY GLOBAL FILTERS ----
function applyGlobalFilters() {
  filteredData = RAW_DATA.map(user => {
    // User filter
    if (globalFilters.users.length > 0 && !globalFilters.users.includes(user.login)) return null;
    // Campus filter
    if (globalFilters.campuses.length > 0 && !globalFilters.campuses.includes(user.campus_name)) return null;

    // Filter projects within user
    let projects = user.python_projects.filter(p => {
      // Module filter
      if (globalFilters.modules.length > 0 && !globalFilters.modules.includes(p.project_name)) return false;
      // Status filter
      if (globalFilters.status !== 'all' && p.status !== globalFilters.status) return false;
      // Validated filter
      if (globalFilters.validatedOnly && !p.validated) return false;
      // Date filter
      if (globalFilters.dateStart && p.start_date && new Date(p.start_date) < new Date(globalFilters.dateStart)) return false;
      if (globalFilters.dateEnd && p.end_date && new Date(p.end_date) > new Date(globalFilters.dateEnd)) return false;
      // Score filter
      if (p.final_mark !== null && p.final_mark !== undefined) {
        if (p.final_mark < globalFilters.scoreMin || p.final_mark > globalFilters.scoreMax) return false;
      }
      // Hour threshold
      if (p.time_spent_hours < globalFilters.hourMin) return false;
      return true;
    });

    if (projects.length === 0) return null;

    return {
      ...user,
      python_projects: projects,
      total_python_hours: projects.reduce((s, p) => s + p.time_spent_hours, 0)
    };
  }).filter(Boolean);
}

// ---- POPULATE GLOBAL FILTERS ----
function populateGlobalFilters() {
  const users = getAllUsers();
  const modules = getAllModules();
  const statuses = getAllStatuses();
  const campuses = getAllCampuses();

  // User multi-select
  const userDropdown = document.getElementById('filter-users-dropdown');
  if (userDropdown) {
    userDropdown.innerHTML = users.map(u =>
      `<label><input type="checkbox" value="${u}" onchange="onGlobalFilterChange()"> ${u}</label>`
    ).join('');
  }

  // Module multi-select
  const moduleDropdown = document.getElementById('filter-modules-dropdown');
  if (moduleDropdown) {
    moduleDropdown.innerHTML = modules.map(m =>
      `<label><input type="checkbox" value="${m}" onchange="onGlobalFilterChange()"> ${m}</label>`
    ).join('');
  }

  // Campus multi-select
  const campusDropdown = document.getElementById('filter-campus-dropdown');
  if (campusDropdown) {
    campusDropdown.innerHTML = campuses.map(c =>
      `<label><input type="checkbox" value="${c}" onchange="onGlobalFilterChange()"> ${c}</label>`
    ).join('');
  }

  // Status select
  const statusSelect = document.getElementById('filter-status');
  if (statusSelect) {
    statusSelect.innerHTML = '<option value="all">All</option>' +
      statuses.map(s => `<option value="${s}">${s}</option>`).join('');
  }

  // Date range
  const allDates = [];
  RAW_DATA.forEach(u => u.python_projects.forEach(p => {
    if (p.start_date) allDates.push(new Date(p.start_date));
    if (p.end_date) allDates.push(new Date(p.end_date));
  }));
  if (allDates.length) {
    const minDate = new Date(Math.min(...allDates));
    const maxDate = new Date(Math.max(...allDates));
    const startInput = document.getElementById('filter-date-start');
    const endInput = document.getElementById('filter-date-end');
    if (startInput) startInput.value = minDate.toISOString().split('T')[0];
    if (endInput) endInput.value = maxDate.toISOString().split('T')[0];
  }
}

function onGlobalFilterChange() {
  // Read user selections
  const userCheckboxes = document.querySelectorAll('#filter-users-dropdown input:checked');
  globalFilters.users = [...userCheckboxes].map(cb => cb.value);
  document.getElementById('filter-users-display-text').textContent =
    globalFilters.users.length ? `${globalFilters.users.length} selected` : 'All Users';

  // Read module selections
  const moduleCheckboxes = document.querySelectorAll('#filter-modules-dropdown input:checked');
  globalFilters.modules = [...moduleCheckboxes].map(cb => cb.value);
  document.getElementById('filter-modules-display-text').textContent =
    globalFilters.modules.length ? `${globalFilters.modules.length} selected` : 'All Modules';

  // Read campus selections
  const campusCheckboxes = document.querySelectorAll('#filter-campus-dropdown input:checked');
  globalFilters.campuses = [...campusCheckboxes].map(cb => cb.value);
  const campusDisplay = document.getElementById('filter-campus-display-text');
  if (campusDisplay) campusDisplay.textContent =
    globalFilters.campuses.length ? `${globalFilters.campuses.length} selected` : 'All Campuses';

  // Read other filters
  globalFilters.status = document.getElementById('filter-status').value;
  globalFilters.validatedOnly = document.getElementById('filter-validated').checked;
  globalFilters.dateStart = document.getElementById('filter-date-start').value;
  globalFilters.dateEnd = document.getElementById('filter-date-end').value;
  globalFilters.scoreMin = parseFloat(document.getElementById('filter-score-min').value) || 0;
  globalFilters.scoreMax = parseFloat(document.getElementById('filter-score-max').value) || 100;
  globalFilters.hourMin = parseFloat(document.getElementById('filter-hour-min').value) || 0;

  applyGlobalFilters();
  updateAllCharts();
}

function resetGlobalFilters() {
  document.querySelectorAll('#filter-users-dropdown input, #filter-modules-dropdown input, #filter-campus-dropdown input').forEach(cb => cb.checked = false);
  document.getElementById('filter-status').value = 'all';
  document.getElementById('filter-validated').checked = false;
  document.getElementById('filter-score-min').value = '0';
  document.getElementById('filter-score-max').value = '100';
  document.getElementById('filter-hour-min').value = '0';
  populateGlobalFilters();
  onGlobalFilterChange();
}

// ---- MULTI-SELECT TOGGLE ----
function toggleMultiSelect(id) {
  const dd = document.getElementById(id);
  document.querySelectorAll('.multi-select-dropdown').forEach(d => {
    if (d.id !== id) d.classList.remove('open');
  });
  dd.classList.toggle('open');
}
document.addEventListener('click', function(e) {
  if (!e.target.closest('.multi-select')) {
    document.querySelectorAll('.multi-select-dropdown').forEach(d => d.classList.remove('open'));
  }
});

// ---- NAVIGATION ----
let activeSection = 'all';

function showSection(section) {
  activeSection = section;
  document.querySelectorAll('.nav button').forEach(b => b.classList.toggle('active', b.dataset.section === section));
  document.querySelectorAll('.section').forEach(s => {
    if (section === 'all') {
      s.classList.remove('hidden');
    } else {
      s.classList.toggle('hidden', s.dataset.section !== section);
    }
  });
}

// ---- UPDATE ALL CHARTS ----
const chartUpdaters = {};

function registerChart(id, updateFn) {
  chartUpdaters[id] = updateFn;
}

function updateAllCharts() {
  Object.values(chartUpdaters).forEach(fn => {
    try { fn(); } catch(e) { console.error('Chart update error:', e); }
  });
}

// ---- HEADER STATS ----
function updateHeaderStats() {
  const stats = document.getElementById('header-stats');
  if (!stats) return;
  const totalUsers = filteredData.length;
  const totalHours = filteredData.reduce((s, u) => s + u.total_python_hours, 0);
  const totalProjects = filteredData.reduce((s, u) => s + u.python_projects.length, 0);
  const campuses = new Set(filteredData.map(u => u.campus_name).filter(Boolean));
  stats.innerHTML = `
    <span>👥 <strong>${totalUsers}</strong> Users</span>
    <span>⏱️ <strong>${formatNumber(totalHours)}</strong> Hours</span>
    <span>📦 <strong>${totalProjects}</strong> Projects</span>
    ${campuses.size > 0 ? `<span>🏫 <strong>${campuses.size}</strong> Campus${campuses.size > 1 ? 'es' : ''}</span>` : ''}
  `;
}
