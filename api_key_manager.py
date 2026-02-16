"""
API Key Manager Module
Manages multiple API keys with rate limiting and persistent usage tracking.
Each key can handle up to 1200 requests per hour.
Usage data persists across program restarts.
"""

import json
import time
from pathlib import Path
from typing import List, Tuple, Optional, Dict


class ApiKeyManager:
    """Manages multiple 42 API key pairs with rate limiting and rotation"""

    MAX_REQUESTS_PER_HOUR = 1200
    USAGE_FILE = ".api_key_usage.json"

    def __init__(self, keys: List[Tuple[str, str]], usage_file: str = None):
        """
        Initialize the API key manager.

        Args:
            keys: List of (client_id, client_secret) tuples
            usage_file: Path to the persistent usage file (default: .api_key_usage.json)
        """
        if not keys:
            raise ValueError("At least one API key pair is required")

        self.keys = keys
        self.usage_file = Path(usage_file or self.USAGE_FILE)
        # Map each key index to its OAuth access token and expiry
        self.tokens: Dict[int, dict] = {}
        # Load persisted usage data
        self.usage = self._load_usage()

    def _load_usage(self) -> Dict[str, list]:
        """
        Load usage data from disk.

        Returns:
            Dictionary mapping key index (as string) to list of request timestamps.
        """
        if self.usage_file.exists():
            try:
                with open(self.usage_file, 'r') as f:
                    data = json.load(f)
                # Prune timestamps older than 1 hour on load
                now = time.time()
                pruned = {}
                for key_idx, timestamps in data.items():
                    pruned[key_idx] = [t for t in timestamps if now - t < 3600]
                return pruned
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save_usage(self):
        """Save usage data to disk for persistence across restarts."""
        try:
            with open(self.usage_file, 'w') as f:
                json.dump(self.usage, f)
        except IOError as e:
            print(f"Warning: Failed to save API key usage: {e}")

    def _prune_old_timestamps(self, key_idx: int):
        """Remove timestamps older than 1 hour for a given key."""
        now = time.time()
        key = str(key_idx)
        if key in self.usage:
            self.usage[key] = [t for t in self.usage[key] if now - t < 3600]

    def get_request_count(self, key_idx: int) -> int:
        """
        Get the number of requests made with a key in the last hour.

        Args:
            key_idx: Index of the key

        Returns:
            Number of requests in the last hour
        """
        self._prune_old_timestamps(key_idx)
        return len(self.usage.get(str(key_idx), []))

    def record_request(self, key_idx: int):
        """
        Record a request for a key.

        Args:
            key_idx: Index of the key
        """
        key = str(key_idx)
        if key not in self.usage:
            self.usage[key] = []
        self.usage[key].append(time.time())
        self._save_usage()

    def select_key(self) -> Tuple[int, str, str]:
        """
        Select the best available API key (least used, under rate limit).

        Returns:
            Tuple of (key_index, client_id, client_secret)

        Raises:
            RuntimeError: If all keys have exceeded their rate limit
        """
        best_idx = None
        best_count = float('inf')

        for idx in range(len(self.keys)):
            count = self.get_request_count(idx)
            if count < self.MAX_REQUESTS_PER_HOUR and count < best_count:
                best_idx = idx
                best_count = count

        if best_idx is None:
            raise RuntimeError(
                "All API keys have reached the rate limit (1200 requests/hour). "
                "Please wait or add more API keys."
            )

        client_id, client_secret = self.keys[best_idx]
        return best_idx, client_id, client_secret

    def get_all_usage_stats(self) -> List[Dict]:
        """
        Get usage statistics for all keys.

        Returns:
            List of dicts with key index, requests in last hour, and remaining quota
        """
        stats = []
        for idx in range(len(self.keys)):
            count = self.get_request_count(idx)
            stats.append({
                'key_index': idx,
                'client_id_prefix': self.keys[idx][0][:8] + '...',
                'requests_last_hour': count,
                'remaining': self.MAX_REQUESTS_PER_HOUR - count,
            })
        return stats

    def get_total_remaining(self) -> int:
        """Get total remaining requests across all keys."""
        return sum(
            max(0, self.MAX_REQUESTS_PER_HOUR - self.get_request_count(idx))
            for idx in range(len(self.keys))
        )
