/* ============================================================
   Charts: Performance Visualizations (7-9)
   7. Scatter Plot - Hours vs Score
   8. Efficiency Score Chart
   9. Completion Rate Gauge
   ============================================================ */

// ---- 7. SCATTER PLOT - HOURS VS SCORE ----
registerChart('scatter', function() {
  const el = document.getElementById('chart-7');
  if (!el) return;
  if (!filteredData.length) { el.innerHTML = '<div class="chart-empty">No data</div>'; return; }

  const colorBy = document.getElementById('scatter-color')?.value || 'user';
  const showTrend = document.getElementById('scatter-trend')?.checked || false;
  const validatedOnly = document.getElementById('scatter-validated')?.checked || false;
  const bubbleSize = document.getElementById('scatter-bubble')?.value || 'fixed';

  const rows = flattenProjects(filteredData).filter(p =>
    p.final_mark !== null && p.final_mark !== undefined && (!validatedOnly || p.validated)
  );

  if (!rows.length) { el.innerHTML = '<div class="chart-empty">No scored projects</div>'; return; }

  // Group for coloring
  const groups = {};
  rows.forEach(r => {
    const key = colorBy === 'module' ? r.project_name : (colorBy === 'status' ? r.status : r.login);
    if (!groups[key]) groups[key] = [];
    groups[key].push(r);
  });

  const traces = Object.entries(groups).map(([name, items], i) => ({
    type: 'scatter',
    mode: 'markers',
    name: name,
    x: items.map(r => r.time_spent_hours),
    y: items.map(r => r.final_mark),
    marker: {
      color: colorBy === 'status' ? items.map(r => STATUS_COLORS[r.status] || '#8e8e8e') : COLORS.palette[i % COLORS.palette.length],
      size: bubbleSize === 'module' ? items.map(() => 8 + Math.random() * 12) : 8,
      opacity: 0.7,
      line: { width: 1, color: 'rgba(255,255,255,0.2)' }
    },
    text: items.map(r => `${r.login}: ${r.project_name}<br>${r.time_spent_hours}h → ${r.final_mark}/100`),
    hoverinfo: 'text'
  }));

  // Trend line
  if (showTrend && rows.length > 2) {
    const xs = rows.map(r => r.time_spent_hours);
    const ys = rows.map(r => r.final_mark);
    const n = xs.length;
    const sumX = sum(xs), sumY = sum(ys);
    const sumXY = xs.reduce((s, x, i) => s + x * ys[i], 0);
    const sumX2 = xs.reduce((s, x) => s + x * x, 0);
    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;
    const xMin = Math.min(...xs), xMax = Math.max(...xs);
    traces.push({
      type: 'scatter', mode: 'lines', name: 'Trend',
      x: [xMin, xMax], y: [slope * xMin + intercept, slope * xMax + intercept],
      line: { color: COLORS.red, dash: 'dash', width: 2 },
      showlegend: true
    });
  }

  const layout = {
    ...PLOTLY_LAYOUT_DEFAULTS,
    xaxis: { ...PLOTLY_LAYOUT_DEFAULTS.xaxis, title: 'Hours Spent' },
    yaxis: { ...PLOTLY_LAYOUT_DEFAULTS.yaxis, title: 'Final Mark', range: [0, 105] },
    legend: { font: { size: 9 }, orientation: 'h', y: -0.15 },
    showlegend: Object.keys(groups).length <= 15
  };
  Plotly.react(el, traces, layout, PLOTLY_CONFIG);
});

// ---- 8. EFFICIENCY SCORE CHART ----
registerChart('efficiency', function() {
  const el = document.getElementById('chart-8');
  if (!el) return;
  if (!filteredData.length) { el.innerHTML = '<div class="chart-empty">No data</div>'; return; }

  const sortBy = document.getElementById('efficiency-sort')?.value || 'efficiency';
  const validatedOnly = document.getElementById('efficiency-validated')?.checked || false;
  const minProjects = parseInt(document.getElementById('efficiency-min-proj')?.value) || 1;
  const threshold = parseFloat(document.getElementById('efficiency-threshold')?.value) || 0;

  const userData = filteredData.map(user => {
    let projects = user.python_projects;
    if (validatedOnly) projects = projects.filter(p => p.validated);
    const scored = projects.filter(p => p.final_mark !== null && p.final_mark !== undefined && p.time_spent_hours > 0);
    const totalHours = scored.reduce((s, p) => s + p.time_spent_hours, 0);
    const avgMark = scored.length ? mean(scored.map(p => p.final_mark)) : 0;
    const efficiency = totalHours > 0 ? scored.length / totalHours : 0;
    return { login: user.login, efficiency, totalHours, avgMark, projectCount: scored.length };
  }).filter(u => u.projectCount >= minProjects && u.efficiency >= threshold);

  if (sortBy === 'hours') userData.sort((a, b) => b.totalHours - a.totalHours);
  else if (sortBy === 'projects') userData.sort((a, b) => b.projectCount - a.projectCount);
  else userData.sort((a, b) => b.efficiency - a.efficiency);

  const top20 = userData.slice(0, 20);
  const avgEff = mean(userData.map(u => u.efficiency));

  const traces = [{
    type: 'bar',
    x: top20.map(u => u.login),
    y: top20.map(u => u.efficiency),
    marker: {
      color: top20.map(u => u.efficiency >= avgEff ? COLORS.green : COLORS.orange)
    },
    text: top20.map(u => `${u.efficiency.toFixed(2)} proj/h`),
    textposition: 'outside',
    textfont: { size: 9, color: '#8e8e8e' },
    hovertext: top20.map(u => `${u.login}<br>Efficiency: ${u.efficiency.toFixed(2)} proj/h<br>Avg Mark: ${u.avgMark.toFixed(1)}<br>Hours: ${u.totalHours.toFixed(1)}<br>Projects: ${u.projectCount}`),
    hoverinfo: 'text'
  }];

  // Average line
  traces.push({
    type: 'scatter', mode: 'lines', name: 'Average',
    x: top20.map(u => u.login), y: top20.map(() => avgEff),
    line: { color: COLORS.red, dash: 'dash', width: 2 }
  });

  const layout = {
    ...PLOTLY_LAYOUT_DEFAULTS,
    yaxis: { ...PLOTLY_LAYOUT_DEFAULTS.yaxis, title: 'Projects per Hour (proj/h)' },
    showlegend: false
  };
  Plotly.react(el, traces, layout, PLOTLY_CONFIG);
});

