"""
Modern Interactive Dashboard Generator
Creates comprehensive visualizations with sliders and customization options
"""

import json
from typing import List, Dict
from datetime import datetime


class DashboardGenerator:
    """Generate modern interactive dashboard with multiple visualization types"""
    
    def __init__(self, data: List[Dict], stats: Dict):
        """
        Initialize dashboard generator
        
        Args:
            data: List of user data dictionaries
            stats: Statistics dictionary
        """
        self.data = data
        self.stats = stats
        
    def generate(self, output_file: str) -> str:
        """
        Generate dashboard HTML file
        
        Args:
            output_file: Path for the JSON output (dashboard will be created alongside)
            
        Returns:
            Path to generated dashboard HTML file
        """
        dashboard_file = output_file.replace('.json', '_dashboard.html')
        
        # Generate HTML
        html_content = self._create_html()
        
        # Save to file
        with open(dashboard_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return dashboard_file
    
    def _create_html(self) -> str:
        """Create complete HTML dashboard"""
        
        # Serialize data for JavaScript
        data_json = json.dumps(self.data, indent=2)
        stats_json = json.dumps(self.stats, indent=2)
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Python Time Analysis Dashboard</title>
    
    <!-- Chart.js for visualizations -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
    
    <style>
        {self._get_css()}
    </style>
</head>
<body>
    <div class="dashboard">
        <!-- Header -->
        <header class="header">
            <div class="header-content">
                <h1>📊 Python Time Analysis Dashboard</h1>
                <div class="header-stats">
                    <span>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
                </div>
            </div>
        </header>
        
        <!-- Global Filters -->
        <section class="filters-section">
            <div class="filters-container">
                <h2>🎛️ Global Filters</h2>
                
                <div class="filters-grid">
                    <!-- Status Filter -->
                    <div class="filter-group">
                        <label for="statusFilter">Status:</label>
                        <select id="statusFilter" onchange="applyFilters()">
                            <option value="all">All</option>
                            <option value="finished">Finished</option>
                            <option value="in_progress">In Progress</option>
                            <option value="waiting">Waiting</option>
                        </select>
                    </div>
                    
                    <!-- Validated Only -->
                    <div class="filter-group">
                        <label for="validatedFilter">Show Only Validated:</label>
                        <input type="checkbox" id="validatedFilter" onchange="applyFilters()">
                    </div>
                    
                    <!-- Hours Threshold -->
                    <div class="filter-group">
                        <label for="hoursThreshold">Min Hours: <span id="hoursValue">0</span></label>
                        <input type="range" id="hoursThreshold" min="0" max="200" value="0" 
                               oninput="updateHoursValue(this.value); applyFilters()">
                    </div>
                    
                    <!-- Score Range -->
                    <div class="filter-group">
                        <label for="minScore">Min Score: <span id="minScoreValue">0</span></label>
                        <input type="range" id="minScore" min="0" max="100" value="0" 
                               oninput="updateMinScore(this.value); applyFilters()">
                    </div>
                    
                    <!-- Top N Users -->
                    <div class="filter-group">
                        <label for="topNUsers">Top N Users: <span id="topNValue">15</span></label>
                        <input type="range" id="topNUsers" min="5" max="50" value="15" step="5"
                               oninput="updateTopN(this.value); applyFilters()">
                    </div>
                    
                    <!-- Reset Button -->
                    <div class="filter-group">
                        <button class="btn-reset" onclick="resetFilters()">Reset All Filters</button>
                    </div>
                </div>
            </div>
        </section>
        
        <!-- KPI Cards -->
        <section class="kpi-section">
            <div class="kpi-grid">
                <div class="kpi-card">
                    <div class="kpi-icon">👥</div>
                    <div class="kpi-content">
                        <h3>Total Users</h3>
                        <p class="kpi-value" id="kpiUsers">-</p>
                    </div>
                </div>
                
                <div class="kpi-card">
                    <div class="kpi-icon">⏱️</div>
                    <div class="kpi-content">
                        <h3>Total Hours</h3>
                        <p class="kpi-value" id="kpiHours">-</p>
                    </div>
                </div>
                
                <div class="kpi-card">
                    <div class="kpi-icon">📊</div>
                    <div class="kpi-content">
                        <h3>Avg Hours/User</h3>
                        <p class="kpi-value" id="kpiAvgHours">-</p>
                    </div>
                </div>
                
                <div class="kpi-card">
                    <div class="kpi-icon">✅</div>
                    <div class="kpi-content">
                        <h3>Completion Rate</h3>
                        <p class="kpi-value" id="kpiCompletion">-</p>
                    </div>
                </div>
            </div>
        </section>
        
        <!-- Visualizations Grid -->
        <section class="charts-section">
            <!-- Top Users Chart -->
            <div class="chart-container">
                <div class="chart-header">
                    <h3>👑 Top Users by Total Hours</h3>
                    <div class="chart-controls">
                        <button onclick="exportChart('topUsersChart')" class="btn-export">Export</button>
                    </div>
                </div>
                <canvas id="topUsersChart"></canvas>
            </div>
            
            <!-- Module Average Times -->
            <div class="chart-container">
                <div class="chart-header">
                    <h3>📚 Average Time per Module</h3>
                    <div class="chart-controls">
                        <button onclick="exportChart('moduleAvgChart')" class="btn-export">Export</button>
                    </div>
                </div>
                <canvas id="moduleAvgChart"></canvas>
            </div>
            
            <!-- Status Distribution -->
            <div class="chart-container">
                <div class="chart-header">
                    <h3>📈 Project Status Distribution</h3>
                    <div class="chart-controls">
                        <button onclick="exportChart('statusChart')" class="btn-export">Export</button>
                    </div>
                </div>
                <canvas id="statusChart"></canvas>
            </div>
            
            <!-- Time Distribution Histogram -->
            <div class="chart-container">
                <div class="chart-header">
                    <h3>⏰ Hours Distribution</h3>
                    <div class="chart-controls">
                        <button onclick="exportChart('timeDistChart')" class="btn-export">Export</button>
                    </div>
                </div>
                <canvas id="timeDistChart"></canvas>
            </div>
            
            <!-- Hours vs Score Scatter -->
            <div class="chart-container chart-container-wide">
                <div class="chart-header">
                    <h3>🎯 Hours vs Final Score</h3>
                    <div class="chart-controls">
                        <button onclick="exportChart('scatterChart')" class="btn-export">Export</button>
                    </div>
                </div>
                <canvas id="scatterChart"></canvas>
            </div>
            
            <!-- Efficiency Chart -->
            <div class="chart-container chart-container-wide">
                <div class="chart-header">
                    <h3>⚡ Efficiency Score (Score per Hour)</h3>
                    <div class="chart-controls">
                        <button onclick="exportChart('efficiencyChart')" class="btn-export">Export</button>
                    </div>
                </div>
                <canvas id="efficiencyChart"></canvas>
            </div>
        </section>
        
        <!-- Data Table -->
        <section class="table-section">
            <div class="table-container">
                <div class="table-header">
                    <h3>📋 Detailed User Rankings</h3>
                    <div class="table-controls">
                        <button onclick="exportTableCSV()" class="btn-export">Export CSV</button>
                        <input type="text" id="searchTable" placeholder="Search users..." 
                               oninput="filterTable()" class="search-input">
                    </div>
                </div>
                <div class="table-wrapper">
                    <table id="dataTable">
                        <thead>
                            <tr>
                                <th onclick="sortTable(0)">Rank</th>
                                <th onclick="sortTable(1)">User</th>
                                <th onclick="sortTable(2)">Projects</th>
                                <th onclick="sortTable(3)">Total Hours</th>
                                <th onclick="sortTable(4)">Avg Hours/Project</th>
                                <th onclick="sortTable(5)">Avg Score</th>
                                <th onclick="sortTable(6)">Completion %</th>
                            </tr>
                        </thead>
                        <tbody id="tableBody">
                            <!-- Populated by JavaScript -->
                        </tbody>
                    </table>
                </div>
            </div>
        </section>
        
        <!-- Footer -->
        <footer class="footer">
            <p>Generated by Python Time Tracker | <a href="https://github.com/Pixyde/PythonTime" target="_blank">GitHub</a></p>
        </footer>
    </div>
    
    <script>
        // Data from Python
        const rawData = {data_json};
        const rawStats = {stats_json};
        
        // Global state
        let filteredData = [...rawData];
        let charts = {{}};
        
        {self._get_javascript()}
    </script>
</body>
</html>
"""
        return html
    
    def _get_css(self) -> str:
        """Get CSS styles for the dashboard"""
        return """
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #333;
    line-height: 1.6;
    min-height: 100vh;
}

