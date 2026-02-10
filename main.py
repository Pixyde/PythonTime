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
from dashboard_generator import DashboardGenerator


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


def select_campus(client: API42Client) -> int:
    """
    Let user select a campus from the available list
    
    Args:
        client: API client instance
        
    Returns:
        Selected campus ID, or None for no filtering
    """
    print("\n" + "=" * 60)
    print("CAMPUS SELECTION")
    print("=" * 60)
    
    campuses = client.get_campuses()
    
    if not campuses:
        print("No campuses found. Analyzing all users globally.")
        return None
    
    # Sort campuses by name for easier navigation
    campuses.sort(key=lambda c: c.get('name', ''))
    
    print("\nAvailable campuses:")
    print("-" * 60)
    print(f"  {'0':>3}. {'ALL USERS (No campus filtering)':<50}")
    print("-" * 60)
    for i, campus in enumerate(campuses, 1):
        name = campus.get('name', 'Unknown')
        city = campus.get('city', 'Unknown')
        country = campus.get('country', 'Unknown')
        campus_id = campus.get('id', 0)
        print(f"  {i:3d}. {name:30s} ({city}, {country}) [ID: {campus_id}]")
    
    print("-" * 60)
    
    # Get user selection
    while True:
        try:
            selection = input("\nEnter campus number (or 'q' to quit): ").strip()
            if selection.lower() == 'q':
                print("Exiting...")
                exit(0)
            
            idx = int(selection)
            
            if idx == 0:
                print(f"\n✓ Selected: ALL USERS (No campus filtering)")
                return None  # None means no filtering
            elif 1 <= idx <= len(campuses):
                selected_campus = campuses[idx - 1]
                campus_id = selected_campus.get('id')
                campus_name = selected_campus.get('name')
                print(f"\n✓ Selected: {campus_name} (ID: {campus_id})")
                return campus_id
            else:
                print(f"Please enter a number between 0 and {len(campuses)}")
        except ValueError:
            print("Please enter a valid number")
        except KeyboardInterrupt:
            print("\nExiting...")
            exit(0)


def get_python_project_ids(client: API42Client, cursus_id: int = 21) -> List[int]:
    """
    Get Python project IDs from the cursus
    
    Args:
        client: API client instance
        cursus_id: Cursus ID
        
    Returns:
        List of Python project IDs
    """
    print("\nIdentifying Python projects...")
    projects = client.get_cursus_projects(cursus_id)
    
    # Match Python Module 00-10 specifically, with flexible patterns
    python_keywords = ['python module', 'python-module', 'py-module']
    python_project_ids = []
    
    for project in projects:
        project_name = project.get('name', '').lower()
        project_slug = project.get('slug', '').lower()
        
        # Check if project is Python-related
        is_python = any(keyword in project_name or keyword in project_slug for keyword in python_keywords)
        
        if is_python:
            project_id = project.get('id')
            if project_id:
                python_project_ids.append(project_id)
                print(f"  Found Python project: {project.get('name')} (ID: {project_id})")
    
    print(f"✓ Identified {len(python_project_ids)} Python projects")
    return python_project_ids


def get_cpp_project_ids(client: API42Client, cursus_id: int = 21) -> List[int]:
    """
    Get C++ project IDs from the cursus
    
    Args:
        client: API client instance
        cursus_id: Cursus ID
        
    Returns:
        List of C++ project IDs
    """
    print("\nIdentifying C++ projects...")
    projects = client.get_cursus_projects(cursus_id)
    
    cpp_keywords = ['c++', 'cpp', 'piscine c', 'libft', 'ft_printf', 'get_next_line', 
                    'born2beroot', 'so_long', 'fdf', 'minitalk', 'push_swap',
                    'philosophers', 'minishell', 'cub3d', 'netpractice', 'cpp module',
                    'webserv', 'ft_irc', 'inception', 'ft_containers']
    cpp_project_ids = []
    
    for project in projects:
        project_name = project.get('name', '').lower()
        project_slug = project.get('slug', '').lower()
        
        # Check if project is C++-related
        is_cpp = any(keyword in project_name or keyword in project_slug for keyword in cpp_keywords)
        
        if is_cpp:
            project_id = project.get('id')
            if project_id:
                cpp_project_ids.append(project_id)
                print(f"  Found C++ project: {project.get('name')} (ID: {project_id})")
    
    print(f"✓ Identified {len(cpp_project_ids)} C++ projects")
    return cpp_project_ids


