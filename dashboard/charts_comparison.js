/* ============================================================
   Charts: Comparison Visualizations (4-6)
   4. Multi-User Bar/Column Chart
   5. Box Plot / Violin Plot
   6. Radar/Spider Chart
   ============================================================ */

// ---- 4. MULTI-USER BAR/COLUMN CHART ----
registerChart('multibar', function() {
  const el = document.getElementById('chart-4');
  if (!el) return;
  if (!filteredData.length) { el.innerHTML = '<div class="chart-empty">No data</div>'; return; }

  const topN = parseInt(document.getElementById('multibar-top')?.value) || 15;
  const groupBy = document.getElementById('multibar-group')?.value || 'user';
  const orientation = document.getElementById('multibar-orient')?.value || 'vertical';
  const stacked = document.getElementById('multibar-stacked')?.checked || false;
  const showAvg = document.getElementById('multibar-avg')?.checked || false;

  const modules = getAllModules();
  const moduleFilter = document.getElementById('multibar-module')?.value || 'all';

  if (groupBy === 'user') {
    // Group by user, bars per module
    let users = filteredData.map(u => ({
      login: u.login,
      hours: u.total_python_hours,
      moduleHours: {}
    }));
    users.forEach(u => {
      const userData = filteredData.find(d => d.login === u.login);
      userData.python_projects.forEach(p => {
        if (moduleFilter !== 'all' && p.project_name !== moduleFilter) return;
        u.moduleHours[p.project_name] = (u.moduleHours[p.project_name] || 0) + p.time_spent_hours;
      });
      u.hours = Object.values(u.moduleHours).reduce((a, b) => a + b, 0);
    });
    users.sort((a, b) => b.hours - a.hours);
    users = users.slice(0, topN);

    const activeModules = [...new Set(users.flatMap(u => Object.keys(u.moduleHours)))].sort();
    const traces = activeModules.map((mod, i) => ({
      type: 'bar',
      name: mod,
      [orientation === 'vertical' ? 'x' : 'y']: users.map(u => u.login),
      [orientation === 'vertical' ? 'y' : 'x']: users.map(u => u.moduleHours[mod] || 0),
      orientation: orientation === 'vertical' ? undefined : 'h',
      marker: { color: COLORS.palette[i % COLORS.palette.length] }
    }));

    if (showAvg && users.length) {
      const avgHours = mean(users.map(u => u.hours));
      traces.push({
        type: 'scatter',
        mode: 'lines',
        name: 'Average',
        [orientation === 'vertical' ? 'x' : 'y']: users.map(u => u.login),
        [orientation === 'vertical' ? 'y' : 'x']: users.map(() => avgHours),
        line: { color: COLORS.red, dash: 'dash', width: 2 }
      });
    }

    const layout = {
      ...PLOTLY_LAYOUT_DEFAULTS,
      barmode: stacked ? 'stack' : 'group',
      legend: { font: { size: 9 }, orientation: 'h', y: -0.2 },
      showlegend: activeModules.length <= 12
    };
    Plotly.react(el, traces, layout, PLOTLY_CONFIG);
  } else {
    // Group by module
    const moduleData = {};
    filteredData.forEach(u => {
      u.python_projects.forEach(p => {
        if (!moduleData[p.project_name]) moduleData[p.project_name] = {};
        moduleData[p.project_name][u.login] = (moduleData[p.project_name][u.login] || 0) + p.time_spent_hours;
      });
    });
    const topUsers = filteredData.sort((a, b) => b.total_python_hours - a.total_python_hours).slice(0, topN).map(u => u.login);
    const mods = Object.keys(moduleData).sort();

    const traces = topUsers.map((user, i) => ({
      type: 'bar',
      name: user,
      [orientation === 'vertical' ? 'x' : 'y']: mods,
      [orientation === 'vertical' ? 'y' : 'x']: mods.map(m => moduleData[m][user] || 0),
      orientation: orientation === 'vertical' ? undefined : 'h',
      marker: { color: COLORS.palette[i % COLORS.palette.length] }
    }));

    const layout = {
      ...PLOTLY_LAYOUT_DEFAULTS,
      barmode: stacked ? 'stack' : 'group',
      legend: { font: { size: 9 }, orientation: 'h', y: -0.2 },
      showlegend: topUsers.length <= 12
    };
    Plotly.react(el, traces, layout, PLOTLY_CONFIG);
  }

  // Populate module filter
  const modSel = document.getElementById('multibar-module');
  if (modSel && modSel.options.length <= 1) {
    modSel.innerHTML = '<option value="all">All Modules</option>' + modules.map(m => `<option value="${m}">${m}</option>`).join('');
  }
});