.dashboard {
    max-width: 1600px;
    margin: 0 auto;
    padding: 20px;
}

/* Header */
.header {
    background: white;
    border-radius: 12px;
    padding: 30px;
    margin-bottom: 30px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.header-content h1 {
    color: #667eea;
    font-size: 2.5rem;
    margin-bottom: 10px;
}

.header-stats span {
    color: #666;
    font-size: 0.9rem;
}

/* Filters Section */
.filters-section {
    background: white;
    border-radius: 12px;
    padding: 25px;
    margin-bottom: 30px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.filters-section h2 {
    color: #667eea;
    margin-bottom: 20px;
}

.filters-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
}

.filter-group {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.filter-group label {
    font-weight: 600;
    color: #555;
    font-size: 0.9rem;
}

.filter-group select,
.filter-group input[type="range"] {
    padding: 8px;
    border: 2px solid #e0e0e0;
    border-radius: 6px;
    font-size: 0.95rem;
}

.filter-group input[type="range"] {
    cursor: pointer;
}

.btn-reset {
    padding: 10px 20px;
    background: #667eea;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 600;
    transition: background 0.3s;
}

.btn-reset:hover {
    background: #5568d3;
}

/* KPI Cards */
.kpi-section {
    margin-bottom: 30px;
}

.kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
}

.kpi-card {
    background: white;
    border-radius: 12px;
    padding: 25px;
    display: flex;
    align-items: center;
    gap: 20px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    transition: transform 0.3s, box-shadow 0.3s;
}

.kpi-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 12px rgba(0, 0, 0, 0.15);
}

