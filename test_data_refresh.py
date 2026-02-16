"""
Test script for cache timestamp, data refresh prompt, and concurrent fetching
"""

import os
import json
import shutil
from unittest.mock import patch, MagicMock
from cache_manager import CacheManager
from api_client import API42Client


def test_cache_timestamp():
    """Test get_cache_timestamp returns the correct timestamp"""
    print("Testing cache timestamp retrieval...")

    cache = CacheManager(cache_dir=".test_cache", cache_ttl_hours=1)

    # No cache entry yet
    ts = cache.get_cache_timestamp("/v2/campus", {'paginated': 'all'})
    assert ts is None, "Should return None for missing entry"
    print("  ✓ Returns None for missing cache entry")

    # Set a cache entry
    cache.set("/v2/campus", [{"id": 1}], {'paginated': 'all'})
    ts = cache.get_cache_timestamp("/v2/campus", {'paginated': 'all'})
    assert ts is not None, "Should return a timestamp"
    assert 'T' in ts, f"Should be ISO format, got: {ts}"
    print(f"  ✓ Returns timestamp: {ts}")

    # Different params = different entry
    ts2 = cache.get_cache_timestamp("/v2/campus", {'paginated': 'all', 'extra': 'param'})
    assert ts2 is None, "Different params should return None"
    print("  ✓ Different params returns None")

    # Cleanup
    cache.clear()
    if os.path.exists(".test_cache"):
        shutil.rmtree(".test_cache")


def test_data_freshness():
    """Test get_data_freshness returns timestamps for all categories"""
    print("\nTesting data freshness...")

    client = API42Client("id1", "s1", use_cache=True, cache_ttl_hours=1)

    # Populate some cache entries
    client.cache.set("/v2/campus", [{"id": 1}], {'paginated': 'all'})
    client.cache.set("/v2/cursus/21/projects", [{"id": 100}], {'paginated': 'all'})
    client.cache.set("/v2/projects/42/projects_users", [{"id": 1}], {'paginated': 'all'})
    client.cache.set("/v2/users/123/locations", [{"begin_at": "2025-01-01"}], {'paginated': 'all'})

    freshness = client.get_data_freshness(campus_id=None, cursus_id=21)
    assert 'Campuses' in freshness
    assert 'Cursus Projects' in freshness
    assert 'Project Users' in freshness
    assert 'User Locations' in freshness
    assert freshness['Campuses'] is not None
    assert freshness['Cursus Projects'] is not None
    assert freshness['Project Users'] is not None
    assert freshness['User Locations'] is not None
    print(f"  ✓ Campuses timestamp: {freshness['Campuses']}")
    print(f"  ✓ Projects timestamp: {freshness['Cursus Projects']}")
    print(f"  ✓ Project Users timestamp: {freshness['Project Users']}")
    print(f"  ✓ User Locations timestamp: {freshness['User Locations']}")

    # With campus_id, should also include Campus Users
    freshness2 = client.get_data_freshness(campus_id=42, cursus_id=21, begin_year=2025)
    assert 'Campus Users' in freshness2
    assert freshness2['Campus Users'] is None  # Not cached yet
    print("  ✓ Campus Users present but None (not cached)")

    # Cleanup
    client.cache.clear()
    shutil.rmtree(".cache", ignore_errors=True)


def test_data_freshness_no_cache():
    """Test get_data_freshness with caching disabled"""
    print("\nTesting data freshness without cache...")

    client = API42Client("id1", "s1", use_cache=False)
    freshness = client.get_data_freshness()
    assert freshness == {}, "Should return empty dict when no cache"
    print("  ✓ Returns empty dict when caching disabled")


