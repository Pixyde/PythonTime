import json
from datetime import datetime

# Create test data
test_data = [
    {
        "user_id": 123,
        "username": "jdoe",
        "projects": [
            {
                "project_name": "Python Module 00",
                "project_id": 2690,
                "status": "finished",
                "final_mark": 100,
                "total_hours": 15.5,
                "created_at": "2024-01-01T10:00:00Z",
                "marked_at": "2024-01-05T15:00:00Z"
            },
            {
                "project_name": "Python Module 01",
                "project_id": 2691,
                "status": "finished",
                "final_mark": 90,
                "total_hours": 20.3,
                "created_at": "2024-01-06T10:00:00Z",
                "marked_at": "2024-01-12T15:00:00Z"
            }
        ]
    },
    {
        "user_id": 456,
        "username": "asmith",
        "projects": [
            {
                "project_name": "Python Module 00",
                "project_id": 2690,
                "status": "finished",
                "final_mark": 85,
                "total_hours": 18.2,
                "created_at": "2024-01-02T10:00:00Z",
                "marked_at": "2024-01-08T15:00:00Z"
            }
        ]
    }
]

# Read template
with open('dashboard_template.html', 'r') as f:
    template = f.read()

# Replace placeholder
html = template.replace('{{DATA_PLACEHOLDER}}', json.dumps(test_data))

# Save
output_file = f'test_dashboard_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
with open(output_file, 'w') as f:
    f.write(html)

print(f"Generated: {output_file}")
print(f"Size: {len(html)} bytes")
print(f"Data injected: {len(json.dumps(test_data))} bytes")

# Verify data was injected
if '{{DATA_PLACEHOLDER}}' in html:
    print("ERROR: Placeholder not replaced!")
else:
    print("✓ Placeholder replaced successfully")

if 'let rawData = [' in html:
    print("✓ JavaScript data variable found")
else:
    print("ERROR: JavaScript data variable not found")
