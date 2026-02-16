"""
42 API Client Module
Handles authentication and API requests to the 42 API
"""

import requests
import time
import os
import threading
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from cache_manager import CacheManager
from api_key_manager import ApiKeyManager


class API42Client:
    """Client for interacting with the 42 API"""
    
    BASE_URL = "https://api.intra.42.fr"
    TOKEN_REFRESH_BUFFER_SECONDS = 60  # Refresh token 60 seconds before expiry
    
    def __init__(self, client_id: str = None, client_secret: str = None, use_cache: bool = True, cache_ttl_hours: int = 24,
                 keys: List[Tuple[str, str]] = None):
        """
        Initialize the 42 API client
        
        Args:
            client_id: OAuth2 client ID (single-key mode, ignored when keys is provided)
            client_secret: OAuth2 client secret (single-key mode, ignored when keys is provided)
            use_cache: Whether to use caching (default: True)
            cache_ttl_hours: Cache time-to-live in hours (default: 24)
            keys: List of (client_id, client_secret) tuples for multi-key mode
        """
        if keys:
            self.key_manager = ApiKeyManager(keys)
        elif client_id and client_secret:
            self.key_manager = ApiKeyManager([(client_id, client_secret)])
        else:
            raise ValueError("Provide either (client_id, client_secret) or keys list")

        # Active key tracking
        self._active_key_idx = None
        self.client_id = None
        self.client_secret = None
        self.access_token = None
        self.token_expires_at = 0
        self.use_cache = use_cache
        self.cache = CacheManager(cache_ttl_hours=cache_ttl_hours) if use_cache else None
        self._auth_lock = threading.Lock()
        
    def authenticate(self) -> bool:
        """
        Authenticate with the 42 API using OAuth2.
        Uses the currently selected key from the key manager.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        # Select the best available key
        key_idx, client_id, client_secret = self.key_manager.select_key()
        self._active_key_idx = key_idx
        self.client_id = client_id
        self.client_secret = client_secret

        # Check if we already have a valid token for this key
        token_info = self.key_manager.tokens.get(key_idx)
        if token_info and time.time() < token_info['expires_at'] - self.TOKEN_REFRESH_BUFFER_SECONDS:
            self.access_token = token_info['access_token']
            self.token_expires_at = token_info['expires_at']
            return True

        url = f"{self.BASE_URL}/oauth/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 7200)
            self.token_expires_at = time.time() + expires_in
            
            # Store token for this key
            self.key_manager.tokens[key_idx] = {
                'access_token': self.access_token,
                'expires_at': self.token_expires_at,
            }
            
            print(f"✓ Successfully authenticated with 42 API (key {key_idx + 1}/{len(self.key_manager.keys)})")
            return True
        except requests.exceptions.RequestException as e:
            print(f"✗ Authentication failed: {e}")
            return False
    
    def _ensure_authenticated(self):
        """Ensure we have a valid access token, rotating keys as needed"""
        with self._auth_lock:
            key_idx, _, _ = self.key_manager.select_key()

            # If best key changed or token expired, re-authenticate
            if (key_idx != self._active_key_idx
                    or not self.access_token
                    or time.time() >= self.token_expires_at - self.TOKEN_REFRESH_BUFFER_SECONDS):
                self.authenticate()
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None, use_cache: bool = True) -> Optional[Dict]:
        """
        Make an authenticated request to the API
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters
            use_cache: Whether to use cache for this request (default: True)
            
        Returns:
            Response data as dictionary, or None if request failed
        """
        # Check cache first
        if use_cache and self.cache:
            cached_data = self.cache.get(endpoint, params)
            if cached_data is not None:
                return cached_data
        
        self._ensure_authenticated()
        
        url = f"{self.BASE_URL}{endpoint}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            # Record the request against the active key
            if self._active_key_idx is not None:
                self.key_manager.record_request(self._active_key_idx)
            response.raise_for_status()
            data = response.json()
            
            # Cache the response
            if use_cache and self.cache:
                self.cache.set(endpoint, data, params)
            
            return data
        except requests.exceptions.RequestException as e:
            print(f"✗ Request failed for {endpoint}: {e}")
            return None
    
    def _make_paginated_request(self, endpoint: str, params: Optional[Dict] = None, use_cache: bool = True) -> List[Dict]:
        """
        Make a paginated request to the API, fetching all pages
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters
            use_cache: Whether to use cache for this request (default: True)
            
        Returns:
            List of all items from all pages
        """
        # For paginated requests, create a cache key that includes all pages
        params = params or {}
        cache_key_params = {**params, 'paginated': 'all'}
        
        # Check if we have the full paginated result cached
        if use_cache and self.cache:
            cached_data = self.cache.get(endpoint, cache_key_params)
            if cached_data is not None:
                return cached_data
        
        all_items = []
        page = 1
        params["per_page"] = 100  # Max items per page
        
        while True:
            params["page"] = page
            # Don't use cache for individual pages, we cache the full result
            data = self._make_request(endpoint, params, use_cache=False)
            
            if not data:
                break
            
            # Handle both single items and lists
            if isinstance(data, list):
                if not data:
                    break
                all_items.extend(data)
                if len(data) < 100:  # Less than page size means last page
                    break
            else:
                all_items.append(data)
                break
            
            page += 1
            time.sleep(0.1)  # Rate limiting courtesy
        
        # Cache the complete paginated result
        if use_cache and self.cache:
            self.cache.set(endpoint, all_items, cache_key_params)
        
        return all_items
    
    def get_campuses(self) -> List[Dict]:
        """
        Get list of all available campuses
        
        Returns:
            List of campus dictionaries with id, name, city, country, etc.
        """
        print("Fetching available campuses...")
        campuses = self._make_paginated_request("/v2/campus")
        print(f"✓ Found {len(campuses)} campuses")
        return campuses
    
    def get_campus_users(self, campus_id: int, cursus_id: int = 21, begin_year: int = None) -> List[Dict]:
        """
        Get all users from a specific campus and cursus
        
        Uses the cursus_users endpoint with filters for correct data retrieval.
        
        Args:
            campus_id: Campus ID (e.g., Havre campus)
            cursus_id: Cursus ID (21 is typically the main 42 cursus)
            begin_year: Optional year to filter by cursus begin_at (e.g., 2025 for promo 2025)
            
        Returns:
            List of cursus_user dictionaries with user and cursus information
        """
        print(f"Fetching users from campus {campus_id} (cursus {cursus_id}){f' promo {begin_year}' if begin_year else ''}...")
        
        # Use cursus_users endpoint with campus and cursus filters
        # This ensures we get the cursus-specific data populated
        params = {
            "filter[campus_id]": campus_id,
            "filter[cursus_id]": cursus_id,
        }
        if begin_year:
            params["range[begin_at]"] = f"{begin_year}-01-01T00:00:00.000Z,{begin_year}-12-31T23:59:59.999Z"
        cursus_users = self._make_paginated_request("/v2/cursus_users", params)
        
        print(f"✓ Found {len(cursus_users)} users in cursus {cursus_id}")
        return cursus_users
    
    def get_cursus_projects(self, cursus_id: int = 21) -> List[Dict]:
        """
        Get all projects for a specific cursus
        
        Args:
            cursus_id: Cursus ID (21 is typically the main 42 cursus)
            
        Returns:
            List of project dictionaries
        """
        print(f"Fetching projects for cursus {cursus_id}...")
        endpoint = f"/v2/cursus/{cursus_id}/projects"
        projects = self._make_paginated_request(endpoint)
        print(f"✓ Found {len(projects)} projects")
        return projects
    
    def get_user_projects(self, user_id: int) -> List[Dict]:
        """
        Get all projects for a specific user
        
        Args:
            user_id: User ID
            
        Returns:
            List of project dictionaries
        """
        endpoint = f"/v2/users/{user_id}/projects_users"
        return self._make_paginated_request(endpoint)
    
    def get_user_locations(self, user_id: int, begin_at: Optional[str] = None, end_at: Optional[str] = None) -> List[Dict]:
        """
        Get location (log time) data for a specific user
        
        Args:
            user_id: User ID
            begin_at: Start date (ISO format)
            end_at: End date (ISO format)
            
        Returns:
            List of location dictionaries with login/logout times
        """
        params = {}
        if begin_at:
            params["range[begin_at]"] = begin_at
        if end_at:
            params["range[end_at]"] = end_at
            
        endpoint = f"/v2/users/{user_id}/locations"
        return self._make_paginated_request(endpoint, params)
    
    def get_project_users(self, project_id: int) -> List[Dict]:
        """
        Get all users who have worked on a specific project
        
        This is more efficient than fetching all projects for every user
        when you want to know which users completed a specific project.
        
        Args:
            project_id: Project ID
            
        Returns:
            List of users_projects dictionaries for users who worked on this project
        """
        print(f"Fetching users for project {project_id}...")
        endpoint = f"/v2/projects/{project_id}/projects_users"
        users = self._make_paginated_request(endpoint)
        print(f"✓ Found {len(users)} users who worked on this project")
        return users
    
    def has_user_completed_project(self, user_id: int, project_id: int) -> Optional[Dict]:
        """
        Check if a specific user has completed a specific project
        
        This uses the efficient project users endpoint to avoid fetching
        all projects for all users.
        
        Args:
            user_id: User ID
            project_id: Project ID
            
        Returns:
            Project user entry if user worked on the project, None otherwise
        """
        project_users = self.get_project_users(project_id)
        
        # Find the user in the project users list
        for project_user in project_users:
            if project_user.get('user', {}).get('id') == user_id:
                return project_user
        
        return None
    

    def get_projects_users_by_user_map(self, user_ids: List[int]) -> Dict[int, List[Dict]]:
        """
        Get projects for multiple users and return as a map
        
        This uses bulk fetching and organizes data by user ID for easy lookup.
        Uses concurrent requests for faster fetching.
        
        Args:
            user_ids: List of user IDs
            
        Returns:
            Dictionary mapping user_id -> list of projects
        """
        print(f"Fetching projects for {len(user_ids)} users...")
        
        # Create a map to store projects by user
        projects_by_user = {user_id: [] for user_id in user_ids}
        
        # Check cache for each user first
        users_needing_fetch = []
        for user_id in user_ids:
            endpoint = f"/v2/users/{user_id}/projects_users"
            cache_key_params = {'paginated': 'all'}
            if self.cache:
                cached_data = self.cache.get(endpoint, cache_key_params)
                if cached_data is not None:
                    projects_by_user[user_id] = cached_data
                else:
                    users_needing_fetch.append(user_id)
            else:
                users_needing_fetch.append(user_id)
        
        # Fetch projects for users not in cache using concurrent requests
        if users_needing_fetch:
            print(f"  Fetching from API for {len(users_needing_fetch)} users (others from cache)...")
            completed = 0
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {
                    executor.submit(self.get_user_projects, uid): uid
                    for uid in users_needing_fetch
                }
                for future in as_completed(futures):
                    uid = futures[future]
                    try:
                        projects_by_user[uid] = future.result()
                    except Exception as e:
                        print(f"    ⚠ Error fetching projects for user {uid}: {e}")
                    completed += 1
                    if completed % 50 == 0:
                        print(f"    Progress: {completed}/{len(users_needing_fetch)}")
        else:
            print("  All data from cache!")
        
        return projects_by_user
    
    def get_locations_by_user_map(self, user_ids: List[int], begin_at: Optional[str] = None, end_at: Optional[str] = None) -> Dict[int, List[Dict]]:
        """
        Get locations for multiple users and return as a map
        
        Uses concurrent requests for faster fetching.
        
        Args:
            user_ids: List of user IDs
            begin_at: Optional start date filter (ISO format)
            end_at: Optional end date filter (ISO format)
            
        Returns:
            Dictionary mapping user_id -> list of locations
        """
        print(f"Fetching locations for {len(user_ids)} users...")
        if begin_at or end_at:
            date_range = []
            if begin_at:
                date_range.append(f"from {begin_at}")
            if end_at:
                date_range.append(f"to {end_at}")
            print(f"  Date range filter: {' '.join(date_range)}")
        
        # Create a map to store locations by user
        locations_by_user = {user_id: [] for user_id in user_ids}
        
        # Check cache for each user first
        users_needing_fetch = []
        cache_key_params = {'paginated': 'all'}
        if begin_at:
            cache_key_params['range[begin_at]'] = begin_at
        if end_at:
            cache_key_params['range[end_at]'] = end_at
            
        for user_id in user_ids:
            endpoint = f"/v2/users/{user_id}/locations"
            if self.cache:
                cached_data = self.cache.get(endpoint, cache_key_params)
                if cached_data is not None:
                    locations_by_user[user_id] = cached_data
                else:
                    users_needing_fetch.append(user_id)
            else:
                users_needing_fetch.append(user_id)
        
        # Fetch locations for users not in cache using concurrent requests
        if users_needing_fetch:
            print(f"  Fetching from API for {len(users_needing_fetch)} users (others from cache)...")
            completed = 0
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {
                    executor.submit(self.get_user_locations, uid, begin_at, end_at): uid
                    for uid in users_needing_fetch
                }
                for future in as_completed(futures):
                    uid = futures[future]
                    try:
                        locations_by_user[uid] = future.result()
                    except Exception as e:
                        print(f"    ⚠ Error fetching locations for user {uid}: {e}")
                    completed += 1
                    if completed % 50 == 0:
                        print(f"    Progress: {completed}/{len(users_needing_fetch)}")
        else:
            print("  All data from cache!")
        
        return locations_by_user

    def refetch_user_locations(self, user_id: int, begin_at: Optional[str] = None, end_at: Optional[str] = None) -> List[Dict]:
        """
        Invalidate cache and re-fetch locations for a user whose logtime was 0.

        Args:
            user_id: User ID
            begin_at: Optional start date filter (ISO format)
            end_at: Optional end date filter (ISO format)

        Returns:
            Fresh list of location dictionaries
        """
        endpoint = f"/v2/users/{user_id}/locations"
        cache_key_params = {'paginated': 'all'}
        if begin_at:
            cache_key_params['range[begin_at]'] = begin_at
        if end_at:
            cache_key_params['range[end_at]'] = end_at

        # Invalidate the cache entry for this user's locations
        if self.cache:
            self.cache.invalidate(endpoint, cache_key_params)

        # Re-fetch from the API
        return self.get_user_locations(user_id, begin_at, end_at)
    
    def clear_cache(self):
        """Clear all cached data"""
        if self.cache:
            self.cache.clear()
            print("✓ Cache cleared")
    
    def get_cache_stats(self) -> Optional[Dict]:
        """Get cache statistics"""
        if self.cache:
            return self.cache.get_cache_stats()
        return None

    def get_key_usage_stats(self) -> List[Dict]:
        """Get usage statistics for all API keys"""
        return self.key_manager.get_all_usage_stats()

    def get_data_freshness(self, campus_id: int = None, cursus_id: int = 21, begin_year: int = None) -> Dict[str, Optional[str]]:
        """
        Get the last-fetch timestamp for each data category.

        Args:
            campus_id: Campus ID used in the current session
            cursus_id: Cursus ID
            begin_year: Promo year filter

        Returns:
            Dictionary mapping data category name to ISO timestamp (or None)
        """
        freshness = {}

        if not self.cache:
            return freshness

        # Campuses
        freshness['Campuses'] = self.cache.get_cache_timestamp(
            "/v2/campus", {'paginated': 'all'}
        )

        # Campus users
        if campus_id:
            params = {
                "filter[campus_id]": campus_id,
                "filter[cursus_id]": cursus_id,
                'paginated': 'all',
            }
            if begin_year:
                params["range[begin_at]"] = f"{begin_year}-01-01T00:00:00.000Z,{begin_year}-12-31T23:59:59.999Z"
            freshness['Campus Users'] = self.cache.get_cache_timestamp(
                "/v2/cursus_users", params
            )

        # Cursus projects
        freshness['Cursus Projects'] = self.cache.get_cache_timestamp(
            f"/v2/cursus/{cursus_id}/projects", {'paginated': 'all'}
        )

        # Project Users (per-project caches)
        freshness['Project Users'] = self.cache.get_oldest_matching_timestamp(
            "/v2/projects/"
        )

        # User Locations / Logtime (per-user caches)
        freshness['User Locations'] = self.cache.get_oldest_matching_timestamp(
            "/v2/users/"
        )

        return freshness

    # --- Refresh methods ---

    def refresh_campuses(self) -> List[Dict]:
        """Invalidate campus cache and re-fetch from API"""
        if self.cache:
            self.cache.invalidate("/v2/campus", {'paginated': 'all'})
        return self.get_campuses()

    def refresh_campus_users(self, campus_id: int, cursus_id: int = 21, begin_year: int = None) -> List[Dict]:
        """Invalidate campus users cache and re-fetch from API"""
        params = {
            "filter[campus_id]": campus_id,
            "filter[cursus_id]": cursus_id,
            'paginated': 'all',
        }
        if begin_year:
            params["range[begin_at]"] = f"{begin_year}-01-01T00:00:00.000Z,{begin_year}-12-31T23:59:59.999Z"
        if self.cache:
            self.cache.invalidate("/v2/cursus_users", params)
        return self.get_campus_users(campus_id, cursus_id, begin_year)

    def refresh_cursus_projects(self, cursus_id: int = 21) -> List[Dict]:
        """Invalidate cursus projects cache and re-fetch from API"""
        endpoint = f"/v2/cursus/{cursus_id}/projects"
        if self.cache:
            self.cache.invalidate(endpoint, {'paginated': 'all'})
        return self.get_cursus_projects(cursus_id)

    def refresh_project_users(self, project_id: int) -> List[Dict]:
        """Invalidate project users cache and re-fetch from API"""
        endpoint = f"/v2/projects/{project_id}/projects_users"
        if self.cache:
            self.cache.invalidate(endpoint, {'paginated': 'all'})
        return self.get_project_users(project_id)

    def refresh_user_projects(self, user_id: int) -> List[Dict]:
        """Invalidate user projects cache and re-fetch from API"""
        endpoint = f"/v2/users/{user_id}/projects_users"
        if self.cache:
            self.cache.invalidate(endpoint, {'paginated': 'all'})
        return self.get_user_projects(user_id)

    def refresh_user_locations(self, user_id: int, begin_at: Optional[str] = None, end_at: Optional[str] = None) -> List[Dict]:
        """Alias for refetch_user_locations for API consistency"""
        return self.refetch_user_locations(user_id, begin_at, end_at)

    def refresh_all(self):
        """Clear the entire cache, forcing all subsequent requests to hit the API"""
        self.clear_cache()
        print("✓ All cached data cleared — next requests will fetch fresh data from the API")
