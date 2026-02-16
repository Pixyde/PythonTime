"""
Test script for ApiKeyManager and multi-key / refresh functionality
"""

import os
import json
import time
import shutil
import requests
from pathlib import Path
from unittest.mock import patch, MagicMock

from api_key_manager import ApiKeyManager
from api_client import API42Client


def test_single_key():
    """Test ApiKeyManager with a single key"""
    print("Testing single key...")

    mgr = ApiKeyManager([("id1", "secret1")], usage_file="/tmp/test_key_usage.json")

    idx, cid, csec = mgr.select_key()
    assert idx == 0
    assert cid == "id1"
    assert csec == "secret1"
    print("  ✓ Single key selected correctly")

    # Cleanup
    if os.path.exists("/tmp/test_key_usage.json"):
        os.remove("/tmp/test_key_usage.json")


def test_key_rotation():
    """Test that key rotation happens when a key is near its limit"""
    print("\nTesting key rotation...")

    mgr = ApiKeyManager(
        [("id1", "secret1"), ("id2", "secret2")],
        usage_file="/tmp/test_key_usage.json"
    )

    # Key 0 should be selected first (both at 0 requests)
    idx, _, _ = mgr.select_key()
    assert idx == 0, f"Expected key 0, got {idx}"
    print("  ✓ Key 0 selected initially")

    # Simulate key 0 having many requests (fill to limit)
    now = time.time()
    mgr.usage["0"] = [now] * 1200

    # Now key 1 should be selected
    idx, cid, _ = mgr.select_key()
    assert idx == 1, f"Expected key 1, got {idx}"
    assert cid == "id2"
    print("  ✓ Key 1 selected after key 0 hits limit")

    # Cleanup
    if os.path.exists("/tmp/test_key_usage.json"):
        os.remove("/tmp/test_key_usage.json")


def test_all_keys_exhausted():
    """Test RuntimeError when all keys are at their limit"""
    print("\nTesting all keys exhausted...")

    mgr = ApiKeyManager(
        [("id1", "secret1"), ("id2", "secret2")],
        usage_file="/tmp/test_key_usage.json"
    )

    now = time.time()
    mgr.usage["0"] = [now] * 1200
    mgr.usage["1"] = [now] * 1200

    try:
        mgr.select_key()
        assert False, "Should have raised RuntimeError"
    except RuntimeError as e:
        assert "rate limit" in str(e).lower()
        print("  ✓ RuntimeError raised when all keys exhausted")

    # Cleanup
    if os.path.exists("/tmp/test_key_usage.json"):
        os.remove("/tmp/test_key_usage.json")


def test_persistence():
    """Test that usage data persists across instances"""
    print("\nTesting persistence across restarts...")

    usage_file = "/tmp/test_key_persist.json"

    # Clean start
    if os.path.exists(usage_file):
        os.remove(usage_file)

    mgr1 = ApiKeyManager([("id1", "secret1")], usage_file=usage_file)
    mgr1.record_request(0)
    mgr1.record_request(0)
    mgr1.record_request(0)
    assert mgr1.get_request_count(0) == 3
    print("  ✓ Recorded 3 requests")

    # Create a new instance (simulates restart)
    mgr2 = ApiKeyManager([("id1", "secret1")], usage_file=usage_file)
    assert mgr2.get_request_count(0) == 3, f"Expected 3, got {mgr2.get_request_count(0)}"
    print("  ✓ 3 requests persisted across restart")

    # Cleanup
    if os.path.exists(usage_file):
        os.remove(usage_file)


def test_old_timestamps_pruned():
    """Test that timestamps older than 1 hour are pruned"""
    print("\nTesting timestamp pruning...")

    mgr = ApiKeyManager([("id1", "secret1")], usage_file="/tmp/test_key_prune.json")

    old = time.time() - 7200  # 2 hours ago
    recent = time.time() - 100  # 100 seconds ago
    mgr.usage["0"] = [old, old, recent]

    count = mgr.get_request_count(0)
    assert count == 1, f"Expected 1 recent request, got {count}"
    print("  ✓ Old timestamps pruned, only 1 recent request remains")

    # Cleanup
    if os.path.exists("/tmp/test_key_prune.json"):
        os.remove("/tmp/test_key_prune.json")


def test_usage_stats():
    """Test get_all_usage_stats"""
    print("\nTesting usage stats...")

    mgr = ApiKeyManager(
        [("id_aaaa1111", "s1"), ("id_bbbb2222", "s2")],
        usage_file="/tmp/test_key_stats.json"
    )
    mgr.record_request(0)
    mgr.record_request(0)
    mgr.record_request(1)

    stats = mgr.get_all_usage_stats()
    assert len(stats) == 2
    assert stats[0]['requests_last_hour'] == 2
    assert stats[0]['remaining'] == 1198
    assert stats[1]['requests_last_hour'] == 1
    assert stats[1]['remaining'] == 1199
    assert stats[0]['client_id_prefix'] == 'id_aaaa1...'
    print("  ✓ Usage stats correct")

    total = mgr.get_total_remaining()
    assert total == 1198 + 1199
    print(f"  ✓ Total remaining: {total}")

    # Cleanup
    if os.path.exists("/tmp/test_key_stats.json"):
        os.remove("/tmp/test_key_stats.json")


