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


# Cursus ID for 42 cursus
MAIN_CURSUS_ID = 21

# Users to exclude from all data collection and analysis
EXCLUDED_USERS = ['suske', 'wkrati']

# New Common Core - Filter for only new common core modules
USE_NEW_COMMON_CORE_ONLY = True  # Set to True to filter only new common core modules

# Promo year filter — only include users whose cursus begin_at is in this year
# Set to None to include all years
PROMO_YEAR = 2025

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


def select_campus(client: API42Client) -> tuple:
    """
    Let user select a campus from the available list
    
    Args:
        client: API client instance
        
    Returns:
        Tuple of (campus_id, campus_name), or (None, None) for no filtering
    """
    print("\n" + "=" * 60)
    print("CAMPUS SELECTION")
    print("=" * 60)
    
    campuses = client.get_campuses()
    
    if not campuses:
        print("No campuses found. Analyzing all users globally.")
        return None, None
    
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
                return None, None
            elif 1 <= idx <= len(campuses):
                selected_campus = campuses[idx - 1]
                campus_id = selected_campus.get('id')
                campus_name = selected_campus.get('name')
                print(f"\n✓ Selected: {campus_name} (ID: {campus_id})")
                return campus_id, campus_name
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


def extract_user_ids(cursus_users: List[Dict]) -> set:
    """Extract unique user IDs from a list of cursus_user records."""
    return set(cu.get('user', {}).get('id') for cu in cursus_users if cu.get('user', {}).get('id'))


def fetch_users_by_projects(client: API42Client, project_ids: List[int], campus_id: int = None, promo_year: int = None) -> Dict[int, List[Dict]]:
    """
    Fetch users who worked on Python projects (project-based approach)
    
    Optionally filters by campus if campus_id is provided.
    When promo_year is set, the campus roster is filtered to that year.
    
    Args:
        client: API client instance
        project_ids: List of Python project IDs
        campus_id: Optional campus ID to filter users by
        promo_year: Optional year to filter campus roster by begin_at
        
    Returns:
        Dictionary mapping user_id -> list of their Python projects
    """
    print(f"\nFetching users for {len(project_ids)} Python projects...")
    if campus_id:
        print(f"(Will filter to campus ID: {campus_id}{f', promo {promo_year}' if promo_year else ''})")
        # Get campus users to filter by
        print(f"Fetching campus users for filtering...")
        cursus_users = client.get_campus_users(campus_id, MAIN_CURSUS_ID, begin_year=promo_year)
        campus_user_ids = extract_user_ids(cursus_users)
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
                login = user.get('login', '')
                
                if user_id:
                    # Skip staff/admin accounts
                    if user.get('staff?', False):
                        continue
                    # Skip excluded users early
                    if login in EXCLUDED_USERS:
                        continue
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


def process_user_from_projects(user_id: int, projects_map: Dict[int, List[Dict]], locations_map: Dict[int, List[Dict]], new_common_core_only: bool = False, campus_name: str = None, campus_id: int = None) -> Dict:
    """
    Process a user's data using pre-fetched project and location data
    
    Args:
        user_id: User ID
        projects_map: Map of user_id -> projects list
        locations_map: Map of user_id -> locations list
        new_common_core_only: If True, filter to only new common core modules
        campus_name: Optional campus name to attach to user record
        campus_id: Optional campus ID to attach to user record
        
    Returns:
        Dictionary with user's Python project analysis
    """
    # Get projects and locations from pre-fetched maps
    projects = projects_map.get(user_id, [])
    locations = locations_map.get(user_id, [])
    
    if not projects:
        return None
    
    # Extract user info from first project entry
    user = projects[0].get('user', {})
    login = user.get('login', 'unknown')
    email = user.get('email', '')
    
    # Skip excluded users
    if login in EXCLUDED_USERS:
        return None
    
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
    
    result = {
        'user_id': user_id,
        'login': login,
        'email': email,
        'cursus_level': cursus_level,
        'python_projects': analysis,
        'total_python_hours': sum(p['time_spent_hours'] for p in analysis)
    }
    
    # Attach campus info if available (used by campus comparison dashboard)
    if campus_name:
        result['campus_name'] = campus_name
    if campus_id is not None:
        result['campus_id'] = campus_id
    
    return result


