/* ============================================================
   Charts: Flow — Module Dropout Funnel (11)
   ============================================================ */

// ---- 11. FUNNEL CHART ----
registerChart('funnel', function() {
  const el = document.getElementById('chart-11');
  if (!el) return;
  if (!filteredData.length) { el.innerHTML = '<div class="chart-empty">No data</div>'; return; }

  const showPct = document.getElementById('funnel-pct')?.checked || false;
  const highlightUser = document.getElementById('funnel-highlight')?.value || '';

  // Count students per module (sorted by module order / number of students)
  const moduleCounts = {};
  filteredData.forEach(user => {
    const modulesSeen = new Set();
    user.python_projects.forEach(p => modulesSeen.add(p.project_name));
    modulesSeen.forEach(m => { moduleCounts[m] = (moduleCounts[m] || 0) + 1; });
  });

  // Sort by count descending (most students first = top of funnel)
  const sorted = Object.entries(moduleCounts).sort((a, b) => b[1] - a[1]);
  const labels = sorted.map(([name]) => name);
  const values = sorted.map(([_, count]) => count);
  const total = filteredData.length;

  const textValues = showPct
    ? values.map(v => `${v} (${((v / total) * 100).toFixed(0)}%)`)
    : values.map(v => `${v} students`);

  const trace = {
    type: 'funnel',
    y: labels,
    x: values,
    textinfo: 'text',
    text: textValues,
    textposition: 'inside',
    textfont: { color: '#fff', size: 11 },
    marker: {
      color: values.map((v, i) => {
        const ratio = v / (values[0] || 1);
        return ratio >= 0.7 ? COLORS.green : ratio >= 0.4 ? COLORS.orange : COLORS.red;
      })
    },
    connector: { line: { color: '#2c3038', width: 1 } }
  };

  const traces = [trace];

  // Highlight specific user path
  if (highlightUser) {
    const user = filteredData.find(u => u.login === highlightUser);
    if (user) {
      const userModules = new Set(user.python_projects.map(p => p.project_name));
      const highlightTrace = {
        type: 'scatter',
        mode: 'markers',
        x: labels.map(l => userModules.has(l) ? moduleCounts[l] : null),
        y: labels,
        marker: { color: COLORS.yellow, size: 12, symbol: 'star', line: { width: 2, color: '#fff' } },
        name: highlightUser,
        showlegend: true
      };
      traces.push(highlightTrace);
    }
  }

  const layout = {
    ...PLOTLY_LAYOUT_DEFAULTS,
    margin: { t: 10, r: 20, b: 40, l: 160 },
    funnelmode: 'stack'
  };
  Plotly.react(el, traces, layout, PLOTLY_CONFIG);

  // Populate highlight user
  const sel = document.getElementById('funnel-highlight');
  if (sel && sel.options.length <= 1) {
    sel.innerHTML = '<option value="">None</option>' + getAllUsers().map(u => `<option value="${u}">${u}</option>`).join('');
  }
});
