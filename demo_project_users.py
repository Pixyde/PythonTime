"""
Demo script showing how to use the efficient project users endpoint
"""

import os
from dotenv import load_dotenv
from api_client import API42Client


def demo_project_users():
    """
    Demonstrate using the efficient project users endpoint
    to find which users completed a specific project
    """
    print("=" * 60)
    print("Demo: Efficient Project User Queries")
    print("=" * 60)
    
    # Load credentials
    load_dotenv()
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("⚠️  Missing API credentials in .env file")
        print("This demo requires valid 42 API credentials to run")
        print("\nYou can still see the code example below:\n")
        show_code_example()
        return
    
    # Initialize client
    print("\nInitializing API client...")
    client = API42Client(client_id, client_secret)
    
    # Authenticate
    if not client.authenticate():
        print("✗ Authentication failed")
        return
    
    # Example 1: Get all users who worked on a specific project
    print("\n" + "=" * 60)
    print("Example 1: Get all users for a project")
    print("=" * 60)
    
    # You need to replace this with an actual project ID from your campus
    # Common Python project IDs vary by campus
    project_id = 1255  # Example: Python Module 00 (adjust for your campus)
    
    print(f"\nQuerying project ID: {project_id}")
    print("Note: Replace with an actual project ID from your campus")
    
    try:
        users = client.get_project_users(project_id)
        
        print(f"\n✓ Found {len(users)} users who worked on this project")
        
        # Analyze the results
        validated_users = [u for u in users if u.get('validated?', False)]
        in_progress = [u for u in users if u.get('status') == 'in_progress']
        
        print(f"  - Validated/Completed: {len(validated_users)}")
        print(f"  - In Progress: {len(in_progress)}")
        
        # Show top 5 users by final mark
        validated_sorted = sorted(
            validated_users, 
            key=lambda x: x.get('final_mark', 0), 
            reverse=True
        )[:5]
        
        if validated_sorted:
            print("\n  Top students:")
            for user_project in validated_sorted:
                user = user_project.get('user', {})
                login = user.get('login', 'unknown')
                mark = user_project.get('final_mark', 'N/A')
                print(f"    - {login}: {mark}/100")
    
    except Exception as e:
        print(f"✗ Error querying project: {e}")
        print("  Note: Make sure the project ID is valid for your campus")
    
    # Example 2: Check if specific user completed a project
    print("\n" + "=" * 60)
    print("Example 2: Check if a specific user completed a project")
    print("=" * 60)
    
    # Replace with actual user ID
    user_id = 12345  # Example user ID (adjust for your campus)
    
    print(f"\nChecking if user {user_id} completed project {project_id}")
    print("Note: Replace with actual user and project IDs")
    
    try:
        user_project = client.has_user_completed_project(user_id, project_id)
        
        if user_project:
            print(f"✓ User completed the project!")
            print(f"  - Status: {user_project.get('status')}")
            print(f"  - Validated: {user_project.get('validated?')}")
            print(f"  - Final Mark: {user_project.get('final_mark')}")
        else:
            print("✓ User did not work on this project")
    
    except Exception as e:
        print(f"✗ Error checking user: {e}")
    
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)


def show_code_example():
    """Show code example without actually running API calls"""
    example = '''
    from api_client import API42Client
    
    # Initialize and authenticate
    client = API42Client(client_id, client_secret)
    client.authenticate()
    
    # Method 1: Get all users for a specific project
    # Much more efficient than fetching all projects for all users
    project_id = 1255  # Python Module 00
    users = client.get_project_users(project_id)
    
    # Filter to completed projects
    completed = [u for u in users if u.get('validated?', False)]
    print(f"{len(completed)} users completed this project")
    
    # Method 2: Check if specific user completed a project
    user_id = 12345
    user_project = client.has_user_completed_project(user_id, project_id)
    
    if user_project:
        print(f"User completed with mark: {user_project['final_mark']}")
    else:
        print("User did not complete this project")
    
    # EFFICIENCY COMPARISON:
    # 
    # Old approach (fetch all projects for each user):
    # - For 200 users checking 1 project: 200 API calls
    # - Must parse all projects for each user
    # 
    # New approach (fetch users for specific project):
    # - For 200 users checking 1 project: 1 API call
    # - Get exactly the users who did this project
    # 
    # Result: ~200x improvement for single project queries!
    '''
    
    print("CODE EXAMPLE:")
    print(example)


if __name__ == "__main__":
    demo_project_users()
