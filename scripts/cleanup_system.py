#!/usr/bin/env python3
"""
Cleanup script voor VSM Freezer Demo Backend.

Wis alle chats, sessies, logs en cache bestanden.
INCLUSIEF opgeslagen conversations in Weaviate.
"""

import os
import sys
import shutil
import asyncio
from pathlib import Path
from typing import List

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def remove_directory(path: Path, description: str) -> bool:
    """Remove directory if it exists."""
    if path.exists() and path.is_dir():
        try:
            shutil.rmtree(path)
            print(f"✅ Verwijderd: {description} ({path})")
            return True
        except Exception as e:
            print(f"❌ Fout bij verwijderen {description}: {e}")
            return False
    else:
        print(f"⏭️  Niet gevonden: {description} ({path})")
        return False


def remove_file(path: Path, description: str) -> bool:
    """Remove file if it exists."""
    if path.exists() and path.is_file():
        try:
            path.unlink()
            print(f"✅ Verwijderd: {description} ({path})")
            return True
        except Exception as e:
            print(f"❌ Fout bij verwijderen {description}: {e}")
            return False
    else:
        print(f"⏭️  Niet gevonden: {description} ({path})")
        return False


def cleanup_logs():
    """Clean up all log files."""
    print("\n📋 Logs opschonen...")
    logs_dir = PROJECT_ROOT / "elysia" / "logs"
    
    removed = []
    
    # Remove session logs
    sessions_dir = logs_dir / "sessions"
    users_dir = logs_dir / "users"
    sessions_log = logs_dir / "sessions.jsonl"
    
    removed.append(remove_directory(sessions_dir, "Session logs directory"))
    removed.append(remove_directory(users_dir, "User logs directory"))
    removed.append(remove_file(sessions_log, "Sessions JSONL log"))
    
    # Remove application logs (but keep directory)
    log_files = [
        ("elysia.log", "Elysia log"),
        ("elysia.log.1", "Elysia log.1"),
        ("elysia.log.2", "Elysia log.2"),
        ("uvicorn.log", "Uvicorn log"),
    ]
    
    for filename, description in log_files:
        log_path = logs_dir / filename
        removed.append(remove_file(log_path, description))
    
    return any(removed)


def cleanup_user_configs():
    """Clean up user config files (but keep __init__.py)."""
    print("\n📋 User configs opschonen...")
    configs_dir = PROJECT_ROOT / "elysia" / "api" / "user_configs"
    
    removed = []
    
    if configs_dir.exists():
        for item in configs_dir.iterdir():
            if item.is_file() and item.name != "__init__.py" and item.suffix == ".json":
                removed.append(remove_file(item, f"User config: {item.name}"))
    
    return any(removed)


def cleanup_python_cache():
    """Clean up Python __pycache__ directories."""
    print("\n📋 Python cache opschonen...")
    
    removed = []
    cache_dirs = []
    
    # Find all __pycache__ directories
    for root, dirs, files in os.walk(PROJECT_ROOT):
        if "__pycache__" in dirs:
            cache_path = Path(root) / "__pycache__"
            cache_dirs.append(cache_path)
    
    for cache_dir in cache_dirs:
        removed.append(remove_directory(cache_dir, f"Python cache: {cache_dir.relative_to(PROJECT_ROOT)}"))
    
    return any(removed)


def cleanup_backup_files():
    """Clean up backup files."""
    print("\n📋 Backup bestanden opschonen...")
    
    removed = []
    backup_files = []
    
    # Find all .backup files
    for root, dirs, files in os.walk(PROJECT_ROOT):
        for file in files:
            if file.endswith(".backup"):
                backup_path = Path(root) / file
                backup_files.append(backup_path)
    
    for backup_file in backup_files:
        removed.append(remove_file(backup_file, f"Backup: {backup_file.relative_to(PROJECT_ROOT)}"))
    
    return any(removed)


async def cleanup_weaviate_conversations():
    """Clean up saved conversations from Weaviate."""
    print("\n📋 Weaviate conversations opschonen...")
    
    try:
        # Import here to avoid issues if not in venv
        from elysia.util.client import ClientManager
        from weaviate.classes.query import Filter
        
        # Create client manager
        client_manager = ClientManager()
        
        if not client_manager.is_client:
            print("⏭️  Weaviate niet geconfigureerd (WCD_URL/WCD_API_KEY niet ingesteld)")
            return False
        
        removed_count = 0
        
        async with client_manager.connect_to_async_client() as client:
            # Check if ELYSIA_TREES__ collection exists
            collection_name = "ELYSIA_TREES__"
            
            if not await client.collections.exists(collection_name):
                print(f"⏭️  Geen {collection_name} collectie gevonden")
                return False
            
            collection = client.collections.get(collection_name)
            
            # Get all saved trees
            results = await collection.query.fetch_objects(limit=1000)
            
            if not results.objects:
                print(f"⏭️  Geen opgeslagen conversations gevonden")
                return False
            
            print(f"🔍 Gevonden: {len(results.objects)} opgeslagen conversation(s)")
            
            # Delete all trees
            for obj in results.objects:
                try:
                    await collection.data.delete_by_id(obj.uuid)
                    removed_count += 1
                except Exception as e:
                    print(f"⚠️  Fout bij verwijderen conversation {obj.uuid}: {e}")
            
            print(f"✅ Verwijderd: {removed_count} conversation(s) uit Weaviate")
            return True
            
    except ImportError as e:
        print(f"⚠️  Kan Weaviate libraries niet laden: {e}")
        return False
    except Exception as e:
        print(f"❌ Fout bij opschonen Weaviate conversations: {e}")
        return False


def main():
    """Main cleanup function."""
    print("🧹 VSM Freezer Demo Backend - Systeem opschoning\n")
    print("=" * 60)
    
    # Ask for confirmation
    print("Dit script verwijdert:")
    print("  - Alle chat sessies en logs")
    print("  - Opgeslagen conversations in Weaviate")
    print("  - User configs en Python cache")
    print("  - Backup bestanden")
    print()
    response = input("Weet je zeker dat je ALLES wilt verwijderen? (ja/n): ")
    if response.lower() not in ["ja", "j", "yes", "y"]:
        print("❌ Geannuleerd.")
        return
    
    print("\n" + "=" * 60)
    
    # Run cleanup functions
    results = {
        "logs": cleanup_logs(),
        "user_configs": cleanup_user_configs(),
        "python_cache": cleanup_python_cache(),
        "backup_files": cleanup_backup_files(),
    }
    
    # Run async cleanup for Weaviate
    try:
        weaviate_result = asyncio.run(cleanup_weaviate_conversations())
        results["weaviate_conversations"] = weaviate_result
    except Exception as e:
        print(f"❌ Fout bij Weaviate cleanup: {e}")
        results["weaviate_conversations"] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Samenvatting:")
    print("=" * 60)
    
    total_removed = sum(results.values())
    
    for category, removed in results.items():
        status = "✅ Opgeschoond" if removed else "⏭️  Geen bestanden gevonden"
        print(f"  {category.replace('_', ' ').title()}: {status}")
    
    print("\n" + "=" * 60)
    
    if total_removed > 0:
        print(f"✅ Opschoning voltooid! {total_removed} categorie(ën) opgeschoond.")
    else:
        print("ℹ️  Geen bestanden gevonden om op te schonen.")
    
    print("\n💡 Volgende stappen:")
    print("   1. Herstart de Elysia server: elysia start")
    print("   2. Ververs de browser (hard refresh: Cmd+Shift+R)")
    print("   3. Alle oude chats zijn nu weg!")


if __name__ == "__main__":
    main()

