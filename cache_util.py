"""
Cache management utility script
Provides commands to manage the cache
"""

import sys
import os
from dotenv import load_dotenv
from cache_manager import CacheManager
from api_client import API42Client


def show_cache_stats():
    """Show cache statistics"""
    cache = CacheManager()
    stats = cache.get_cache_stats()
    
    print("\n" + "=" * 60)
    print("CACHE STATISTICS")
    print("=" * 60)
    print(f"Cache directory: {stats['cache_dir']}")
    print(f"Total files: {stats['total_files']}")
    print(f"Total size: {stats['total_size_mb']} MB ({stats['total_size_bytes']:,} bytes)")
    print("=" * 60 + "\n")


def clear_cache():
    """Clear all cached data"""
    cache = CacheManager()
    cache.clear()
    print("\n✓ Cache cleared successfully!\n")


def validate_cache():
    """Validate cached data"""
    cache = CacheManager()
    stats = cache.get_cache_stats()
    
    print("\n" + "=" * 60)
    print("CACHE VALIDATION")
    print("=" * 60)
    
    if stats['total_files'] == 0:
        print("No cached files found.")
    else:
        print(f"Found {stats['total_files']} cached files")
        print("Cache appears to be valid.")
    
    print("=" * 60 + "\n")


def test_connection():
    """Test API connection and authentication"""
    load_dotenv()
    
    keys = []
    idx = 1
    while True:
        cid = os.getenv(f'CLIENT_ID_{idx}')
        csec = os.getenv(f'CLIENT_SECRET_{idx}')
        if cid and csec:
            keys.append((cid, csec))
            idx += 1
        else:
            break
    if not keys:
        client_id = os.getenv('CLIENT_ID')
        client_secret = os.getenv('CLIENT_SECRET')
        if client_id and client_secret:
            keys.append((client_id, client_secret))
    
    if not keys:
        print("\n✗ Error: Missing API credentials in .env file\n")
        return
    
    print(f"\nTesting API connection ({len(keys)} key(s))...")
    client = API42Client(keys=keys, use_cache=False)
    
    if client.authenticate():
        print("✓ Successfully connected to 42 API\n")
    else:
        print("✗ Failed to connect to 42 API\n")


def show_help():
    """Show help message"""
    print("""
╔══════════════════════════════════════════════════════════╗
║           CACHE MANAGEMENT UTILITY                       ║
╚══════════════════════════════════════════════════════════╝

Usage: python cache_util.py [command]

Commands:
  stats      Show cache statistics
  clear      Clear all cached data
  validate   Validate cached data integrity
  test       Test API connection
  help       Show this help message

Examples:
  python cache_util.py stats
  python cache_util.py clear
  python cache_util.py test
""")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    commands = {
        'stats': show_cache_stats,
        'clear': clear_cache,
        'validate': validate_cache,
        'test': test_connection,
        'help': show_help,
    }
    
    if command in commands:
        commands[command]()
    else:
        print(f"\n✗ Unknown command: {command}\n")
        show_help()


if __name__ == "__main__":
    main()
