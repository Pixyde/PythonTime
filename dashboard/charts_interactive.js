/* ============================================================
   Charts: Interactive Dashboard Components (22-24)
   22. KPI Cards with Trends
   23. Filterable Data Table
   24. Animated Race Bar Chart
   ============================================================ */

// ---- 22. KPI CARDS WITH TRENDS ----
registerChart('kpi', function() {
  const el = document.getElementById('chart-22');
  if (!el) return;

  const allProjects = flattenProjects(filteredData);
  const scored = allProjects.filter(p => p.final_mark !== null && p.final_mark !== undefined);
  const finished = allProjects.filter(p => p.status === 'finished');
  const validated = allProjects.filter(p => p.validated);

  const totalHours = filteredData.reduce((s, u) => s + u.total_python_hours, 0);
  const avgScore = scored.length ? mean(scored.map(p => p.final_mark)) : 0;
  const completionRate = allProjects.length ? (finished.length / allProjects.length) * 100 : 0;
  const validationRate = allProjects.length ? (validated.length / allProjects.length) * 100 : 0;
  const activeUsers = filteredData.length;
  const avgHoursPerUser = activeUsers ? totalHours / activeUsers : 0;

  // Simple trend: compare first half vs second half of users
  const half = Math.floor(filteredData.length / 2);
  const firstHalfHours = filteredData.slice(0, half).reduce((s, u) => s + u.total_python_hours, 0);
  const secondHalfHours = filteredData.slice(half).reduce((s, u) => s + u.total_python_hours, 0);
  const hoursTrend = half > 0 ? ((secondHalfHours / Math.max(firstHalfHours, 1)) - 1) * 100 : 0;

  // Average total completion time: days from first project start to last project end per user
  const completionDays = [];
  filteredData.forEach(u => {
    const starts = u.python_projects.map(p => p.start_date).filter(Boolean).map(d => new Date(d));
    const ends = u.python_projects.map(p => p.end_date).filter(Boolean).map(d => new Date(d));
    if (starts.length && ends.length) {
      const earliest = new Date(Math.min(...starts));
      const latest = new Date(Math.max(...ends));
      const days = (latest - earliest) / (1000 * 60 * 60 * 24);
      if (days > 0) completionDays.push(days);
    }
  });
  const avgCompletionDays = completionDays.length ? mean(completionDays) : 0;

  const kpis = [
    { label: 'Total Hours', value: formatNumber(totalHours), icon: '⏱️', color: COLORS.primary, trend: hoursTrend },
    { label: 'Active Users', value: activeUsers, icon: '👥', color: COLORS.cyan },
    { label: 'Avg Score', value: avgScore.toFixed(1), icon: '📊', color: COLORS.purple },
    { label: 'Completion Rate', value: completionRate.toFixed(0) + '%', icon: '✅', color: COLORS.green },
    { label: 'Validation Rate', value: validationRate.toFixed(0) + '%', icon: '🏆', color: COLORS.orange },
    { label: 'Avg Hours/User', value: avgHoursPerUser.toFixed(1), icon: '📈', color: COLORS.yellow },
    { label: 'Total Projects', value: allProjects.length, icon: '📦', color: COLORS.red },
    { label: 'Projects/Hour', value: (activeUsers > 0 && totalHours > 0 ? allProjects.length / totalHours : 0).toFixed(2), icon: '⚡', color: COLORS.cyan },
    { label: 'Avg Completion Time', value: avgCompletionDays > 0 ? avgCompletionDays.toFixed(0) + 'd' : '-', icon: '📅', color: COLORS.purple }
  ];

  el.innerHTML = '<div class="kpi-grid">' + kpis.map(kpi => `
    <div class="kpi-card">
      <div style="font-size:24px;margin-bottom:4px">${kpi.icon}</div>
      <div class="kpi-value" style="color:${kpi.color}">${kpi.value}</div>
      <div class="kpi-label">${kpi.label}</div>
      ${kpi.trend !== undefined ? `<div class="kpi-trend ${kpi.trend >= 0 ? 'up' : 'down'}">${kpi.trend >= 0 ? '▲' : '▼'} ${Math.abs(kpi.trend).toFixed(1)}%</div>` : ''}
    </div>
  `).join('') + '</div>';
});