def get_all_project_types(client: API42Client, cursus_id: int = 21) -> Dict[str, List[int]]:
    """
    Get all project IDs organized by language/type
    
    Args:
        client: API client instance
        cursus_id: Cursus ID
        
    Returns:
        Dictionary mapping project type to list of project IDs
    """
    print("\nIdentifying all project types...")
    projects = client.get_cursus_projects(cursus_id)
    
    project_types = {
        'Python': [],
        'C++': [],
        'Web': [],
        'System': [],
        'Other': []
    }
    
    # Match Python Module 00-10 specifically, with flexible patterns
    python_keywords = ['python module', 'python-module', 'py-module']
    cpp_keywords = ['c++', 'cpp', 'piscine c', 'libft', 'ft_printf', 'get_next_line',
                    'philosophers', 'minishell', 'cub3d', 'push_swap', 'cpp module',
                    'webserv', 'ft_irc', 'ft_containers']
    web_keywords = ['ft_transcendence', 'webserv', 'matcha', 'hypertube', 'red_tetris']
    system_keywords = ['born2beroot', 'inception', 'netpractice']
    
    for project in projects:
        project_name = project.get('name', '').lower()
        project_slug = project.get('slug', '').lower()
        project_id = project.get('id')
        
        if not project_id:
            continue
        
        # Categorize project
        if any(kw in project_name or kw in project_slug for kw in python_keywords):
            project_types['Python'].append(project_id)
            print(f"  [Python] {project.get('name')} (ID: {project_id})")
        elif any(kw in project_name or kw in project_slug for kw in cpp_keywords):
            project_types['C++'].append(project_id)
            print(f"  [C++] {project.get('name')} (ID: {project_id})")
        elif any(kw in project_name or kw in project_slug for kw in web_keywords):
            project_types['Web'].append(project_id)
            print(f"  [Web] {project.get('name')} (ID: {project_id})")
        elif any(kw in project_name or kw in project_slug for kw in system_keywords):
            project_types['System'].append(project_id)
            print(f"  [System] {project.get('name')} (ID: {project_id})")
    
    for ptype, pids in project_types.items():
        if pids:
            print(f"✓ Identified {len(pids)} {ptype} projects")
    
    return project_types


def fetch_users_by_projects(client: API42Client, project_ids: List[int], campus_id: int = None) -> Dict[int, List[Dict]]:
    """
    Fetch users who worked on Python projects (project-based approach)
    
    Optionally filters by campus if campus_id is provided.
    
    Args:
        client: API client instance
        project_ids: List of Python project IDs
        campus_id: Optional campus ID to filter users by
        
    Returns:
        Dictionary mapping user_id -> list of their Python projects
    """
    print(f"\nFetching users for {len(project_ids)} Python projects...")
    if campus_id:
        print(f"(Will filter to campus ID: {campus_id})")
        # Get campus users to filter by
        print(f"Fetching campus users for filtering...")
        cursus_users = client.get_campus_users(campus_id, MAIN_CURSUS_ID)
        campus_user_ids = set(cu.get('user', {}).get('id') for cu in cursus_users if cu.get('user', {}).get('id'))
        print(f"✓ Found {len(campus_user_ids)} users in campus {campus_id}")
    else:
        print("(No campus filtering - analyzing all users globally)")
        campus_user_ids = None
    
    # Map to store projects by user
    users_projects_map = {}
    total_api_calls = 0
    
    for i, project_id in enumerate(project_ids, 1):
        print(f"  [{i}/{len(project_ids)}] Fetching users for project ID {project_id}...")
        
        try:
            project_users = client.get_project_users(project_id)
            total_api_calls += 1
            
            # Add users who worked on this project (with optional campus filtering)
            for project_user in project_users:
                user = project_user.get('user', {})
                user_id = user.get('id')
                
                if user_id:
                    # Apply campus filter if provided
                    if campus_user_ids is not None and user_id not in campus_user_ids:
                        continue
                    
                    if user_id not in users_projects_map:
                        users_projects_map[user_id] = []
                    users_projects_map[user_id].append(project_user)
        except Exception as e:
            print(f"    ⚠ Error fetching project {project_id}: {e}")
            continue
    
    print(f"\n✓ Fetched data with {total_api_calls} API calls")
    print(f"✓ Found {len(users_projects_map)} users with Python projects")
    
    return users_projects_map


