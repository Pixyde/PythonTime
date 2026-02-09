"""
42 API Python Time Tracker
Main application to track time spent on Python modules by students
"""

import os
import json
from datetime import datetime
from typing import List, Dict
from dotenv import load_dotenv

from api_client import API42Client
from data_processor import DataProcessor


# Campus IDs (you may need to adjust these)
# Common campus IDs:
# Paris: 1
# Lyon: 6
# Havre: Need to be determined (you can find it via API)
HAVRE_CAMPUS_ID = 14  # This is an example, adjust as needed

# Cursus ID for 42 cursus
MAIN_CURSUS_ID = 21

# New Common Core - Filter for only new common core modules
# The new common core uses a different cursus or has specific identifiers
# You can filter by:
# 1. Cursus ID (if new common core has a different cursus ID)
# 2. Project slugs/names (specific to new common core)
# 3. Begin date range (new common core started at a specific date)
USE_NEW_COMMON_CORE_ONLY = True  # Set to True to filter only new common core modules

# API Call Optimization Settings
# Set to limit student processing (useful for testing)
MAX_STUDENTS = None  # Set to a number (e.g., 50) to limit, or None for all students

# Date range for location data (reduces API response size)
# Set to None to fetch all location history
# Example: LOCATION_BEGIN_DATE = "2024-01-01T00:00:00Z"
LOCATION_BEGIN_DATE = None  # Start date for location data (ISO format)
LOCATION_END_DATE = None    # End date for location data (ISO format)


def load_config():
    """Load configuration from .env file"""
    load_dotenv()
    
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    
    if not client_id or not client_secret:
        raise ValueError(
            "Missing API credentials. Please create a .env file with CLIENT_ID and CLIENT_SECRET.\n"
            "See .env.example for template."
        )
    
    return client_id, client_secret


def get_all_students(cursus_users: List[Dict]) -> List[Dict]:
    """
    Get all students from the cursus users list
    
    Note: This currently returns all students. To filter for promotion 4 specifically,
    you would need to implement filtering based on your campus's promotion criteria
    (e.g., begin_at date, level range, or specific cursus fields).
    
    Args:
        cursus_users: List of cursus user dictionaries
        
    Returns:
        List of all students
    """
    students = []
    
    for cursus_user in cursus_users:
        # The exact way to determine promotion may vary by campus
        # Common approaches:
        # 1. Check cursus level/grade range
        # 2. Check begin_at date range
        # 3. Check a specific field in the cursus_user data
        
        # For now, we include all students
        # Adjust this logic based on your campus's promotion definition
        user = cursus_user.get('user', {})
        if user:
            students.append(cursus_user)
    
    return students


def process_student_optimized(cursus_user: Dict, projects_map: Dict[int, List[Dict]], locations_map: Dict[int, List[Dict]], new_common_core_only: bool = False) -> Dict:
    """
    Process a single student's data using pre-fetched data maps
    
    Args:
        cursus_user: Cursus user dictionary
        projects_map: Map of user_id -> projects list
        locations_map: Map of user_id -> locations list
        new_common_core_only: If True, filter to only new common core modules
        
    Returns:
        Dictionary with student's Python project analysis
    """
    user = cursus_user.get('user', {})
    user_id = user.get('id')
    login = user.get('login', 'unknown')
    
    if not user_id:
        return None
    
    # Get projects and locations from pre-fetched maps
    projects = projects_map.get(user_id, [])
    locations = locations_map.get(user_id, [])
    
    # Filter to Python projects (optionally only new common core)
    python_projects = DataProcessor.filter_python_projects(projects, new_common_core_only=new_common_core_only)
    
    if not python_projects:
        return None
    
    # Analyze time spent on Python projects
    analysis = DataProcessor.analyze_python_time(python_projects, locations)
    
    return {
        'user_id': user_id,
        'login': login,
        'email': user.get('email', ''),
        'cursus_level': cursus_user.get('level', 0),
        'python_projects': analysis,
        'total_python_hours': sum(p['time_spent_hours'] for p in analysis)
    }


def process_student(client: API42Client, cursus_user: Dict) -> Dict:
    """
    Process a single student's data
    
    Args:
        client: API client instance
        cursus_user: Cursus user dictionary
        
    Returns:
        Dictionary with student's Python project analysis
    """
    user = cursus_user.get('user', {})
    user_id = user.get('id')
    login = user.get('login', 'unknown')
    
    if not user_id:
        return None
    
    print(f"\nProcessing student: {login}")
    
    # Get all projects for this user
    print(f"  Fetching projects...")
    projects = client.get_user_projects(user_id)
    
    # Filter to Python projects (with new common core filtering if enabled)
    python_projects = DataProcessor.filter_python_projects(projects, new_common_core_only=USE_NEW_COMMON_CORE_ONLY)
    print(f"  Found {len(python_projects)} Python projects")
    
    if not python_projects:
        return None
    
    # Get log time data
    print(f"  Fetching log time data...")
    locations = client.get_user_locations(user_id, LOCATION_BEGIN_DATE, LOCATION_END_DATE)
    print(f"  Found {len(locations)} log entries")
    
    # Analyze time spent on Python projects
    analysis = DataProcessor.analyze_python_time(python_projects, locations)
    
    return {
        'user_id': user_id,
        'login': login,
        'email': user.get('email', ''),
        'cursus_level': cursus_user.get('level', 0),
        'python_projects': analysis,
        'total_python_hours': sum(p['time_spent_hours'] for p in analysis)
    }


