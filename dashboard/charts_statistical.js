/* ============================================================
   Charts: Statistical Visualizations (13-15)
   13. Histogram - Hour Distribution
   14. Cumulative Distribution (CDF)
   15. Correlation Matrix
   ============================================================ */

// ---- 13. HISTOGRAM - HOUR DISTRIBUTION ----
registerChart('histogram', function() {
  const el = document.getElementById('chart-13');
  if (!el) return;
  if (!filteredData.length) { el.innerHTML = '<div class="chart-empty">No data</div>'; return; }

  const binSize = parseFloat(document.getElementById('histogram-bins')?.value) || 5;
  const splitByModule = document.getElementById('histogram-split')?.checked || false;
  const showMean = document.getElementById('histogram-mean')?.checked !== false;
  const showMedian = document.getElementById('histogram-median')?.checked || false;
  const logScale = document.getElementById('histogram-log')?.checked || false;
  const showNormal = document.getElementById('histogram-normal')?.checked || false;

  const allHours = flattenProjects(filteredData).map(p => p.time_spent_hours);

  let traces;
  if (splitByModule) {
    const moduleHours = {};
    flattenProjects(filteredData).forEach(p => {
      if (!moduleHours[p.project_name]) moduleHours[p.project_name] = [];
      moduleHours[p.project_name].push(p.time_spent_hours);
    });
    traces = Object.entries(moduleHours).map(([mod, hours], i) => ({
      type: 'histogram',
      x: hours,
      name: mod,
      opacity: 0.7,
      xbins: { size: binSize },
      marker: { color: COLORS.palette[i % COLORS.palette.length] }
    }));
  } else {
    traces = [{
      type: 'histogram',
      x: allHours,
      xbins: { size: binSize },
      marker: { color: COLORS.primary + 'cc' },
      name: 'Hours'
    }];
  }

  const shapes = [];
  if (showMean && allHours.length) {
    const m = mean(allHours);
    shapes.push({ type: 'line', x0: m, x1: m, y0: 0, y1: 1, yref: 'paper', line: { color: COLORS.red, width: 2, dash: 'dash' } });
  }
  if (showMedian && allHours.length) {
    const med = percentile(allHours, 50);
    shapes.push({ type: 'line', x0: med, x1: med, y0: 0, y1: 1, yref: 'paper', line: { color: COLORS.green, width: 2, dash: 'dot' } });
  }

  // Normal distribution overlay
  if (showNormal && allHours.length > 2) {
    const m = mean(allHours);
    const std = Math.sqrt(allHours.reduce((s, x) => s + (x - m) ** 2, 0) / allHours.length);
    if (std > 0) {
      const xRange = [];
      const yRange = [];
      const minX = Math.max(0, m - 3 * std);
      const maxX = m + 3 * std;
      for (let x = minX; x <= maxX; x += (maxX - minX) / 100) {
        xRange.push(x);
        yRange.push((allHours.length * binSize) / (std * Math.sqrt(2 * Math.PI)) * Math.exp(-0.5 * ((x - m) / std) ** 2));
      }
      traces.push({
        type: 'scatter', mode: 'lines', name: 'Normal Dist.',
        x: xRange, y: yRange,
        line: { color: COLORS.yellow, width: 2 }
      });
    }
  }

  const layout = {
    ...PLOTLY_LAYOUT_DEFAULTS,
    barmode: splitByModule ? 'overlay' : undefined,
    xaxis: { ...PLOTLY_LAYOUT_DEFAULTS.xaxis, title: 'Hours' },
    yaxis: { ...PLOTLY_LAYOUT_DEFAULTS.yaxis, title: 'Count', type: logScale ? 'log' : 'linear' },
    shapes,
    legend: { font: { size: 9 }, orientation: 'h', y: -0.15 },
    showlegend: splitByModule
  };
  Plotly.react(el, traces, layout, PLOTLY_CONFIG);
});