def process_user_from_projects(user_id: int, projects_map: Dict[int, List[Dict]], locations_map: Dict[int, List[Dict]], client: 'API42Client' = None, begin_at: str = None, end_at: str = None, new_common_core_only: bool = False) -> Dict:
    """
    Process a user's data using pre-fetched project and location data
    
    Args:
        user_id: User ID
        projects_map: Map of user_id -> projects list
        locations_map: Map of user_id -> locations list
        client: API client for cache validation
        begin_at: Start date for location filtering
        end_at: End date for location filtering
        new_common_core_only: If True, filter to only new common core modules
        
    Returns:
        Dictionary with user's Python project analysis
    """
    # Get projects and locations from pre-fetched maps
    projects = projects_map.get(user_id, [])
    locations = locations_map.get(user_id, [])
    
    if not projects:
        return None
    
    # Validate cached location data and refresh if bad cache detected
    # Note: Check 'is not None' instead of truthiness to handle empty lists []
    if client and locations is not None:
        locations = client.validate_and_refresh_locations(
            user_id, projects, locations, begin_at, end_at
        )
        # Update the map with validated locations
        locations_map[user_id] = locations
    
    # Extract user info from first project entry
    user = projects[0].get('user', {})
    login = user.get('login', 'unknown')
    email = user.get('email', '')
    
    # Extract campus information from user data
    campus_id = None
    campus_name = 'Unknown'
    if 'campus' in user and user['campus']:
        if isinstance(user['campus'], list) and len(user['campus']) > 0:
            # Campus is a list, take the first one
            campus_id = user['campus'][0].get('id')
            campus_name = user['campus'][0].get('name', 'Unknown')
        elif isinstance(user['campus'], dict):
            # Campus is a dict
            campus_id = user['campus'].get('id')
            campus_name = user['campus'].get('name', 'Unknown')
    
    # Filter to Python projects (optionally only new common core)
    python_projects = DataProcessor.filter_python_projects(projects, new_common_core_only=new_common_core_only)
    
    if not python_projects:
        return None
    
    # Analyze time spent on Python projects
    analysis = DataProcessor.analyze_python_time(python_projects, locations)
    
    # Try to get cursus level from first project (if available)
    cursus_level = 0
    if projects and projects[0].get('cursus_ids'):
        # cursus_level might not be directly available, set to 0 or extract from user data
        cursus_level = 0
    
    return {
        'user_id': user_id,
        'login': login,
        'email': email,
        'campus_id': campus_id,
        'campus_name': campus_name,
        'cursus_level': cursus_level,
        'python_projects': analysis,
        'total_python_hours': sum(p['time_spent_hours'] for p in analysis)
    }


