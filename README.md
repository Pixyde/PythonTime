# PythonTime

A Python tool that uses the 42 API to estimate how much time students spend on Python modules, and generates a self-contained interactive dashboard from the results.

Instead of walking every student's project list (1000+ API calls on a large campus), it fetches users directly from each Python project's endpoint — cutting a typical run down to roughly 15 API calls.

## Features

- OAuth2 authentication with the 42 API
- Fetches users per-project via `/v2/projects/:project_id/projects_users` instead of per-student
- Optional campus filtering, or analyze all users globally
- Matches campus log-time entries against each project's timeframe to approximate hours spent
- Disk-backed caching (24h TTL by default) so repeat runs are near-instant
- Exports a timestamped JSON file plus a self-contained HTML dashboard (25 Plotly.js panels: timelines, comparisons, correlations, campus comparison, and more)

## Setup

1. Create a 42 OAuth application at [profile.intra.42.fr/oauth/applications](https://profile.intra.42.fr/oauth/applications) and note the Client ID/Secret.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure environment:
   ```bash
   cp .env.example .env
   # then fill in CLIENT_ID and CLIENT_SECRET
   ```

## Usage

```bash
python main.py
```

You'll be prompted to select a campus (or enter `0` to analyze all users globally). The app then:

1. Authenticates with the 42 API
2. Identifies Python-related projects in the cursus
3. Fetches the users who worked on each one (optionally filtered by campus)
4. Pulls log-time data only for those users
5. Calculates approximate time per module and writes:
   - `python_time_analysis_YYYYMMDD_HHMMSS.json` — raw per-user, per-module data
   - `python_time_analysis_YYYYMMDD_HHMMSS_dashboard.html` — open this directly in a browser

## Configuration

A few things are worth tuning in `main.py` / `data_processor.py`:

| Setting | Where | Purpose |
|---|---|---|
| `MAX_STUDENTS` | `main.py` | Cap the number of students processed (testing) |
| `LOCATION_BEGIN_DATE` / `LOCATION_END_DATE` | `main.py` | Restrict log-time lookups to a date range |
| `USE_NEW_COMMON_CORE_ONLY` | `main.py` | Filter to the new common-core Python modules only |
| `NEW_COMMON_CORE_PYTHON_MODULES` | `data_processor.py` | The list of module slugs used by the filter above |
| `python_keywords` | `data_processor.py` | Keywords used to detect "Python" projects |

## Cache management

Cached API responses live in `.cache/` (git-ignored). Manage it with:

```bash
python cache_util.py stats     # show cache statistics
python cache_util.py clear     # clear all cached data
python cache_util.py validate  # check cache integrity
python cache_util.py test      # test the API connection
```

Pass `use_cache=False` or a custom `cache_ttl_hours` when constructing `API42Client` in `main.py` to change caching behavior.

## Project structure

```
main.py                  # entry point
api_client.py            # 42 API client with caching
cache_manager.py         # cache implementation
cache_util.py            # cache management CLI
data_processor.py        # time calculation & filtering logic
dashboard/               # modular dashboard template (HTML/CSS/JS per chart group)
test_*.py                # unit tests
requirements.txt
.env.example
```

## Limitations

Time-spent figures are an approximation based on campus log time overlapping a project's active window — they can be thrown off by multitasking, breaks, or work done outside the tracked campus.
