# Configuration Guide

This guide will help you configure the application to work with your specific 42 campus.

## Finding Your Campus ID

The application needs the correct Campus ID to fetch student data. Here's how to find it:

### Method 1: Check the 42 API Campus List

You can query the 42 API to get a list of all campuses and their IDs:

```bash
# Get an access token (replace with your credentials)
curl -X POST https://api.intra.42.fr/oauth/token \
  -d "grant_type=client_credentials" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET"

# Use the token to get campus list
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  https://api.intra.42.fr/v2/campus
```

This will return a JSON array with all campuses. Look for your campus and note its `id`.

### Method 2: Use Python to Find Campus IDs

Create a simple Python script to list all campuses:

```python
import requests

# Replace with your credentials
CLIENT_ID = "your_client_id"
CLIENT_SECRET = "your_client_secret"

# Get token
token_response = requests.post(
    "https://api.intra.42.fr/oauth/token",
    data={
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
)
token = token_response.json()["access_token"]

# Get campuses
campuses_response = requests.get(
    "https://api.intra.42.fr/v2/campus",
    headers={"Authorization": f"Bearer {token}"}
)

# Display campuses
for campus in campuses_response.json():
    print(f"{campus['name']}: ID = {campus['id']}")
```

### Common Campus IDs

Here are some common campus IDs (may change):

- **Paris**: 1
- **Fremont**: 7
- **Lyon**: 6
- **Le Havre**: 14 (default in this app)
- **Nice**: 9
- **Brussels**: 12

## Configuring the Campus ID

Once you have your campus ID, update it in `main.py`:

```python
# Line ~27 in main.py
HAVRE_CAMPUS_ID = 14  # Change this to your campus ID
```

Or rename the constant to better reflect your campus:

```python
MY_CAMPUS_ID = 7  # For Fremont, for example
```

And update the references to use the new constant name.

## Understanding Cursus ID

The application also uses a Cursus ID. The main 42 cursus typically has ID `21`. This is usually correct for most campuses, but you can verify it:

```bash
# Get cursus list
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  https://api.intra.42.fr/v2/cursus
```

## Filtering for Promotion 4

The concept of "promotion" can vary by campus. To properly filter for promotion 4:

1. **Check the begin_at date**: Students who started in a specific date range
2. **Check the level**: Students within a specific level range
3. **Check custom fields**: Some campuses have specific fields for promotions

### Example: Filter by Begin Date

Edit the `get_all_students()` function in `main.py`:

```python
from datetime import datetime

def get_all_students(cursus_users: List[Dict]) -> List[Dict]:
    students = []
    
    # Define promotion 4 date range (adjust to your campus)
    promo4_start = datetime(2023, 9, 1)  # Example: Sept 2023
    promo4_end = datetime(2024, 8, 31)   # Example: Aug 2024
    
    for cursus_user in cursus_users:
        begin_at = cursus_user.get('begin_at')
        if begin_at:
            begin_date = datetime.fromisoformat(begin_at.replace('Z', '+00:00'))
            # Check if student started in promotion 4 timeframe
            if promo4_start <= begin_date <= promo4_end:
                user = cursus_user.get('user', {})
                if user:
                    students.append(cursus_user)
    
    return students
```

### Example: Filter by Level Range

```python
def get_all_students(cursus_users: List[Dict]) -> List[Dict]:
    students = []
    
    # Students in levels 4-6 might be promotion 4
    MIN_LEVEL = 4.0
    MAX_LEVEL = 7.0
    
    for cursus_user in cursus_users:
        level = cursus_user.get('level', 0)
        if MIN_LEVEL <= level <= MAX_LEVEL:
            user = cursus_user.get('user', {})
            if user:
                students.append(cursus_user)
    
    return students
```

## Testing Your Configuration

After configuring, test with a small subset first:

1. Limit the number of students processed initially:
   ```python
   # In main.py, after getting students
   students = students[:5]  # Process only first 5 students
   ```

2. Run the application:
   ```bash
   python main.py
   ```

3. Check the output to verify you're getting the correct students

4. Once confirmed, remove the limit and process all students

## Troubleshooting

### "No students found"

- Verify campus ID is correct
- Check that cursus ID (21) is correct for your campus
- Ensure your API credentials have proper permissions

### "Authentication failed"

- Double-check CLIENT_ID and CLIENT_SECRET in .env
- Ensure your OAuth application is active
- Try regenerating your credentials

### "Rate limit exceeded"

- Add delays between requests (already implemented)
- Reduce the number of students processed at once
- Contact 42 API support for rate limit increase if needed

## Advanced Configuration

### Custom Python Project Keywords

To detect additional Python projects, edit `data_processor.py`:

```python
# Line ~20
python_keywords = ['python', 'py', 'django', 'flask', 'ft_transcendence', 
                   'your-custom-keyword', 'another-keyword']
```

### Date Range for Log Times

To limit log time queries to specific dates:

```python
# In process_student() in main.py
locations = client.get_user_locations(
    user_id,
    begin_at="2024-01-01T00:00:00Z",
    end_at="2024-12-31T23:59:59Z"
)
```

This reduces API calls and focuses on a specific time period.

## Getting Help

If you need help with configuration:

1. Check the [42 API documentation](https://api.intra.42.fr/apidoc)
2. Consult your campus staff about promotion definitions
3. Test with the demo script first: `python demo.py`
4. Review the README.md for general usage information
