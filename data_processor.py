"""
Data Processor Module
Processes and analyzes data from the 42 API
"""

from typing import Dict, List, Tuple
from datetime import datetime, timedelta, timezone
from collections import defaultdict


class DataProcessor:
    """Process and analyze 42 API data"""
    
    # New Common Core Python projects
    # These are the Python modules specific to the new common core curriculum
    # Update this list based on your campus's new common core structure
    NEW_COMMON_CORE_PYTHON_MODULES = [
        'python-0-starting',
        'python-1-base',
        'python-2-datascience',
        'python-3-oop',
        'python-module-00',
        'python-module-01',
        'python-module-02',
        'python-module-03',
        'python-module-04',
        'piscine-python',
        'piscine-python-datascience',
        'django-0-starting',
        'django-1-base-django',
        'django-2-sql',
        'django-3-advanced',
        'django-4-final',
    ]
    
    @staticmethod
    def is_new_common_core_project(project: Dict) -> bool:
        """
        Check if a project is from the new common core
        
        Args:
            project: Project dictionary
            
        Returns:
            True if project is from new common core, False otherwise
        """
        project_slug = project.get('project', {}).get('slug', '').lower()
        project_name = project.get('project', {}).get('name', '').lower()
        
        # Check if slug matches any new common core module
        for module in DataProcessor.NEW_COMMON_CORE_PYTHON_MODULES:
            if module.lower() in project_slug or module.lower() in project_name:
                return True
        
        # Additional check: cursus_ids field
        # New common core projects often have specific cursus IDs
        cursus_ids = project.get('cursus_ids', [])
        if cursus_ids:
            # Cursus ID 21 is typically the main common core
            # You may need to adjust this based on your campus
            if 21 in cursus_ids:
                return True
        
        return False
    
    @staticmethod
    def filter_python_projects(projects: List[Dict], new_common_core_only: bool = False) -> List[Dict]:
        """
        Filter projects to only include Python modules
        
        Args:
            projects: List of project dictionaries
            new_common_core_only: If True, filter to only new common core modules
            
        Returns:
            List of Python projects only
        """
        python_projects = []
        python_keywords = ['python', 'py', 'django', 'flask', 'ft_transcendence']
        
        for project in projects:
            project_name = project.get('project', {}).get('name', '').lower()
            project_slug = project.get('project', {}).get('slug', '').lower()
            
            # Check if project name or slug contains Python-related keywords
            is_python = any(keyword in project_name or keyword in project_slug for keyword in python_keywords)
            
            if is_python:
                # If filtering for new common core only, check if it's a new common core project
                if new_common_core_only:
                    if DataProcessor.is_new_common_core_project(project):
                        python_projects.append(project)
                else:
                    python_projects.append(project)
        
        return python_projects
    
    @staticmethod
    def get_project_dates(project: Dict) -> Tuple[datetime, datetime]:
        """
        Extract start and end dates from a project
        
        Args:
            project: Project dictionary
            
        Returns:
            Tuple of (start_date, end_date)
        """
        # Try to get dates from different possible fields
        marked_at = project.get('marked_at')
        created_at = project.get('created_at')
        updated_at = project.get('updated_at')
        validated_at = project.get('validated_at')
        
        # Start date is when the project was created/started
        start_date = None
        if created_at:
            start_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        
        # End date is when it was marked/validated
        end_date = None
        if marked_at:
            end_date = datetime.fromisoformat(marked_at.replace('Z', '+00:00'))
        elif validated_at:
            end_date = datetime.fromisoformat(validated_at.replace('Z', '+00:00'))
        elif updated_at:
            end_date = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
        
        # If no end date, assume project is ongoing (use current date)
        if not end_date and start_date:
            end_date = datetime.now(timezone.utc)
        
        return start_date, end_date
    
    @staticmethod
    def calculate_logtime_duration(location: Dict) -> float:
        """
        Calculate duration in hours from a location entry
        
        Args:
            location: Location dictionary with begin_at and end_at
            
        Returns:
            Duration in hours
        """
        begin_at = location.get('begin_at')
        end_at = location.get('end_at')
        
        if not begin_at:
            return 0.0
        
        begin = datetime.fromisoformat(begin_at.replace('Z', '+00:00'))
        
        # If still logged in (no end_at), use current time
        if not end_at:
            end = datetime.now(timezone.utc)
        else:
            end = datetime.fromisoformat(end_at.replace('Z', '+00:00'))
        
        duration = (end - begin).total_seconds() / 3600  # Convert to hours
        return max(0, duration)  # Ensure non-negative
    
    @staticmethod
    def match_logtimes_to_project(
        locations: List[Dict],
        project_start: datetime,
        project_end: datetime
    ) -> float:
        """
        Calculate total log time that overlaps with a project's timeframe
        
        Args:
            locations: List of location dictionaries
            project_start: Project start date
            project_end: Project end date
            
        Returns:
            Total hours spent during the project timeframe
        """
        total_hours = 0.0
        
        for location in locations:
            begin_at = location.get('begin_at')
            end_at = location.get('end_at')
            
            if not begin_at:
                continue
            
            log_start = datetime.fromisoformat(begin_at.replace('Z', '+00:00'))
            
            if not end_at:
                log_end = datetime.now(timezone.utc)
            else:
                log_end = datetime.fromisoformat(end_at.replace('Z', '+00:00'))
            
            # Calculate overlap between log time and project timeframe
            overlap_start = max(log_start, project_start)
            overlap_end = min(log_end, project_end)
            
            if overlap_start < overlap_end:
                overlap_hours = (overlap_end - overlap_start).total_seconds() / 3600
                total_hours += overlap_hours
        
        return total_hours
    
    @staticmethod
    def analyze_python_time(
        python_projects: List[Dict],
        all_locations: List[Dict]
    ) -> List[Dict]:
        """
        Analyze time spent on each Python project
        
        Args:
            python_projects: List of Python project dictionaries
            all_locations: List of all location entries for the user
            
        Returns:
            List of dictionaries with project analysis
        """
        results = []
        
        for project in python_projects:
            project_name = project.get('project', {}).get('name', 'Unknown')
            start_date, end_date = DataProcessor.get_project_dates(project)
            
            if not start_date or not end_date:
                continue
            
            # Calculate time spent based on log times during project period
            time_spent = DataProcessor.match_logtimes_to_project(
                all_locations,
                start_date,
                end_date
            )
            
            result = {
                'project_name': project_name,
                'project_slug': project.get('project', {}).get('slug', ''),
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'time_spent_hours': round(time_spent, 2),
                'status': project.get('status', 'unknown'),
                'final_mark': project.get('final_mark'),
                'validated': project.get('validated?', False)
            }
            
            results.append(result)
        
        return results