.kpi-icon {
    font-size: 3rem;
}

.kpi-content h3 {
    font-size: 0.9rem;
    color: #666;
    margin-bottom: 5px;
}

.kpi-value {
    font-size: 2rem;
    font-weight: bold;
    color: #667eea;
}

/* Charts Section */
.charts-section {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
    gap: 30px;
    margin-bottom: 30px;
}

.chart-container {
    background: white;
    border-radius: 12px;
    padding: 25px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.chart-container-wide {
    grid-column: span 2;
}

.chart-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}

.chart-header h3 {
    color: #667eea;
    font-size: 1.2rem;
}

.btn-export {
    padding: 6px 12px;
    background: #764ba2;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.85rem;
    transition: background 0.3s;
}

.btn-export:hover {
    background: #5d3a82;
}

/* Table Section */
.table-section {
    background: white;
    border-radius: 12px;
    padding: 25px;
    margin-bottom: 30px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.table-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}

.table-header h3 {
    color: #667eea;
    font-size: 1.2rem;
}

.table-controls {
    display: flex;
    gap: 10px;
}

.search-input {
    padding: 8px 15px;
    border: 2px solid #e0e0e0;
    border-radius: 6px;
    font-size: 0.9rem;
}

.table-wrapper {
    overflow-x: auto;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th {
    background: #667eea;
    color: white;
    padding: 12px;
    text-align: left;
    cursor: pointer;
    user-select: none;
}

th:hover {
    background: #5568d3;
}

td {
    padding: 12px;
    border-bottom: 1px solid #e0e0e0;
}

tr:hover {
    background: #f5f5f5;
}

.completion-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 0.85rem;
    font-weight: 600;
}

.completion-high {
    background: #d4edda;
    color: #155724;
}

.completion-medium {
    background: #fff3cd;
    color: #856404;
}

.completion-low {
    background: #f8d7da;
    color: #721c24;
}

/* Footer */
.footer {
    background: white;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.footer a {
    color: #667eea;
    text-decoration: none;
    font-weight: 600;
}

.footer a:hover {
    text-decoration: underline;
}

/* Responsive */
@media (max-width: 768px) {
    .charts-section {
        grid-template-columns: 1fr;
    }
    
    .chart-container-wide {
        grid-column: span 1;
    }
    
    .filters-grid {
        grid-template-columns: 1fr;
    }
}
"""
    
    def _get_javascript(self) -> str:
        """Get JavaScript code for dashboard interactivity"""
        return """
// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    applyFilters();
});

