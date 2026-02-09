"""
Test script for the Python Time Tracker
Tests basic functionality without requiring API credentials
"""

from datetime import datetime, timedelta
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
    print(f"  ✓ Found {len(python_projects)} Python projects")
    for p in python_projects:
        print(f"    - {p['project']['name']}")


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
    
    from datetime import timezone
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