// ---- 9. COMPLETION RATE GAUGE ----
registerChart('gauge', function() {
  const el = document.getElementById('chart-9');
  if (!el) return;
  if (!filteredData.length) { el.innerHTML = '<div class="chart-empty">No data</div>'; return; }

  const viewMode = document.getElementById('gauge-mode')?.value || 'aggregate';
  const includeInProgress = document.getElementById('gauge-in-progress')?.checked || false;

  if (viewMode === 'aggregate') {
    const allProjects = flattenProjects(filteredData);
    const finished = allProjects.filter(p => p.status === 'finished').length;
    const inProgress = allProjects.filter(p => p.status === 'in_progress').length;
    const total = allProjects.length;
    const completed = includeInProgress ? finished + inProgress : finished;
    const rate = total > 0 ? (completed / total) * 100 : 0;

    const trace = {
      type: 'indicator',
      mode: 'gauge+number+delta',
      value: rate,
      number: { suffix: '%', font: { color: '#e0e0e0', size: 40 } },
      gauge: {
        axis: { range: [0, 100], tickcolor: '#8e8e8e', dtick: 25 },
        bar: { color: rate >= 75 ? COLORS.green : rate >= 50 ? COLORS.orange : COLORS.red },
        bgcolor: '#1a1d23',
        bordercolor: '#2c3038',
        steps: [
          { range: [0, 25], color: 'rgba(242,73,92,0.1)' },
          { range: [25, 50], color: 'rgba(255,152,48,0.1)' },
          { range: [50, 75], color: 'rgba(250,222,42,0.1)' },
          { range: [75, 100], color: 'rgba(115,191,105,0.1)' }
        ],
        threshold: { line: { color: COLORS.red, width: 3 }, thickness: 0.8, value: 50 }
      },
      title: { text: `${finished} finished / ${total} total`, font: { color: '#8e8e8e', size: 12 } }
    };

    const layout = { ...PLOTLY_LAYOUT_DEFAULTS, margin: { t: 30, r: 30, b: 10, l: 30 }, height: 300 };
    Plotly.react(el, [trace], layout, PLOTLY_CONFIG);
  } else {
    // Per-user gauges - show top users as horizontal bars
    const userRates = filteredData.map(u => {
      const finished = u.python_projects.filter(p => p.status === 'finished').length;
      const total = u.python_projects.length;
      return { login: u.login, rate: total > 0 ? (finished / total) * 100 : 0, finished, total };
    }).sort((a, b) => b.rate - a.rate).slice(0, 15);

    const trace = {
      type: 'bar',
      orientation: 'h',
      y: userRates.map(u => u.login),
      x: userRates.map(u => u.rate),
      marker: { color: userRates.map(u => u.rate >= 75 ? COLORS.green : u.rate >= 50 ? COLORS.orange : COLORS.red) },
      text: userRates.map(u => `${u.rate.toFixed(0)}% (${u.finished}/${u.total})`),
      textposition: 'inside',
      textfont: { color: '#fff', size: 10 },
      hoverinfo: 'text'
    };

    const layout = {
      ...PLOTLY_LAYOUT_DEFAULTS,
      margin: { t: 10, r: 20, b: 40, l: 120 },
      xaxis: { ...PLOTLY_LAYOUT_DEFAULTS.xaxis, title: 'Completion Rate (%)', range: [0, 105] },
      yaxis: { ...PLOTLY_LAYOUT_DEFAULTS.yaxis, autorange: 'reversed' }
    };
    Plotly.react(el, [trace], layout, PLOTLY_CONFIG);
  }
});
