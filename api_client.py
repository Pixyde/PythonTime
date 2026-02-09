"""
42 API Client Module
Handles authentication and API requests to the 42 API
"""

import requests
import time
import os
from typing import Dict, List, Optional
from datetime import datetime


class API42Client:
    """Client for interacting with the 42 API"""
    
    BASE_URL = "https://api.intra.42.fr"
    
    def __init__(self, client_id: str, client_secret: str):
        """
        Initialize the 42 API client
        
        Args:
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expires_at = 0
        
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
        if not self.access_token or time.time() >= self.token_expires_at - 60:
            self.authenticate()
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make an authenticated request to the API
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters
            
        Returns:
            Response data as dictionary, or None if request failed
        """
        self._ensure_authenticated()
        
        url = f"{self.BASE_URL}{endpoint}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"✗ Request failed for {endpoint}: {e}")
            return None
    
    def _make_paginated_request(self, endpoint: str, params: Optional[Dict] = None) -> List[Dict]:
        """
        Make a paginated request to the API, fetching all pages
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters
            
        Returns:
            List of all items from all pages
        """
        all_items = []
        page = 1
        params = params or {}
        params["page[size]"] = 100  # Max items per page
        
        while True:
            params["page[number]"] = page
            data = self._make_request(endpoint, params)
            
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
