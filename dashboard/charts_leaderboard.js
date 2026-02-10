/* ============================================================
   Charts: Leaderboard Visualizations (16-17)
   16. Ranking Table with Sparklines
   17. Bump Chart (Rank Over Time)
   ============================================================ */

// ---- 16. RANKING TABLE WITH SPARKLINES ----
registerChart('ranking', function() {
  const el = document.getElementById('chart-16');
  if (!el) return;
  if (!filteredData.length) { el.innerHTML = '<div class="chart-empty">No data</div>'; return; }

  const sortMetric = document.getElementById('ranking-sort')?.value || 'hours';
  const pageSize = 15;
  const currentPage = parseInt(el.dataset.page || '1');

  // Build user stats
  let users = filteredData.map(u => {
    const scored = u.python_projects.filter(p => p.final_mark !== null && p.final_mark !== undefined);
    const finished = u.python_projects.filter(p => p.status === 'finished');
    const avgMark = scored.length ? mean(scored.map(p => p.final_mark)) : 0;
    const completionRate = u.python_projects.length ? (finished.length / u.python_projects.length) * 100 : 0;
    const efficiency = u.total_python_hours > 0 ? avgMark / u.total_python_hours : 0;

    // Build sparkline data (hours per project over time)
    const projsSorted = [...u.python_projects].filter(p => p.start_date).sort((a, b) => new Date(a.start_date) - new Date(b.start_date));
    const sparkData = projsSorted.map(p => p.time_spent_hours);

    return {
      login: u.login,
      hours: u.total_python_hours,
      avgMark,
      completionRate,
      efficiency,
      numProjects: u.python_projects.length,
      numFinished: finished.length,
      sparkData
    };
  });

  // Sort
  if (sortMetric === 'marks') users.sort((a, b) => b.avgMark - a.avgMark);
  else if (sortMetric === 'completion') users.sort((a, b) => b.completionRate - a.completionRate);
  else if (sortMetric === 'efficiency') users.sort((a, b) => b.efficiency - a.efficiency);
  else if (sortMetric === 'projects') users.sort((a, b) => b.numProjects - a.numProjects);
  else users.sort((a, b) => b.hours - a.hours);

  // Paginate
  const totalPages = Math.ceil(users.length / pageSize);
  const page = Math.min(currentPage, totalPages);
  const pageUsers = users.slice((page - 1) * pageSize, page * pageSize);

  // Build sparkline SVG
  function sparkline(data) {
    if (!data.length) return '';
    const w = 80, h = 24;
    const maxVal = Math.max(...data, 1);
    const points = data.map((v, i) => {
      const x = data.length > 1 ? (i / (data.length - 1)) * w : w / 2;
      const y = h - (v / maxVal) * h;
      return `${x},${y}`;
    }).join(' ');
    return `<svg width="${w}" height="${h}" style="vertical-align:middle"><polyline points="${points}" fill="none" stroke="#33a2e5" stroke-width="1.5"/></svg>`;
  }

  // Render table
  const offset = (page - 1) * pageSize;
  let html = `<div class="data-table-wrapper"><table class="data-table">
    <thead><tr>
      <th>#</th><th>User</th><th>Hours</th><th>Avg Mark</th><th>Completion</th><th>Projects</th><th>Efficiency</th><th>Trend</th>
    </tr></thead><tbody>`;

  pageUsers.forEach((u, i) => {
    const rank = offset + i + 1;
    const medal = rank <= 3 ? ['🥇','🥈','🥉'][rank - 1] : rank;
    html += `<tr>
      <td>${medal}</td>
      <td><strong>${u.login}</strong></td>
      <td>${u.hours.toFixed(1)}h</td>
      <td>${u.avgMark.toFixed(1)}</td>
      <td><span class="badge ${u.completionRate >= 75 ? 'badge-finished' : u.completionRate >= 50 ? 'badge-in_progress' : 'badge-waiting'}">${u.completionRate.toFixed(0)}%</span></td>
      <td>${u.numFinished}/${u.numProjects}</td>
      <td>${u.efficiency.toFixed(2)} pts/h</td>
      <td>${sparkline(u.sparkData)}</td>
    </tr>`;
  });

  html += '</tbody></table></div>';

  // Pagination
  if (totalPages > 1) {
    html += '<div class="pagination">';
    for (let p = 1; p <= totalPages; p++) {
      html += `<button class="${p === page ? 'active' : ''}" onclick="document.getElementById('chart-16').dataset.page='${p}'; chartUpdaters.ranking();">${p}</button>`;
    }
    html += '</div>';
  }

  el.innerHTML = html;
});

