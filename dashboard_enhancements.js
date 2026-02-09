// Enhanced analytics for comprehensive project tracking
// This adds C++ tracking and extensive additional statistics

// Extract all project types from user data
function analyzeAllProjects(data) {
    const analysis = {
        languages: {},
        projects: {},
        users: {
            total: data.length,
            withProjects: 0
        },
        completion: {
            total: 0,
            finished: 0,
            inProgress: 0,
            failed: 0
        }
    };
    
    data.forEach(user => {
        if (user.python_projects && user.python_projects.length > 0) {
            analysis.users.withProjects++;
            
            user.python_projects.forEach(project => {
                const name = project.project_name || 'Unknown';
                const slug = project.project_slug || '';
                const status = project.status || 'unknown';
                const hours = project.time_spent_hours || 0;
                
                // Detect language/type
                let language = detectProjectLanguage(name, slug);
                
                // Track by language
                if (!analysis.languages[language]) {
                    analysis.languages[language] = {
                        projects: [],
                        totalHours: 0,
                        avgHours: 0,
                        finished: 0,
                        total: 0
                    };
                }
                analysis.languages[language].projects.push(project);
                analysis.languages[language].totalHours += hours;
                analysis.languages[language].total++;
                if (status === 'finished') {
                    analysis.languages[language].finished++;
                }
                
                // Track by project
                if (!analysis.projects[name]) {
                    analysis.projects[name] = {
                        attempts: 0,
                        finished: 0,
                        totalHours: 0,
                        avgHours: 0,
                        language: language
                    };
                }
                analysis.projects[name].attempts++;
                analysis.projects[name].totalHours += hours;
                if (status === 'finished') {
                    analysis.projects[name].finished++;
                }
                
                // Track completion stats
                analysis.completion.total++;
                if (status === 'finished') analysis.completion.finished++;
                else if (status === 'in_progress') analysis.completion.inProgress++;
                else if (status === 'failed') analysis.completion.failed++;
            });
        }
    });
    
    // Calculate averages
    Object.keys(analysis.languages).forEach(lang => {
        const langData = analysis.languages[lang];
        langData.avgHours = langData.total > 0 ? langData.totalHours / langData.total : 0;
        langData.completionRate = langData.total > 0 ? (langData.finished / langData.total * 100) : 0;
    });
    
    Object.keys(analysis.projects).forEach(proj => {
        const projData = analysis.projects[proj];
        projData.avgHours = projData.attempts > 0 ? projData.totalHours / projData.attempts : 0;
        projData.completionRate = projData.attempts > 0 ? (projData.finished / projData.attempts * 100) : 0;
    });
    
    return analysis;
}

function detectProjectLanguage(name, slug) {
    name = name.toLowerCase();
    slug = slug.toLowerCase();
    
    if (name.includes('python') || name.includes('django') || slug.includes('python') || slug.includes('django')) {
        return 'Python';
    }
    if (name.includes('c++') || name.includes('cpp') || slug.includes('cpp')) {
        return 'C++';
    }
    if (name.includes('libft') || name.includes('ft_printf') || name.includes('get_next_line') ||
        name.includes('born2beroot') || name.includes('so_long') || name.includes('fdf') ||
        name.includes('minitalk') || name.includes('push_swap') || name.includes('philosophers') ||
        name.includes('minishell') || name.includes('cub3d') || slug.includes('piscine c')) {
        return 'C';
    }
    if (name.includes('webserv') || name.includes('ft_irc') || name.includes('inception') ||
        name.includes('ft_transcendence') || name.includes('matcha') || name.includes('hypertube')) {
        return 'Web/System';
    }
    return 'Other';
}

// Generate insights HTML
function generateInsightsHTML(analysis) {
    let html = '<div class="insights-grid">';
    
    // Language breakdown
    html += '<div class="insight-card"><h4>🌐 Languages Tracked</h4><ul>';
    Object.keys(analysis.languages).sort().forEach(lang => {
        const data = analysis.languages[lang];
        html += `<li><strong>${lang}</strong>: ${data.total} projects, ${data.totalHours.toFixed(1)}h total, ${data.completionRate.toFixed(1)}% completion</li>`;
    });
    html += '</ul></div>';
    
    // Top projects by attempts
    html += '<div class="insight-card"><h4>🔥 Most Popular Projects</h4><ul>';
    Object.entries(analysis.projects)
        .sort((a, b) => b[1].attempts - a[1].attempts)
        .slice(0, 10)
        .forEach(([name, data]) => {
            html += `<li><strong>${name}</strong>: ${data.attempts} attempts, ${data.completionRate.toFixed(1)}% success</li>`;
        });
    html += '</ul></div>';
    
    // Hardest projects (lowest completion rate with enough attempts)
    html += '<div class="insight-card"><h4>💀 Hardest Projects</h4><ul>';
    Object.entries(analysis.projects)
        .filter(([_, data]) => data.attempts >= 5)
        .sort((a, b) => a[1].completionRate - b[1].completionRate)
        .slice(0, 10)
        .forEach(([name, data]) => {
            html += `<li><strong>${name}</strong>: ${data.completionRate.toFixed(1)}% completion, ${data.avgHours.toFixed(1)}h avg</li>`;
        });
    html += '</ul></div>';
    
    // Fastest projects (least time)
    html += '<div class="insight-card"><h4>⚡ Fastest Projects</h4><ul>';
    Object.entries(analysis.projects)
        .filter(([_, data]) => data.attempts >= 5)
        .sort((a, b) => a[1].avgHours - b[1].avgHours)
        .slice(0, 10)
        .forEach(([name, data]) => {
            html += `<li><strong>${name}</strong>: ${data.avgHours.toFixed(1)}h avg, ${data.attempts} attempts</li>`;
        });
    html += '</ul></div>';
    
    html += '</div>';
    return html;
}