// ---- 23. FILTERABLE DATA TABLE ----
registerChart('datatable', function() {
  const el = document.getElementById('chart-23');
  if (!el) return;
  if (!filteredData.length) { el.innerHTML = '<div class="chart-empty">No data</div>'; return; }

  const sortCol = el.dataset.sortCol || 'hours';
  const sortDir = el.dataset.sortDir || 'desc';
  const searchTerm = document.getElementById('datatable-search')?.value?.toLowerCase() || '';
  const pageSize = parseInt(document.getElementById('datatable-pagesize')?.value) || 20;
  const page = parseInt(el.dataset.page || '1');

  // Build flat rows
  let rows = flattenProjects(filteredData);

  // Search filter
  if (searchTerm) {
    rows = rows.filter(r =>
      r.login.toLowerCase().includes(searchTerm) ||
      r.project_name.toLowerCase().includes(searchTerm)
    );
  }

  // Sort
  const sortFns = {
    user: (a, b) => a.login.localeCompare(b.login),
    module: (a, b) => a.project_name.localeCompare(b.project_name),
    hours: (a, b) => a.time_spent_hours - b.time_spent_hours,
    mark: (a, b) => (a.final_mark || 0) - (b.final_mark || 0),
    status: (a, b) => a.status.localeCompare(b.status),
    start: (a, b) => new Date(a.start_date || 0) - new Date(b.start_date || 0),
    end: (a, b) => new Date(a.end_date || 0) - new Date(b.end_date || 0)
  };
  if (sortFns[sortCol]) {
    rows.sort(sortFns[sortCol]);
    if (sortDir === 'desc') rows.reverse();
  }

  // Paginate
  const totalPages = Math.ceil(rows.length / pageSize);
  const currentPage = Math.min(page, totalPages);
  const pageRows = rows.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  // Render
  const columns = [
    { key: 'user', label: 'User' },
    { key: 'module', label: 'Module' },
    { key: 'hours', label: 'Hours' },
    { key: 'mark', label: 'Mark' },
    { key: 'status', label: 'Status' },
    { key: 'start', label: 'Start Date' },
    { key: 'end', label: 'End Date' }
  ];

  let html = `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;padding:0 4px">
    <span style="color:#8e8e8e;font-size:11px">${rows.length} entries</span>
    <button class="export-btn" onclick="exportTableCSV()">📥 Export CSV</button>
  </div>`;

  html += '<div class="data-table-wrapper"><table class="data-table" id="datatable-table"><thead><tr>';
  columns.forEach(col => {
    const isActive = sortCol === col.key;
    const cls = isActive ? (sortDir === 'asc' ? 'sort-asc' : 'sort-desc') : '';
    html += `<th class="${cls}" onclick="sortDataTable('${col.key}')">${col.label}</th>`;
  });
  html += '</tr></thead><tbody>';

  pageRows.forEach(r => {
    html += `<tr>
      <td><strong>${r.login}</strong></td>
      <td>${r.project_name}</td>
      <td>${r.time_spent_hours.toFixed(1)}h</td>
      <td>${r.final_mark !== null && r.final_mark !== undefined ? r.final_mark : '-'}</td>
      <td><span class="badge badge-${r.status}">${r.status}</span>${r.validated ? ' <span class="badge badge-validated">✓</span>' : ''}</td>
      <td>${dateStr(r.start_date)}</td>
      <td>${dateStr(r.end_date)}</td>
    </tr>`;
  });
  html += '</tbody></table></div>';

  // Pagination
  if (totalPages > 1) {
    html += '<div class="pagination">';
    for (let p = 1; p <= Math.min(totalPages, 20); p++) {
      html += `<button class="${p === currentPage ? 'active' : ''}" onclick="document.getElementById('chart-23').dataset.page='${p}';chartUpdaters.datatable();">${p}</button>`;
    }
    if (totalPages > 20) html += `<span style="color:#8e8e8e;padding:4px">... ${totalPages}</span>`;
    html += '</div>';
  }

  el.innerHTML = html;
});