def test_format_timestamp():
    """Test _format_timestamp helper"""
    print("\nTesting timestamp formatting...")

    from main import _format_timestamp
    from datetime import datetime, timedelta

    # Recent timestamp
    recent = (datetime.now() - timedelta(minutes=30)).isoformat()
    formatted = _format_timestamp(recent)
    assert 'ago' in formatted
    assert '30m' in formatted or '29m' in formatted or '31m' in formatted
    print(f"  ✓ Recent: {formatted}")

    # Hours ago
    hours_ago = (datetime.now() - timedelta(hours=5)).isoformat()
    formatted = _format_timestamp(hours_ago)
    assert 'h ago' in formatted
    print(f"  ✓ Hours ago: {formatted}")

    # Days ago
    days_ago = (datetime.now() - timedelta(days=3)).isoformat()
    formatted = _format_timestamp(days_ago)
    assert 'd ago' in formatted
    print(f"  ✓ Days ago: {formatted}")


def test_prompt_data_refresh_none():
    """Test prompt_data_refresh with 'none' selection"""
    print("\nTesting refresh prompt with 'none' input...")

    from main import prompt_data_refresh

    client = API42Client("id1", "s1", use_cache=True, cache_ttl_hours=1)
    client.cache.set("/v2/campus", [{"id": 1}], {'paginated': 'all'})

    with patch('builtins.input', return_value=''):
        refreshed = prompt_data_refresh(client)
    assert refreshed == [], "Should return empty list for empty input"
    print("  ✓ Empty input keeps cached data")

    with patch('builtins.input', return_value='none'):
        refreshed = prompt_data_refresh(client)
    assert refreshed == [], "Should return empty list for 'none'"
    print("  ✓ 'none' keeps cached data")

    # Cleanup
    client.cache.clear()
    shutil.rmtree(".cache", ignore_errors=True)


def test_prompt_data_refresh_all():
    """Test prompt_data_refresh with 'all' selection"""
    print("\nTesting refresh prompt with 'all' input...")

    from main import prompt_data_refresh

    client = API42Client("id1", "s1", use_cache=True, cache_ttl_hours=1)
    client.cache.set("/v2/campus", [{"id": 1}], {'paginated': 'all'})
    client.cache.set("/v2/cursus/21/projects", [{"id": 100}], {'paginated': 'all'})

    with patch('builtins.input', return_value='all'):
        refreshed = prompt_data_refresh(client)

    # All categories should be refreshed
    assert len(refreshed) > 0, "Should have refreshed some categories"
    print(f"  ✓ Refreshed {len(refreshed)} categories: {refreshed}")

    # Cache should be cleared
    assert client.cache.get("/v2/campus", {'paginated': 'all'}) is None
    print("  ✓ Cache cleared after 'all'")

    # Cleanup
    client.cache.clear()
    shutil.rmtree(".cache", ignore_errors=True)


def test_prompt_data_refresh_specific():
    """Test prompt_data_refresh with specific selection"""
    print("\nTesting refresh prompt with specific selection...")

    from main import prompt_data_refresh

    client = API42Client("id1", "s1", use_cache=True, cache_ttl_hours=1)
    client.cache.set("/v2/campus", [{"id": 1}], {'paginated': 'all'})
    client.cache.set("/v2/cursus/21/projects", [{"id": 100}], {'paginated': 'all'})

    # Mock refresh_campuses to avoid real API call
    with patch.object(client, 'refresh_campuses') as mock_refresh:
        with patch('builtins.input', return_value='1'):
            refreshed = prompt_data_refresh(client)

    assert 'Campuses' in refreshed
    mock_refresh.assert_called_once()
    print(f"  ✓ Refreshed specific category: {refreshed}")

    # Cleanup
    client.cache.clear()
    shutil.rmtree(".cache", ignore_errors=True)


def test_prompt_data_refresh_no_cache():
    """Test prompt_data_refresh when no cache exists"""
    print("\nTesting refresh prompt with no cache...")

    from main import prompt_data_refresh

    client = API42Client("id1", "s1", use_cache=True, cache_ttl_hours=1)

    # Don't populate any cache — freshness will show all as "Not cached"
    # User presses Enter to skip
    with patch('builtins.input', return_value=''):
        refreshed = prompt_data_refresh(client)
    assert refreshed == [], "Should return empty when user skips"
    print("  ✓ Returns empty when user skips on uncached data")

    # Cleanup
    shutil.rmtree(".cache", ignore_errors=True)


