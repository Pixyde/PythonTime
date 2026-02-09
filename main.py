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


def select_campus(client: API42Client) -> int:
    """
    Let user select a campus from the available list
    
    Args:
        client: API client instance
        
    Returns:
        Selected campus ID, or 0 for "all campuses"
    """
    print("\n" + "=" * 60)
    print("CAMPUS SELECTION")
    print("=" * 60)
    
    campuses = client.get_campuses()
    
    if not campuses:
        print("No campuses found. Using default (Le Havre, ID: 14)")
        return 14
    
    # Sort campuses by name for easier navigation
    campuses.sort(key=lambda c: c.get('name', ''))
    
    print("\nAvailable campuses:")
    print("-" * 60)
    print(f"  {'0':>3}. {'ALL CAMPUSES (Average Statistics)':<50}")
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
                print(f"\n✓ Selected: ALL CAMPUSES (will show average statistics per campus)")
                return 0  # Special value for "all campuses"
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
    
    python_keywords = ['python', 'py', 'django', 'flask', 'ft_transcendence']
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


def fetch_users_by_projects(client: API42Client, project_ids: List[int]) -> Dict[int, List[Dict]]:
    """
    Fetch users who worked on Python projects (project-based approach)
    
    Gets users directly from project endpoints without campus filtering.
    
    Args:
        client: API client instance
        project_ids: List of Python project IDs
        
    Returns:
        Dictionary mapping user_id -> list of their Python projects
    """
    print(f"\nFetching users for {len(project_ids)} Python projects...")
    print("(Getting users directly from project endpoints)")
    
    # Map to store projects by user
    users_projects_map = {}
    total_api_calls = 0
    
    for i, project_id in enumerate(project_ids, 1):
        print(f"  [{i}/{len(project_ids)}] Fetching users for project ID {project_id}...")
        
        try:
            project_users = client.get_project_users(project_id)
            total_api_calls += 1
            
            # Add all users who worked on this project
            for project_user in project_users:
                user = project_user.get('user', {})
                user_id = user.get('id')
                
                if user_id:
                    if user_id not in users_projects_map:
                        users_projects_map[user_id] = []
                    users_projects_map[user_id].append(project_user)
        except Exception as e:
            print(f"    ⚠ Error fetching project {project_id}: {e}")
            continue
    
    print(f"\n✓ Fetched data with {total_api_calls} API calls")
    print(f"✓ Found {len(users_projects_map)} users with Python projects")
    
    return users_projects_map


def process_all_campuses(client: API42Client, cursus_id: int = 21):
    """
    Process all campuses and calculate average statistics for each
    
    Args:
        client: API client instance
        cursus_id: Cursus ID to analyze
    """
    print("\n" + "=" * 60)
    print("PROCESSING ALL CAMPUSES - AVERAGE STATISTICS")
    print("=" * 60)
    
    campuses = client.get_campuses()
    
    if not campuses:
        print("No campuses found.")
        return
    
    # Get Python project IDs once (they're the same for all campuses)
    python_project_ids = get_python_project_ids(client, cursus_id)
    
    if not python_project_ids:
        print("\n✗ No Python projects found in this cursus")
        return
    
    campus_stats = []
    
    for campus in campuses:
        campus_id = campus.get('id')
        campus_name = campus.get('name', 'Unknown')
        
        print(f"\n{'='*60}")
        print(f"Processing: {campus_name} (ID: {campus_id})")
        print(f"{'='*60}")
        
        try:
            # Get students from campus
            cursus_users = client.get_campus_users(campus_id, cursus_id)
            
            if not cursus_users:
                print(f"  No students found in cursus {cursus_id}")
                continue
            
            students = get_all_students(cursus_users)
            user_ids = [cu.get('user', {}).get('id') for cu in students if cu.get('user', {}).get('id')]
            campus_user_ids = set(user_ids)
            
            print(f"  Found {len(students)} students")
            
            # Fetch project data
            projects_map = fetch_users_by_projects(client, python_project_ids, campus_user_ids)
            
            if not projects_map:
                print(f"  No students with Python projects")
                continue
            
            # Fetch location data
            python_users = list(projects_map.keys())
            locations_map = client.get_locations_by_user_map(
                python_users,
                begin_at=LOCATION_BEGIN_DATE,
                end_at=LOCATION_END_DATE
            )
            
            # Process students
            results = []
            for user_id in projects_map.keys():
                cursus_user = next((cu for cu in students if cu.get('user', {}).get('id') == user_id), None)
                if not cursus_user:
                    continue
                
                student_data = process_student_optimized(
                    cursus_user,
                    projects_map,
                    locations_map,
                    new_common_core_only=USE_NEW_COMMON_CORE_ONLY
                )
                if student_data:
                    results.append(student_data)
            
            # Calculate statistics for this campus
            if results:
                stats = calculate_module_statistics(results)
                
                campus_stat = {
                    'campus_id': campus_id,
                    'campus_name': campus_name,
                    'total_students': len(students),
                    'students_with_python': len(results),
                    'average_hours': stats['overall']['average_hours_per_student'],
                    'total_hours': stats['overall']['total_hours'],
                    'modules': stats['modules']
                }
                campus_stats.append(campus_stat)
                
                print(f"  ✓ Processed {len(results)} students with Python projects")
                print(f"  ✓ Average hours per student: {stats['overall']['average_hours_per_student']:.2f}")
            
        except Exception as e:
            print(f"  ✗ Error processing campus {campus_name}: {e}")
            continue
    
    # Display campus comparison
    display_campus_comparison(campus_stats)
    
    # Save results
    output_file = f"campus_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(campus_stats, f, indent=2)
    print(f"\n✓ Campus comparison saved to: {output_file}")