def test_no_keys_raises():
    """Test that providing no keys raises ValueError"""
    print("\nTesting no keys error...")

    try:
        ApiKeyManager([])
        assert False, "Should have raised ValueError"
    except ValueError:
        print("  ✓ ValueError raised for empty keys list")


def test_api_client_multi_key():
    """Test API42Client with multiple keys"""
    print("\nTesting API42Client with multi-key...")

    client = API42Client(keys=[("id1", "s1"), ("id2", "s2")], use_cache=False)
    assert len(client.key_manager.keys) == 2
    print("  ✓ Client initialized with 2 keys")

    # Test key_usage_stats
    stats = client.get_key_usage_stats()
    assert len(stats) == 2
    print("  ✓ Key usage stats available")


def test_api_client_backward_compat():
    """Test API42Client backward compatibility with single key"""
    print("\nTesting API42Client backward compatibility...")

    client = API42Client("id1", "secret1", use_cache=False)
    assert len(client.key_manager.keys) == 1
    print("  ✓ Backward compatible single-key mode works")


def test_refresh_methods_invalidate_cache():
    """Test that refresh methods invalidate cache before re-fetching"""
    print("\nTesting refresh methods invalidate cache...")

    client = API42Client("id1", "s1", use_cache=True, cache_ttl_hours=1)

    # Manually populate cache
    client.cache.set("/v2/campus", [{"id": 1, "name": "Test"}], {'paginated': 'all'})
    assert client.cache.get("/v2/campus", {'paginated': 'all'}) is not None
    print("  ✓ Cache populated")

    # Mock _make_paginated_request to avoid real API call
    with patch.object(client, '_make_paginated_request', return_value=[{"id": 2, "name": "Fresh"}]) as mock_req:
        result = client.refresh_campuses()
        # After refresh, cache for /v2/campus should have been invalidated first
        # The mock returns fresh data
        assert result == [{"id": 2, "name": "Fresh"}]
        mock_req.assert_called_once()
        print("  ✓ refresh_campuses invalidates cache and re-fetches")

    # Test refresh_all
    client.cache.set("/v2/test", {"data": 1})
    client.refresh_all()
    assert client.cache.get("/v2/test") is None
    print("  ✓ refresh_all clears entire cache")

    # Cleanup
    client.cache.clear()
    shutil.rmtree(".cache", ignore_errors=True)


def test_load_config_multi_key():
    """Test load_config supports multiple keys"""
    print("\nTesting load_config multi-key...")

    from main import load_config

    # Test with numbered keys
    with patch.dict(os.environ, {
        'CLIENT_ID_1': 'id1', 'CLIENT_SECRET_1': 's1',
        'CLIENT_ID_2': 'id2', 'CLIENT_SECRET_2': 's2',
    }, clear=False):
        keys = load_config()
        assert len(keys) == 2
        assert keys[0] == ('id1', 's1')
        assert keys[1] == ('id2', 's2')
        print("  ✓ Loaded 2 numbered key pairs")

    # Test fallback to single key
    with patch.dict(os.environ, {
        'CLIENT_ID': 'single_id', 'CLIENT_SECRET': 'single_secret',
    }, clear=True):
        keys = load_config()
        assert len(keys) == 1
        assert keys[0] == ('single_id', 'single_secret')
        print("  ✓ Loaded single key pair via fallback")


def test_ensure_authenticated_returns_snapshot():
    """Test that _ensure_authenticated returns a consistent token/key snapshot"""
    print("\nTesting _ensure_authenticated returns snapshot...")

    client = API42Client(keys=[("id1", "s1"), ("id2", "s2")], use_cache=False)
    # Isolate usage state
    client.key_manager.usage_file = Path("/tmp/test_snapshot.json")
    client.key_manager.usage = {}

    # Pre-set authentication state so _ensure_authenticated won't call real API
    client.access_token = "token_for_key0"
    client._active_key_idx = 0
    client.token_expires_at = time.time() + 7200
    client.key_manager.tokens[0] = {
        'access_token': 'token_for_key0',
        'expires_at': client.token_expires_at,
    }

    token, key_idx = client._ensure_authenticated()

    assert token == "token_for_key0", f"Expected token_for_key0, got {token}"
    assert key_idx == 0, f"Expected key 0, got {key_idx}"
    print("  ✓ _ensure_authenticated returns (token, key_idx) tuple")

    # Cleanup
    if os.path.exists("/tmp/test_snapshot.json"):
        os.remove("/tmp/test_snapshot.json")