def main():
    """Main application entry point"""
    print("=" * 60)
    print("42 API Python Time Tracker")
    print("=" * 60)
    
    try:
        # Load configuration
        print("\nLoading configuration...")
        client_id, client_secret = load_config()
        
        # Initialize API client with caching enabled
        print("Initializing 42 API client with caching...")
        client = API42Client(client_id, client_secret, use_cache=True, cache_ttl_hours=24)
        
        # Authenticate
        if not client.authenticate():
            print("Failed to authenticate. Please check your credentials.")
            return
        
        # Show cache stats
        cache_stats = client.get_cache_stats()
        if cache_stats:
            print(f"Cache: {cache_stats['total_files']} files, {cache_stats['total_size_mb']} MB")
        
        # Get students from Havre campus
        print(f"\nFetching students from Havre campus (ID: {HAVRE_CAMPUS_ID})...")
        cursus_users = client.get_campus_users(HAVRE_CAMPUS_ID, MAIN_CURSUS_ID)
        
        if not cursus_users:
            print("No students found. This might be due to:")
            print("  - Incorrect campus ID")
            print("  - API permissions")
            print("  - No students in this cursus")
            return
        
        # Get all students (adjust filter logic as needed for promotion 4)
        print(f"Filtering students...")
        students = get_all_students(cursus_users)
        
        # Apply MAX_STUDENTS limit if configured
        if MAX_STUDENTS and len(students) > MAX_STUDENTS:
            print(f"Limiting to first {MAX_STUDENTS} students (MAX_STUDENTS setting)")
            students = students[:MAX_STUDENTS]
        
        print(f"Found {len(students)} students to analyze")
        
        # Extract user IDs for bulk fetching
        user_ids = [cu.get('user', {}).get('id') for cu in students if cu.get('user', {}).get('id')]
        print(f"Extracted {len(user_ids)} valid user IDs")
        
        # Bulk fetch projects and locations for all users
        print("\n" + "=" * 60)
        print("OPTIMIZED BULK FETCHING")
        print("=" * 60)
        
        projects_map = client.get_projects_users_by_user_map(user_ids)
        locations_map = client.get_locations_by_user_map(
            user_ids, 
            begin_at=LOCATION_BEGIN_DATE,
            end_at=LOCATION_END_DATE
        )
        
        print("\n" + "=" * 60)
        print("PROCESSING STUDENTS")
        if USE_NEW_COMMON_CORE_ONLY:
            print("(Filtering for NEW COMMON CORE Python modules only)")
        print("=" * 60)
        
        # Process each student using pre-fetched data
        results = []
        python_students = 0
        for i, cursus_user in enumerate(students, 1):
            user = cursus_user.get('user', {})
            login = user.get('login', 'unknown')
            
            student_data = process_student_optimized(
                cursus_user, 
                projects_map, 
                locations_map,
                new_common_core_only=USE_NEW_COMMON_CORE_ONLY
            )
            if student_data:
                results.append(student_data)
                python_students += 1
                print(f"[{i}/{len(students)}] {login}: {student_data['total_python_hours']:.2f}h across {len(student_data['python_projects'])} projects")
            else:
                print(f"[{i}/{len(students)}] {login}: No Python projects")
        
        # Save results
        output_file = f"python_time_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print("\n" + "=" * 60)
        print(f"Analysis complete!")
        print(f"Processed {len(students)} students")
        print(f"Found {python_students} students with Python projects")
        if USE_NEW_COMMON_CORE_ONLY:
            print(f"(Filtered for NEW COMMON CORE modules only)")
        print(f"Results saved to: {output_file}")
        
        # Show cache stats again
        cache_stats = client.get_cache_stats()
        if cache_stats:
            print(f"\nCache after run: {cache_stats['total_files']} files, {cache_stats['total_size_mb']} MB")
        
        print("=" * 60)
        
        # Print summary
        if results:
            print("\nTop 10 Students by Python Hours:")
            sorted_results = sorted(results, key=lambda x: x['total_python_hours'], reverse=True)[:10]
            for student in sorted_results:
                print(f"  {student['login']}: {student['total_python_hours']:.2f} hours across {len(student['python_projects'])} Python projects")
    
    except ValueError as e:
        print(f"\n✗ Configuration error: {e}")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
