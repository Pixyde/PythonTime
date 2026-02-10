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

// ---- 28. PROMO COMPLETION — % who finished all modules (New Common Core only) ----
registerChart('promoCompletion', function() {
  const el = document.getElementById('chart-28');
  if (!el) return;

  const hasCampus = filteredData.some(u => u.campus_name);
  if (!hasCampus || !filteredData.length) {
    el.innerHTML = '<div class="chart-empty">Campus data not available</div>';
    return;
  }

  // Only consider new common core modules and users
  const nccModules = getNewCommonCoreModules();
  const moduleCount = nccModules.length;
  if (moduleCount === 0) { el.innerHTML = '<div class="chart-empty">No new common core modules found</div>'; return; }

  // Filter to only users on the new common core
  const nccUsers = filteredData.filter(u => isNewCommonCoreUser(u));
  if (!nccUsers.length) { el.innerHTML = '<div class="chart-empty">No new common core users found</div>'; return; }

  // Group by campus
  const campusGroups = {};
  nccUsers.forEach(u => {
    const campus = u.campus_name || 'Unknown';
    if (!campusGroups[campus]) campusGroups[campus] = [];
    campusGroups[campus].push(u);
  });

  const campusNames = Object.keys(campusGroups).sort();

  // For each campus, calculate % of new common core users who finished ALL NCC modules
  const finishedAll = [];
  const finishedMost = []; // >= 75% modules
  const totalUsers = [];
  const pctAll = [];
  const pctMost = [];

  campusNames.forEach(name => {
    const users = campusGroups[name];
    let doneAll = 0;
    let doneMost = 0;
    users.forEach(u => {
      const finishedModules = new Set(
        u.python_projects
          .filter(p => p.status === 'finished' && isNewCommonCoreProject(p))
          .map(p => p.project_name)
      );
      if (finishedModules.size >= moduleCount) doneAll++;
      if (finishedModules.size >= moduleCount * 0.75) doneMost++;
    });
    finishedAll.push(doneAll);
    finishedMost.push(doneMost);
    totalUsers.push(users.length);
    pctAll.push(users.length > 0 ? (doneAll / users.length) * 100 : 0);
    pctMost.push(users.length > 0 ? (doneMost / users.length) * 100 : 0);
  });

  // Global row
  const globalAll = sum(finishedAll);
  const globalMost = sum(finishedMost);
  const globalTotal = sum(totalUsers);
  const globalPctAll = globalTotal > 0 ? (globalAll / globalTotal) * 100 : 0;
  const globalPctMost = globalTotal > 0 ? (globalMost / globalTotal) * 100 : 0;

  const traces = [
    {
      type: 'bar',
      name: `Finished all ${moduleCount} NCC modules`,
      x: [...campusNames, '⊕ Global'],
      y: [...pctAll, globalPctAll],
      text: [...pctAll.map((v, i) => `${v.toFixed(0)}% (${finishedAll[i]}/${totalUsers[i]})`), `${globalPctAll.toFixed(0)}% (${globalAll}/${globalTotal})`],
      textposition: 'outside',
      textfont: { size: 9, color: '#8e8e8e' },
      marker: { color: COLORS.green },
      hovertext: campusNames.map((c, i) => `${c}<br>${finishedAll[i]}/${totalUsers[i]} NCC users finished all ${moduleCount} modules`).concat([`Global: ${globalAll}/${globalTotal}`]),
      hoverinfo: 'text'
    },
    {
      type: 'bar',
      name: `Finished ≥75% NCC modules`,
      x: [...campusNames, '⊕ Global'],
      y: [...pctMost, globalPctMost],
      text: [...pctMost.map((v, i) => `${v.toFixed(0)}%`), `${globalPctMost.toFixed(0)}%`],
      textposition: 'outside',
      textfont: { size: 9, color: '#8e8e8e' },
      marker: { color: COLORS.cyan },
      hovertext: campusNames.map((c, i) => `${c}<br>${finishedMost[i]}/${totalUsers[i]} NCC users finished ≥75% of modules`).concat([`Global: ${globalMost}/${globalTotal}`]),
      hoverinfo: 'text'
    }
  ];

  const layout = {
    ...PLOTLY_LAYOUT_DEFAULTS,
    barmode: 'group',
    xaxis: { ...PLOTLY_LAYOUT_DEFAULTS.xaxis, title: 'Campus' },
    yaxis: { ...PLOTLY_LAYOUT_DEFAULTS.yaxis, title: 'Percentage of NCC Students', range: [0, Math.max(...pctMost, globalPctMost, 10) * 1.2] },
    legend: { font: { size: 10 } }
  };
  Plotly.react(el, traces, layout, PLOTLY_CONFIG);
});

// ---- 29. PER-MODULE AVERAGES BY CAMPUS ----
registerChart('campusmodule', function() {
  const el = document.getElementById('chart-29');
  if (!el) return;

  const hasCampus = filteredData.some(u => u.campus_name);
  if (!hasCampus || !filteredData.length) {
    el.innerHTML = '<div class="chart-empty">Campus data not available</div>';
    return;
  }

  const metricSel = document.getElementById('campus-module-metric')?.value || 'avg_hours';

  // Group by campus
  const campusGroups = {};
  filteredData.forEach(u => {
    const campus = u.campus_name || 'Unknown';
    if (!campusGroups[campus]) campusGroups[campus] = [];
    campusGroups[campus].push(u);
  });

  const campusNames = Object.keys(campusGroups).sort();
  const modules = getAllModules();

  // For each campus × module, compute metric
  const traces = campusNames.map((campus, ci) => {
    const users = campusGroups[campus];
    const yValues = modules.map(mod => {
      const values = [];
      users.forEach(u => {
        u.python_projects.forEach(p => {
          if (p.project_name === mod) {
            if (metricSel === 'avg_mark' || metricSel === 'median_mark') {
              if (p.final_mark !== null && p.final_mark !== undefined) values.push(p.final_mark);
            } else {
              values.push(p.time_spent_hours);
            }
          }
        });
      });
      if (!values.length) return 0;
      if (metricSel === 'median_hours' || metricSel === 'median_mark') return median(values);
      return mean(values);
    });

    return {
      type: 'bar',
      name: campus,
      x: modules,
      y: yValues,
      marker: { color: COLORS.palette[ci % COLORS.palette.length] }
    };
  });

  // Global average line
  const globalValues = modules.map(mod => {
    const values = [];
    filteredData.forEach(u => {
      u.python_projects.forEach(p => {
        if (p.project_name === mod) {
          if (metricSel === 'avg_mark' || metricSel === 'median_mark') {
            if (p.final_mark !== null && p.final_mark !== undefined) values.push(p.final_mark);
          } else {
            values.push(p.time_spent_hours);
          }
        }
      });
    });
    if (!values.length) return 0;
    return mean(values);
  });

  traces.push({
    type: 'scatter', mode: 'lines+markers', name: '⊕ Global Avg',
    x: modules, y: globalValues,
    line: { color: COLORS.yellow, dash: 'dash', width: 3 },
    marker: { size: 6 }
  });

  const yLabel = metricSel.includes('mark') ? 'Mark' : 'Hours';

  const layout = {
    ...PLOTLY_LAYOUT_DEFAULTS,
    barmode: 'group',
    xaxis: { ...PLOTLY_LAYOUT_DEFAULTS.xaxis, title: 'Module', tickangle: -30 },
    yaxis: { ...PLOTLY_LAYOUT_DEFAULTS.yaxis, title: yLabel },
    legend: { font: { size: 10 } }
  };
  Plotly.react(el, traces, layout, PLOTLY_CONFIG);
});