def test_request_recorded_after_success_only():
    """Test that requests are only counted after a successful response"""
    print("\nTesting request recorded only after success...")

    client = API42Client(keys=[("id1", "s1")], use_cache=False)
    # Use a separate usage file for this test
    client.key_manager.usage_file = Path("/tmp/test_req_success.json")
    client.key_manager.usage = {}

    # Pre-set authentication state
    client.access_token = "test_token"
    client._active_key_idx = 0
    client.token_expires_at = time.time() + 7200
    client.key_manager.tokens[0] = {
        'access_token': 'test_token',
        'expires_at': client.token_expires_at,
    }

    # Mock a failed request (e.g. 429 rate limit)
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("429 Too Many Requests")

    with patch('requests.get', return_value=mock_response):
        result = client._make_request("/v2/test", use_cache=False)

    assert result is None, "Failed request should return None"
    count = client.key_manager.get_request_count(0)
    assert count == 0, f"Failed request should NOT be recorded, got count={count}"
    print("  ✓ Failed request not recorded against key quota")

    # Mock a successful request
    mock_response_ok = MagicMock()
    mock_response_ok.raise_for_status.return_value = None
    mock_response_ok.json.return_value = {"data": "test"}

    with patch('requests.get', return_value=mock_response_ok):
        result = client._make_request("/v2/test2", use_cache=False)

    assert result == {"data": "test"}, "Successful request should return data"
    count = client.key_manager.get_request_count(0)
    assert count == 1, f"Successful request should be recorded, got count={count}"
    print("  ✓ Successful request recorded against key quota")

    # Cleanup
    if os.path.exists("/tmp/test_req_success.json"):
        os.remove("/tmp/test_req_success.json")


def test_concurrent_requests_use_correct_key():
    """Test that concurrent requests record against the correct key"""
    print("\nTesting concurrent requests use correct key...")

    client = API42Client(keys=[("id1", "s1"), ("id2", "s2")], use_cache=False)
    # Use a separate usage file for this test
    client.key_manager.usage_file = Path("/tmp/test_concurrent_key.json")
    client.key_manager.usage = {}

    # Pre-set authentication state so _ensure_authenticated won't try real API
    client.access_token = "test_token"
    client._active_key_idx = 0
    client.token_expires_at = time.time() + 7200
    client.key_manager.tokens[0] = {
        'access_token': 'test_token',
        'expires_at': client.token_expires_at,
    }

    # Track which key each request was recorded against
    recorded_keys = []
    original_record = client.key_manager.record_request

    def tracking_record(key_idx):
        recorded_keys.append(key_idx)
        original_record(key_idx)

    client.key_manager.record_request = tracking_record

    # Mock both requests.get (for API calls) and authenticate (to prevent
    # real auth attempts when key rotation triggers re-authentication)
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = [{"id": 1}]

    def fake_authenticate():
        """Fake authenticate that just sets the token for the new key"""
        client.key_manager.tokens[client._active_key_idx] = {
            'access_token': f'token_key{client._active_key_idx}',
            'expires_at': time.time() + 7200,
        }
        client.access_token = f'token_key{client._active_key_idx}'
        client.token_expires_at = time.time() + 7200
        return True

    with patch('requests.get', return_value=mock_response), \
         patch.object(client, 'authenticate', side_effect=fake_authenticate):
        # Verify _ensure_authenticated returns a consistent snapshot
        token, key_idx = client._ensure_authenticated()
        assert token == "test_token"
        assert key_idx == 0
        print(f"  ✓ Got snapshot: key_idx={key_idx}")

        # Make a few requests — they should all use key 0 (with 0 usage)
        client._make_request("/v2/test1", use_cache=False)
        client._make_request("/v2/test2", use_cache=False)

    assert all(k == 0 for k in recorded_keys), f"All requests should use key 0, got {recorded_keys}"
    print(f"  ✓ All {len(recorded_keys)} requests recorded against correct key")

    # Cleanup
    if os.path.exists("/tmp/test_concurrent_key.json"):
        os.remove("/tmp/test_concurrent_key.json")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Running API Key Manager & Refresh Tests")
    print("=" * 60)

    tests = [
        test_single_key,
        test_key_rotation,
        test_all_keys_exhausted,
        test_persistence,
        test_old_timestamps_pruned,
        test_usage_stats,
        test_no_keys_raises,
        test_api_client_multi_key,
        test_api_client_backward_compat,
        test_refresh_methods_invalidate_cache,
        test_load_config_multi_key,
        test_ensure_authenticated_returns_snapshot,
        test_request_recorded_after_success_only,
        test_concurrent_requests_use_correct_key,
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
        print("✓ All API key manager tests passed!")
    else:
        print(f"✗ {failed} test(s) failed")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(main())
