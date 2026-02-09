import json
from datetime import datetime

# Create comprehensive test data
test_data = [
    {
        "user_id": 123,
        "login": "jdoe",
        "python_projects": [
            {
                "project_name": "Python Module 00",
                "project_id": 2690,
                "status": "finished",
                "final_mark": 100,
                "time_spent_hours": 15.5,
                "created_at": "2024-01-01T10:00:00Z",
                "marked_at": "2024-01-05T15:00:00Z"
            },
            {
                "project_name": "Python Module 01",
                "project_id": 2691,
                "status": "finished",
                "final_mark": 90,
                "time_spent_hours": 20.3,
                "created_at": "2024-01-06T10:00:00Z",
                "marked_at": "2024-01-12T15:00:00Z"
            }
        ],
        "total_python_hours": 35.8
    },
    {
        "user_id": 456,
        "login": "asmith",
        "python_projects": [
            {
                "project_name": "Python Module 00",
                "project_id": 2690,
                "status": "finished",
                "final_mark": 85,
                "time_spent_hours": 18.2,
                "created_at": "2024-01-02T10:00:00Z",
                "marked_at": "2024-01-08T15:00:00Z"
            },
            {
                "project_name": "Python Module 01",
                "project_id": 2691,
                "status": "in_progress",
                "final_mark": 0,
                "time_spent_hours": 12.1,
                "created_at": "2024-01-10T10:00:00Z",
                "marked_at": None
            }
        ],
        "total_python_hours": 30.3
    },
    {
        "user_id": 789,
        "login": "bmiller",
        "python_projects": [
            {
                "project_name": "Python Module 00",
                "project_id": 2690,
                "status": "finished",
                "final_mark": 95,
                "time_spent_hours": 22.7,
                "created_at": "2024-01-03T10:00:00Z",
                "marked_at": "2024-01-10T15:00:00Z"
            }
        ],
        "total_python_hours": 22.7
    }
]

# Read template
with open('dashboard_template.html', 'r') as f:
    template = f.read()

# Replace placeholder
html = template.replace('{{DATA_PLACEHOLDER}}', json.dumps(test_data))

# Save
output_file = f'grafana_dashboard_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
with open(output_file, 'w') as f:
    f.write(html)

print(f"✓ Generated: {output_file}")
print(f"✓ Size: {len(html)} bytes")
print(f"✓ Data: {len(test_data)} users, {sum(len(u['python_projects']) for u in test_data)} projects")

# Verify
if '{{DATA_PLACEHOLDER}}' in html:
    print("✗ ERROR: Placeholder not replaced!")
else:
    print("✓ Placeholder replaced successfully")

if 'let rawData = [' in html:
    print("✓ JavaScript data variable found")
else:
    print("✗ ERROR: JavaScript data variable not found")
