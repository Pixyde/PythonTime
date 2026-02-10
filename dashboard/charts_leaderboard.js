/* ============================================================
   Charts: Leaderboard Visualizations (16)
   16. Ranking Table with Sparklines
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
    const efficiency = u.total_python_hours > 0 ? u.python_projects.length / u.total_python_hours : 0;

    // Count unique finished module slugs
    const finishedSlugs = new Set();
    u.python_projects.forEach(p => {
      if (p.status === 'finished') {
        const slug = (p.project_slug || '').toLowerCase();
        NEW_COMMON_CORE_SLUGS.forEach(m => { if (slug.includes(m)) finishedSlugs.add(m); });
      }
    });
    const numFinished = finishedSlugs.size;
    const totalModules = NEW_COMMON_CORE_SLUGS.length;
    const completionRate = (numFinished / totalModules) * 100;

    // Total completion time: days from first start to last end
    const starts = u.python_projects.map(p => p.start_date).filter(Boolean).map(d => new Date(d));
    const ends = u.python_projects.map(p => p.end_date).filter(Boolean).map(d => new Date(d));
    let completionDays = null;
    if (starts.length && ends.length) {
      const days = (new Date(Math.max(...ends)) - new Date(Math.min(...starts))) / MS_PER_DAY;
      if (days > 0) completionDays = days;
    }

    // Build sparkline data (hours per project over time)
    const projsSorted = [...u.python_projects].filter(p => p.start_date).sort((a, b) => new Date(a.start_date) - new Date(b.start_date));
    const sparkData = projsSorted.map(p => p.time_spent_hours);

    return {
      login: u.login,
      hours: u.total_python_hours,
      avgMark,
      completionRate,
      efficiency,
      completionDays,
      numProjects: u.python_projects.length,
      numFinished,
      totalModules,
      sparkData
    };
  });

  // Sort
  if (sortMetric === 'marks') users.sort((a, b) => b.avgMark - a.avgMark);
  else if (sortMetric === 'completion') users.sort((a, b) => b.numFinished - a.numFinished || b.completionRate - a.completionRate);
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
      <th>#</th><th>User</th><th>Hours</th><th>Completion Time</th><th>Avg Mark</th><th>Modules Finished</th><th>Completion</th><th>Efficiency</th><th>Trend</th>
    </tr></thead><tbody>`;

  pageUsers.forEach((u, i) => {
    const rank = offset + i + 1;
    const medal = rank <= 3 ? ['🥇','🥈','🥉'][rank - 1] : rank;
    html += `<tr>
      <td>${medal}</td>
      <td><strong>${u.login}</strong></td>
      <td>${u.hours.toFixed(1)}h</td>
      <td>${u.completionDays !== null ? u.completionDays.toFixed(0) + 'd' : '-'}</td>
      <td>${u.avgMark.toFixed(1)}</td>
      <td>${u.numFinished}/${u.totalModules}</td>
      <td><span class="badge ${u.completionRate >= 75 ? 'badge-finished' : u.completionRate >= 50 ? 'badge-in_progress' : 'badge-waiting'}">${u.completionRate.toFixed(0)}%</span></td>
      <td>${u.efficiency.toFixed(2)} proj/h</td>
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
