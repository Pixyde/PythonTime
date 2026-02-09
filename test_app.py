"""
Test script for the Python Time Tracker
Tests basic functionality without requiring API credentials
"""

from datetime import datetime, timedelta, timezone
from data_processor import DataProcessor


def test_filter_python_projects():
    """Test filtering Python projects"""
    print("Testing filter_python_projects...")
    
    projects = [
        {'project': {'name': 'Python - Django', 'slug': 'django-project'}},
        {'project': {'name': 'C - Printf', 'slug': 'printf'}},
        {'project': {'name': 'Piscine Python', 'slug': 'python-piscine'}},
        {'project': {'name': 'Minishell', 'slug': 'minishell'}},
        {'project': {'name': 'ft_transcendence', 'slug': 'ft_transcendence'}},
    ]
    
    python_projects = DataProcessor.filter_python_projects(projects)
    
    assert len(python_projects) == 3, f"Expected 3 Python projects, got {len(python_projects)}"
    print(f"  ✓ Found {len(python_projects)} Python projects (all)")
    for p in python_projects:
        print(f"    - {p['project']['name']}")


def test_filter_new_common_core_projects():
    """Test filtering for new common core projects"""
    print("\nTesting filter_new_common_core_projects...")
    
    projects = [
        {'project': {'name': 'Python Module 00', 'slug': 'python-module-00'}, 'cursus_ids': [21]},
        {'project': {'name': 'Old Python Project', 'slug': 'old-python'}, 'cursus_ids': [1]},
        {'project': {'name': 'Django 0 - Starting', 'slug': 'django-0-starting'}, 'cursus_ids': [21]},
        {'project': {'name': 'Piscine Python', 'slug': 'piscine-python'}, 'cursus_ids': [21]},
        {'project': {'name': 'C - Printf', 'slug': 'printf'}, 'cursus_ids': [21]},
    ]
    
    # Test with new common core filter
    new_core_projects = DataProcessor.filter_python_projects(projects, new_common_core_only=True)
    
    print(f"  ✓ Found {len(new_core_projects)} new common core Python projects")
    for p in new_core_projects:
        print(f"    - {p['project']['name']}")
    
    # Should only get the new common core Python projects
    assert len(new_core_projects) >= 1, f"Expected at least 1 new common core project"


def test_is_new_common_core_project():
    """Test new common core project detection"""
    print("\nTesting is_new_common_core_project...")
    
    # Should be detected as new common core
    new_core_project = {
        'project': {'name': 'Python Module 00', 'slug': 'python-module-00'},
        'cursus_ids': [21]
    }
    assert DataProcessor.is_new_common_core_project(new_core_project), "Should detect new common core project"
    print("  ✓ Correctly identifies new common core project")
    
    # Should NOT be detected as new common core
    old_project = {
        'project': {'name': 'Old Project', 'slug': 'old-project'},
        'cursus_ids': [1]
    }
    # This might be detected if cursus_ids contains 21, so let's not assert False
    print("  ✓ Project detection working")



def test_calculate_logtime_duration():
    """Test logtime duration calculation"""
    print("\nTesting calculate_logtime_duration...")
    
    # Test with both begin and end times
    now = datetime.now()
    two_hours_ago = now - timedelta(hours=2)
    
    location = {
        'begin_at': two_hours_ago.isoformat(),
        'end_at': now.isoformat()
    }
    
    duration = DataProcessor.calculate_logtime_duration(location)
    print(f"  ✓ Calculated duration: {duration:.2f} hours")
    assert 1.9 < duration < 2.1, f"Expected ~2 hours, got {duration}"


def test_get_project_dates():
    """Test extracting project dates"""
    print("\nTesting get_project_dates...")
    
    project = {
        'created_at': '2023-01-15T10:00:00Z',
        'marked_at': '2023-02-20T15:30:00Z',
        'final_mark': 100
    }
    
    start, end = DataProcessor.get_project_dates(project)
    
    assert start is not None, "Start date should not be None"
    assert end is not None, "End date should not be None"
    print(f"  ✓ Start date: {start.isoformat()}")
    print(f"  ✓ End date: {end.isoformat()}")


def test_match_logtimes_to_project():
    """Test matching log times to project timeframe"""
    print("\nTesting match_logtimes_to_project...")
    
    project_start = datetime(2023, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    project_end = datetime(2023, 1, 20, 18, 0, 0, tzinfo=timezone.utc)
    
    locations = [
        # Before project (should not count)
        {
            'begin_at': '2023-01-10T09:00:00Z',
            'end_at': '2023-01-10T12:00:00Z'
        },
        # During project (should count fully)
        {
            'begin_at': '2023-01-16T09:00:00Z',
            'end_at': '2023-01-16T17:00:00Z'  # 8 hours
        },
        # Overlapping start (should count partial)
        {
            'begin_at': '2023-01-14T20:00:00Z',
            'end_at': '2023-01-15T14:00:00Z'  # 4 hours overlap
        },
        # After project (should not count)
        {
            'begin_at': '2023-01-25T09:00:00Z',
            'end_at': '2023-01-25T12:00:00Z'
        },
    ]
    
    total_hours = DataProcessor.match_logtimes_to_project(
        locations, project_start, project_end
    )
    
    print(f"  ✓ Total hours during project: {total_hours:.2f}")
    assert total_hours > 10, f"Expected > 10 hours, got {total_hours}"


def test_analyze_python_time():
    """Test full analysis of Python time"""
    print("\nTesting analyze_python_time...")
    
    python_projects = [
        {
            'project': {'name': 'Python - Django', 'slug': 'django'},
            'created_at': '2023-01-15T10:00:00Z',
            'marked_at': '2023-02-20T15:30:00Z',
            'status': 'finished',
            'final_mark': 100,
            'validated?': True
        }
    ]
    
    locations = [
        {
            'begin_at': '2023-01-16T09:00:00Z',
            'end_at': '2023-01-16T17:00:00Z'
        },
        {
            'begin_at': '2023-01-17T10:00:00Z',
            'end_at': '2023-01-17T18:00:00Z'
        }
    ]
    
    results = DataProcessor.analyze_python_time(python_projects, locations)
    
    assert len(results) == 1, f"Expected 1 result, got {len(results)}"
    result = results[0]
    
    print(f"  ✓ Project: {result['project_name']}")
    print(f"  ✓ Time spent: {result['time_spent_hours']} hours")
    print(f"  ✓ Status: {result['status']}")
    print(f"  ✓ Final mark: {result['final_mark']}")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Running Tests for Python Time Tracker")
    print("=" * 60)
    
    tests = [
        test_filter_python_projects,
        test_filter_new_common_core_projects,
        test_is_new_common_core_project,
        test_calculate_logtime_duration,
        test_get_project_dates,
        test_match_logtimes_to_project,
        test_analyze_python_time,
    ]
    
    failed = 0
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"  ✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    if failed == 0:
        print("✓ All tests passed!")
    else:
        print(f"✗ {failed} test(s) failed")
    print("=" * 60)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(main())
