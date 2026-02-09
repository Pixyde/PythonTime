"""
42 API Client Module
Handles authentication and API requests to the 42 API
"""

import requests
import time
import os
from typing import Dict, List, Optional
from datetime import datetime
from cache_manager import CacheManager


class API42Client:
    """Client for interacting with the 42 API"""
    
    BASE_URL = "https://api.intra.42.fr"
    TOKEN_REFRESH_BUFFER_SECONDS = 60  # Refresh token 60 seconds before expiry
    
    def __init__(self, client_id: str, client_secret: str, use_cache: bool = True, cache_ttl_hours: int = 24):
        """
        Initialize the 42 API client
        
        Args:
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            use_cache: Whether to use caching (default: True)
            cache_ttl_hours: Cache time-to-live in hours (default: 24)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expires_at = 0
        self.use_cache = use_cache
        self.cache = CacheManager(cache_ttl_hours=cache_ttl_hours) if use_cache else None
        
    def authenticate(self) -> bool:
        """
        Authenticate with the 42 API using OAuth2
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
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
            
            print("✓ Successfully authenticated with 42 API")
            return True
        except requests.exceptions.RequestException as e:
            print(f"✗ Authentication failed: {e}")
            return False
    
    def _ensure_authenticated(self):
        """Ensure we have a valid access token"""
        if not self.access_token or time.time() >= self.token_expires_at - self.TOKEN_REFRESH_BUFFER_SECONDS:
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
        params["page[size]"] = 100  # Max items per page
        
        while True:
            params["page[number]"] = page
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
    
    def get_campus_users(self, campus_id: int, cursus_id: int = 21) -> List[Dict]:
        """
        Get all users from a specific campus and cursus
        
        Args:
            campus_id: Campus ID (e.g., Havre campus)
            cursus_id: Cursus ID (21 is typically the main 42 cursus)
            
        Returns:
            List of user dictionaries
        """
        print(f"Fetching users from campus {campus_id}...")
        params = {
            "filter[campus_id]": campus_id,
            "filter[cursus_id]": cursus_id,
        }
        users = self._make_paginated_request("/v2/cursus_users", params)
        print(f"✓ Found {len(users)} users")
        return users
    
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
    
    def get_project_details(self, project_id: int) -> Optional[Dict]:
        """
        Get details for a specific project
        
        Args:
            project_id: Project ID
            
        Returns:
            Project details dictionary
        """
        endpoint = f"/v2/projects/{project_id}"
        return self._make_request(endpoint)
    
    def get_all_projects_users(self, user_ids: Optional[List[int]] = None) -> List[Dict]:
        """
        Get all projects_users data globally or for specific users
        
        This is more efficient than fetching per user when dealing with many users.
        
        Args:
            user_ids: Optional list of user IDs to filter by (filters in code after fetch)
            
        Returns:
            List of projects_users dictionaries
        """
        print("Fetching all projects_users data...")
        # Fetch all projects_users without user filter
        # The API doesn't support filtering by multiple user IDs, 
        # so we fetch broadly and filter in code
        all_projects = self._make_paginated_request("/v2/projects_users")
        
        # Filter by user IDs if provided
        if user_ids:
            user_id_set = set(user_ids)
            all_projects = [
                p for p in all_projects 
                if p.get('user', {}).get('id') in user_id_set
            ]
        
        print(f"✓ Found {len(all_projects)} projects_users entries")
        return all_projects
    
    def get_projects_users_by_user_map(self, user_ids: List[int]) -> Dict[int, List[Dict]]:
        """
        Get projects for multiple users and return as a map
        
        This uses bulk fetching and organizes data by user ID for easy lookup.
        
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
        
        # Fetch projects for users not in cache
        if users_needing_fetch:
            print(f"  Fetching from API for {len(users_needing_fetch)} users (others from cache)...")
            for i, user_id in enumerate(users_needing_fetch, 1):
                if i % 50 == 0:
                    print(f"    Progress: {i}/{len(users_needing_fetch)}")
                projects = self.get_user_projects(user_id)
                projects_by_user[user_id] = projects
        else:
            print("  All data from cache!")
        
        return projects_by_user
    
    def get_locations_by_user_map(self, user_ids: List[int]) -> Dict[int, List[Dict]]:
        """
        Get locations for multiple users and return as a map
        
        Args:
            user_ids: List of user IDs
            
        Returns:
            Dictionary mapping user_id -> list of locations
        """
        print(f"Fetching locations for {len(user_ids)} users...")
        
        # Create a map to store locations by user
        locations_by_user = {user_id: [] for user_id in user_ids}
        
        # Check cache for each user first
        users_needing_fetch = []
        for user_id in user_ids:
            endpoint = f"/v2/users/{user_id}/locations"
            cache_key_params = {'paginated': 'all'}
            if self.cache:
                cached_data = self.cache.get(endpoint, cache_key_params)
                if cached_data is not None:
                    locations_by_user[user_id] = cached_data
                else:
                    users_needing_fetch.append(user_id)
            else:
                users_needing_fetch.append(user_id)
        
        # Fetch locations for users not in cache
        if users_needing_fetch:
            print(f"  Fetching from API for {len(users_needing_fetch)} users (others from cache)...")
            for i, user_id in enumerate(users_needing_fetch, 1):
                if i % 50 == 0:
                    print(f"    Progress: {i}/{len(users_needing_fetch)}")
                locations = self.get_user_locations(user_id)
                locations_by_user[user_id] = locations
        else:
            print("  All data from cache!")
        
        return locations_by_user
    
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