// ---- 14. CUMULATIVE DISTRIBUTION (CDF) ----
registerChart('cdf', function() {
  const el = document.getElementById('chart-14');
  if (!el) return;
  if (!filteredData.length) { el.innerHTML = '<div class="chart-empty">No data</div>'; return; }

  const perModule = document.getElementById('cdf-module')?.checked || false;
  const p50 = document.getElementById('cdf-p50')?.checked !== false;
  const p75 = document.getElementById('cdf-p75')?.checked || false;
  const p90 = document.getElementById('cdf-p90')?.checked || false;

  function buildCDF(values) {
    const sorted = [...values].sort((a, b) => a - b);
    const x = sorted;
    const y = sorted.map((_, i) => (i + 1) / sorted.length * 100);
    return { x, y };
  }

  let traces = [];
  const shapes = [];

  if (perModule) {
    const moduleHours = {};
    flattenProjects(filteredData).forEach(p => {
      if (!moduleHours[p.project_name]) moduleHours[p.project_name] = [];
      moduleHours[p.project_name].push(p.time_spent_hours);
    });
    traces = Object.entries(moduleHours).map(([mod, hours], i) => {
      const cdf = buildCDF(hours);
      return {
        type: 'scatter', mode: 'lines', name: mod,
        x: cdf.x, y: cdf.y,
        line: { color: COLORS.palette[i % COLORS.palette.length], width: 2 }
      };
    });
  } else {
    const allHours = filteredData.map(u => u.total_python_hours);
    const cdf = buildCDF(allHours);
    traces.push({
      type: 'scatter', mode: 'lines', name: 'All Users',
      x: cdf.x, y: cdf.y,
      line: { color: COLORS.primary, width: 2 },
      fill: 'tozeroy',
      fillcolor: COLORS.primary + '20'
    });

    // Percentile lines
    const pctLines = [];
    if (p50) pctLines.push({ p: 50, color: COLORS.green });
    if (p75) pctLines.push({ p: 75, color: COLORS.orange });
    if (p90) pctLines.push({ p: 90, color: COLORS.red });
    pctLines.forEach(({ p: pct, color }) => {
      const val = percentile(allHours, pct);
      shapes.push({ type: 'line', x0: val, x1: val, y0: 0, y1: pct, line: { color, width: 1, dash: 'dot' } });
      shapes.push({ type: 'line', x0: 0, x1: val, y0: pct, y1: pct, line: { color, width: 1, dash: 'dot' } });
      traces.push({
        type: 'scatter', mode: 'markers+text', name: `P${pct}`,
        x: [val], y: [pct],
        marker: { color, size: 8 },
        text: [`P${pct}: ${val.toFixed(1)}h`],
        textposition: 'top right',
        textfont: { color, size: 10 }
      });
    });
  }

  const layout = {
    ...PLOTLY_LAYOUT_DEFAULTS,
    xaxis: { ...PLOTLY_LAYOUT_DEFAULTS.xaxis, title: 'Hours' },
    yaxis: { ...PLOTLY_LAYOUT_DEFAULTS.yaxis, title: 'Cumulative %', range: [0, 105] },
    shapes,
    legend: { font: { size: 9 } },
    showlegend: true
  };
  Plotly.react(el, traces, layout, PLOTLY_CONFIG);
});

// ---- 15. CORRELATION MATRIX ----
registerChart('correlation', function() {
  const el = document.getElementById('chart-15');
  if (!el) return;
  if (!filteredData.length) { el.innerHTML = '<div class="chart-empty">No data</div>'; return; }

  const showValues = document.getElementById('corr-values')?.checked !== false;

  // Build metrics per user
  const metrics = {};
  const metricNames = ['Total Hours', 'Avg Mark', 'Completion Rate', 'Num Projects', 'Max Hours', 'Avg Hours/Project'];

  filteredData.forEach(u => {
    const scored = u.python_projects.filter(p => p.final_mark !== null && p.final_mark !== undefined);
    const finished = u.python_projects.filter(p => p.status === 'finished');
    const row = {
      'Total Hours': u.total_python_hours,
      'Avg Mark': scored.length ? mean(scored.map(p => p.final_mark)) : 0,
      'Completion Rate': u.python_projects.length ? (finished.length / u.python_projects.length) * 100 : 0,
      'Num Projects': u.python_projects.length,
      'Max Hours': Math.max(...u.python_projects.map(p => p.time_spent_hours), 0),
      'Avg Hours/Project': u.python_projects.length ? u.total_python_hours / u.python_projects.length : 0
    };
    metricNames.forEach(m => {
      if (!metrics[m]) metrics[m] = [];
      metrics[m].push(row[m]);
    });
  });

  // Calculate correlation matrix
  function correlate(a, b) {
    const n = a.length;
    if (n < 2) return 0;
    const ma = mean(a), mb = mean(b);
    const num = a.reduce((s, ai, i) => s + (ai - ma) * (b[i] - mb), 0);
    const da = Math.sqrt(a.reduce((s, ai) => s + (ai - ma) ** 2, 0));
    const db = Math.sqrt(b.reduce((s, bi) => s + (bi - mb) ** 2, 0));
    return da && db ? num / (da * db) : 0;
  }

  const matrix = metricNames.map(a => metricNames.map(b => correlate(metrics[a], metrics[b])));
  const textMatrix = matrix.map(row => row.map(v => v.toFixed(2)));

  const trace = {
    type: 'heatmap',
    x: metricNames,
    y: metricNames,
    z: matrix,
    zmin: -1,
    zmax: 1,
    colorscale: [[0, '#f2495c'], [0.5, '#1a1d23'], [1, '#73bf69']],
    text: showValues ? textMatrix : undefined,
    texttemplate: showValues ? '%{text}' : undefined,
    textfont: { size: 10, color: '#e0e0e0' },
    hovertemplate: '%{x} vs %{y}: %{z:.2f}<extra></extra>',
    showscale: true,
    colorbar: { title: 'Correlation', titleside: 'right', tickfont: { color: '#8e8e8e' } }
  };

  const layout = {
    ...PLOTLY_LAYOUT_DEFAULTS,
    margin: { t: 10, r: 80, b: 100, l: 120 },
    xaxis: { ...PLOTLY_LAYOUT_DEFAULTS.xaxis, tickangle: -45 },
    yaxis: { ...PLOTLY_LAYOUT_DEFAULTS.yaxis, autorange: 'reversed' }
  };
  Plotly.react(el, [trace], layout, PLOTLY_CONFIG);
});
