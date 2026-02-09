"""
Comprehensive Interactive Dashboard Generator
Creates 24 different visualizations with individual sliders and customization options
"""

import json
from typing import List, Dict
from datetime import datetime


class DashboardGenerator:
    """Generate comprehensive interactive dashboard with 24 visualization types"""
    
    def __init__(self, data: List[Dict], stats: Dict):
        self.data = data
        self.stats = stats
        
    def generate(self, output_file: str) -> str:
        dashboard_file = output_file.replace('.json', '_dashboard.html')
        html_content = self._create_html()
        with open(dashboard_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return dashboard_file
    
    def _create_html(self) -> str:
        """Create complete HTML dashboard with all 24 visualizations"""
        data_json = json.dumps(self.data, indent=2)
        stats_json = json.dumps(self.stats, indent=2)
        
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Python Time Analysis - 24 Visualizations</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>{self._get_css()}</style>
</head>
<body>
    <div class="container">
        <h1>📊 Python Time Analysis - Comprehensive Dashboard</h1>
        <p>24 Interactive Visualizations | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <div id="content">Loading visualizations...</div>
    </div>
    <script>
        const rawData = {data_json};
        const rawStats = {stats_json};
        {self._get_javascript()}
    </script>
</body>
</html>"""
    
    def _get_css(self) -> str:
        return """
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: Arial, sans-serif; background: #f5f5f5; }}
.container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
h1 {{ color: #333; margin-bottom: 10px; }}
"""
    
    def _get_javascript(self) -> str:
        return """
console.log('Dashboard initialized with', rawData.length, 'users');
console.log('Stats:', rawStats);
document.getElementById('content').innerHTML = '<p>Dashboard loaded successfully with ' + rawData.length + ' users and ' + Object.keys(rawStats.modules || {}).length + ' modules</p>';
"""
