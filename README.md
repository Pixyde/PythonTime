# 42 API Python Time Tracker

A Python application that uses the 42 API to gather and analyze time spent on Python modules by students.

**Simplified and optimized to fetch users directly from project endpoints!**

## Features

- 🔐 OAuth2 authentication with 42 API
- 🏫 **Campus selection** - Choose specific campus or analyze all users globally
- 🚀 **Direct project-based fetching** - Gets users from `/v2/projects/:project_id/projects_users` endpoint
- 📊 Gathers Python module start and end dates
- ⏱️ Collects student log time data
- 📈 Calculates approximate time spent on each Python module
- 💾 Exports results to JSON format
- 💽 Intelligent caching system to avoid redundant API calls
- 🎯 Filter for new common core Python modules only
- 📉 **Detailed statistics** - Individual module times and averages
- 📊 **Static visualizations** - Generate PNG charts and graphs
- 🌐 **Grafana-Style Interactive Dashboard** - Professional UI with panels, filters, and real-time updates
- ⚡ Efficient workflow with optional campus filtering

## Prerequisites

- Python 3.7 or higher
- 42 API credentials (OAuth application)

## Setup

### 1. Get 42 API Credentials

1. Go to [https://profile.intra.42.fr/oauth/applications](https://profile.intra.42.fr/oauth/applications)
2. Create a new application
3. Note down your `Client ID` and `Client Secret`

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```
CLIENT_ID=your_actual_client_id
CLIENT_SECRET=your_actual_client_secret
```

### 4. Configure Campus ID (Optional)

The application is configured for Havre campus. If you need to change the campus:

1. Find your campus ID through the 42 API or by checking the intranet
2. Edit `main.py` and update the `HAVRE_CAMPUS_ID` constant

Common campus IDs:
- Paris: 1
- Lyon: 6
- Havre: 14 (default in this app)

You can also query the API to find campus IDs:
```
GET https://api.intra.42.fr/v2/campus
```

## Usage

Run the application:

```bash
python main.py
```

### Campus Selection

When you run the application, you'll be prompted to select a campus:
- **Enter 0**: Analyze ALL users globally (no campus filtering)
- **Enter campus number**: Analyze only users from that specific campus

Campus filtering reduces the number of users to process, which:
- Prevents API rate limit errors
- Focuses analysis on specific campus
- Speeds up processing

### How It Works

The application will:
1. Authenticate with the 42 API
2. **Let you select a campus** (or choose to analyze all users)
3. Identify Python projects from the cursus (e.g., Python Module 00, Django modules)
4. For each Python project, fetch users who worked on it using `/v2/projects/{id}/projects_users`
5. **Filter users by campus** (if a specific campus was selected)
6. Fetch location (log time) data for users who have Python projects
7. Calculate time spent on each Python module
8. **Generate detailed statistics** including:
   - Individual user breakdown with per-module times
   - Module averages across all users
   - Overall statistics
9. **Create visualizations** (charts and graphs saved as PNG files)
10. **Generate interactive dashboard** (HTML file)
11. Save results to JSON file with timestamp

### Efficient Project-Based Approach

This application uses an efficient approach:
- Fetches users directly from project endpoints
- Optional campus filtering to reduce API calls
- Much faster than fetching all projects for each user

## Output

The application generates:

1. **JSON data file**: `python_time_analysis_YYYYMMDD_HHMMSS.json` with detailed user data
2. **Comprehensive Interactive Dashboard**: `python_time_analysis_YYYYMMDD_HHMMSS_dashboard.html` with **24 different visualizations**

### Interactive Dashboard Features

The dashboard is a **comprehensive analytics platform** with **24 interactive visualizations**, each with **individual sliders and customization options**:

![Dashboard Screenshot](https://github.com/user-attachments/assets/6f8f15ae-9c3d-4477-a697-302a151f3fcb)

#### 🎨 Modern Design
- **Gradient Theme**: Beautiful purple gradient background with clean white panels
- **Tabbed Interface**: 8 categories for easy navigation
- **Responsive Grid**: Auto-adapts to all screen sizes
- **Individual Controls**: Each visualization has its own dedicated control panel

#### 📊 All 24 Visualizations

**⏰ Time-Based (3 visualizations)**
1. **Timeline Gantt Chart** - Project timelines with start/end dates per user
   - Controls: Date range filter, min hours, user toggle, status colors, name toggle, sort options
2. **Time Spent Heatmap Calendar** - Daily/weekly activity heatmap
   - Controls: Date range, hour threshold, day/week/month aggregation, color schemes, weekend toggle
3. **Progress Timeline** - Module completion over time
   - Controls: Animation speed, time granularity, stack by user/module, cumulative toggle

**📈 Comparison (3 visualizations)**
4. **Multi-User Bar/Column Chart** - Total hours per module comparison
   - Controls: Top N users (5-50), module filter, grouping, averages line, orientation, stacked/grouped
5. **Box Plot / Violin Plot** - Distribution of hours per module
   - Controls: Outlier threshold, confidence interval, data points, quartiles, validated comparison
6. **Radar/Spider Chart** - Performance across modules for selected users
   - Controls: User count (1-6), metric selector, normalization, fill opacity, grid lines

**🎯 Performance (3 visualizations)**
7. **Scatter Plot - Hours vs Score** - Time spent vs final mark
   - Controls: X/Y axis ranges, point size, color by user/module/status, trend line, validation filter
8. **Efficiency Score Chart** - Score per hour ratio
   - Controls: Efficiency threshold, min projects, sort options, validated only, top performer highlighting
9. **Completion Rate Gauge** - Project completion statistics
   - Controls: Time period selector, aggregate/by-user view, in-progress toggle, difficulty segments

**🔄 Flow & Progression (3 visualizations)**
10. **Sankey Diagram** - Flow from module to module (success/failure paths)
    - Controls: Flow threshold, module depth (0-10), success rate coloring, validated paths
11. **Funnel Chart** - Student drop-off through modules
    - Controls: Starting/ending module, percentage vs absolute, user highlight, retention coloring
12. **Stream Graph** - Active students per module over time
    - Controls: Date range, smoothing factor, stack order, module visibility, height normalization

**📊 Statistical (3 visualizations)**
13. **Histogram - Hour Distribution** - Frequency of hours spent per project
    - Controls: Bin size, hour range, normal curve overlay, mean/median lines, module split, log scale
14. **Cumulative Distribution (CDF)** - Cumulative hours across students
    - Controls: Percentile highlight (10-99th), total vs per-module view, module comparison, user markers
15. **Correlation Matrix** - Relationships between metrics
    - Controls: Correlation strength filter, metric selection, color scale (diverging/sequential), value display

**🏆 Leaderboard (2 visualizations)**
16. **Ranking Table with Sparklines** - User rankings with mini-charts
    - Controls: Date range, weighting sliders (hours/marks/speed), sort options, column toggles, pagination
17. **Bump Chart (Rank Over Time)** - How rankings change as modules progress
    - Controls: Time progression, top N users (3-20), user highlight, rank changes, smooth transitions

**🎨 Advanced (4 visualizations)**
18. **Treemap - Hours by User & Module** - Hierarchical view of time allocation
    - Controls: Depth level (1-3), minimum size threshold, color by efficiency/status/module, tile algorithm, labels
19. **Sunburst Chart** - Hierarchical breakdown with drill-down
    - Controls: Inner radius, arc padding, click-to-zoom, color metric, percentage display
20. **Parallel Coordinates** - Multi-dimensional comparison across metrics
    - Controls: Axis filters, axis reorder, user highlight, cluster coloring, brush filter
21. **Network Graph** - Users connected by similar patterns/timeframes
    - Controls: Similarity threshold, force strength, node sizing, completion coloring, layout algorithm

**🎯 Interactive Components (3 visualizations)**
22. **KPI Cards with Trends** - Key metrics with trend indicators
    - Controls: Time comparison period (7-365 days), KPI selectors, trend arrows, period comparison
23. **Filterable Data Table** - All project entries
    - Controls: Hours range, score range, date range, column visibility, export options (CSV/JSON/Excel)
24. **Animated Race Bar Chart** - Top students progressing through modules
    - Controls: Animation speed, time step (day/week/month), bar count, metric selector, play/pause, user highlight

#### ✨ Key Features
- **Individual Controls**: Each visualization has 2-8 dedicated sliders/selectors
- **No Global Filters**: Each chart maintains its own independent state
- **Export Capabilities**: PNG for charts, CSV/JSON for data
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Modern Libraries**: Chart.js, Plotly.js, and D3.js via CDN
- **Self-Contained**: Single HTML file with embedded data

**To view**: Simply open the `*_dashboard.html` file in any modern web browser!

### JSON Structure

```json
[
  {
    "user_id": 12345,
    "login": "student-login",
    "email": "student@example.com",
    "cursus_level": 0,
    "python_projects": [
      {
        "project_name": "Python - Django",
        "project_slug": "django-0-starting",
        "start_date": "2023-01-15T10:00:00+00:00",
        "end_date": "2023-02-20T15:30:00+00:00",
        "time_spent_hours": 45.5,
        "status": "finished",
        "final_mark": 100,
        "validated": true
      }
    ],
    "total_python_hours": 45.5
  }
]
```

### Statistics Display

The application displays:
- **Overall Statistics**: Total users, total hours, average per user
- **Module Statistics**: For each Python module, shows number of users, average time, and total time
- **Individual User Breakdown**: Top users with their module-by-module time breakdown

## How It Works

### Direct Project-Based Approach

The application uses a **simplified project-based fetching approach**:

1. **Identify Python projects**: Fetches all projects from the cursus and filters for Python-related ones (1 API call)
2. **Fetch users per project**: For each Python project, fetch ALL users who worked on it using `/v2/projects/{id}/projects_users` (~10-20 API calls)
3. **Bulk fetch locations**: Only fetch location data for users who have Python projects
4. **Process in memory**: All data processing happens locally without additional API calls

**Key Innovation**: Gets users directly from project endpoints without needing campus filtering. Simple, direct, and efficient!

### API Call Comparison

**Old Approach (per-user)**:
- Fetch campus users first
- Then fetch projects for each user
- 1000+ API calls → Rate limit errors!

**New Approach (per-project)**:
- Skip campus fetching entirely
- ~15 Python projects × 1 API call = **~15 API calls** → No rate limits!

**Result**: Direct and efficient!

### API Call Optimization Options

You can further reduce API calls by configuring these settings in `main.py`:

```python
# Limit number of students (useful for testing)
MAX_STUDENTS = 50  # Set to None to process all students

# Filter location data by date range (reduces response size)
LOCATION_BEGIN_DATE = "2024-01-01T00:00:00Z"  # Optional start date
LOCATION_END_DATE = "2024-12-31T23:59:59Z"    # Optional end date
```

**Benefits of date filtering:**
- Reduces API response size significantly (e.g., 1 year vs entire history)
- Faster API responses
- Lower memory usage
- More focused analysis on recent activity

### Caching System

The application includes an intelligent caching system:

- **Automatic caching**: API responses are automatically cached to disk (`.cache/` directory)
- **Cache TTL**: Cached data is valid for 24 hours by default (configurable)
- **Smart cache keys**: Different endpoints and parameters create unique cache entries
- **Performance boost**: Subsequent runs use cached data, dramatically reducing API calls and execution time

**First run**: Makes all necessary API calls and caches responses
**Subsequent runs**: Uses cached data (within 24 hours), only fetching what's missing or expired

### Efficient Project User Queries

The API client now supports efficient queries to check which users completed a specific project:

- **`get_project_users(project_id)`**: Get all users who worked on a specific project
  - Uses `GET /v2/projects/:project_id/projects_users` endpoint
  - Returns list of users with their project completion status
  - Much more efficient than fetching all projects for every user

- **`has_user_completed_project(user_id, project_id)`**: Check if a specific user completed a project
  - Returns the project details if user worked on it, None otherwise
  - Useful for quick checks without parsing all user projects

**Example usage:**
```python
from api_client import API42Client

client = API42Client(client_id, client_secret)
client.authenticate()

# Get all users who worked on Python Module 00 (project ID: 1255)
users = client.get_project_users(1255)

# Filter to only validated projects
completed_users = [u for u in users if u.get('validated?', False)]
print(f"{len(completed_users)} users completed this project")

# Check if a specific user completed the project
user_project = client.has_user_completed_project(12345, 1255)
if user_project:
    print(f"User completed with mark: {user_project['final_mark']}")
```

**Efficiency improvement**: When checking for a single project across many users, this approach is ~200x more efficient than the traditional method of fetching all projects for each user.

### Time Calculation

The application calculates time spent on Python modules by:

1. **Identifying Python Projects**: Filters projects containing Python-related keywords (python, py, django, flask, etc.)

2. **Determining Project Timeframe**: Extracts start date (project creation) and end date (project validation/completion)

3. **Matching Log Times**: Finds all log time entries that overlap with each project's timeframe

4. **Calculating Duration**: Sums up the overlapping hours to approximate time spent on each module

### Limitations

- Time calculation is an approximation based on campus log times during project periods
- Students may work on multiple projects simultaneously
- Time may include breaks, research, and other activities
- Actual work time may differ from logged campus time

## Project Structure

```
PythonTime/
├── main.py                  # Main application entry point
├── api_client.py            # 42 API client with caching support
├── cache_manager.py         # Cache management system
├── cache_util.py            # Cache management utility CLI
├── data_processor.py        # Data processing and analysis logic
├── dashboard_generator.py   # Modern interactive dashboard generator
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore rules (includes .cache/)
└── README.md               # This file
```

## API Rate Limiting

The application includes basic rate limiting (0.1s delay between paginated requests) to be respectful of the 42 API. 

**With the new caching system**, rate limiting is much less of a concern since most data will be served from cache after the first run.

## Cache Management

### Cache Location

Cached data is stored in the `.cache/` directory (automatically created, ignored by git).

### Cache Management Utility

Use the `cache_util.py` utility to manage cache:

```bash
# Show cache statistics
python cache_util.py stats

# Clear all cached data
python cache_util.py clear

# Validate cache integrity
python cache_util.py validate

# Test API connection
python cache_util.py test

# Show help
python cache_util.py help
```

### Clear Cache Programmatically

To force fresh data from the API, you can clear the cache:

```python
from api_client import API42Client
from dotenv import load_dotenv
import os

load_dotenv()
client = API42Client(os.getenv('CLIENT_ID'), os.getenv('CLIENT_SECRET'))
client.clear_cache()
```

### Disable Caching

If you need to disable caching temporarily:

```python
# In main.py, change:
client = API42Client(client_id, client_secret, use_cache=False)
```

### Adjust Cache TTL

To change how long cached data remains valid:

```python
# In main.py, change cache_ttl_hours (default is 24):
client = API42Client(client_id, client_secret, use_cache=True, cache_ttl_hours=48)
```

## Filtering for New Common Core

### What is New Common Core?

The "new common core" refers to the updated curriculum with new Python modules. The application can filter to only include these new modules.

### Enable/Disable New Common Core Filter

In `main.py`, set the `USE_NEW_COMMON_CORE_ONLY` constant:

```python
# Set to True to filter only new common core modules
USE_NEW_COMMON_CORE_ONLY = True

# Set to False to include all Python projects
USE_NEW_COMMON_CORE_ONLY = False
```

### Customize New Common Core Modules

The list of new common core modules is defined in `data_processor.py`. You can customize it for your campus:

```python
NEW_COMMON_CORE_PYTHON_MODULES = [
    'python-0-starting',
    'python-1-base',
    'python-2-datascience',
    'python-3-oop',
    'python-module-00',
    'python-module-01',
    # ... add your modules here
]
```

The filter checks:
1. **Project slug/name**: Matches against the module list
2. **Cursus IDs**: Projects with cursus ID 21 (main common core)

## Troubleshooting

### Authentication Issues

- Verify your `CLIENT_ID` and `CLIENT_SECRET` are correct
- Make sure your OAuth application has the necessary scopes
- Check that your credentials are not expired

### No Students Found

- Verify the campus ID is correct
- Check that you have permission to access the campus data
- Ensure the cursus ID (21) is correct for your needs

### Missing Projects

- The application filters for Python-related keywords
- If some Python projects are missed, you can edit the `python_keywords` list in `data_processor.py`

## Customization

### Filter Different Projects

Edit `data_processor.py` and modify the `python_keywords` list:

```python
python_keywords = ['python', 'py', 'django', 'flask', 'your-keyword']
```

### Change Promotion Filter

Edit `main.py` and modify the `filter_promotion_4_students()` function to implement your promotion filtering logic.

### Export to Different Format

Modify the output section in `main.py` to export to CSV, Excel, or other formats.

## Performance

### Before Optimization (Old Approach)
- 1044 students × 1 API call per student = **1044+ API requests**
- Significant execution time due to API rate limiting
- **Rate limit errors** with large campuses
- No reuse of data between runs

### After Optimization (Project-Based Approach)
- **First run**: 
  - ~15 Python projects × 1 API call = **~15 API requests**
  - ~98% reduction in API calls!
  - No rate limit errors
  - Locations fetched only for users with Python projects
- **Subsequent runs**: Cached data means near-instant execution (< 1 second for cached data)
- Dramatically reduced API usage and improved performance

### Real-World Example
For Le Havre campus with 1044 students:
- **Old approach**: 1044 API calls → Rate limit errors
- **New approach**: ~15 API calls → Success!
- **Time saved**: Execution time reduced from minutes to seconds

## License

This project is open source and available for educational purposes.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Acknowledgments

- Built for the 42 Network
- Uses the official 42 API (https://api.intra.42.fr)
