"""
42 API Client Module
Handles authentication and API requests to the 42 API
"""

import requests
import time
import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path


class API42Client:
    """Client for interacting with the 42 API"""
    
    BASE_URL = "https://api.intra.42.fr"
    TOKEN_REFRESH_BUFFER_SECONDS = 60  # Refresh token 60 seconds before expiry
    
    def __init__(self, client_id: str, client_secret: str, cache_dir: str = ".cache"):
        """
        Initialize the 42 API client
        
        Args:
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            cache_dir: Directory to store cached responses
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expires_at = 0
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self._cache = {}
        
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
    
    def _get_cache_key(self, endpoint: str, params: Optional[Dict] = None) -> str:
        """Generate a cache key for an endpoint and parameters"""
        params_str = json.dumps(params or {}, sort_keys=True)
        return f"{endpoint}_{hash(params_str)}"
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Get data from memory cache"""
        return self._cache.get(cache_key)
    
    def _store_in_cache(self, cache_key: str, data: Any):
        """Store data in memory cache"""
        self._cache[cache_key] = data
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None, use_cache: bool = True) -> Optional[Dict]:
        """
        Make an authenticated request to the API
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters
            use_cache: Whether to use cached responses
            
        Returns:
            Response data as dictionary, or None if request failed
        """
        # Check cache first if enabled
        if use_cache:
            cache_key = self._get_cache_key(endpoint, params)
            cached_data = self._get_from_cache(cache_key)
            if cached_data is not None:
                return cached_data
        
        self._ensure_authenticated()
        
        url = f"{self.BASE_URL}{endpoint}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Store in cache if enabled
            if use_cache:
                cache_key = self._get_cache_key(endpoint, params)
                self._store_in_cache(cache_key, data)
            
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
            use_cache: Whether to use cached responses
            
        Returns:
            List of all items from all pages
        """
        all_items = []
        page = 1
        params = params or {}
        params["page[size]"] = 100  # Max items per page
        
        while True:
            params["page[number]"] = page
            data = self._make_request(endpoint, params, use_cache=use_cache)
            
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
    
    def get_all_cursus_users(self, cursus_id: int = 21) -> List[Dict]:
        """
        Get ALL users from a specific cursus (global endpoint)
        This is more efficient than filtering by campus in the API
        
        Args:
            cursus_id: Cursus ID (21 is typically the main 42 cursus)
            
        Returns:
            List of all cursus_user dictionaries
        """
        print(f"Fetching all users from cursus {cursus_id}...")
        params = {
            "filter[cursus_id]": cursus_id,
        }
        users = self._make_paginated_request("/v2/cursus_users", params)
        print(f"✓ Found {len(users)} total cursus users")
        return users
    
    def filter_users_by_campus(self, cursus_users: List[Dict], campus_id: int) -> List[Dict]:
        """
        Filter cursus users to only those from a specific campus
        This is done locally to avoid making separate API requests
        
        Args:
            cursus_users: List of all cursus users
            campus_id: Campus ID to filter by
            
        Returns:
            List of users from the specified campus
        """
        filtered_users = []
        for cursus_user in cursus_users:
            user = cursus_user.get('user', {})
            if user:
                # Check if user has the campus in their campus_users list
                campus_users = user.get('campus_users', [])
                for cu in campus_users:
                    if cu.get('campus_id') == campus_id:
                        filtered_users.append(cursus_user)
                        break
        
        print(f"✓ Filtered to {len(filtered_users)} users from campus {campus_id}")
        return filtered_users
    
    def get_bulk_projects_data(self, user_ids: List[int]) -> Dict[int, List[Dict]]:
        """
        Get projects for multiple users efficiently
        Uses caching to avoid redundant requests
        
        Args:
            user_ids: List of user IDs
            
        Returns:
            Dictionary mapping user_id to list of projects
        """
        print(f"Fetching projects for {len(user_ids)} users...")
        projects_by_user = {}
        
        for i, user_id in enumerate(user_ids, 1):
            if i % 10 == 0:
                print(f"  Progress: {i}/{len(user_ids)} users processed")
            projects_by_user[user_id] = self.get_user_projects(user_id)
        
        print(f"✓ Fetched projects for {len(user_ids)} users")
        return projects_by_user
    
    def get_bulk_locations_data(self, user_ids: List[int], begin_at: Optional[str] = None, end_at: Optional[str] = None) -> Dict[int, List[Dict]]:
        """
        Get locations for multiple users efficiently
        Uses caching to avoid redundant requests
        
        Args:
            user_ids: List of user IDs
            begin_at: Start date (ISO format)
            end_at: End date (ISO format)
            
        Returns:
            Dictionary mapping user_id to list of locations
        """
        print(f"Fetching locations for {len(user_ids)} users...")
        locations_by_user = {}
        
        for i, user_id in enumerate(user_ids, 1):
            if i % 10 == 0:
                print(f"  Progress: {i}/{len(user_ids)} users processed")
            locations_by_user[user_id] = self.get_user_locations(user_id, begin_at, end_at)
        
        print(f"✓ Fetched locations for {len(user_ids)} users")
        return locations_by_user
