/* ============================================================
   Charts: Advanced Visualizations (18-21)
   18. Treemap - Hours by User & Module
   19. Sunburst Chart
   20. Parallel Coordinates
   21. Network Graph
   ============================================================ */

// ---- 18. TREEMAP ----
registerChart('treemap', function() {
  const el = document.getElementById('chart-18');
  if (!el) return;
  if (!filteredData.length) { el.innerHTML = '<div class="chart-empty">No data</div>'; return; }

  const colorBy = document.getElementById('treemap-color')?.value || 'module';
  const minSize = parseFloat(document.getElementById('treemap-min')?.value) || 0;

  const ids = ['All'];
  const labels = ['All Users'];
  const parents = [''];
  const values = [0];
  const colors = [0];

  filteredData.forEach((user, ui) => {
    const userId = `user-${user.login}`;
    ids.push(userId);
    labels.push(user.login);
    parents.push('All');
    values.push(0);
    colors.push(user.total_python_hours);

    user.python_projects.forEach((proj, pi) => {
      if (proj.time_spent_hours < minSize) return;
      const projId = `${userId}-${pi}`;
      ids.push(projId);
      labels.push(proj.project_name);
      parents.push(userId);
      values.push(proj.time_spent_hours);

      if (colorBy === 'status') {
        colors.push(proj.status === 'finished' ? 1 : proj.status === 'in_progress' ? 0.5 : 0);
      } else if (colorBy === 'efficiency') {
        colors.push(proj.final_mark && proj.time_spent_hours > 0 ? proj.final_mark / proj.time_spent_hours : 0);
      } else {
        colors.push(getAllModules().indexOf(proj.project_name));
      }
    });
  });

  const colorscale = colorBy === 'status'
    ? [[0, COLORS.orange], [0.5, COLORS.cyan], [1, COLORS.green]]
    : 'Viridis';

  const trace = {
    type: 'treemap',
    ids, labels, parents, values,
    marker: {
      colors,
      colorscale,
      line: { width: 1, color: '#2c3038' }
    },
    textinfo: 'label+value',
    texttemplate: '%{label}<br>%{value:.1f}h',
    textfont: { size: 10 },
    hovertemplate: '%{label}<br>%{value:.1f} hours<extra></extra>',
    branchvalues: 'total'
  };

  const layout = {
    ...PLOTLY_LAYOUT_DEFAULTS,
    margin: { t: 10, r: 10, b: 10, l: 10 },
    treemapcolorway: COLORS.palette
  };
  Plotly.react(el, [trace], layout, PLOTLY_CONFIG);
});

// ---- 19. SUNBURST CHART ----
registerChart('sunburst', function() {
  const el = document.getElementById('chart-19');
  if (!el) return;
  if (!filteredData.length) { el.innerHTML = '<div class="chart-empty">No data</div>'; return; }

  const colorMetric = document.getElementById('sunburst-color')?.value || 'hours';
  const showPct = document.getElementById('sunburst-pct')?.checked || false;

  const ids = ['Total'];
  const labels = ['Total'];
  const parents = [''];
  const values = [0];
  const markerColors = [COLORS.primary];

  filteredData.forEach(user => {
    const userId = `u-${user.login}`;
    ids.push(userId);
    labels.push(user.login);
    parents.push('Total');
    values.push(0);
    markerColors.push(COLORS.palette[filteredData.indexOf(user) % COLORS.palette.length]);

    user.python_projects.forEach((proj, pi) => {
      const projId = `${userId}-${pi}`;
      ids.push(projId);
      labels.push(proj.project_name);
      parents.push(userId);
      values.push(proj.time_spent_hours);

      if (colorMetric === 'status') {
        markerColors.push(STATUS_COLORS[proj.status] || '#8e8e8e');
      } else if (colorMetric === 'marks') {
        const mark = proj.final_mark || 0;
        markerColors.push(mark >= 80 ? COLORS.green : mark >= 50 ? COLORS.orange : COLORS.red);
      } else {
        markerColors.push(COLORS.palette[getAllModules().indexOf(proj.project_name) % COLORS.palette.length]);
      }

      // Status level
      const statusId = `${projId}-${proj.status}`;
      ids.push(statusId);
      labels.push(proj.status);
      parents.push(projId);
      values.push(proj.time_spent_hours);
      markerColors.push(STATUS_COLORS[proj.status] || '#8e8e8e');
    });
  });

  const trace = {
    type: 'sunburst',
    ids, labels, parents, values,
    marker: { colors: markerColors, line: { width: 1, color: '#2c3038' } },
    textinfo: showPct ? 'label+percent entry' : 'label',
    hovertemplate: '%{label}<br>%{value:.1f}h<br>%{percentEntry:.1%}<extra></extra>',
    branchvalues: 'total',
    insidetextorientation: 'radial'
  };

  const layout = {
    ...PLOTLY_LAYOUT_DEFAULTS,
    margin: { t: 10, r: 10, b: 10, l: 10 },
    sunburstcolorway: COLORS.palette
  };
  Plotly.react(el, [trace], layout, PLOTLY_CONFIG);
});

