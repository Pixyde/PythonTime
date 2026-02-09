"""
Cache Manager Module
Handles caching of API responses to reduce redundant API calls
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Any, Optional, Dict
from pathlib import Path


class CacheManager:
    """Manages caching of API responses to disk"""
    
    def __init__(self, cache_dir: str = ".cache", cache_ttl_hours: int = 24):
        """
        Initialize cache manager
        
        Args:
            cache_dir: Directory to store cache files
            cache_ttl_hours: Cache time-to-live in hours (default: 24)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        
        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(exist_ok=True)
        
    def _get_cache_key(self, endpoint: str, params: Optional[Dict] = None) -> str:
        """
        Generate a unique cache key for an endpoint and parameters
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            Cache key string
        """
        # Create a string representation of the request
        params_str = json.dumps(params or {}, sort_keys=True)
        key_str = f"{endpoint}:{params_str}"
        
        # Hash it to create a valid filename
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get the file path for a cache key"""
        return self.cache_dir / f"{cache_key}.json"
    
    def _is_cache_valid(self, cache_path: Path) -> bool:
        """
        Check if cache file exists and is not expired
        
        Args:
            cache_path: Path to cache file
            
        Returns:
            True if cache is valid, False otherwise
        """
        if not cache_path.exists():
            return False
        
        # Check if cache has expired
        file_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
        age = datetime.now() - file_time
        
        return age < self.cache_ttl
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Any]:
        """
        Get cached data for an endpoint
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            Cached data if available and valid, None otherwise
        """
        cache_key = self._get_cache_key(endpoint, params)
        cache_path = self._get_cache_path(cache_key)
        
        if not self._is_cache_valid(cache_path):
            return None
        
        try:
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
                return cache_data.get('data')
        except (json.JSONDecodeError, IOError):
            # If cache file is corrupted, treat as cache miss
            return None
    
    def set(self, endpoint: str, data: Any, params: Optional[Dict] = None):
        """
        Cache data for an endpoint
        
        Args:
            endpoint: API endpoint
            data: Data to cache
            params: Query parameters
        """
        cache_key = self._get_cache_key(endpoint, params)
        cache_path = self._get_cache_path(cache_key)
        
        cache_data = {
            'endpoint': endpoint,
            'params': params,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        try:
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except IOError as e:
            # If we can't write cache, just log and continue
            print(f"Warning: Failed to write cache: {e}")
    
    def clear(self):
        """Clear all cached data"""
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
            except IOError:
                pass
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache
        
        Returns:
            Dictionary with cache statistics
        """
        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            'total_files': len(cache_files),
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'cache_dir': str(self.cache_dir)
        }