def calculate_module_statistics(results: List[Dict]) -> Dict:
    """
    Calculate statistics for each module, overall averages, and campus comparisons
    
    Args:
        results: List of student data dictionaries
        
    Returns:
        Dictionary with module statistics, overall stats, and campus stats
    """
    from collections import defaultdict
    
    # Collect data per module
    module_data = defaultdict(lambda: {'times': [], 'students': 0, 'total_time': 0})
    
    # Collect data per campus
    campus_data = defaultdict(lambda: {
        'total_hours': 0,
        'students': 0,
        'projects_finished': 0,
        'projects_total': 0,
        'scores': []
    })
    
    for student in results:
        campus_name = student.get('campus_name', 'Unknown')
        campus_id = student.get('campus_id')
        
        # Track campus-level stats
        campus_data[campus_name]['students'] += 1
        campus_data[campus_name]['total_hours'] += student.get('total_python_hours', 0)
        
        for project in student['python_projects']:
            module_name = project['project_name']
            time_spent = project['time_spent_hours']
            
            # Module stats
            module_data[module_name]['times'].append(time_spent)
            module_data[module_name]['students'] += 1
            module_data[module_name]['total_time'] += time_spent
            
            # Campus project stats
            campus_data[campus_name]['projects_total'] += 1
            if project.get('status') == 'finished':
                campus_data[campus_name]['projects_finished'] += 1
            if project.get('final_mark') is not None:
                campus_data[campus_name]['scores'].append(project['final_mark'])
    
    # Calculate module averages
    module_stats = {}
    for module_name, data in module_data.items():
        module_stats[module_name] = {
            'total_students': data['students'],
            'total_time': data['total_time'],
            'average_time': data['total_time'] / data['students'] if data['students'] > 0 else 0,
            'min_time': min(data['times']) if data['times'] else 0,
            'max_time': max(data['times']) if data['times'] else 0,
        }
    
    # Calculate campus statistics
    campus_stats = {}
    for campus_name, data in campus_data.items():
        avg_hours = data['total_hours'] / data['students'] if data['students'] > 0 else 0
        completion_rate = (data['projects_finished'] / data['projects_total'] * 100) if data['projects_total'] > 0 else 0
        avg_score = sum(data['scores']) / len(data['scores']) if data['scores'] else 0
        
        campus_stats[campus_name] = {
            'students': data['students'],
            'total_hours': data['total_hours'],
            'average_hours': avg_hours,
            'projects_total': data['projects_total'],
            'projects_finished': data['projects_finished'],
            'completion_rate': completion_rate,
            'average_score': avg_score,
            'efficiency': avg_score / avg_hours if avg_hours > 0 else 0
        }
    
    # Calculate overall statistics
    total_hours = sum(s['total_python_hours'] for s in results)
    overall_stats = {
        'total_students': len(results),
        'total_hours': total_hours,
        'average_hours_per_student': total_hours / len(results) if results else 0,
        'total_campuses': len(campus_stats)
    }
    
    return {
        'modules': module_stats,
        'overall': overall_stats,
        'campuses': campus_stats
    }