// Update slider values
function updateHoursValue(val) {
    document.getElementById('hoursValue').textContent = val;
}

function updateMinScore(val) {
    document.getElementById('minScoreValue').textContent = val;
}

function updateTopN(val) {
    document.getElementById('topNValue').textContent = val;
}

// Apply filters
function applyFilters() {
    const statusFilter = document.getElementById('statusFilter').value;
    const validatedOnly = document.getElementById('validatedFilter').checked;
    const minHours = parseFloat(document.getElementById('hoursThreshold').value);
    const minScore = parseFloat(document.getElementById('minScore').value);
    
    // Filter data
    filteredData = rawData.filter(user => {
        // Apply hours filter
        if (user.total_python_hours < minHours) return false;
        
        // Apply validation filter
        if (validatedOnly) {
            const hasValidated = user.python_projects.some(p => p.validated === true);
            if (!hasValidated) return false;
        }
        
        // Apply status filter
        if (statusFilter !== 'all') {
            const hasStatus = user.python_projects.some(p => p.status === statusFilter);
            if (!hasStatus) return false;
        }
        
        // Apply score filter
        if (minScore > 0) {
            const avgScore = user.python_projects.reduce((sum, p) => sum + (p.final_mark || 0), 0) / 
                           (user.python_projects.length || 1);
            if (avgScore < minScore) return false;
        }
        
        return true;
    });
    
    // Update UI
    updateKPIs();
    updateCharts();
    updateTable();
}

// Reset filters
function resetFilters() {
    document.getElementById('statusFilter').value = 'all';
    document.getElementById('validatedFilter').checked = false;
    document.getElementById('hoursThreshold').value = 0;
    document.getElementById('minScore').value = 0;
    document.getElementById('topNUsers').value = 15;
    
    updateHoursValue(0);
    updateMinScore(0);
    updateTopN(15);
    
    applyFilters();
}

// Update KPIs
function updateKPIs() {
    const totalUsers = filteredData.length;
    const totalHours = filteredData.reduce((sum, u) => sum + u.total_python_hours, 0);
    const avgHours = totalUsers > 0 ? totalHours / totalUsers : 0;
    
    // Calculate completion rate
    let totalProjects = 0;
    let finishedProjects = 0;
    filteredData.forEach(user => {
        user.python_projects.forEach(proj => {
            totalProjects++;
            if (proj.status === 'finished') finishedProjects++;
        });
    });
    const completionRate = totalProjects > 0 ? (finishedProjects / totalProjects * 100) : 0;
    
    document.getElementById('kpiUsers').textContent = totalUsers;
    document.getElementById('kpiHours').textContent = totalHours.toFixed(1) + 'h';
    document.getElementById('kpiAvgHours').textContent = avgHours.toFixed(1) + 'h';
    document.getElementById('kpiCompletion').textContent = completionRate.toFixed(1) + '%';
}

// Update all charts
function updateCharts() {
    updateTopUsersChart();
    updateModuleAvgChart();
    updateStatusChart();
    updateTimeDistChart();
    updateScatterChart();
    updateEfficiencyChart();
}

// Top Users Chart
function updateTopUsersChart() {
    const topN = parseInt(document.getElementById('topNUsers').value);
    const sortedUsers = [...filteredData].sort((a, b) => b.total_python_hours - a.total_python_hours).slice(0, topN);
    
    const ctx = document.getElementById('topUsersChart');
    
    if (charts.topUsers) {
        charts.topUsers.destroy();
    }
    
    charts.topUsers = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: sortedUsers.map(u => u.login),
            datasets: [{
                label: 'Total Hours',
                data: sortedUsers.map(u => u.total_python_hours),
                backgroundColor: 'rgba(102, 126, 234, 0.8)',
                borderColor: 'rgba(102, 126, 234, 1)',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.parsed.y.toFixed(1) + ' hours';
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Hours'
                    }
                }
            }
        }
    });
}

