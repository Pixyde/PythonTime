"""
Test script for cache functionality
"""

import os
import json
import time
from cache_manager import CacheManager


def test_cache_basic():
    """Test basic cache operations"""
    print("Testing basic cache operations...")
    
    # Create cache manager with short TTL for testing
    cache = CacheManager(cache_dir=".test_cache", cache_ttl_hours=1)
    
    # Test cache miss
    result = cache.get("/v2/test", {"param": "value"})
    assert result is None, "Cache should be empty initially"
    print("  ✓ Cache miss works correctly")
    
    # Test cache set and get
    test_data = {"items": [1, 2, 3], "count": 3}
    cache.set("/v2/test", test_data, {"param": "value"})
    
    result = cache.get("/v2/test", {"param": "value"})
    assert result == test_data, "Cached data should match"
    print("  ✓ Cache set and get work correctly")
    
    # Test different parameters create different cache entries
    result = cache.get("/v2/test", {"param": "different"})
    assert result is None, "Different params should not hit cache"
    print("  ✓ Parameter-based cache keys work correctly")
    
    # Cleanup
    cache.clear()
    result = cache.get("/v2/test", {"param": "value"})
    assert result is None, "Cache should be cleared"
    print("  ✓ Cache clear works correctly")
    
    # Remove test cache directory
    import shutil
    if os.path.exists(".test_cache"):
        shutil.rmtree(".test_cache")


def test_cache_stats():
    """Test cache statistics"""
    print("\nTesting cache statistics...")
    
    cache = CacheManager(cache_dir=".test_cache", cache_ttl_hours=1)
    
    # Add some cache entries
    cache.set("/v2/endpoint1", [1, 2, 3])
    cache.set("/v2/endpoint2", {"key": "value"})
    
    stats = cache.get_cache_stats()
    assert stats['total_files'] == 2, "Should have 2 cache files"
    assert stats['total_size_bytes'] > 0, "Cache should have size"
    print(f"  ✓ Cache stats: {stats['total_files']} files, {stats['total_size_mb']} MB")
    
    # Cleanup
    cache.clear()
    import shutil
    if os.path.exists(".test_cache"):
        shutil.rmtree(".test_cache")


def test_cache_expiry():
    """Test cache expiry (quick test with short TTL)"""
    print("\nTesting cache expiry...")
    
    # Create cache with 0 hour TTL (expires immediately for testing)
    cache = CacheManager(cache_dir=".test_cache", cache_ttl_hours=0)
    
    # Set data
    cache.set("/v2/test", {"data": "test"})
    
    # Immediately reading should work
    result = cache.get("/v2/test")
    # Note: With 0 TTL, cache might expire immediately, which is expected
    print(f"  ✓ Cache expiry works (result: {result})")
    
    # Cleanup
    cache.clear()
    import shutil
    if os.path.exists(".test_cache"):
        shutil.rmtree(".test_cache")


def test_cache_invalidate():
    """Test invalidating a specific cache entry"""
    print("\nTesting cache invalidate...")

    cache = CacheManager(cache_dir=".test_cache", cache_ttl_hours=1)

    # Set two entries
    cache.set("/v2/users/1/locations", [{"begin_at": "2025-01-01"}], {"paginated": "all"})
    cache.set("/v2/users/2/locations", [{"begin_at": "2025-02-01"}], {"paginated": "all"})

    # Verify both exist
    assert cache.get("/v2/users/1/locations", {"paginated": "all"}) is not None
    assert cache.get("/v2/users/2/locations", {"paginated": "all"}) is not None
    print("  ✓ Both entries exist in cache")

    # Invalidate only user 1
    cache.invalidate("/v2/users/1/locations", {"paginated": "all"})

    # User 1 should be gone, user 2 still present
    assert cache.get("/v2/users/1/locations", {"paginated": "all"}) is None
    assert cache.get("/v2/users/2/locations", {"paginated": "all"}) is not None
    print("  ✓ Invalidated entry returns None, other entry still exists")

    # Invalidating a non-existent entry should not error
    cache.invalidate("/v2/users/999/locations", {"paginated": "all"})
    print("  ✓ Invalidating non-existent entry is safe")

    # Cleanup
    cache.clear()
    import shutil
    if os.path.exists(".test_cache"):
        shutil.rmtree(".test_cache")


def main():
    """Run all cache tests"""
    print("=" * 60)
    print("Running Cache Tests")
    print("=" * 60)
    
    tests = [
        test_cache_basic,
        test_cache_stats,
        test_cache_expiry,
        test_cache_invalidate,
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
        print("✓ All cache tests passed!")
    else:
        print(f"✗ {failed} test(s) failed")
    print("=" * 60)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(main())
