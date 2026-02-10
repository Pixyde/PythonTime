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
  const totalModules = NEW_COMMON_CORE_SLUGS.length;

  if (viewMode === 'completed') {
    // Show % of users who completed each module
    const moduleCounts = {};
    NEW_COMMON_CORE_SLUGS.forEach(m => { moduleCounts[m] = 0; });

    filteredData.forEach(u => {
      const finished = new Set();
      u.python_projects.forEach(p => {
        if (p.status === 'finished') {
          const slug = (p.project_slug || '').toLowerCase();
          NEW_COMMON_CORE_SLUGS.forEach(m => { if (slug.includes(m)) finished.add(m); });
        }
      });
      finished.forEach(m => { moduleCounts[m]++; });
    });

    const slugs = NEW_COMMON_CORE_SLUGS.slice();
    const pcts = slugs.map(m => (moduleCounts[m] / totalUsers) * 100);

    const trace = {
      type: 'bar',
      x: slugs,
      y: pcts,
      marker: { color: pcts.map(p => p >= 50 ? COLORS.green : p >= 25 ? COLORS.orange : COLORS.red) },
      text: pcts.map((p, i) => `${p.toFixed(0)}% (${moduleCounts[slugs[i]]}/${totalUsers})`),
      textposition: 'outside',
      textfont: { size: 9, color: '#8e8e8e' }
    };

    const layout = {
      ...PLOTLY_LAYOUT_DEFAULTS,
      xaxis: { ...PLOTLY_LAYOUT_DEFAULTS.xaxis, title: 'Module', tickangle: -30 },
      yaxis: { ...PLOTLY_LAYOUT_DEFAULTS.yaxis, title: '% of Users Who Completed', range: [0, Math.max(...pcts, 10) * 1.15] }
    };
    Plotly.react(el, [trace], layout, PLOTLY_CONFIG);

  } else {
    // Show % of users at each module stage (how many modules finished)
    const stageCounts = new Array(totalModules + 1).fill(0);

    filteredData.forEach(u => {
      const finished = new Set();
      u.python_projects.forEach(p => {
        if (p.status === 'finished') {
          const slug = (p.project_slug || '').toLowerCase();
          NEW_COMMON_CORE_SLUGS.forEach(m => { if (slug.includes(m)) finished.add(m); });
        }
      });
      stageCounts[finished.size]++;
    });

    const labels = stageCounts.map((_, i) => i === totalModules ? `${i} (All Done)` : `${i}`);
    const pcts = stageCounts.map(c => (c / totalUsers) * 100);

    const trace = {
      type: 'bar',
      x: labels,
      y: pcts,
      marker: {
        color: labels.map((_, i) => i === totalModules ? COLORS.green : i >= totalModules * 0.75 ? COLORS.cyan : i >= totalModules * 0.5 ? COLORS.orange : COLORS.red)
      },
      text: pcts.map((p, i) => `${p.toFixed(1)}% (${stageCounts[i]})`),
      textposition: 'outside',
      textfont: { size: 9, color: '#8e8e8e' }
    };

    const layout = {
      ...PLOTLY_LAYOUT_DEFAULTS,
      xaxis: { ...PLOTLY_LAYOUT_DEFAULTS.xaxis, title: 'Modules Finished' },
      yaxis: { ...PLOTLY_LAYOUT_DEFAULTS.yaxis, title: '% of Users', range: [0, Math.max(...pcts, 10) * 1.15] }
    };
    Plotly.react(el, [trace], layout, PLOTLY_CONFIG);
  }
});
