/* ============================================================
   Charts: Flow & Progression Visualizations (10-12)
   10. Sankey Diagram
   11. Funnel Chart
   12. Stream Graph
   ============================================================ */

// ---- 10. SANKEY DIAGRAM ----
registerChart('sankey', function() {
  const el = document.getElementById('chart-10');
  if (!el) return;
  if (!filteredData.length) { el.innerHTML = '<div class="chart-empty">No data</div>'; return; }

  const minFlow = parseInt(document.getElementById('sankey-min-flow')?.value) || 1;
  const validatedOnly = document.getElementById('sankey-validated')?.checked || false;
  const colorBySuccess = document.getElementById('sankey-color')?.checked !== false;

  // Build module sequence per user
  const modules = getAllModules();
  const transitions = {};

  filteredData.forEach(user => {
    let projects = user.python_projects.filter(p => p.start_date);
    if (validatedOnly) projects = projects.filter(p => p.validated);
    projects.sort((a, b) => new Date(a.start_date) - new Date(b.start_date));

    for (let i = 0; i < projects.length - 1; i++) {
      const from = projects[i].project_name;
      const to = projects[i + 1].project_name;
      const key = `${from}|||${to}`;
      if (!transitions[key]) transitions[key] = { count: 0, validated: 0 };
      transitions[key].count++;
      if (projects[i].validated) transitions[key].validated++;
    }
  });

  // Build sankey data
  const nodeLabels = [...new Set(Object.keys(transitions).flatMap(k => k.split('|||')))];
  const links = Object.entries(transitions)
    .filter(([_, v]) => v.count >= minFlow)
    .map(([key, val]) => {
      const [from, to] = key.split('|||');
      const successRate = val.count > 0 ? val.validated / val.count : 0;
      return {
        source: nodeLabels.indexOf(from),
        target: nodeLabels.indexOf(to),
        value: val.count,
        color: colorBySuccess
          ? `rgba(${Math.round(255 * (1 - successRate))},${Math.round(255 * successRate)},100,0.4)`
          : 'rgba(51,162,229,0.3)'
      };
    });

  if (!links.length) { el.innerHTML = '<div class="chart-empty">No transitions found</div>'; return; }

  const trace = {
    type: 'sankey',
    orientation: 'h',
    node: {
      label: nodeLabels,
      color: nodeLabels.map((_, i) => COLORS.palette[i % COLORS.palette.length]),
      pad: 15,
      thickness: 20,
      line: { color: '#2c3038', width: 1 }
    },
    link: {
      source: links.map(l => l.source),
      target: links.map(l => l.target),
      value: links.map(l => l.value),
      color: links.map(l => l.color)
    }
  };

  const layout = { ...PLOTLY_LAYOUT_DEFAULTS, margin: { t: 10, r: 20, b: 10, l: 20 } };
  Plotly.react(el, [trace], layout, PLOTLY_CONFIG);
});

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

// ---- 12. STREAM GRAPH ----
registerChart('stream', function() {
  const el = document.getElementById('chart-12');
  if (!el) return;
  if (!filteredData.length) { el.innerHTML = '<div class="chart-empty">No data</div>'; return; }

  const normalize = document.getElementById('stream-normalize')?.checked || false;

  // Build time series of active students per module
  const allDates = new Set();
  filteredData.forEach(u => u.python_projects.forEach(p => {
    if (p.start_date) allDates.add(dateStr(p.start_date));
    if (p.end_date) allDates.add(dateStr(p.end_date));
  }));

  const sortedDates = [...allDates].sort();
  if (sortedDates.length < 2) { el.innerHTML = '<div class="chart-empty">Insufficient date data</div>'; return; }

  // Sample dates (max 50 points for performance)
  const step = Math.max(1, Math.floor(sortedDates.length / 50));
  const sampledDates = sortedDates.filter((_, i) => i % step === 0);

  const modules = getAllModules();
  const traces = modules.map((mod, i) => {
    const counts = sampledDates.map(date => {
      const d = new Date(date);
      let count = 0;
      filteredData.forEach(u => {
        u.python_projects.forEach(p => {
          if (p.project_name === mod && p.start_date && p.end_date) {
            if (d >= new Date(p.start_date) && d <= new Date(p.end_date)) count++;
          }
        });
      });
      return count;
    });

    return {
      type: 'scatter',
      mode: 'lines',
      name: mod,
      x: sampledDates,
      y: counts,
      stackgroup: 'one',
      groupnorm: normalize ? 'percent' : '',
      fillcolor: COLORS.palette[i % COLORS.palette.length] + '80',
      line: { width: 0.5, color: COLORS.palette[i % COLORS.palette.length] }
    };
  });

  const layout = {
    ...PLOTLY_LAYOUT_DEFAULTS,
    xaxis: { ...PLOTLY_LAYOUT_DEFAULTS.xaxis, title: 'Date' },
    yaxis: { ...PLOTLY_LAYOUT_DEFAULTS.yaxis, title: normalize ? 'Percentage' : 'Active Students' },
    legend: { font: { size: 9 }, orientation: 'h', y: -0.15 },
    showlegend: modules.length <= 12
  };
  Plotly.react(el, traces, layout, PLOTLY_CONFIG);
});
