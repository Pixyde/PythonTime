/* ============================================================
   Charts: Module Statistics (26-27)
   26. Module Statistics Table (avg, median, std dev, completion)
   27. Average Time per Module Bar Chart
   ============================================================ */

// ---- 26. MODULE STATISTICS TABLE ----
registerChart('modulestats', function() {
  const el = document.getElementById('chart-26');
  if (!el) return;
  if (!filteredData.length) { el.innerHTML = '<div class="chart-empty">No data</div>'; return; }

  const sortBy = document.getElementById('modstats-sort')?.value || 'avg';
  const sortDir = document.getElementById('modstats-dir')?.value || 'desc';

  // Collect per-module data
  const moduleMap = {};
  const allModules = getAllModules();
  const totalUsers = filteredData.length;

  filteredData.forEach(user => {
    user.python_projects.forEach(proj => {
      const name = proj.project_name;
      if (!moduleMap[name]) moduleMap[name] = { hours: [], marks: [], finished: 0, total: 0, validated: 0, users: new Set() };
      moduleMap[name].hours.push(proj.time_spent_hours);
      if (proj.final_mark !== null && proj.final_mark !== undefined) moduleMap[name].marks.push(proj.final_mark);
      if (proj.status === 'finished') moduleMap[name].finished++;
      if (proj.validated) moduleMap[name].validated++;
      moduleMap[name].total++;
      moduleMap[name].users.add(user.login);
    });
  });

  // Build stats array
  let stats = Object.entries(moduleMap).map(([name, d]) => {
    const avgH = mean(d.hours);
    const medH = median(d.hours);
    const stdH = stddev(d.hours);
    const minH = Math.min(...d.hours);
    const maxH = Math.max(...d.hours);
    const avgMark = d.marks.length ? mean(d.marks) : null;
    const medMark = d.marks.length ? median(d.marks) : null;
    const completionPct = d.total > 0 ? (d.finished / d.total) * 100 : 0;
    const validationPct = d.total > 0 ? (d.validated / d.total) * 100 : 0;
    return { name, avgH, medH, stdH, minH, maxH, avgMark, medMark, completionPct, validationPct, students: d.users.size, total: d.total };
  });

  // Sort
  const sortFns = {
    name: (a, b) => a.name.localeCompare(b.name),
    avg: (a, b) => a.avgH - b.avgH,
    median: (a, b) => a.medH - b.medH,
    students: (a, b) => a.students - b.students,
    completion: (a, b) => a.completionPct - b.completionPct
  };
  if (sortFns[sortBy]) {
    stats.sort(sortFns[sortBy]);
    if (sortDir === 'desc') stats.reverse();
  }

  // Overall stats row
  const allHours = stats.flatMap(s => moduleMap[s.name].hours);
  const allMarks = stats.flatMap(s => moduleMap[s.name].marks);
  const overallAvgH = mean(allHours);
  const overallMedH = median(allHours);
  const overallStdH = stddev(allHours);

  // Render table
  let html = '<div class="data-table-wrapper"><table class="data-table"><thead><tr>';
  html += '<th>Module</th><th>Students</th><th>Avg Hours</th><th>Median Hours</th><th>Std Dev</th><th>Min</th><th>Max</th>';
  html += '<th>Avg Mark</th><th>Median Mark</th><th>Completion %</th><th>Validation %</th>';
  html += '</tr></thead><tbody>';

  // Overall row
  html += '<tr style="background:rgba(51,162,229,0.08);font-weight:600">';
  html += `<td>📊 Overall (All Modules)</td>`;
  html += `<td>${totalUsers}</td>`;
  html += `<td>${overallAvgH.toFixed(1)}h</td>`;
  html += `<td>${overallMedH.toFixed(1)}h</td>`;
  html += `<td>${overallStdH.toFixed(1)}</td>`;
  html += `<td>${allHours.length ? Math.min(...allHours).toFixed(1) : '-'}h</td>`;
  html += `<td>${allHours.length ? Math.max(...allHours).toFixed(1) : '-'}h</td>`;
  html += `<td>${allMarks.length ? mean(allMarks).toFixed(1) : '-'}</td>`;
  html += `<td>${allMarks.length ? median(allMarks).toFixed(1) : '-'}</td>`;
  html += `<td>-</td><td>-</td>`;
  html += '</tr>';

  stats.forEach(s => {
    html += '<tr>';
    html += `<td><strong>${s.name}</strong></td>`;
    html += `<td>${s.students}</td>`;
    html += `<td>${s.avgH.toFixed(1)}h</td>`;
    html += `<td>${s.medH.toFixed(1)}h</td>`;
    html += `<td>${s.stdH.toFixed(1)}</td>`;
    html += `<td>${s.minH.toFixed(1)}h</td>`;
    html += `<td>${s.maxH.toFixed(1)}h</td>`;
    html += `<td>${s.avgMark !== null ? s.avgMark.toFixed(1) : '-'}</td>`;
    html += `<td>${s.medMark !== null ? s.medMark.toFixed(1) : '-'}</td>`;
    html += `<td><span class="badge ${s.completionPct >= 75 ? 'badge-finished' : s.completionPct >= 50 ? 'badge-in_progress' : 'badge-waiting'}">${s.completionPct.toFixed(0)}%</span></td>`;
    html += `<td><span class="badge ${s.validationPct >= 75 ? 'badge-validated' : s.validationPct >= 50 ? 'badge-in_progress' : 'badge-waiting'}">${s.validationPct.toFixed(0)}%</span></td>`;
    html += '</tr>';
  });

  html += '</tbody></table></div>';
  el.innerHTML = html;
});

