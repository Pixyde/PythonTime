# 42 API Python Time Tracker

A Python application that uses the 42 API to gather and analyze time spent on Python modules by students at the Havre campus (promotion 4).

## Features

- 🔐 OAuth2 authentication with 42 API
- 👥 Fetches student data from specific campus and cursus
- 📊 Gathers Python module start and end dates
- ⏱️ Collects student log time data
- 📈 Calculates approximate time spent on each Python module
- 💾 Exports results to JSON format
- 🚀 **Optimized API requests** with caching and bulk fetching
- 💡 **Reduced API calls** by fetching all cursus users once and filtering locally

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

The application will:
1. Authenticate with the 42 API
2. Fetch all students from the main cursus (21) in a single bulk request
3. Filter students locally to those from the Havre campus (promotion 4)
4. Bulk fetch projects data for all students (with caching)
5. Bulk fetch log time data for all students (with caching)
6. For each student:
   - Filter to Python-related projects
   - Calculate time spent on each Python module
7. Save results to a JSON file with timestamp

## Output

The application generates a JSON file named `python_time_analysis_YYYYMMDD_HHMMSS.json` with the following structure:

```json
[
  {
    "user_id": 12345,
    "login": "student-login",
    "email": "student@example.com",
    "cursus_level": 5.42,
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

## How It Works

### Optimized API Request Strategy

The application is optimized to minimize API requests:

1. **Bulk Fetching**: Instead of fetching users campus-by-campus, it fetches all cursus users in one request
2. **Local Filtering**: Campus filtering is done locally on the fetched data, avoiding separate API calls
3. **Caching**: All API responses are cached in memory to avoid redundant requests
4. **Batch Processing**: Projects and locations are fetched for all users before processing

This approach reduces the number of API requests from `O(n * m)` to `O(n)`, where:
- `n` = number of students
- `m` = number of API calls per student (previously 2-3, now cached)

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
├── main.py              # Main application entry point
├── api_client.py        # 42 API client with authentication
├── data_processor.py    # Data processing and analysis logic
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

## API Rate Limiting

The application includes several features to be respectful of the 42 API:

- **Built-in rate limiting**: 0.1s delay between paginated requests
- **Request caching**: Responses are cached in memory to avoid duplicate requests
- **Bulk operations**: Multiple data points fetched together to minimize total requests

If you encounter rate limiting errors, you may need to add additional delays or contact 42 API support.

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

## License

This project is open source and available for educational purposes.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Acknowledgments

- Built for the 42 Network
- Uses the official 42 API (https://api.intra.42.fr)
