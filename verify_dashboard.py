#!/usr/bin/env python3
"""Verify dashboard functionality"""

import json
import re

def verify_dashboard():
    """Verify dashboard template is properly set up"""
    
    print("="*60)
    print("DASHBOARD VERIFICATION")
    print("="*60)
    
    # Load template
    with open('dashboard_template.html', 'r') as f:
        template = f.read()
    
    checks = []
    
    # 1. Check placeholder exists
    has_placeholder = '{{DATA_PLACEHOLDER}}' in template
    checks.append(('Placeholder exists', has_placeholder))
    
    # 2. Check Plotly.js is loaded
    has_plotly = 'plotly' in template.lower() and 'cdn' in template.lower()
    checks.append(('Plotly.js CDN loaded', has_plotly))
    
    # 3. Check for key JavaScript functions
    has_transform = 'transformData' in template or 'filteredData' in template
    checks.append(('Data transformation function', has_transform))
    
    # 4. Check for chart rendering functions
    chart_functions = [
        'renderTopPerformers',
        'renderModuleStats',
        'updateGanttChart',
        'updateScatterChart'
    ]
    has_charts = any(func in template for func in chart_functions)
    checks.append(('Chart rendering functions', has_charts))
    
    # 5. Check for global filters
    has_filters = 'filter-users' in template and 'filter-modules' in template
    checks.append(('Global filters', has_filters))
    
    # 6. Check for tabs
    has_tabs = 'tab-overview' in template and 'switchTab' in template
    checks.append(('Tab navigation', has_tabs))
    
    # 7. Check for KPI cards
    has_kpis = 'kpi-total-users' in template and 'kpi-total-hours' in template
    checks.append(('KPI cards', has_kpis))
    
    # 8. Check CSS styling
    has_css = 'background' in template and '--bg-canvas' in template
    checks.append(('CSS styling', has_css))
    
    # 9. Check for Grafana-style colors
    has_grafana_theme = '#0b0c0e' in template or '#111217' in template
    checks.append(('Grafana theme colors', has_grafana_theme))
    
    # Print results
    print("\nVerification Results:")
    print("-"*60)
    
    all_passed = True
    for check_name, result in checks:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:10} | {check_name}")
        if not result:
            all_passed = False
    
    print("-"*60)
    print(f"\nTotal: {sum(1 for _, r in checks if r)}/{len(checks)} checks passed")
    
    # Test with sample data
    print("\n" + "="*60)
    print("DATA INJECTION TEST")
    print("="*60)
    
    test_data = [
        {
            'user_id': 1,
            'login': 'testuser',
            'python_projects': [
                {
                    'project_id': 1,
                    'project_name': 'Python Module 00',
                    'status': 'finished',
                    'validated?': True,
                    'final_mark': 85,
                    'time_spent_hours': 12.5,
                    'created_at': '2024-01-15T10:00:00Z',
                    'updated_at': '2024-01-20T16:00:00Z'
                }
            ]
        }
    ]
    
    try:
        dashboard = template.replace('{{DATA_PLACEHOLDER}}', json.dumps(test_data))
        
        # Verify data was injected
        has_data = 'testuser' in dashboard and '"project_name":"Python Module 00"' in dashboard
        print(f"\n{'✓' if has_data else '✗'} Data injection: {'SUCCESS' if has_data else 'FAILED'}")
        
        # Verify no placeholder remains
        no_placeholder = '{{DATA_PLACEHOLDER}}' not in dashboard
        print(f"{'✓' if no_placeholder else '✗'} Placeholder removed: {'SUCCESS' if no_placeholder else 'FAILED'}")
        
        # Check size
        size_kb = len(dashboard) / 1024
        print(f"✓ Generated size: {size_kb:.1f} KB")
        
        # Save test file
        with open('test_dashboard_final.html', 'w') as f:
            f.write(dashboard)
        print(f"✓ Saved test dashboard: test_dashboard_final.html")
        
        all_passed = all_passed and has_data and no_placeholder
        
    except Exception as e:
        print(f"✗ Error during data injection: {e}")
        all_passed = False
    
    # Final verdict
    print("\n" + "="*60)
    if all_passed:
        print("✓ ALL CHECKS PASSED - Dashboard is working!")
    else:
        print("✗ SOME CHECKS FAILED - Review issues above")
    print("="*60)
    
    return all_passed

if __name__ == '__main__':
    import sys
    success = verify_dashboard()
    sys.exit(0 if success else 1)