// Module Average Chart
function updateModuleAvgChart() {
    const moduleStats = {};
    
    filteredData.forEach(user => {
        user.python_projects.forEach(proj => {
            const name = proj.project_name;
            if (!moduleStats[name]) {
                moduleStats[name] = { total: 0, count: 0 };
            }
            moduleStats[name].total += proj.time_spent_hours;
            moduleStats[name].count += 1;
        });
    });
    
    const modules = Object.keys(moduleStats).map(name => ({
        name,
        avg: moduleStats[name].total / moduleStats[name].count
    })).sort((a, b) => b.avg - a.avg).slice(0, 15);
    
    const ctx = document.getElementById('moduleAvgChart');
    
    if (charts.moduleAvg) {
        charts.moduleAvg.destroy();
    }
    
    charts.moduleAvg = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: modules.map(m => m.name),
            datasets: [{
                label: 'Average Hours',
                data: modules.map(m => m.avg),
                backgroundColor: 'rgba(118, 75, 162, 0.8)',
                borderColor: 'rgba(118, 75, 162, 1)',
                borderWidth: 2
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Average Hours'
                    }
                }
            }
        }
    });
}

// Status Distribution Chart
function updateStatusChart() {
    const statusCount = { finished: 0, in_progress: 0, waiting: 0 };
    
    filteredData.forEach(user => {
        user.python_projects.forEach(proj => {
            if (statusCount.hasOwnProperty(proj.status)) {
                statusCount[proj.status]++;
            }
        });
    });
    
    const ctx = document.getElementById('statusChart');
    
    if (charts.status) {
        charts.status.destroy();
    }
    
    charts.status = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Finished', 'In Progress', 'Waiting'],
            datasets: [{
                data: [statusCount.finished, statusCount.in_progress, statusCount.waiting],
                backgroundColor: [
                    'rgba(75, 192, 192, 0.8)',
                    'rgba(255, 206, 86, 0.8)',
                    'rgba(255, 99, 132, 0.8)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// Time Distribution Histogram
function updateTimeDistChart() {
    const hours = filteredData.map(u => u.total_python_hours);
    const bins = 20;
    const max = Math.max(...hours);
    const binSize = max / bins;
    
    const histogram = Array(bins).fill(0);
    hours.forEach(h => {
        const binIndex = Math.min(Math.floor(h / binSize), bins - 1);
        histogram[binIndex]++;
    });
    
    const labels = Array(bins).fill(0).map((_, i) => 
        `${(i * binSize).toFixed(0)}-${((i + 1) * binSize).toFixed(0)}h`
    );
    
    const ctx = document.getElementById('timeDistChart');
    
    if (charts.timeDist) {
        charts.timeDist.destroy();
    }
    
    charts.timeDist = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Number of Users',
                data: histogram,
                backgroundColor: 'rgba(75, 192, 192, 0.8)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Users'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Hours Range'
                    }
                }
            }
        }
    });
}

// Scatter Chart: Hours vs Score
function updateScatterChart() {
    const scatterData = [];
    
    filteredData.forEach(user => {
        user.python_projects.forEach(proj => {
            if (proj.final_mark !== null && proj.time_spent_hours > 0) {
                scatterData.push({
                    x: proj.time_spent_hours,
                    y: proj.final_mark,
                    user: user.login,
                    project: proj.project_name
                });
            }
        });
    });
    
    const ctx = document.getElementById('scatterChart');
    
    if (charts.scatter) {
        charts.scatter.destroy();
    }
    
    charts.scatter = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Projects',
                data: scatterData,
                backgroundColor: 'rgba(102, 126, 234, 0.6)',
                borderColor: 'rgba(102, 126, 234, 1)',
                pointRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const point = context.raw;
                            return [
                                `User: ${point.user}`,
                                `Project: ${point.project}`,
                                `Hours: ${point.x.toFixed(1)}`,
                                `Score: ${point.y}`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Hours Spent'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Final Score'
                    },
                    min: 0,
                    max: 100
                }
            }
        }
    });
}