function sortDataTable(col) {
  const el = document.getElementById('chart-23');
  const current = el.dataset.sortCol;
  if (current === col) {
    el.dataset.sortDir = el.dataset.sortDir === 'asc' ? 'desc' : 'asc';
  } else {
    el.dataset.sortCol = col;
    el.dataset.sortDir = 'desc';
  }
  el.dataset.page = '1';
  chartUpdaters.datatable();
}

function exportTableCSV() {
  const rows = flattenProjects(filteredData);
  let csv = 'User,Module,Hours,Mark,Status,Validated,Start Date,End Date\n';
  rows.forEach(r => {
    csv += `"${r.login}","${r.project_name}",${r.time_spent_hours},${r.final_mark || ''},${r.status},${r.validated},${dateStr(r.start_date)},${dateStr(r.end_date)}\n`;
  });
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = 'python_time_data.csv'; a.click();
  URL.revokeObjectURL(url);
}

// ---- 24. ANIMATED RACE BAR CHART ----
registerChart('racebar', function() {
  const el = document.getElementById('chart-24');
  if (!el) return;
  if (!filteredData.length) { el.innerHTML = '<div class="chart-empty">No data</div>'; return; }

  const metric = document.getElementById('racebar-metric')?.value || 'hours';
  const numBars = parseInt(document.getElementById('racebar-bars')?.value) || 10;
  const speed = parseInt(document.getElementById('racebar-speed')?.value) || 500;

  // Build timeline of cumulative data
  const allDates = new Set();
  filteredData.forEach(u => u.python_projects.forEach(p => {
    if (p.end_date) allDates.add(dateStr(p.end_date));
  }));
  const dates = [...allDates].sort();
  if (dates.length < 2) { el.innerHTML = '<div class="chart-empty">Insufficient data</div>'; return; }

  // Pre-compute user color index map for O(1) lookups
  const allUsersList = getAllUsers();
  const userColorIdx = {};
  allUsersList.forEach((u, i) => { userColorIdx[u] = i; });

  // Sample dates for animation frames (max 30)
  const step = Math.max(1, Math.floor(dates.length / 30));
  const frames = [];

  for (let di = 0; di < dates.length; di += step) {
    const date = dates[di];
    const snapshot = filteredData.map(u => {
      const completedByDate = u.python_projects.filter(p => p.end_date && dateStr(p.end_date) <= date);
      let val;
      if (metric === 'modules') {
        val = completedByDate.length;
      } else {
        val = completedByDate.reduce((s, p) => s + p.time_spent_hours, 0);
      }
      return { login: u.login, value: val };
    }).sort((a, b) => b.value - a.value).slice(0, numBars);

    // Only add frames that have at least one non-zero value
    if (snapshot.some(s => s.value > 0)) {
      frames.push({ date, snapshot });
    }
  }
  // Always include the last date as the final frame
  const lastDate = dates[dates.length - 1];
  if (!frames.length || frames[frames.length - 1].date !== lastDate) {
    const lastSnapshot = filteredData.map(u => {
      const completedByDate = u.python_projects.filter(p => p.end_date && dateStr(p.end_date) <= lastDate);
      let val;
      if (metric === 'modules') {
        val = completedByDate.length;
      } else {
        val = completedByDate.reduce((s, p) => s + p.time_spent_hours, 0);
      }
      return { login: u.login, value: val };
    }).sort((a, b) => b.value - a.value).slice(0, numBars);
    if (lastSnapshot.some(s => s.value > 0)) {
      frames.push({ date: lastDate, snapshot: lastSnapshot });
    }
  }

  if (!frames.length) { el.innerHTML = '<div class="chart-empty">No animation frames</div>'; return; }

  function getUserColor(login) {
    return COLORS.palette[(userColorIdx[login] || 0) % COLORS.palette.length];
  }

  // Compute max value across all frames
  let maxVal = 1;
  frames.forEach(f => f.snapshot.forEach(s => { if (s.value > maxVal) maxVal = s.value; }));

  // Animation frames
  const plotlyFrames = frames.map(f => ({
    name: f.date,
    data: [{
      type: 'bar',
      orientation: 'h',
      y: f.snapshot.map(s => s.login).reverse(),
      x: f.snapshot.map(s => s.value).reverse(),
      marker: {
        color: f.snapshot.map(s => getUserColor(s.login)).reverse()
      },
      text: f.snapshot.map(s => `${s.value.toFixed(1)}`).reverse(),
      textposition: 'outside',
      textfont: { size: 10, color: '#8e8e8e' }
    }],
    layout: {
      title: { text: f.date, font: { color: '#8e8e8e', size: 14 }, x: 0.95, xanchor: 'right' }
    }
  }));

  // Initial state
  const first = frames[0];
  const trace = {
    type: 'bar',
    orientation: 'h',
    y: first.snapshot.map(s => s.login).reverse(),
    x: first.snapshot.map(s => s.value).reverse(),
    marker: {
      color: first.snapshot.map(s => getUserColor(s.login)).reverse()
    },
    text: first.snapshot.map(s => `${s.value.toFixed(1)}`).reverse(),
    textposition: 'outside',
    textfont: { size: 10, color: '#8e8e8e' }
  };

  const layout = {
    ...PLOTLY_LAYOUT_DEFAULTS,
    margin: { t: 40, r: 60, b: 40, l: 120 },
    xaxis: { ...PLOTLY_LAYOUT_DEFAULTS.xaxis, title: metric === 'modules' ? 'Modules Completed' : 'Cumulative Hours', range: [0, maxVal * 1.15] },
    yaxis: { ...PLOTLY_LAYOUT_DEFAULTS.yaxis },
    title: { text: first.date, font: { color: '#8e8e8e', size: 14 }, x: 0.95, xanchor: 'right' },
    updatemenus: [{
      type: 'buttons',
      showactive: false,
      x: 0, xanchor: 'left', y: 1.15, yanchor: 'top',
      buttons: [
        { label: '▶ Play', method: 'animate', args: [null, { frame: { duration: speed, redraw: true }, transition: { duration: speed / 2 }, fromcurrent: true, mode: 'immediate' }] },
        { label: '⏸ Pause', method: 'animate', args: [[null], { frame: { duration: 0, redraw: false }, mode: 'immediate' }] }
      ],
      font: { color: '#e0e0e0', size: 11 },
      bgcolor: '#22252b',
      bordercolor: '#3a3f4a'
    }],
    sliders: [{
      active: 0,
      steps: frames.map(f => ({ label: f.date, method: 'animate', args: [[f.date], { frame: { duration: 0, redraw: true }, mode: 'immediate' }] })),
      x: 0, len: 1,
      currentvalue: { prefix: 'Date: ', font: { color: '#8e8e8e', size: 12 } },
      font: { color: '#8e8e8e', size: 9 },
      bgcolor: '#22252b',
      bordercolor: '#3a3f4a',
      activebgcolor: '#33a2e5'
    }]
  };

  // Use Plotly.newPlot for proper animation support, then add frames
  Plotly.newPlot(el, [trace], layout, PLOTLY_CONFIG).then(function() {
    if (plotlyFrames.length > 0) {
      Plotly.addFrames(el, plotlyFrames);
    }
  }).catch(function(err) {
    console.error('Race bar chart animation error:', err);
  });
});