// ---- 20. PARALLEL COORDINATES ----
registerChart('parallel', function() {
  const el = document.getElementById('chart-20');
  if (!el) return;
  if (!filteredData.length) { el.innerHTML = '<div class="chart-empty">No data</div>'; return; }

  const colorByMetric = document.getElementById('parallel-color')?.value || 'hours';

  // Build dimensions
  const userData = filteredData.map(u => {
    const scored = u.python_projects.filter(p => p.final_mark !== null && p.final_mark !== undefined);
    const finished = u.python_projects.filter(p => p.status === 'finished');
    return {
      login: u.login,
      totalHours: u.total_python_hours,
      avgMark: scored.length ? mean(scored.map(p => p.final_mark)) : 0,
      completionRate: u.python_projects.length ? (finished.length / u.python_projects.length) * 100 : 0,
      numProjects: u.python_projects.length,
      avgHoursPerProj: u.python_projects.length ? u.total_python_hours / u.python_projects.length : 0,
      maxSingleProj: Math.max(...u.python_projects.map(p => p.time_spent_hours), 0)
    };
  });

  let colorValues;
  if (colorByMetric === 'completion') colorValues = userData.map(u => u.completionRate);
  else if (colorByMetric === 'marks') colorValues = userData.map(u => u.avgMark);
  else colorValues = userData.map(u => u.totalHours);

  const trace = {
    type: 'parcoords',
    line: {
      color: colorValues,
      colorscale: [[0, '#f2495c'], [0.5, '#ff9830'], [1, '#73bf69']],
      showscale: true,
      cmin: Math.min(...colorValues),
      cmax: Math.max(...colorValues)
    },
    dimensions: [
      { label: 'Total Hours', values: userData.map(u => u.totalHours), range: [0, Math.max(...userData.map(u => u.totalHours))] },
      { label: 'Avg Mark', values: userData.map(u => u.avgMark), range: [0, 100] },
      { label: 'Completion %', values: userData.map(u => u.completionRate), range: [0, 100] },
      { label: 'Num Projects', values: userData.map(u => u.numProjects), range: [0, Math.max(...userData.map(u => u.numProjects))] },
      { label: 'Avg h/Project', values: userData.map(u => u.avgHoursPerProj), range: [0, Math.max(...userData.map(u => u.avgHoursPerProj))] },
      { label: 'Max Single Proj', values: userData.map(u => u.maxSingleProj), range: [0, Math.max(...userData.map(u => u.maxSingleProj))] }
    ]
  };

  const layout = {
    ...PLOTLY_LAYOUT_DEFAULTS,
    margin: { t: 40, r: 40, b: 20, l: 40 }
  };
  Plotly.react(el, [trace], layout, PLOTLY_CONFIG);
});