def calculate_module_statistics(results: List[Dict]) -> Dict:
    """
    Calculate statistics for each module and overall averages
    
    Args:
        results: List of student data dictionaries
        
    Returns:
        Dictionary with module statistics and averages
    """
    from collections import defaultdict
    
    # Collect data per module
    module_data = defaultdict(lambda: {'times': [], 'students': 0, 'total_time': 0})
    
    for student in results:
        for project in student['python_projects']:
            module_name = project['project_name']
            time_spent = project['time_spent_hours']
            
            module_data[module_name]['times'].append(time_spent)
            module_data[module_name]['students'] += 1
            module_data[module_name]['total_time'] += time_spent
    
    # Calculate averages
    module_stats = {}
    for module_name, data in module_data.items():
        module_stats[module_name] = {
            'total_students': data['students'],
            'total_time': data['total_time'],
            'average_time': data['total_time'] / data['students'] if data['students'] > 0 else 0,
            'min_time': min(data['times']) if data['times'] else 0,
            'max_time': max(data['times']) if data['times'] else 0,
        }
    
    # Calculate overall statistics
    total_hours = sum(s['total_python_hours'] for s in results)
    overall_stats = {
        'total_students': len(results),
        'total_hours': total_hours,
        'average_hours_per_student': total_hours / len(results) if results else 0,
    }
    
    return {
        'modules': module_stats,
        'overall': overall_stats
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


def generate_dashboard(results: List[Dict], output_file: str, metadata: Dict = None):
    """
    Generate an interactive HTML dashboard from results.

    Assembles a comprehensive single-file dashboard from modular template
    parts in the dashboard/ directory.  The output contains 25 visualization
    types (24 standard + campus comparison), each with their own sliders
    and controls, plus global filters.

    Args:
        results: List of user data dictionaries
        output_file: Path to save the dashboard HTML file
        metadata: Optional metadata dict (promo totals, etc.)
    """
    print("\n📊 Generating interactive dashboard...")

    try:
        dashboard_dir = os.path.join(os.path.dirname(__file__), 'dashboard')

        # Read template parts
        def read_part(filename):
            path = os.path.join(dashboard_dir, filename)
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()

        template = read_part('template.html')
        styles = read_part('styles.css')
        core_js = read_part('core.js')

        # Read all chart modules in order
        chart_files = [
            'charts_flow.js',
            'charts_statistical.js',
            'charts_leaderboard.js',
            'charts_interactive.js',
            'charts_modulestats.js',
            'charts_campus.js',
        ]
        charts_js = '\n'.join(read_part(f) for f in chart_files)

        # Convert results to JSON
        data_json = json.dumps(results, indent=2)
        metadata_json = json.dumps(metadata or {}, indent=2)

        # Assemble dashboard: inject CSS, JS, and data into the template
        html = template
        html = html.replace('{{STYLES}}', styles)
        html = html.replace('{{CORE_JS}}', core_js)
        html = html.replace('{{CHARTS_JS}}', charts_js)
        html = html.replace('{{DATA_PLACEHOLDER}}', data_json)
        html = html.replace('{{METADATA_PLACEHOLDER}}', metadata_json)

        # Save dashboard
        dashboard_file = output_file.replace('.json', '_dashboard.html')
        with open(dashboard_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"  ✓ Dashboard saved to: {dashboard_file}")
        print(f"  ✓ Open in browser to view interactive visualizations!")

        return dashboard_file
    except Exception as e:
        print(f"  ⚠️  Could not generate dashboard: {e}")
        return None


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
        selected_campus_id, selected_campus_name = select_campus(client)
        
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
        projects_map = fetch_users_by_projects(client, python_project_ids, selected_campus_id, promo_year=PROMO_YEAR)
        
        if not projects_map:
            print("\n✗ No users found working on Python projects")
            return
        
        print("\n" + "=" * 60)
        print("PRE-FILTERING USERS")
        if USE_NEW_COMMON_CORE_ONLY:
            print("(Filtering for NEW COMMON CORE Python modules only)")
        print("=" * 60)
        
        # Build user -> campus mapping from existing campus data (no extra API calls)
        # When a campus is selected, all users belong to that campus.
        # When ALL is selected, resolve via get_campus_users (one call per campus, cached).
        user_campus_map = {}
        metadata = {'promo_year': PROMO_YEAR, 'total_promo_users': 0, 'campus_promo_totals': {}}
        if selected_campus_id:
            # Single campus — all users in projects_map belong to it
            for uid in projects_map:
                user_campus_map[uid] = (selected_campus_name, selected_campus_id)
            # Track promo totals (same API call as fetch_users_by_projects, cached)
            promo_users = client.get_campus_users(selected_campus_id, MAIN_CURSUS_ID, begin_year=PROMO_YEAR)
            promo_ids = extract_user_ids(promo_users)
            metadata['total_promo_users'] = len(promo_ids)
            if selected_campus_name:
                metadata['campus_promo_totals'][selected_campus_name] = len(promo_ids)
        else:
            # No campus filter — resolve by iterating campuses
            print("\nResolving campus info from campus rosters...")
            user_ids_set = set(projects_map.keys())
            campuses = client.get_campuses()
            for campus in campuses:
                cid = campus.get('id')
                cname = campus.get('name')
                if not cid or not cname:
                    continue
                cursus_users = client.get_campus_users(cid, MAIN_CURSUS_ID, begin_year=PROMO_YEAR)
                # Track total promo users per campus
                campus_all_ids = extract_user_ids(cursus_users)
                for uid in campus_all_ids:
                        if uid in user_ids_set and uid not in user_campus_map:
                            user_campus_map[uid] = (cname, cid)
                if campus_all_ids:
                    metadata['campus_promo_totals'][cname] = len(campus_all_ids)
            metadata['total_promo_users'] = sum(metadata['campus_promo_totals'].values())
            mapped = len(user_campus_map)
            print(f"✓ Mapped {mapped}/{len(projects_map)} users to campuses")
        
        # Pre-filter: only keep users who will appear in final results
        # This avoids fetching locations for users who would be discarded
        original_count = len(projects_map)
        filtered_user_ids = []
        for user_id in list(projects_map.keys()):
            # Skip users not in promo year roster
            if PROMO_YEAR and user_id not in user_campus_map:
                continue
            # Skip users with no new common core projects after filtering
            if USE_NEW_COMMON_CORE_ONLY:
                user_projects = projects_map.get(user_id, [])
                filtered = DataProcessor.filter_python_projects(user_projects, new_common_core_only=True)
                if not filtered:
                    continue
            filtered_user_ids.append(user_id)
        
        print(f"✓ Pre-filtered: {len(filtered_user_ids)}/{original_count} users have relevant Python modules")
        
        # Step 3: Fetch locations only for pre-filtered users
        print(f"\nFetching locations for {len(filtered_user_ids)} users...")
        locations_map = client.get_locations_by_user_map(
            filtered_user_ids,
            begin_at=LOCATION_BEGIN_DATE,
            end_at=LOCATION_END_DATE
        )
        
        print("\n" + "=" * 60)
        print("PROCESSING USERS")
        print("=" * 60)
        
        # Process pre-filtered users
        results = []
        zero_logtime_retries = 0
        for i, user_id in enumerate(filtered_user_ids, 1):
            # Determine campus from map
            if user_id in user_campus_map:
                c_name, c_id = user_campus_map[user_id]
            else:
                c_name = 'Not Found'
                c_id = None

            user_data = process_user_from_projects(
                user_id,
                projects_map, 
                locations_map,
                new_common_core_only=USE_NEW_COMMON_CORE_ONLY,
                campus_name=c_name,
                campus_id=c_id
            )
            if user_data:
                # If total hours is 0 and caching is enabled, the cached
                # location data may be stale.  Invalidate and re-fetch once.
                if user_data['total_python_hours'] == 0 and client.cache:
                    print(f"[{i}/{len(projects_map)}] {user_data['login']}: 0h detected — clearing cache and re-fetching locations...")
                    fresh_locations = client.refetch_user_locations(
                        user_id,
                        begin_at=LOCATION_BEGIN_DATE,
                        end_at=LOCATION_END_DATE
                    )
                    locations_map[user_id] = fresh_locations
                    zero_logtime_retries += 1
                    # Re-process with fresh location data
                    user_data = process_user_from_projects(
                        user_id,
                        projects_map,
                        locations_map,
                        new_common_core_only=USE_NEW_COMMON_CORE_ONLY,
                        campus_name=c_name,
                        campus_id=c_id
                    )
                    if user_data:
                        results.append(user_data)
                        print(f"[{i}/{len(projects_map)}] {user_data['login']}: {user_data['total_python_hours']:.2f}h across {len(user_data['python_projects'])} projects (after retry)")
                    else:
                        projects = projects_map.get(user_id, [])
                        login = projects[0].get('user', {}).get('login', 'unknown') if projects else 'unknown'
                        print(f"[{i}/{len(projects_map)}] {login}: No Python projects (after retry)")
                else:
                    results.append(user_data)
                    print(f"[{i}/{len(projects_map)}] {user_data['login']}: {user_data['total_python_hours']:.2f}h across {len(user_data['python_projects'])} projects")
            else:
                # Get login from projects if available
                projects = projects_map.get(user_id, [])
                login = projects[0].get('user', {}).get('login', 'unknown') if projects else 'unknown'
                print(f"[{i}/{len(projects_map)}] {login}: No Python projects (after filtering)")
        
        if zero_logtime_retries:
            print(f"\n⟳ Re-fetched locations for {zero_logtime_retries} user(s) with 0h logtime")
        
        # Save results
        output_file = f"python_time_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print("\n" + "=" * 60)
        print(f"Analysis complete!")
        print(f"Total users processed: {len(filtered_user_ids)}")
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
                generate_dashboard(results, output_file, metadata)
            except Exception as e:
                print(f"\n⚠️  Could not generate dashboard: {e}")
        
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