def display_campus_comparison(campus_stats: List[Dict]):
    """
    Display comparison statistics across all campuses
    
    Args:
        campus_stats: List of campus statistics dictionaries
    """
    print("\n" + "=" * 80)
    print("CAMPUS COMPARISON - AVERAGE STATISTICS")
    print("=" * 80)
    
    if not campus_stats:
        print("No campus data available")
        return
    
    # Sort by average hours
    sorted_campuses = sorted(campus_stats, key=lambda x: x['average_hours'], reverse=True)
    
    print("\n📊 Campus Rankings by Average Python Hours:")
    print("-" * 80)
    print(f"{'Rank':<6} {'Campus':<30} {'Students':<12} {'Avg Hours':<12} {'Total Hours':<12}")
    print("-" * 80)
    
    for rank, campus in enumerate(sorted_campuses, 1):
        print(f"{rank:<6} {campus['campus_name']:<30} "
              f"{campus['students_with_python']:<12} "
              f"{campus['average_hours']:<12.2f} "
              f"{campus['total_hours']:<12.2f}")
    
    print("-" * 80)
    
    # Overall statistics
    total_students = sum(c['students_with_python'] for c in campus_stats)
    total_hours = sum(c['total_hours'] for c in campus_stats)
    overall_avg = total_hours / total_students if total_students > 0 else 0
    
    print(f"\n📈 Overall Across All Campuses:")
    print(f"  Total Campuses: {len(campus_stats)}")
    print(f"  Total Students with Python: {total_students}")
    print(f"  Total Hours: {total_hours:.2f}")
    print(f"  Overall Average: {overall_avg:.2f} hours per student")
    
    # Module comparison across campuses
    print(f"\n📚 Module Averages Across Campuses:")
    print("-" * 80)
    
    # Collect all modules
    all_modules = set()
    for campus in campus_stats:
        all_modules.update(campus['modules'].keys())
    
    # Calculate average for each module across campuses
    module_averages = {}
    for module in all_modules:
        total_time = 0
        total_students = 0
        
        for campus in campus_stats:
            if module in campus['modules']:
                module_data = campus['modules'][module]
                total_time += module_data['total_time']
                total_students += module_data['total_students']
        
        if total_students > 0:
            module_averages[module] = total_time / total_students
    
    # Display top modules
    sorted_modules = sorted(module_averages.items(), key=lambda x: x[1], reverse=True)[:10]
    
    print(f"{'Module Name':<50} {'Avg Time (all campuses)':<20}")
    print("-" * 80)
    for module, avg_time in sorted_modules:
        print(f"{module:<50} {avg_time:<20.2f}")
    print("-" * 80)


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


