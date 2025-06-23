# src/scripts/reset_chromadb.py

"""
ChromaDB Reset Script
Safely reset your ChromaDB to start fresh with clean data.

Usage:
    python src/scripts/reset_chromadb.py

This will:
1. Show current database contents
2. Ask for confirmation
3. Delete all existing data
4. Reinitialize clean ChromaDB
5. Verify the reset was successful

Author: Nitanshu (ChromaDB & RAG Pipeline)
"""

import sys
import os
from pathlib import Path
import shutil
import time

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

def show_current_database_info():
    """Show information about current database state."""
    print("📊 Current ChromaDB Information:")
    print("-" * 40)
    
    try:
        from src.db.chroma_store import SemanticSearchStore
        
        # Initialize store to check current state
        store = SemanticSearchStore()
        
        # Get current count
        current_count = store.collection.count()
        print(f"📈 Total tools in database: {current_count}")
        
        if current_count > 0:
            # Get sample of current data
            sample_data = store.collection.get(limit=5)
            
            if sample_data['documents']:
                print(f"\n📋 Sample entries (showing first 5):")
                for i, doc in enumerate(sample_data['documents'][:5]):
                    metadata = sample_data['metadatas'][i] if sample_data['metadatas'] else {}
                    name = metadata.get('name', 'Unknown')
                    source = metadata.get('source', 'Unknown')
                    print(f"  {i+1}. {name} (Source: {source})")
                    print(f"     Content: {doc[:100]}{'...' if len(doc) > 100 else ''}")
            
            # Check sources
            if sample_data['metadatas']:
                sources = set()
                for metadata in sample_data['metadatas']:
                    if metadata:
                        sources.add(metadata.get('source', 'Unknown'))
                
                print(f"\n🏷️  Data sources found: {', '.join(sources)}")
        else:
            print("📭 Database is already empty.")
        
        return current_count
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return -1

def reset_chromadb_directory():
    """Reset ChromaDB by deleting the data directory."""
    print("\n🗑️  Resetting ChromaDB directory...")
    
    # Default ChromaDB directory
    chroma_dir = project_root / "data" / "chroma"
    
    try:
        if chroma_dir.exists():
            print(f"📁 Deleting directory: {chroma_dir}")
            shutil.rmtree(chroma_dir)
            print("✅ ChromaDB directory deleted successfully")
        else:
            print("📁 ChromaDB directory doesn't exist - already clean")
        
        # Create fresh directory
        chroma_dir.mkdir(parents=True, exist_ok=True)
        print("📁 Created fresh ChromaDB directory")
        
        return True
        
    except Exception as e:
        print(f"❌ Error resetting directory: {e}")
        return False

def verify_reset():
    """Verify that the reset was successful."""
    print("\n🔍 Verifying reset...")
    
    try:
        from src.db.chroma_store import SemanticSearchStore
        
        # Initialize fresh store
        store = SemanticSearchStore()
        
        # Check count
        count = store.collection.count()
        
        if count == 0:
            print("✅ Reset successful - database is empty")
            return True
        else:
            print(f"⚠️  Reset may have failed - still {count} items in database")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying reset: {e}")
        return False

def reset_with_confirmation():
    """Reset ChromaDB with user confirmation."""
    print("🧹 ChromaDB Reset Tool")
    print("=" * 30)
    
    # Show current state
    current_count = show_current_database_info()
    
    if current_count == -1:
        print("❌ Could not check database state. Continuing anyway...")
    elif current_count == 0:
        print("\n✅ Database is already empty - no reset needed!")
        return True
    
    # Ask for confirmation
    print(f"\n⚠️  WARNING: This will permanently delete all data in ChromaDB")
    if current_count > 0:
        print(f"   This includes {current_count} existing tools/entries")
    
    print("\n❓ Are you sure you want to reset ChromaDB?")
    print("   Type 'yes' to confirm, anything else to cancel:")
    
    confirmation = input("   > ").strip().lower()
    
    if confirmation != 'yes':
        print("❌ Reset cancelled by user")
        return False
    
    print("\n🚀 Starting reset process...")
    
    # Perform reset
    success = reset_chromadb_directory()
    
    if not success:
        print("❌ Reset failed!")
        return False
    
    # Verify reset
    time.sleep(1)  # Give it a moment
    verified = verify_reset()
    
    if verified:
        print("\n🎉 ChromaDB reset completed successfully!")
        print("✨ You now have a clean, empty database ready for fresh data")
        print("\n🎯 Next steps:")
        print("1. Run Biopython integration: python src/scripts/load_biopython_tools.py")
        print("2. Or add your own data: python src/scripts/initialize_store.py")
        return True
    else:
        print("❌ Reset verification failed")
        return False

def quick_reset():
    """Quick reset without confirmation (for automation)."""
    print("🚀 Quick ChromaDB Reset (No Confirmation)")
    print("-" * 40)
    
    success = reset_chromadb_directory()
    if success:
        time.sleep(1)
        verified = verify_reset()
        if verified:
            print("✅ Quick reset completed successfully")
            return True
    
    print("❌ Quick reset failed")
    return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Reset ChromaDB database")
    parser.add_argument("--force", action="store_true", 
                       help="Reset without confirmation (USE WITH CAUTION)")
    parser.add_argument("--check-only", action="store_true",
                       help="Only check current database state, don't reset")
    
    args = parser.parse_args()
    
    if args.check_only:
        print("🔍 Checking ChromaDB state only...")
        show_current_database_info()
    elif args.force:
        print("⚠️  FORCE MODE - Resetting without confirmation!")
        success = quick_reset()
        sys.exit(0 if success else 1)
    else:
        success = reset_with_confirmation()
        sys.exit(0 if success else 1)