def test_concurrent_locations_fetch():
    """Test that concurrent location fetching works correctly"""
    print("\nTesting concurrent location fetching...")

    client = API42Client("id1", "s1", use_cache=False)

    # Mock get_user_locations to return deterministic data
    def mock_locations(user_id, begin_at=None, end_at=None):
        return [{"user_id": user_id, "begin_at": "2025-01-01"}]

    with patch.object(client, 'get_user_locations', side_effect=mock_locations):
        result = client.get_locations_by_user_map([1, 2, 3])

    assert len(result) == 3
    assert result[1] == [{"user_id": 1, "begin_at": "2025-01-01"}]
    assert result[2] == [{"user_id": 2, "begin_at": "2025-01-01"}]
    assert result[3] == [{"user_id": 3, "begin_at": "2025-01-01"}]
    print("  ✓ Concurrent fetch returned correct data for all users")


def test_concurrent_projects_fetch():
    """Test that concurrent project fetching works correctly"""
    print("\nTesting concurrent project fetching...")

    client = API42Client("id1", "s1", use_cache=False)

    # Mock get_user_projects to return deterministic data
    def mock_projects(user_id):
        return [{"user_id": user_id, "project": "test"}]

    with patch.object(client, 'get_user_projects', side_effect=mock_projects):
        result = client.get_projects_users_by_user_map([10, 20, 30])

    assert len(result) == 3
    assert result[10] == [{"user_id": 10, "project": "test"}]
    assert result[20] == [{"user_id": 20, "project": "test"}]
    assert result[30] == [{"user_id": 30, "project": "test"}]
    print("  ✓ Concurrent fetch returned correct project data for all users")


def test_oldest_matching_timestamp():
    """Test get_oldest_matching_timestamp scans cache files by endpoint prefix"""
    print("\nTesting oldest matching timestamp...")

    cache = CacheManager(cache_dir=".test_cache", cache_ttl_hours=1)

    # No entries yet
    ts = cache.get_oldest_matching_timestamp("/v2/projects/")
    assert ts is None, "Should return None when no matches"
    print("  ✓ Returns None when no matches")

    # Add two project-user entries with different timestamps
    cache.set("/v2/projects/42/projects_users", [{"id": 1}], {'paginated': 'all'})
    import time as _time
    _time.sleep(0.05)  # ensure different timestamp
    cache.set("/v2/projects/99/projects_users", [{"id": 2}], {'paginated': 'all'})

    ts = cache.get_oldest_matching_timestamp("/v2/projects/")
    assert ts is not None
    # The oldest should be the first one we set
    ts42 = cache.get_cache_timestamp("/v2/projects/42/projects_users", {'paginated': 'all'})
    assert ts == ts42, f"Should return oldest: {ts} vs {ts42}"
    print(f"  ✓ Returns oldest timestamp: {ts}")

    # Non-matching prefix
    ts_none = cache.get_oldest_matching_timestamp("/v2/nonexistent/")
    assert ts_none is None
    print("  ✓ Non-matching prefix returns None")

    # Cleanup
    cache.clear()
    if os.path.exists(".test_cache"):
        shutil.rmtree(".test_cache")


def test_invalidate_matching():
    """Test invalidate_matching removes all cache files for a prefix"""
    print("\nTesting invalidate matching...")

    cache = CacheManager(cache_dir=".test_cache", cache_ttl_hours=1)

    # Add entries with different prefixes
    cache.set("/v2/projects/42/projects_users", [{"id": 1}], {'paginated': 'all'})
    cache.set("/v2/projects/99/projects_users", [{"id": 2}], {'paginated': 'all'})
    cache.set("/v2/users/123/locations", [{"begin_at": "x"}], {'paginated': 'all'})
    cache.set("/v2/campus", [{"id": 1}], {'paginated': 'all'})

    # Invalidate project entries
    cache.invalidate_matching("/v2/projects/")

    # Project entries should be gone
    assert cache.get("/v2/projects/42/projects_users", {'paginated': 'all'}) is None
    assert cache.get("/v2/projects/99/projects_users", {'paginated': 'all'}) is None
    print("  ✓ Project entries invalidated")

    # Other entries should remain
    assert cache.get("/v2/users/123/locations", {'paginated': 'all'}) is not None
    assert cache.get("/v2/campus", {'paginated': 'all'}) is not None
    print("  ✓ Unrelated entries preserved")

    # Cleanup
    cache.clear()
    if os.path.exists(".test_cache"):
        shutil.rmtree(".test_cache")


