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
- 🌐 **Grafana-Style Interactive Dashboard** - Professional UI with 25 visualization panels, filters, and real-time updates
- 🏫 **Campus Comparison** - Compare averages and metrics across campuses
- 🔄 **Zero-logtime retry** - Automatically re-fetches location data when a user's logtime is 0 (cache invalidation)
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

### 4. Run the application

Campus selection is interactive — you'll be prompted to choose from all available campuses at startup.

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
9. **Generate interactive dashboard** (HTML file)
10. Save results to JSON file with timestamp

### Efficient Project-Based Approach

This application uses an efficient approach:
- Fetches users directly from project endpoints
- Optional campus filtering to reduce API calls
- Much faster than fetching all projects for each user

## Output

The application generates:

1. **JSON data file**: `python_time_analysis_YYYYMMDD_HHMMSS.json` with detailed user data
2. **Interactive Dashboard**: `python_time_analysis_YYYYMMDD_HHMMSS_dashboard.html` — a single self-contained HTML file with 25 Plotly.js visualizations

### Interactive Dashboard Features

The dashboard is a **Grafana-inspired analytics platform** — a single self-contained HTML file powered by Plotly.js with 25 interactive visualization panels:

**🎨 Design**:
- Dark theme matching Grafana color scheme
- Responsive grid layout with per-section navigation
- Professional panel system with header, controls, and chart area

**🔧 Global Filters**:
- Multi-select users and modules
- Status and validated toggle
- Date range picker
- Score range and minimum hour threshold
- Apply / Reset buttons

**📊 25 Visualization Panels** (each with their own sliders & controls):

| # | Chart | Section |
|---|-------|---------|
| 1 | Timeline Gantt Chart | Timeline |
| 2 | Time Spent Heatmap Calendar | Timeline |
| 3 | Progress Timeline | Timeline |
| 4 | Multi-User Bar / Column Chart | Comparison |
| 5 | Box Plot / Violin Plot | Comparison |
| 6 | Radar / Spider Chart | Comparison |
| 7 | Scatter Plot — Hours vs Score | Performance |
| 8 | Efficiency Score Chart | Performance |
| 9 | Completion Rate Gauge | Performance |
| 10 | Sankey Diagram | Flow |
| 11 | Funnel Chart | Flow |
| 12 | Stream Graph | Flow |
| 13 | Histogram — Hour Distribution | Statistical |
| 14 | Cumulative Distribution (CDF) | Statistical |
| 15 | Correlation Matrix | Statistical |
| 16 | Ranking Table with Sparklines | Leaderboard |
| 17 | Bump Chart (Rank Over Time) | Leaderboard |
| 18 | Treemap — Hours by User & Module | Advanced |
| 19 | Sunburst Chart | Advanced |
| 20 | Parallel Coordinates | Advanced |
| 21 | Network Graph | Advanced |
| 22 | KPI Cards with Trends | Interactive |
| 23 | Filterable & Sortable Data Table | Interactive |
| 24 | Animated Race Bar Chart | Interactive |
| 25 | Campus Comparison (bar / radar) | Campus |

**🏫 Campus Comparison Tab**:
- Compare average hours, marks, completion rate, validation rate, efficiency across campuses
- Radar overlay for multi-metric comparison
- Global average reference line

**To view**: Simply open the `*_dashboard.html` file in any modern web browser!

### JSON Structure

```json
[
  {
    "user_id": 12345,
    "login": "student-login",
    "email": "student@example.com",
    "cursus_level": 0,
    "campus_name": "Le Havre",
    "campus_id": 14,
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
├── main.py                # Main application entry point (optimized)
├── api_client.py          # 42 API client with caching support
├── cache_manager.py       # Cache management system
├── cache_util.py          # Cache management utility CLI
├── data_processor.py      # Data processing and analysis logic
├── dashboard/             # Modular dashboard template parts
│   ├── template.html      # Main HTML skeleton
│   ├── styles.css         # Dark theme CSS
│   ├── core.js            # Data processing, filters, utilities
│   ├── charts_timeline.js     # Charts 1-3 (Gantt, Heatmap, Progress)
│   ├── charts_comparison.js   # Charts 4-6 (Bar, Box/Violin, Radar)
│   ├── charts_performance.js  # Charts 7-9 (Scatter, Efficiency, Gauge)
│   ├── charts_flow.js         # Charts 10-12 (Sankey, Funnel, Stream)
│   ├── charts_statistical.js  # Charts 13-15 (Histogram, CDF, Correlation)
│   ├── charts_leaderboard.js  # Charts 16-17 (Ranking, Bump)
│   ├── charts_advanced.js     # Charts 18-21 (Treemap, Sunburst, Parallel, Network)
│   ├── charts_interactive.js  # Charts 22-24 (KPI, Data Table, Race Bar)
│   └── charts_campus.js       # Chart 25 (Campus Comparison)
├── test_app.py            # Tests for data processing
├── test_cache.py          # Tests for caching system
├── test_project_users.py  # Tests for project users endpoint
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variables template
├── .gitignore            # Git ignore rules (includes .cache/)
└── README.md             # This file
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