// Efficiency Chart
function updateEfficiencyChart() {
    const userEfficiency = filteredData.map(user => {
        let totalScore = 0;
        let totalHours = 0;
        let validProjects = 0;
        
        user.python_projects.forEach(proj => {
            if (proj.final_mark !== null && proj.time_spent_hours > 0) {
                totalScore += proj.final_mark;
                totalHours += proj.time_spent_hours;
                validProjects++;
            }
        });
        
        const efficiency = totalHours > 0 ? totalScore / totalHours : 0;
        
        return {
            login: user.login,
            efficiency: efficiency,
            totalHours: totalHours
        };
    }).filter(u => u.efficiency > 0)
      .sort((a, b) => b.efficiency - a.efficiency)
      .slice(0, 20);
    
    const ctx = document.getElementById('efficiencyChart');
    
    if (charts.efficiency) {
        charts.efficiency.destroy();
    }
    
    charts.efficiency = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: userEfficiency.map(u => u.login),
            datasets: [{
                label: 'Score per Hour',
                data: userEfficiency.map(u => u.efficiency),
                backgroundColor: 'rgba(255, 159, 64, 0.8)',
                borderColor: 'rgba(255, 159, 64, 1)',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const user = userEfficiency[context.dataIndex];
                            return [
                                `Efficiency: ${context.parsed.y.toFixed(2)} pts/hr`,
                                `Total Hours: ${user.totalHours.toFixed(1)}h`
                            ];
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Score per Hour'
                    }
                }
            }
        }
    });
}

// Update table
function updateTable() {
    const tbody = document.getElementById('tableBody');
    tbody.innerHTML = '';
    
    const sortedData = [...filteredData].sort((a, b) => b.total_python_hours - a.total_python_hours);
    
    sortedData.forEach((user, index) => {
        const avgHours = user.total_python_hours / (user.python_projects.length || 1);
        const avgScore = user.python_projects.reduce((sum, p) => sum + (p.final_mark || 0), 0) / 
                        (user.python_projects.length || 1);
        const finishedCount = user.python_projects.filter(p => p.status === 'finished').length;
        const completionRate = (finishedCount / user.python_projects.length) * 100;
        
        let badgeClass = 'completion-low';
        if (completionRate >= 75) badgeClass = 'completion-high';
        else if (completionRate >= 50) badgeClass = 'completion-medium';
        
        const row = `
            <tr>
                <td>${index + 1}</td>
                <td>${user.login}</td>
                <td>${user.python_projects.length}</td>
                <td>${user.total_python_hours.toFixed(1)}h</td>
                <td>${avgHours.toFixed(1)}h</td>
                <td>${avgScore.toFixed(1)}</td>
                <td><span class="completion-badge ${badgeClass}">${completionRate.toFixed(0)}%</span></td>
            </tr>
        `;
        tbody.innerHTML += row;
    });
}

// Table sorting
let sortColumn = -1;
let sortAsc = true;

function sortTable(col) {
    const table = document.getElementById('dataTable');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    if (sortColumn === col) {
        sortAsc = !sortAsc;
    } else {
        sortColumn = col;
        sortAsc = true;
    }
    
    rows.sort((a, b) => {
        const aVal = a.children[col].textContent.replace(/[^0-9.-]/g, '');
        const bVal = b.children[col].textContent.replace(/[^0-9.-]/g, '');
        
        const aNum = parseFloat(aVal) || aVal;
        const bNum = parseFloat(bVal) || bVal;
        
        if (aNum < bNum) return sortAsc ? -1 : 1;
        if (aNum > bNum) return sortAsc ? 1 : -1;
        return 0;
    });
    
    rows.forEach(row => tbody.appendChild(row));
}

// Filter table
function filterTable() {
    const searchTerm = document.getElementById('searchTable').value.toLowerCase();
    const rows = document.querySelectorAll('#tableBody tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm) ? '' : 'none';
    });
}

// Export chart
function exportChart(chartId) {
    const canvas = document.getElementById(chartId);
    const url = canvas.toDataURL('image/png');
    const link = document.createElement('a');
    link.download = chartId + '.png';
    link.href = url;
    link.click();
}

// Export table to CSV
function exportTableCSV() {
    const table = document.getElementById('dataTable');
    let csv = [];
    
    // Headers
    const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent);
    csv.push(headers.join(','));
    
    // Rows
    const rows = Array.from(table.querySelectorAll('tbody tr'));
    rows.forEach(row => {
        if (row.style.display !== 'none') {
            const cols = Array.from(row.querySelectorAll('td')).map(td => 
                td.textContent.replace(/,/g, '')
            );
            csv.push(cols.join(','));
        }
    });
    
    // Download
    const csvContent = csv.join('\\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.download = 'python_time_analysis.csv';
    link.href = url;
    link.click();
}
"""
