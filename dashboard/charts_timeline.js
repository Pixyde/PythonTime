/* ============================================================
   Charts: Timeline Visualizations (1-3)
   1. Timeline Gantt Chart
   2. Time Spent Heatmap Calendar
   3. Progress Timeline
   ============================================================ */

// ---- 1. TIMELINE GANTT CHART ----
registerChart('gantt', function() {
  const el = document.getElementById('chart-1');
  if (!el) return;
  if (!filteredData.length) { el.innerHTML = '<div class="chart-empty">No data</div>'; return; }

  const userSelect = document.getElementById('gantt-user');
  const colorBy = document.getElementById('gantt-color');
  const sortBy = document.getElementById('gantt-sort');
  const showNames = document.getElementById('gantt-names');
  const minHours = parseFloat(document.getElementById('gantt-min-hours')?.value) || 0;

  // Populate user dropdown (no "All Users" option)
  if (userSelect && userSelect.options.length === 0) {
    const users = getAllUsers();
    userSelect.innerHTML = users.map(u => `<option value="${u}">${u}</option>`).join('');
  }

  // Always show a single user
  const selectedUser = userSelect?.value || '';
  if (!selectedUser) { el.innerHTML = '<div class="chart-empty">Select a user</div>'; return; }
  const data = filteredData.filter(u => u.login === selectedUser);

  const allRows = [];

  data.forEach(user => {
    user.python_projects.forEach(proj => {
      if (proj.time_spent_hours < minHours) return;
      if (!proj.start_date || !proj.end_date) return;
      allRows.push({ user: user.login, proj, start: new Date(proj.start_date), end: new Date(proj.end_date) });
    });
  });

  if (!allRows.length) { el.innerHTML = '<div class="chart-empty">No projects with dates</div>'; return; }

  if (sortBy && sortBy.value === 'hours') {
    allRows.sort((a, b) => b.proj.time_spent_hours - a.proj.time_spent_hours);
  } else {
    allRows.sort((a, b) => a.user.localeCompare(b.user) || a.start - b.start);
  }

  // Use one scatter trace per row to draw horizontal bars (reliable Gantt)
  const traces = allRows.map((r, i) => {
    const yLabel = `${r.user} - ${r.proj.project_name}`;
    const color = (colorBy && colorBy.value === 'status')
      ? (STATUS_COLORS[r.proj.status] || '#8e8e8e')
      : COLORS.palette[i % COLORS.palette.length];
    return {
      type: 'scatter',
      mode: 'lines',
      x: [r.start.toISOString(), r.end.toISOString()],
      y: [yLabel, yLabel],
      line: { color: color, width: 16 },
      hovertext: `${r.user}: ${r.proj.project_name}<br>${r.proj.time_spent_hours.toFixed(1)}h | ${r.proj.status}`,
      hoverinfo: 'text',
      showlegend: false,
      text: showNames?.checked ? [r.proj.project_name, ''] : undefined,
      textposition: 'middle center',
      textfont: { size: 9, color: '#fff' }
    };
  });

  const yLabels = allRows.map(r => `${r.user} - ${r.proj.project_name}`);
  const layout = {
    ...PLOTLY_LAYOUT_DEFAULTS,
    margin: { t: 10, r: 20, b: 40, l: 200 },
    xaxis: { ...PLOTLY_LAYOUT_DEFAULTS.xaxis, type: 'date', title: 'Date' },
    yaxis: { ...PLOTLY_LAYOUT_DEFAULTS.yaxis, categoryorder: 'array', categoryarray: [...yLabels].reverse(), type: 'category' },
    height: Math.max(350, allRows.length * 28 + 60)
  };

  Plotly.react(el, traces, layout, PLOTLY_CONFIG);
});