// ---- 21. NETWORK GRAPH ----
registerChart('network', function() {
  const el = document.getElementById('chart-21');
  if (!el) return;
  if (!filteredData.length) { el.innerHTML = '<div class="chart-empty">No data</div>'; return; }

  const simThreshold = parseFloat(document.getElementById('network-threshold')?.value) || 0.5;

  // Calculate similarity between users based on shared modules
  const users = filteredData.map(u => ({
    login: u.login,
    modules: new Set(u.python_projects.map(p => p.project_name)),
    hours: u.total_python_hours,
    completionRate: u.python_projects.length
      ? u.python_projects.filter(p => p.status === 'finished').length / u.python_projects.length
      : 0
  }));

  // Jaccard similarity
  const edges = [];
  for (let i = 0; i < users.length; i++) {
    for (let j = i + 1; j < users.length; j++) {
      const intersection = [...users[i].modules].filter(m => users[j].modules.has(m)).length;
      const union = new Set([...users[i].modules, ...users[j].modules]).size;
      const sim = union > 0 ? intersection / union : 0;
      if (sim >= simThreshold) {
        edges.push({ i, j, sim });
      }
    }
  }

  // Simple force-directed layout
  const positions = users.map((_, i) => ({
    x: Math.cos(2 * Math.PI * i / users.length) * 100 + (Math.random() - 0.5) * 40,
    y: Math.sin(2 * Math.PI * i / users.length) * 100 + (Math.random() - 0.5) * 40
  }));

  // Iterative force layout (simplified)
  for (let iter = 0; iter < 50; iter++) {
    positions.forEach((p1, i) => {
      let fx = 0, fy = 0;
      positions.forEach((p2, j) => {
        if (i === j) return;
        const dx = p1.x - p2.x;
        const dy = p1.y - p2.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        // Repulsion
        fx += (dx / dist) * 500 / (dist * dist);
        fy += (dy / dist) * 500 / (dist * dist);
      });
      // Attraction for edges
      edges.forEach(e => {
        let other = -1;
        if (e.i === i) other = e.j;
        else if (e.j === i) other = e.i;
        if (other < 0) return;
        const dx = positions[other].x - p1.x;
        const dy = positions[other].y - p1.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        fx += dx * 0.01 * e.sim;
        fy += dy * 0.01 * e.sim;
      });
      p1.x += fx * 0.1;
      p1.y += fy * 0.1;
    });
  }

  // Edge traces
  const edgeX = [], edgeY = [];
  edges.forEach(e => {
    edgeX.push(positions[e.i].x, positions[e.j].x, null);
    edgeY.push(positions[e.i].y, positions[e.j].y, null);
  });

  const traces = [
    {
      type: 'scatter', mode: 'lines',
      x: edgeX, y: edgeY,
      line: { color: 'rgba(51,162,229,0.2)', width: 1 },
      hoverinfo: 'none', showlegend: false
    },
    {
      type: 'scatter', mode: 'markers+text',
      x: positions.map(p => p.x), y: positions.map(p => p.y),
      marker: {
        size: users.map(u => Math.max(8, Math.min(30, u.hours / 5))),
        color: users.map(u => u.completionRate),
        colorscale: [[0, '#f2495c'], [0.5, '#ff9830'], [1, '#73bf69']],
        cmin: 0, cmax: 1,
        showscale: true,
        colorbar: { title: 'Completion', titleside: 'right', tickfont: { color: '#8e8e8e' } },
        line: { width: 1, color: 'rgba(255,255,255,0.2)' }
      },
      text: users.map(u => u.login),
      textposition: 'top center',
      textfont: { size: 9, color: '#8e8e8e' },
      hovertext: users.map(u => `${u.login}<br>Hours: ${u.hours.toFixed(1)}<br>Modules: ${u.modules.size}<br>Completion: ${(u.completionRate * 100).toFixed(0)}%`),
      hoverinfo: 'text',
      showlegend: false
    }
  ];

  const layout = {
    ...PLOTLY_LAYOUT_DEFAULTS,
    xaxis: { visible: false, showgrid: false, zeroline: false },
    yaxis: { visible: false, showgrid: false, zeroline: false },
    margin: { t: 10, r: 40, b: 10, l: 10 }
  };
  Plotly.react(el, traces, layout, PLOTLY_CONFIG);
});
