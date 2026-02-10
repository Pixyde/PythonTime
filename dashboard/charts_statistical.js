/* ============================================================
   Charts: Statistical Visualizations — Funnel only
   ============================================================ */

// ---- 30. MODULE PROGRESS DISTRIBUTION ----
registerChart('moduleprogress', function() {
  const el = document.getElementById('chart-30');
  if (!el) return;
  if (!filteredData.length) { el.innerHTML = '<div class="chart-empty">No data</div>'; return; }

  const viewMode = document.getElementById('modprogress-view')?.value || 'stage';
  const totalUsers = filteredData.length;
  const allModuleNames = getAllModules();
  const totalModules = allModuleNames.length;

  if (viewMode === 'completed') {
    // Show how many users completed each module (user counts on y-axis)
    const moduleCounts = {};
    allModuleNames.forEach(m => { moduleCounts[m] = 0; });

    filteredData.forEach(u => {
      const finished = new Set();
      u.python_projects.forEach(p => {
        if (p.status === 'finished') finished.add(p.project_name);
      });
      finished.forEach(m => { moduleCounts[m]++; });
    });

    const names = allModuleNames.slice();
    const counts = names.map(m => moduleCounts[m]);
    const pcts = counts.map(c => (c / totalUsers) * 100);

    const trace = {
      type: 'bar',
      x: names,
      y: counts,
      marker: { color: pcts.map(p => p >= 50 ? COLORS.green : p >= 25 ? COLORS.orange : COLORS.red) },
      text: counts.map((c, i) => `${pcts[i].toFixed(0)}% (${c}/${totalUsers})`),
      textposition: 'outside',
      textfont: { size: 9, color: '#8e8e8e' }
    };

    const layout = {
      ...PLOTLY_LAYOUT_DEFAULTS,
      xaxis: { ...PLOTLY_LAYOUT_DEFAULTS.xaxis, title: 'Module', tickangle: -30 },
      yaxis: { ...PLOTLY_LAYOUT_DEFAULTS.yaxis, title: 'Number of Users', range: [0, Math.max(...counts, 1) * 1.2] }
    };
    Plotly.react(el, [trace], layout, PLOTLY_CONFIG);

  } else {
    // Show how many users at each module stage (user counts on y-axis)
    const stageCounts = new Array(totalModules + 1).fill(0);

    filteredData.forEach(u => {
      const n = countFinishedModules(u);
      stageCounts[Math.min(n, totalModules)]++;
    });

    const labels = stageCounts.map((_, i) => i === totalModules ? `${i} (All Done)` : `${i}`);
    const pcts = stageCounts.map(c => (c / totalUsers) * 100);

    const trace = {
      type: 'bar',
      x: labels,
      y: stageCounts,
      marker: {
        color: labels.map((_, i) => i === totalModules ? COLORS.green : i >= totalModules * 0.75 ? COLORS.cyan : i >= totalModules * 0.5 ? COLORS.orange : COLORS.red)
      },
      text: stageCounts.map((c, i) => `${pcts[i].toFixed(1)}% (${c})`),
      textposition: 'outside',
      textfont: { size: 9, color: '#8e8e8e' }
    };

    const layout = {
      ...PLOTLY_LAYOUT_DEFAULTS,
      xaxis: { ...PLOTLY_LAYOUT_DEFAULTS.xaxis, title: 'Modules Finished' },
      yaxis: { ...PLOTLY_LAYOUT_DEFAULTS.yaxis, title: 'Number of Users', range: [0, Math.max(...stageCounts, 1) * 1.2] }
    };
    Plotly.react(el, [trace], layout, PLOTLY_CONFIG);
  }
});