def test_prompt_refresh_project_users():
    """Test refreshing 'Project Users' category invalidates project caches"""
    print("\nTesting refresh of Project Users category...")

    from main import prompt_data_refresh

    client = API42Client("id1", "s1", use_cache=True, cache_ttl_hours=1)

    # Populate project-user cache entries
    client.cache.set("/v2/projects/42/projects_users", [{"id": 1}], {'paginated': 'all'})
    client.cache.set("/v2/projects/99/projects_users", [{"id": 2}], {'paginated': 'all'})
    client.cache.set("/v2/campus", [{"id": 1}], {'paginated': 'all'})

    # Find which index 'Project Users' is
    freshness = client.get_data_freshness()
    categories = list(freshness.keys())
    idx = categories.index('Project Users') + 1

    with patch('builtins.input', return_value=str(idx)):
        refreshed = prompt_data_refresh(client)

    assert 'Project Users' in refreshed
    assert client.cache.get("/v2/projects/42/projects_users", {'paginated': 'all'}) is None
    assert client.cache.get("/v2/projects/99/projects_users", {'paginated': 'all'}) is None
    # Campus should be untouched
    assert client.cache.get("/v2/campus", {'paginated': 'all'}) is not None
    print("  ✓ Project Users refresh invalidated project caches only")

    # Cleanup
    client.cache.clear()
    shutil.rmtree(".cache", ignore_errors=True)


def test_prompt_refresh_user_locations():
    """Test refreshing 'User Locations' category invalidates location caches"""
    print("\nTesting refresh of User Locations category...")

    from main import prompt_data_refresh

    client = API42Client("id1", "s1", use_cache=True, cache_ttl_hours=1)

    # Populate user location cache entries
    client.cache.set("/v2/users/123/locations", [{"begin_at": "x"}], {'paginated': 'all'})
    client.cache.set("/v2/users/456/locations", [{"begin_at": "y"}], {'paginated': 'all'})
    client.cache.set("/v2/campus", [{"id": 1}], {'paginated': 'all'})

    # Find which index 'User Locations' is
    freshness = client.get_data_freshness()
    categories = list(freshness.keys())
    idx = categories.index('User Locations') + 1

    with patch('builtins.input', return_value=str(idx)):
        refreshed = prompt_data_refresh(client)

    assert 'User Locations' in refreshed
    assert client.cache.get("/v2/users/123/locations", {'paginated': 'all'}) is None
    assert client.cache.get("/v2/users/456/locations", {'paginated': 'all'}) is None
    # Campus should be untouched
    assert client.cache.get("/v2/campus", {'paginated': 'all'}) is not None
    print("  ✓ User Locations refresh invalidated location caches only")

    # Cleanup
    client.cache.clear()
    shutil.rmtree(".cache", ignore_errors=True)


def main():
    """Run all tests"""
    print("=" * 60)
    print("Running Data Refresh & Concurrent Fetch Tests")
    print("=" * 60)

    tests = [
        test_cache_timestamp,
        test_data_freshness,
        test_data_freshness_no_cache,
        test_format_timestamp,
        test_prompt_data_refresh_none,
        test_prompt_data_refresh_all,
        test_prompt_data_refresh_specific,
        test_prompt_data_refresh_no_cache,
        test_concurrent_locations_fetch,
        test_concurrent_projects_fetch,
        test_oldest_matching_timestamp,
        test_invalidate_matching,
        test_prompt_refresh_project_users,
        test_prompt_refresh_user_locations,
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
        print("✓ All data refresh & concurrent tests passed!")
    else:
        print(f"✗ {failed} test(s) failed")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(main())
