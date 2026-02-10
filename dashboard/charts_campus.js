/* ============================================================
   Charts: Campus Comparison (25)
   25. Campus Comparison Dashboard
   ============================================================ */

// ---- 25. CAMPUS COMPARISON ----
registerChart('campus', function() {
  const el = document.getElementById('chart-25');
  if (!el) return;

  // Check if campus data is available
  const hasCampus = filteredData.some(u => u.campus_name);
  if (!hasCampus) {
    el.innerHTML = '<div class="chart-empty">Campus data not available.<br>Run analysis with campus info or across multiple campuses to enable comparison.</div>';
    return;
  }

  const metric = document.getElementById('campus-metric')?.value || 'avg_hours';
  const showAll = document.getElementById('campus-show-all')?.checked !== false;

  // Group data by campus
  const campusGroups = {};
  filteredData.forEach(u => {
    const campus = u.campus_name || 'Unknown';
    if (!campusGroups[campus]) campusGroups[campus] = [];
    campusGroups[campus].push(u);
  });

  const campusNames = Object.keys(campusGroups).sort();
  if (campusNames.length < 1) {
    el.innerHTML = '<div class="chart-empty">Only one campus found. Need multiple campuses for comparison.</div>';
    return;
  }

  // Calculate metrics per campus
  const campusStats = campusNames.map(name => {
    const users = campusGroups[name];
    const allProjects = users.flatMap(u => u.python_projects);
    const scored = allProjects.filter(p => p.final_mark !== null && p.final_mark !== undefined);
    const finished = allProjects.filter(p => p.status === 'finished');
    const validated = allProjects.filter(p => p.validated);

    return {
      name,
      userCount: users.length,
      totalHours: users.reduce((s, u) => s + u.total_python_hours, 0),
      avgHours: users.length ? mean(users.map(u => u.total_python_hours)) : 0,
      avgMark: scored.length ? mean(scored.map(p => p.final_mark)) : 0,
      completionRate: allProjects.length ? (finished.length / allProjects.length) * 100 : 0,
      validationRate: allProjects.length ? (validated.length / allProjects.length) * 100 : 0,
      totalProjects: allProjects.length,
      avgProjectsPerUser: users.length ? allProjects.length / users.length : 0,
      efficiency: users.length && users.reduce((s, u) => s + u.total_python_hours, 0) > 0
        ? (scored.length ? mean(scored.map(p => p.final_mark)) : 0) / (users.reduce((s, u) => s + u.total_python_hours, 0) / users.length)
        : 0
    };
  });

  // Global average
  const globalAvg = {
    avgHours: mean(campusStats.map(c => c.avgHours)),
    avgMark: mean(campusStats.map(c => c.avgMark)),
    completionRate: mean(campusStats.map(c => c.completionRate)),
    validationRate: mean(campusStats.map(c => c.validationRate)),
    avgProjectsPerUser: mean(campusStats.map(c => c.avgProjectsPerUser)),
    efficiency: mean(campusStats.map(c => c.efficiency))
  };

  // Build chart based on metric
  let traces = [];
  let yTitle = '';

  if (metric === 'radar') {
    // Radar comparison of all campuses
    const metrics = ['avgHours', 'avgMark', 'completionRate', 'avgProjectsPerUser', 'efficiency'];
    const metricLabels = ['Avg Hours', 'Avg Mark', 'Completion %', 'Avg Projects/User', 'Efficiency'];

    // Normalize each metric 0-100
    const maxVals = metrics.map(m => Math.max(...campusStats.map(c => c[m]), 1));

    campusStats.forEach((campus, i) => {
      const values = metrics.map((m, mi) => (campus[m] / maxVals[mi]) * 100);
      traces.push({
        type: 'scatterpolar',
        r: [...values, values[0]],
        theta: [...metricLabels, metricLabels[0]],
        fill: 'toself',
        fillcolor: COLORS.palette[i % COLORS.palette.length] + '30',
        name: campus.name,
        line: { color: COLORS.palette[i % COLORS.palette.length] }
      });
    });

    // Add global average
    if (showAll) {
      const avgValues = metrics.map((m, mi) => (globalAvg[m] / maxVals[mi]) * 100);
      traces.push({
        type: 'scatterpolar',
        r: [...avgValues, avgValues[0]],
        theta: [...metricLabels, metricLabels[0]],
        fill: 'none',
        name: '⊕ Global Avg',
        line: { color: COLORS.yellow, dash: 'dash', width: 3 }
      });
    }

    const layout = {
      ...PLOTLY_LAYOUT_DEFAULTS,
      polar: {
        bgcolor: 'rgba(0,0,0,0)',
        radialaxis: { visible: true, gridcolor: '#2c3038', color: '#8e8e8e', range: [0, 100] },
        angularaxis: { gridcolor: '#2c3038', color: '#8e8e8e' }
      },
      legend: { font: { size: 10 } }
    };
    Plotly.react(el, traces, layout, PLOTLY_CONFIG);
    return;
  }

  // Bar chart mode
  const metricMap = {
    'avg_hours': { key: 'avgHours', label: 'Average Hours per User' },
    'avg_mark': { key: 'avgMark', label: 'Average Mark' },
    'completion': { key: 'completionRate', label: 'Completion Rate (%)' },
    'validation': { key: 'validationRate', label: 'Validation Rate (%)' },
    'users': { key: 'userCount', label: 'Number of Users' },
    'total_hours': { key: 'totalHours', label: 'Total Hours' },
    'efficiency': { key: 'efficiency', label: 'Efficiency (pts/hour)' },
    'projects_per_user': { key: 'avgProjectsPerUser', label: 'Avg Projects per User' }
  };

  const m = metricMap[metric] || metricMap['avg_hours'];
  const values = campusStats.map(c => c[m.key]);
  const globalVal = globalAvg[m.key] || mean(values);

  traces.push({
    type: 'bar',
    x: campusNames,
    y: values,
    marker: {
      color: values.map(v => v >= globalVal ? COLORS.green : COLORS.orange)
    },
    text: values.map(v => v.toFixed(1)),
    textposition: 'outside',
    textfont: { size: 10, color: '#8e8e8e' },
    hovertext: campusStats.map(c =>
      `${c.name}<br>Users: ${c.userCount}<br>Avg Hours: ${c.avgHours.toFixed(1)}<br>Avg Mark: ${c.avgMark.toFixed(1)}<br>Completion: ${c.completionRate.toFixed(0)}%`
    ),
    hoverinfo: 'text'
  });

  // Global average line
  if (showAll) {
    traces.push({
      type: 'scatter', mode: 'lines', name: 'Global Average',
      x: campusNames, y: campusNames.map(() => globalVal),
      line: { color: COLORS.red, dash: 'dash', width: 2 }
    });
  }

  const layout = {
    ...PLOTLY_LAYOUT_DEFAULTS,
    yaxis: { ...PLOTLY_LAYOUT_DEFAULTS.yaxis, title: m.label },
    xaxis: { ...PLOTLY_LAYOUT_DEFAULTS.xaxis, title: 'Campus' },
    showlegend: showAll
  };
  Plotly.react(el, traces, layout, PLOTLY_CONFIG);
});