// ---- 27. AVERAGE TIME PER MODULE BAR CHART ----
registerChart('modulestatbar', function() {
  const el = document.getElementById('chart-27');
  if (!el) return;
  if (!filteredData.length) { el.innerHTML = '<div class="chart-empty">No data</div>'; return; }

  const showMedian = document.getElementById('modbar-median')?.checked !== false;
  const showStdDev = document.getElementById('modbar-stddev')?.checked || false;

  // Collect per-module hours
  const moduleMap = {};
  filteredData.forEach(user => {
    user.python_projects.forEach(proj => {
      if (!moduleMap[proj.project_name]) moduleMap[proj.project_name] = [];
      moduleMap[proj.project_name].push(proj.time_spent_hours);
    });
  });

  const modules = Object.keys(moduleMap).sort();
  const avgs = modules.map(m => mean(moduleMap[m]));
  const meds = modules.map(m => median(moduleMap[m]));
  const stds = modules.map(m => stddev(moduleMap[m]));

  const traces = [];

  // Average bars
  traces.push({
    type: 'bar',
    name: 'Average',
    x: modules,
    y: avgs,
    marker: { color: COLORS.primary },
    error_y: showStdDev ? { type: 'data', array: stds, visible: true, color: '#8e8e8e' } : undefined,
    text: avgs.map(v => v.toFixed(1) + 'h'),
    textposition: 'outside',
    textfont: { size: 9, color: '#8e8e8e' }
  });

  // Median markers
  if (showMedian) {
    traces.push({
      type: 'scatter',
      mode: 'markers',
      name: 'Median',
      x: modules,
      y: meds,
      marker: { color: COLORS.orange, size: 10, symbol: 'diamond' }
    });
  }

  const layout = {
    ...PLOTLY_LAYOUT_DEFAULTS,
    xaxis: { ...PLOTLY_LAYOUT_DEFAULTS.xaxis, title: 'Module', tickangle: -30 },
    yaxis: { ...PLOTLY_LAYOUT_DEFAULTS.yaxis, title: 'Hours' },
    legend: { font: { size: 10 } },
    barmode: 'group'
  };
  Plotly.react(el, traces, layout, PLOTLY_CONFIG);
});
