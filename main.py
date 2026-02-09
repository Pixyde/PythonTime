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


def process_student_with_cached_data(
    cursus_user: Dict, 
    projects_data: Dict[int, List[Dict]], 
    locations_data: Dict[int, List[Dict]]
) -> Dict:
    """
    Process a single student's data using pre-fetched bulk data
    
    Args:
        cursus_user: Cursus user dictionary
        projects_data: Pre-fetched projects data for all users
        locations_data: Pre-fetched locations data for all users
        
    Returns:
        Dictionary with student's Python project analysis
    """
    user = cursus_user.get('user', {})
    user_id = user.get('id')
    login = user.get('login', 'unknown')
    
    if not user_id:
        return None
    
    print(f"\nProcessing student: {login}")
    
    # Get projects from pre-fetched data
    projects = projects_data.get(user_id, [])
    
    # Filter to Python projects
    python_projects = DataProcessor.filter_python_projects(projects)
    print(f"  Found {len(python_projects)} Python projects")
    
    if not python_projects:
        return None
    
    # Get locations from pre-fetched data
    locations = locations_data.get(user_id, [])
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
    
    # Filter to Python projects
    python_projects = DataProcessor.filter_python_projects(projects)
    print(f"  Found {len(python_projects)} Python projects")
    
    if not python_projects:
        return None
    
    # Get log time data
    print(f"  Fetching log time data...")
    locations = client.get_user_locations(user_id)
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
        
        # Initialize API client
        print("Initializing 42 API client...")
        client = API42Client(client_id, client_secret)
        
        # Authenticate
        if not client.authenticate():
            print("Failed to authenticate. Please check your credentials.")
            return
        
        # OPTIMIZED: Get all cursus users in one bulk request
        print(f"\nFetching all users from cursus {MAIN_CURSUS_ID}...")
        all_cursus_users = client.get_all_cursus_users(MAIN_CURSUS_ID)
        
        if not all_cursus_users:
            print("No users found in cursus.")
            return
        
        # OPTIMIZED: Filter by campus locally instead of making separate API request
        print(f"\nFiltering for Havre campus (ID: {HAVRE_CAMPUS_ID})...")
        cursus_users = client.filter_users_by_campus(all_cursus_users, HAVRE_CAMPUS_ID)
        
        if not cursus_users:
            print("No students found from Havre campus. This might be due to:")
            print("  - Incorrect campus ID")
            print("  - API permissions")
            print("  - No students in this cursus at this campus")
            return
        
        # Get all students (adjust filter logic as needed for promotion 4)
        print(f"Filtering students...")
        students = get_all_students(cursus_users)
        print(f"Found {len(students)} students to analyze")
        
        # Extract user IDs for bulk fetching
        user_ids = [s.get('user', {}).get('id') for s in students if s.get('user', {}).get('id')]
        print(f"\nPreparing to fetch data for {len(user_ids)} students...")
        
        # OPTIMIZED: Bulk fetch all projects data
        print("\n" + "=" * 60)
        print("BULK FETCHING PROJECTS DATA")
        print("=" * 60)
        projects_data = client.get_bulk_projects_data(user_ids)
        
        # OPTIMIZED: Bulk fetch all locations data
        print("\n" + "=" * 60)
        print("BULK FETCHING LOCATIONS DATA")
        print("=" * 60)
        locations_data = client.get_bulk_locations_data(user_ids)
        
        # Process each student with cached data
        print("\n" + "=" * 60)
        print("ANALYZING STUDENT DATA")
        print("=" * 60)
        results = []
        for i, cursus_user in enumerate(students, 1):
            print(f"\n[{i}/{len(students)}] ", end="")
            student_data = process_student_with_cached_data(
                cursus_user, 
                projects_data, 
                locations_data
            )
            if student_data:
                results.append(student_data)
        
        # Save results
        output_file = f"python_time_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print("\n" + "=" * 60)
        print(f"Analysis complete!")
        print(f"Processed {len(results)} students")
        print(f"Results saved to: {output_file}")
        print("=" * 60)
        
        # Print summary
        if results:
            print("\nSummary:")
            for student in results:
                print(f"  {student['login']}: {student['total_python_hours']:.2f} hours across {len(student['python_projects'])} Python projects")
    
    except ValueError as e:
        print(f"\n✗ Configuration error: {e}")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