// ---- 2. TIME SPENT HEATMAP CALENDAR ----
registerChart('heatmap', function() {
  const el = document.getElementById('chart-2');
  if (!el) return;
  if (!filteredData.length) { el.innerHTML = '<div class="chart-empty">No data</div>'; return; }

  const aggBy = document.getElementById('heatmap-agg')?.value || 'day';
  const threshold = parseFloat(document.getElementById('heatmap-threshold')?.value) || 0;
  const showWeekends = document.getElementById('heatmap-weekends')?.checked !== false;

  // Build daily activity map
  const dayMap = {};
  filteredData.forEach(user => {
    user.python_projects.forEach(proj => {
      if (!proj.start_date || !proj.end_date) return;
      const start = new Date(proj.start_date);
      const end = new Date(proj.end_date);
      const days = Math.max(1, (end - start) / (1000 * 3600 * 24));
      const hoursPerDay = proj.time_spent_hours / days;
      for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
        const key = d.toISOString().split('T')[0];
        if (!showWeekends && (d.getDay() === 0 || d.getDay() === 6)) continue;
        dayMap[key] = (dayMap[key] || 0) + hoursPerDay;
      }
    });
  });

  const dates = Object.keys(dayMap).sort();
  if (!dates.length) { el.innerHTML = '<div class="chart-empty">No date data</div>'; return; }

  let xLabels, yLabels, zValues;

  if (aggBy === 'week') {
    // Aggregate by week
    const weekMap = {};
    dates.forEach(d => {
      const dt = new Date(d);
      const week = getWeekNumber(dt);
      const year = dt.getFullYear();
      const key = `${year}-W${String(week).padStart(2, '0')}`;
      weekMap[key] = (weekMap[key] || 0) + dayMap[d];
    });
    xLabels = Object.keys(weekMap).sort();
    zValues = [xLabels.map(k => weekMap[k] >= threshold ? weekMap[k] : 0)];
    yLabels = ['Activity'];
  } else if (aggBy === 'month') {
    const monthMap = {};
    dates.forEach(d => {
      const key = d.substring(0, 7);
      monthMap[key] = (monthMap[key] || 0) + dayMap[d];
    });
    xLabels = Object.keys(monthMap).sort();
    zValues = [xLabels.map(k => monthMap[k] >= threshold ? monthMap[k] : 0)];
    yLabels = ['Activity'];
  } else {
    // Daily - organize by week/day
    const weeks = {};
    dates.forEach(d => {
      const dt = new Date(d);
      const day = dt.getDay();
      const weekStart = new Date(dt);
      weekStart.setDate(weekStart.getDate() - day);
      const wk = weekStart.toISOString().split('T')[0];
      if (!weeks[wk]) weeks[wk] = new Array(7).fill(0);
      weeks[wk][day] = dayMap[d] >= threshold ? dayMap[d] : 0;
    });
    xLabels = Object.keys(weeks).sort();
    yLabels = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
    zValues = yLabels.map((_, dayIdx) => xLabels.map(wk => weeks[wk][dayIdx]));
  }

  const trace = {
    type: 'heatmap',
    x: xLabels,
    y: yLabels,
    z: zValues,
    colorscale: [[0,'#0b0c0e'],[0.25,'#1a3a5c'],[0.5,'#2a6a9c'],[0.75,'#33a2e5'],[1,'#73bf69']],
    hovertemplate: '%{x}<br>%{y}: %{z:.1f}h<extra></extra>',
    showscale: true,
    colorbar: { title: 'Hours', titleside: 'right', tickfont: { color: '#8e8e8e' }, titlefont: { color: '#8e8e8e' } }
  };

  const layout = {
    ...PLOTLY_LAYOUT_DEFAULTS,
    margin: { t: 10, r: 80, b: 60, l: 60 },
    xaxis: { ...PLOTLY_LAYOUT_DEFAULTS.xaxis, title: aggBy === 'day' ? 'Week Starting' : (aggBy === 'week' ? 'Week' : 'Month') },
    yaxis: { ...PLOTLY_LAYOUT_DEFAULTS.yaxis }
  };

  Plotly.react(el, [trace], layout, PLOTLY_CONFIG);
});

function getWeekNumber(d) {
  d = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
  d.setUTCDate(d.getUTCDate() + 4 - (d.getUTCDay() || 7));
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  return Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
}

// ---- 3. PROGRESS TIMELINE ----
registerChart('progress', function() {
  const el = document.getElementById('chart-3');
  if (!el) return;
  if (!filteredData.length) { el.innerHTML = '<div class="chart-empty">No data</div>'; return; }

  const granularity = document.getElementById('progress-granularity')?.value || 'weekly';
  const stackBy = document.getElementById('progress-stack')?.value || 'module';
  const cumulative = document.getElementById('progress-cumulative')?.checked !== false;

  // Collect completion events
  const events = [];
  filteredData.forEach(user => {
    user.python_projects.forEach(proj => {
      if (proj.status === 'finished' && proj.end_date) {
        events.push({ date: new Date(proj.end_date), module: proj.project_name, user: user.login, hours: proj.time_spent_hours });
      }
    });
  });
  events.sort((a, b) => a.date - b.date);

  if (!events.length) { el.innerHTML = '<div class="chart-empty">No completion data</div>'; return; }

  // Group by time period
  const groupKey = stackBy === 'user' ? 'user' : 'module';
  const groups = [...new Set(events.map(e => e[groupKey]))].sort();
  const periodMap = {};

  events.forEach(e => {
    let pk;
    if (granularity === 'daily') pk = e.date.toISOString().split('T')[0];
    else if (granularity === 'monthly') pk = e.date.toISOString().substring(0, 7);
    else {
      const d = new Date(e.date);
      d.setDate(d.getDate() - d.getDay());
      pk = d.toISOString().split('T')[0];
    }
    if (!periodMap[pk]) periodMap[pk] = {};
    periodMap[pk][e[groupKey]] = (periodMap[pk][e[groupKey]] || 0) + 1;
  });

  const periods = Object.keys(periodMap).sort();
  const traces = groups.map((g, i) => {
    let runningTotal = 0;
    const yVals = periods.map(p => {
      const val = periodMap[p][g] || 0;
      if (cumulative) { runningTotal += val; return runningTotal; }
      return val;
    });
    return {
      type: 'scatter',
      mode: 'lines',
      name: g,
      x: periods,
      y: yVals,
      stackgroup: cumulative ? undefined : 'one',
      line: { width: 2 },
      marker: { color: COLORS.palette[i % COLORS.palette.length] }
    };
  });

  const layout = {
    ...PLOTLY_LAYOUT_DEFAULTS,
    margin: { t: 10, r: 20, b: 50, l: 50 },
    xaxis: { ...PLOTLY_LAYOUT_DEFAULTS.xaxis, title: 'Date' },
    yaxis: { ...PLOTLY_LAYOUT_DEFAULTS.yaxis, title: cumulative ? 'Cumulative Completions' : 'Completions' },
    legend: { font: { size: 10 }, orientation: 'h', y: -0.15 },
    showlegend: groups.length <= 15
  };

  Plotly.react(el, traces, layout, PLOTLY_CONFIG);
});