def display_statistics(results: List[Dict], stats: Dict):
    """
    Display detailed statistics about modules and students
    
    Args:
        results: List of student data dictionaries
        stats: Statistics dictionary from calculate_module_statistics
    """
    print("\n" + "=" * 80)
    print("DETAILED STATISTICS")
    print("=" * 80)
    
    # Overall statistics
    print("\n📊 Overall Statistics:")
    print(f"  Total Students: {stats['overall']['total_students']}")
    print(f"  Total Hours: {stats['overall']['total_hours']:.2f}")
    print(f"  Average Hours per Student: {stats['overall']['average_hours_per_student']:.2f}")
    
    # Module statistics
    print("\n📚 Module Statistics:")
    print("-" * 80)
    print(f"{'Module Name':<40} {'Students':<12} {'Avg Time':<12} {'Total Time':<12}")
    print("-" * 80)
    
    # Sort modules by total time (descending)
    sorted_modules = sorted(
        stats['modules'].items(),
        key=lambda x: x[1]['total_time'],
        reverse=True
    )
    
    for module_name, module_stats in sorted_modules:
        print(f"{module_name:<40} {module_stats['total_students']:<12} "
              f"{module_stats['average_time']:<12.2f} {module_stats['total_time']:<12.2f}")
    
    # Campus statistics (if available)
    if 'campuses' in stats and stats['campuses']:
        print("\n🏫 Campus Statistics:")
        print("-" * 100)
        print(f"{'Campus Name':<30} {'Students':<10} {'Avg Hours':<12} {'Completion %':<15} {'Avg Score':<12}")
        print("-" * 100)
        
        # Sort campuses by number of students (descending)
        sorted_campuses = sorted(
            stats['campuses'].items(),
            key=lambda x: x[1]['students'],
            reverse=True
        )
        
        for campus_name, campus_stats in sorted_campuses:
            print(f"{campus_name:<30} {campus_stats['students']:<10} "
                  f"{campus_stats['average_hours']:<12.2f} {campus_stats['completion_rate']:<15.1f} "
                  f"{campus_stats['average_score']:<12.1f}")
    
    print("-" * 80)
    
    # Individual student breakdown
    print("\n👥 Individual Student Breakdown:")
    print("-" * 80)
    
    for student in results[:10]:  # Show top 10
        print(f"\n  Student: {student['login']} (Level: {student['cursus_level']:.2f})")
        print(f"  Total Time: {student['total_python_hours']:.2f} hours")
        print(f"  Projects:")
        
        for project in student['python_projects']:
            print(f"    • {project['project_name']:<40} {project['time_spent_hours']:>8.2f}h "
                  f"[{project['status']}] Mark: {project['final_mark']}")





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
        
        # Let user select campus
        selected_campus_id = select_campus(client)
        
        # PROJECT-BASED USER FETCHING
        print("\n" + "=" * 60)
        print("PROJECT-BASED USER FETCHING")
        if selected_campus_id:
            print(f"(Filtering to campus ID: {selected_campus_id})")
        else:
            print("(No campus filtering - analyzing all users)")
        print("=" * 60)
        
        # Step 1: Get Python project IDs
        python_project_ids = get_python_project_ids(client, MAIN_CURSUS_ID)
        
        if not python_project_ids:
            print("\n✗ No Python projects found in this cursus")
            return
        
        # Step 2: Fetch users from each Python project (with optional campus filtering)
        projects_map = fetch_users_by_projects(client, python_project_ids, selected_campus_id)
        
        if not projects_map:
            print("\n✗ No users found working on Python projects")
            return
        
        # Step 3: Fetch locations only for users who have Python projects
        python_users = list(projects_map.keys())
        print(f"\nFetching locations for {len(python_users)} users with Python projects...")
        locations_map = client.get_locations_by_user_map(
            python_users,
            begin_at=LOCATION_BEGIN_DATE,
            end_at=LOCATION_END_DATE
        )
        
        print("\n" + "=" * 60)
        print("PROCESSING USERS")
        if USE_NEW_COMMON_CORE_ONLY:
            print("(Filtering for NEW COMMON CORE Python modules only)")
        print("=" * 60)
        
        # Process users who have Python projects
        results = []
        for i, user_id in enumerate(projects_map.keys(), 1):
            user_data = process_user_from_projects(
                user_id,
                projects_map, 
                locations_map,
                client=client,
                begin_at=LOCATION_BEGIN_DATE,
                end_at=LOCATION_END_DATE,
                new_common_core_only=USE_NEW_COMMON_CORE_ONLY
            )
            if user_data:
                results.append(user_data)
                print(f"[{i}/{len(projects_map)}] {user_data['login']}: {user_data['total_python_hours']:.2f}h across {len(user_data['python_projects'])} projects")
            else:
                # Get login from projects if available
                projects = projects_map.get(user_id, [])
                login = projects[0].get('user', {}).get('login', 'unknown') if projects else 'unknown'
                print(f"[{i}/{len(projects_map)}] {login}: No Python projects (after filtering)")
        
        # Save results
        output_file = f"python_time_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print("\n" + "=" * 60)
        print(f"Analysis complete!")
        print(f"Total users processed: {len(projects_map)}")
        print(f"Users with Python projects: {len(results)}")
        if USE_NEW_COMMON_CORE_ONLY:
            print(f"(Filtered for NEW COMMON CORE modules only)")
        print(f"Results saved to: {output_file}")
        
        # Calculate and display statistics
        if results:
            stats = calculate_module_statistics(results)
            display_statistics(results, stats)
            
            # Generate interactive dashboard
            try:
                print("\n📊 Generating interactive dashboard...")
                generator = DashboardGenerator(results, stats)
                dashboard_file = generator.generate(output_file)
                print(f"  ✓ Dashboard saved to: {dashboard_file}")
                print(f"  ✓ Open in browser to view interactive visualizations!")
            except Exception as e:
                print(f"\n⚠️  Could not generate dashboard: {e}")
                import traceback
                traceback.print_exc()
        
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