def create_visualizations(results: List[Dict], stats: Dict, output_dir: str = "."):
    """
    Create visualizations for the data using matplotlib
    
    Args:
        results: List of student data dictionaries
        stats: Statistics dictionary
        output_dir: Directory to save visualizations
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend
    except ImportError:
        print("\n⚠️  Matplotlib not installed. Skipping visualizations.")
        print("   Install with: pip install matplotlib")
        return
    
    print("\n📈 Generating visualizations...")
    
    # 1. Module Average Time Bar Chart
    fig, ax = plt.subplots(figsize=(12, 8))
    
    modules = list(stats['modules'].keys())
    avg_times = [stats['modules'][m]['average_time'] for m in modules]
    
    # Sort by average time
    sorted_data = sorted(zip(modules, avg_times), key=lambda x: x[1], reverse=True)
    modules_sorted, avg_times_sorted = zip(*sorted_data) if sorted_data else ([], [])
    
    bars = ax.barh(range(len(modules_sorted)), avg_times_sorted, color='steelblue')
    ax.set_yticks(range(len(modules_sorted)))
    ax.set_yticklabels(modules_sorted, fontsize=9)
    ax.set_xlabel('Average Time (hours)', fontsize=12)
    ax.set_title('Average Time per Module', fontsize=14, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)
    
    # Add value labels on bars
    for i, (bar, time) in enumerate(zip(bars, avg_times_sorted)):
        ax.text(time + 0.5, i, f'{time:.1f}h', va='center', fontsize=8)
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/module_average_times.png", dpi=150, bbox_inches='tight')
    print(f"  ✓ Saved: {output_dir}/module_average_times.png")
    plt.close()
    
    # 2. Top Students Bar Chart
    fig, ax = plt.subplots(figsize=(10, 6))
    
    top_students = sorted(results, key=lambda x: x['total_python_hours'], reverse=True)[:15]
    logins = [s['login'] for s in top_students]
    hours = [s['total_python_hours'] for s in top_students]
    
    bars = ax.bar(range(len(logins)), hours, color='coral')
    ax.set_xticks(range(len(logins)))
    ax.set_xticklabels(logins, rotation=45, ha='right', fontsize=9)
    ax.set_ylabel('Total Hours', fontsize=12)
    ax.set_title('Top 15 Students by Total Python Hours', fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for bar, hour in zip(bars, hours):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{hour:.0f}h', ha='center', va='bottom', fontsize=8)
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/top_students.png", dpi=150, bbox_inches='tight')
    print(f"  ✓ Saved: {output_dir}/top_students.png")
    plt.close()
    
    # 3. Time Distribution Histogram
    fig, ax = plt.subplots(figsize=(10, 6))
    
    all_times = [s['total_python_hours'] for s in results]
    ax.hist(all_times, bins=20, color='mediumseagreen', edgecolor='black', alpha=0.7)
    ax.set_xlabel('Total Hours', fontsize=12)
    ax.set_ylabel('Number of Students', fontsize=12)
    ax.set_title('Distribution of Total Python Hours', fontsize=14, fontweight='bold')
    ax.axvline(stats['overall']['average_hours_per_student'], 
               color='red', linestyle='--', linewidth=2, label='Average')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/time_distribution.png", dpi=150, bbox_inches='tight')
    print(f"  ✓ Saved: {output_dir}/time_distribution.png")
    plt.close()
    
    print("  ✓ All visualizations generated successfully!")


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
        
        # Let user select campus (for reference/filtering if needed later)
        selected_campus_id = select_campus(client)
        
        # Check if user selected "all campuses"
        if selected_campus_id == 0:
            # Process all campuses and show comparison
            process_all_campuses(client, MAIN_CURSUS_ID)
            return
        
        print(f"\nNote: Selected campus ID {selected_campus_id} for reference")
        print("Fetching users directly from Python projects...")
        
        # SIMPLIFIED APPROACH: Get users directly from projects
        print("\n" + "=" * 60)
        print("PROJECT-BASED USER FETCHING")
        print("=" * 60)
        
        # Step 1: Get Python project IDs
        python_project_ids = get_python_project_ids(client, MAIN_CURSUS_ID)
        
        if not python_project_ids:
            print("\n✗ No Python projects found in this cursus")
            return
        
        # Step 2: Fetch users directly from each Python project
        projects_map = fetch_users_by_projects(client, python_project_ids)
        
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
        print("PROCESSING STUDENTS")
        if USE_NEW_COMMON_CORE_ONLY:
            print("(Filtering for NEW COMMON CORE Python modules only)")
        print("=" * 60)
        
        # Process only students who have Python projects
        results = []
        processed = 0
        for user_id in projects_map.keys():
            # Find the cursus_user for this user_id
            cursus_user = next((cu for cu in students if cu.get('user', {}).get('id') == user_id), None)
            if not cursus_user:
                continue
                
            processed += 1
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
                print(f"[{processed}/{len(projects_map)}] {login}: {student_data['total_python_hours']:.2f}h across {len(student_data['python_projects'])} projects")
            else:
                print(f"[{processed}/{len(projects_map)}] {login}: No Python projects (after filtering)")
        
        # Save results
        output_file = f"python_time_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print("\n" + "=" * 60)
        print(f"Analysis complete!")
        print(f"Total campus students: {len(students)}")
        print(f"Students with Python projects: {len(results)}")
        if USE_NEW_COMMON_CORE_ONLY:
            print(f"(Filtered for NEW COMMON CORE modules only)")
        print(f"Results saved to: {output_file}")
        
        # Calculate and display statistics
        if results:
            stats = calculate_module_statistics(results)
            display_statistics(results, stats)
            
            # Create visualizations
            try:
                create_visualizations(results, stats)
            except Exception as e:
                print(f"\n⚠️  Could not generate visualizations: {e}")
        
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