// ---- 5. BOX PLOT / VIOLIN PLOT ----
registerChart('boxplot', function() {
  const el = document.getElementById('chart-5');
  if (!el) return;
  if (!filteredData.length) { el.innerHTML = '<div class="chart-empty">No data</div>'; return; }

  const chartType = document.getElementById('boxplot-type')?.value || 'box';
  const showPoints = document.getElementById('boxplot-points')?.checked || false;
  const showQuartiles = document.getElementById('boxplot-quartiles')?.checked !== false;
  const compareValidated = document.getElementById('boxplot-validated')?.checked || false;

  const moduleHours = {};
  filteredData.forEach(u => {
    u.python_projects.forEach(p => {
      const key = compareValidated ? `${p.project_name} (${p.validated ? 'Validated' : 'Not Validated'})` : p.project_name;
      if (!moduleHours[key]) moduleHours[key] = [];
      moduleHours[key].push(p.time_spent_hours);
    });
  });

  const mods = Object.keys(moduleHours).sort();
  const traces = mods.map((mod, i) => ({
    type: chartType === 'violin' ? 'violin' : 'box',
    name: mod,
    y: moduleHours[mod],
    boxpoints: showPoints ? 'all' : false,
    points: showPoints ? 'all' : false,
    jitter: 0.3,
    pointpos: -1.5,
    marker: { color: COLORS.palette[i % COLORS.palette.length], size: 3 },
    line: { color: COLORS.palette[i % COLORS.palette.length] },
    fillcolor: COLORS.palette[i % COLORS.palette.length] + '40',
    box: chartType === 'violin' ? { visible: showQuartiles } : undefined,
    meanline: chartType === 'violin' ? { visible: true } : undefined
  }));

  const layout = {
    ...PLOTLY_LAYOUT_DEFAULTS,
    yaxis: { ...PLOTLY_LAYOUT_DEFAULTS.yaxis, title: 'Hours' },
    showlegend: false
  };
  Plotly.react(el, traces, layout, PLOTLY_CONFIG);
});

// ---- 6. RADAR / SPIDER CHART ----
registerChart('radar', function() {
  const el = document.getElementById('chart-6');
  if (!el) return;
  if (!filteredData.length) { el.innerHTML = '<div class="chart-empty">No data</div>'; return; }

  const numUsers = parseInt(document.getElementById('radar-users')?.value) || 3;
  const metric = document.getElementById('radar-metric')?.value || 'hours';
  const normalize = document.getElementById('radar-normalize')?.checked || false;
  const fillOpacity = parseFloat(document.getElementById('radar-opacity')?.value) || 0.2;
  const showGrid = document.getElementById('radar-grid')?.checked !== false;

  const modules = getAllModules();
  const topUsers = filteredData.sort((a, b) => b.total_python_hours - a.total_python_hours).slice(0, numUsers);

  const traces = topUsers.map((user, i) => {
    const values = modules.map(mod => {
      const proj = user.python_projects.find(p => p.project_name === mod);
      if (!proj) return 0;
      if (metric === 'marks') return proj.final_mark || 0;
      if (metric === 'completion') return proj.status === 'finished' ? 100 : (proj.status === 'in_progress' ? 50 : 0);
      return proj.time_spent_hours;
    });

    let plotValues = values;
    if (normalize && values.length) {
      const maxVal = Math.max(...values, 1);
      plotValues = values.map(v => (v / maxVal) * 100);
    }

    return {
      type: 'scatterpolar',
      r: [...plotValues, plotValues[0]],
      theta: [...modules, modules[0]],
      fill: 'toself',
      fillcolor: COLORS.palette[i % COLORS.palette.length] + Math.round(fillOpacity * 255).toString(16).padStart(2, '0'),
      name: user.login,
      line: { color: COLORS.palette[i % COLORS.palette.length] },
      marker: { size: 4 }
    };
  });

  const layout = {
    ...PLOTLY_LAYOUT_DEFAULTS,
    polar: {
      bgcolor: 'rgba(0,0,0,0)',
      radialaxis: { visible: showGrid, gridcolor: '#2c3038', color: '#8e8e8e', tickfont: { size: 9 } },
      angularaxis: { gridcolor: '#2c3038', color: '#8e8e8e', tickfont: { size: 9 } }
    },
    legend: { font: { size: 10 } }
  };
  Plotly.react(el, traces, layout, PLOTLY_CONFIG);
});
