#!/usr/bin/env python3
"""
Final comprehensive verification of the Python Time Tracker Dashboard
"""

import json
import os
from datetime import datetime

def test_dashboard_generation():
    """Test complete dashboard generation flow"""
    
    print("="*70)
    print(" FINAL COMPREHENSIVE VERIFICATION ".center(70, "="))
    print("="*70)
    
    # Test 1: Template exists and is readable
    print("\n[1/6] Checking template file...")
    try:
        with open('dashboard_template.html', 'r') as f:
            template = f.read()
        print(f"  ✓ Template loaded: {len(template):,} bytes")
        assert len(template) > 1000, "Template too small"
        assert '{{DATA_PLACEHOLDER}}' in template, "Placeholder missing"
        print("  ✓ Placeholder found")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False
    
    # Test 2: Create realistic test data
    print("\n[2/6] Creating test data...")
    test_data = [
        {
            'user_id': 12345,
            'login': 'john_doe',
            'python_projects': [
                {
                    'project_id': 2690,
                    'project_name': 'Python Module 00',
                    'status': 'finished',
                    'validated?': True,
                    'final_mark': 95,
                    'time_spent_hours': 15.5,
                    'created_at': '2024-01-15T10:00:00Z',
                    'updated_at': '2024-01-20T16:00:00Z'
                },
                {
                    'project_id': 2691,
                    'project_name': 'Python Module 01',
                    'status': 'in_progress',
                    'validated?': False,
                    'final_mark': 0,
                    'time_spent_hours': 8.2,
                    'created_at': '2024-01-22T10:00:00Z',
                    'updated_at': '2024-02-09T16:00:00Z'
                }
            ]
        },
        {
            'user_id': 23456,
            'login': 'alice_smith',
            'python_projects': [
                {
                    'project_id': 2690,
                    'project_name': 'Python Module 00',
                    'status': 'finished',
                    'validated?': True,
                    'final_mark': 88,
                    'time_spent_hours': 22.0,
                    'created_at': '2024-01-16T10:00:00Z',
                    'updated_at': '2024-01-23T16:00:00Z'
                },
                {
                    'project_id': 2692,
                    'project_name': 'Python Module 02',
                    'status': 'finished',
                    'validated?': True,
                    'final_mark': 75,
                    'time_spent_hours': 18.5,
                    'created_at': '2024-01-24T10:00:00Z',
                    'updated_at': '2024-02-05T16:00:00Z'
                }
            ]
        },
        {
            'user_id': 34567,
            'login': 'bob_jones',
            'python_projects': [
                {
                    'project_id': 2690,
                    'project_name': 'Python Module 00',
                    'status': 'waiting_for_correction',
                    'validated?': False,
                    'final_mark': 0,
                    'time_spent_hours': 12.0,
                    'created_at': '2024-02-01T10:00:00Z',
                    'updated_at': '2024-02-09T16:00:00Z'
                }
            ]
        }
    ]
    
    total_projects = sum(len(u['python_projects']) for u in test_data)
    print(f"  ✓ Created {len(test_data)} users with {total_projects} projects")
    
    # Test 3: Generate dashboard
    print("\n[3/6] Generating dashboard...")
    try:
        dashboard_html = template.replace('{{DATA_PLACEHOLDER}}', json.dumps(test_data))
        print(f"  ✓ Dashboard generated: {len(dashboard_html):,} bytes")
        
        # Verify no placeholder remains
        assert '{{DATA_PLACEHOLDER}}' not in dashboard_html, "Placeholder not replaced"
        print("  ✓ Placeholder replaced")
        
        # Verify data is in HTML
        assert 'john_doe' in dashboard_html, "User data missing"
        assert 'Python Module 00' in dashboard_html, "Project data missing"
        print("  ✓ Data injected correctly")
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False
    
    # Test 4: Verify HTML structure
    print("\n[4/6] Verifying HTML structure...")
    checks = [
        ('Chart.js library', 'chart.js' in dashboard_html.lower()),
        ('CSS styling', '<style>' in dashboard_html),
        ('Grafana colors', '#0b0c0e' in dashboard_html),
        ('JavaScript code', '<script>' in dashboard_html),
        ('Filter elements', 'filter-modules' in dashboard_html),
        ('Chart containers', 'top-performers' in dashboard_html),
        ('Statistics cards', 'kpi-total-users' in dashboard_html),
        ('Data table', 'data-table' in dashboard_html),
    ]
    
    all_passed = True
    for name, result in checks:
        status = "✓" if result else "✗"
        print(f"  {status} {name}")
        if not result:
            all_passed = False
    
    if not all_passed:
        print("  ✗ Some HTML structure checks failed")
        return False
    
    # Test 5: Verify JavaScript functions
    print("\n[5/6] Verifying JavaScript functions...")
    critical_functions = [
        'transformData',
        'applyFilters',
        'createTopUsersChart',
        'createModuleTimesChart',
        'createStatusChart',
        'createDistributionChart',
        'updateStats',
        'updateTable',
    ]
    
    for func in critical_functions:
        if func not in dashboard_html:
            print(f"  ✗ Missing function: {func}")
            return False
    print(f"  ✓ All {len(critical_functions)} critical functions present")
    
    # Test 6: Save and verify output
    print("\n[6/6] Saving output files...")
    try:
        output_filename = f'dashboard_final_verified_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
        with open(output_filename, 'w') as f:
            f.write(dashboard_html)
        
        file_size = os.path.getsize(output_filename)
        print(f"  ✓ Saved: {output_filename}")
        print(f"  ✓ File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        
        # Verify file is readable
        with open(output_filename, 'r') as f:
            verify = f.read()
        assert len(verify) == len(dashboard_html), "File write/read mismatch"
        print(f"  ✓ File verified readable")
        
    except Exception as e:
        print(f"  ✗ Error saving file: {e}")
        return False
    
    # Success summary
    print("\n" + "="*70)
    print(" SUCCESS! ".center(70, "="))
    print("="*70)
    print("\n📊 Dashboard Summary:")
    print(f"  • Users: {len(test_data)}")
    print(f"  • Projects: {total_projects}")
    print(f"  • HTML size: {len(dashboard_html):,} bytes")
    print(f"  • Output file: {output_filename}")
    print(f"\n✓ Dashboard is WORKING and ready to use!")
    print(f"\n🌐 To view: open {output_filename} in your browser")
    print("="*70)
    
    return True

if __name__ == '__main__':
    import sys
    success = test_dashboard_generation()
    sys.exit(0 if success else 1)
