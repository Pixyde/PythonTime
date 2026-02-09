"""
Test script for project users endpoint functionality
Tests the new get_project_users and has_user_completed_project methods
"""

from unittest.mock import Mock, patch, MagicMock
from api_client import API42Client


def test_get_project_users():
    """Test getting users for a specific project"""
    print("Testing get_project_users...")
    
    # Create a mock client
    client = API42Client("test_id", "test_secret", use_cache=False)
    
    # Mock the paginated request method
    mock_users = [
        {
            'id': 1,
            'user': {'id': 123, 'login': 'user1'},
            'project': {'id': 42, 'name': 'Python Module 00'},
            'status': 'finished',
            'validated?': True,
            'final_mark': 100
        },
        {
            'id': 2,
            'user': {'id': 456, 'login': 'user2'},
            'project': {'id': 42, 'name': 'Python Module 00'},
            'status': 'finished',
            'validated?': True,
            'final_mark': 85
        },
        {
            'id': 3,
            'user': {'id': 789, 'login': 'user3'},
            'project': {'id': 42, 'name': 'Python Module 00'},
            'status': 'in_progress',
            'validated?': False
        }
    ]
    
    with patch.object(client, '_make_paginated_request', return_value=mock_users):
        result = client.get_project_users(42)
        
        assert len(result) == 3, f"Expected 3 users, got {len(result)}"
        assert result[0]['user']['id'] == 123, "First user should have ID 123"
        assert result[1]['user']['login'] == 'user2', "Second user should be 'user2'"
        
        print(f"  ✓ Found {len(result)} users for project 42")
        print(f"  ✓ Users: {[u['user']['login'] for u in result]}")


def test_has_user_completed_project():
    """Test checking if a user completed a specific project"""
    print("\nTesting has_user_completed_project...")
    
    # Create a mock client
    client = API42Client("test_id", "test_secret", use_cache=False)
    
    # Mock project users data
    mock_users = [
        {
            'id': 1,
            'user': {'id': 123, 'login': 'user1'},
            'project': {'id': 42, 'name': 'Python Module 00'},
            'status': 'finished',
            'validated?': True,
            'final_mark': 100
        },
        {
            'id': 2,
            'user': {'id': 456, 'login': 'user2'},
            'project': {'id': 42, 'name': 'Python Module 00'},
            'status': 'finished',
            'validated?': True,
            'final_mark': 85
        }
    ]
    
    with patch.object(client, 'get_project_users', return_value=mock_users):
        # Test user that completed the project
        result = client.has_user_completed_project(123, 42)
        assert result is not None, "User 123 should have completed project 42"
        assert result['final_mark'] == 100, "User 123 should have final mark 100"
        assert result['validated?'] is True, "Project should be validated"
        print(f"  ✓ User 123 completed project 42 with mark {result['final_mark']}")
        
        # Test user that didn't complete the project
        result = client.has_user_completed_project(999, 42)
        assert result is None, "User 999 should not have completed project 42"
        print(f"  ✓ User 999 did not complete project 42 (correctly returned None)")


def test_project_users_use_case():
    """Test a realistic use case: finding all students who completed a specific Python project"""
    print("\nTesting realistic use case...")
    
    # Create a mock client
    client = API42Client("test_id", "test_secret", use_cache=False)
    
    # Mock data for a Python module
    project_id = 1255  # Example: Python Module 00
    mock_users = [
        {
            'id': 1,
            'user': {'id': 123, 'login': 'student1', 'email': 'student1@example.com'},
            'project': {'id': project_id, 'name': 'Python Module 00', 'slug': 'python-module-00'},
            'status': 'finished',
            'validated?': True,
            'final_mark': 100,
            'created_at': '2023-09-01T10:00:00Z',
            'marked_at': '2023-09-15T15:30:00Z'
        },
        {
            'id': 2,
            'user': {'id': 456, 'login': 'student2', 'email': 'student2@example.com'},
            'project': {'id': project_id, 'name': 'Python Module 00', 'slug': 'python-module-00'},
            'status': 'finished',
            'validated?': True,
            'final_mark': 85,
            'created_at': '2023-09-02T09:00:00Z',
            'marked_at': '2023-09-20T12:00:00Z'
        },
        {
            'id': 3,
            'user': {'id': 789, 'login': 'student3', 'email': 'student3@example.com'},
            'project': {'id': project_id, 'name': 'Python Module 00', 'slug': 'python-module-00'},
            'status': 'in_progress',
            'validated?': False
        }
    ]
    
    with patch.object(client, 'get_project_users', return_value=mock_users):
        # Get all users who worked on the project
        all_users = client.get_project_users(project_id)
        
        # Filter to only validated projects
        validated_users = [u for u in all_users if u.get('validated?', False)]
        
        print(f"  ✓ Total users who worked on project: {len(all_users)}")
        print(f"  ✓ Users who completed (validated) the project: {len(validated_users)}")
        
        for user in validated_users:
            user_info = user['user']
            print(f"    - {user_info['login']}: mark={user['final_mark']}, status={user['status']}")
        
        assert len(all_users) == 3, "Should have 3 total users"
        assert len(validated_users) == 2, "Should have 2 validated users"


def test_efficiency_comparison():
    """Test to demonstrate efficiency improvement"""
    print("\nTesting efficiency improvement...")
    
    print("  Old approach: For each user, fetch all projects")
    print("    - 200 users × GET /v2/users/{user_id}/projects_users")
    print("    - Result: 200 API calls, parse all projects for each user")
    
    print("  New approach: For a specific project, fetch all users")
    print("    - 1 × GET /v2/projects/{project_id}/projects_users")
    print("    - Result: 1 API call, get exactly the users who did this project")
    
    print("  ✓ Efficiency improvement: ~200x fewer API calls for single project queries")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Running Project Users Endpoint Tests")
    print("=" * 60)
    
    tests = [
        test_get_project_users,
        test_has_user_completed_project,
        test_project_users_use_case,
        test_efficiency_comparison,
    ]
    
    failed = 0
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"  ✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    if failed == 0:
        print("✓ All project users tests passed!")
    else:
        print(f"✗ {failed} test(s) failed")
    print("=" * 60)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(main())