// ---- 17. BUMP CHART (RANK OVER TIME) ----
registerChart('bump', function() {
  const el = document.getElementById('chart-17');
  if (!el) return;
  if (!filteredData.length) { el.innerHTML = '<div class="chart-empty">No data</div>'; return; }

  const topN = parseInt(document.getElementById('bump-top')?.value) || 10;
  const highlightUser = document.getElementById('bump-highlight')?.value || '';

  // Build cumulative hours over time for each user
  const allDates = new Set();
  filteredData.forEach(u => u.python_projects.forEach(p => {
    if (p.end_date) allDates.add(dateStr(p.end_date));
  }));
  const dates = [...allDates].sort();
  if (dates.length < 2) { el.innerHTML = '<div class="chart-empty">Insufficient data</div>'; return; }

  // Get top N users by total hours
  const topUsers = [...filteredData].sort((a, b) => b.total_python_hours - a.total_python_hours).slice(0, topN);
  const userLogins = topUsers.map(u => u.login);

  // Calculate cumulative hours at each date
  const cumHours = {};
  userLogins.forEach(login => {
    cumHours[login] = {};
    let running = 0;
    const user = topUsers.find(u => u.login === login);
    const projects = [...user.python_projects].filter(p => p.end_date).sort((a, b) => new Date(a.end_date) - new Date(b.end_date));
    let projIdx = 0;
    dates.forEach(date => {
      while (projIdx < projects.length && dateStr(projects[projIdx].end_date) <= date) {
        running += projects[projIdx].time_spent_hours;
        projIdx++;
      }
      cumHours[login][date] = running;
    });
  });

  // Calculate ranks at each date
  const rankings = {};
  dates.forEach(date => {
    const sorted = userLogins.map(login => ({ login, hours: cumHours[login][date] || 0 }))
      .sort((a, b) => b.hours - a.hours);
    sorted.forEach((u, i) => {
      if (!rankings[u.login]) rankings[u.login] = [];
      rankings[u.login].push(i + 1);
    });
  });

  // Create traces
  const traces = userLogins.map((login, i) => {
    const isHighlighted = highlightUser === login;
    return {
      type: 'scatter',
      mode: 'lines+markers',
      name: login,
      x: dates,
      y: rankings[login],
      line: {
        color: COLORS.palette[i % COLORS.palette.length],
        width: isHighlighted ? 4 : 2
      },
      marker: {
        size: isHighlighted ? 8 : 4,
        color: COLORS.palette[i % COLORS.palette.length]
      },
      opacity: highlightUser && !isHighlighted ? 0.3 : 1
    };
  });

  const layout = {
    ...PLOTLY_LAYOUT_DEFAULTS,
    xaxis: { ...PLOTLY_LAYOUT_DEFAULTS.xaxis, title: 'Date' },
    yaxis: { ...PLOTLY_LAYOUT_DEFAULTS.yaxis, title: 'Rank', autorange: 'reversed', dtick: 1, range: [0.5, topN + 0.5] },
    legend: { font: { size: 9 } },
    hovermode: 'x unified'
  };
  Plotly.react(el, traces, layout, PLOTLY_CONFIG);

  // Populate highlight
  const sel = document.getElementById('bump-highlight');
  if (sel && sel.options.length <= 1) {
    sel.innerHTML = '<option value="">None</option>' + userLogins.map(u => `<option value="${u}">${u}</option>`).join('');
  }
});
