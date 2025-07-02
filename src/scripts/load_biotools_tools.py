#!/usr/bin/env python3
"""
Bio.tools Integration Script
Loads bio.tools entries into ChromaDB.
Follows the same pattern as load_biopython_tools.py and load_bioconductor_tools.py

Usage:
    python src/scripts/load_biotools_tools.py

This will:
1. Collect all bio.tools entries (excluding Biopython and Bioconductor)
2. Load them into ChromaDB using SemanticSearchStore
3. Test search quality with bio.tools-specific queries
4. Generate a comprehensive report

Author: Based on existing loader patterns
"""

import asyncio
import sys
import os
from pathlib import Path
import time
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

async def main():
    """Main function to load bio.tools entries."""
    
    print("🧬 Bio.tools Integration for ChromaDB")
    print("=" * 50)
    print("Loading bio.tools entries into your ChromaDB...")
    print("Excluding Biopython and Bioconductor tools as requested")
    print("This will take 30-60 minutes for 30,000+ tools.\n")
    
    try:
        # Check internet connectivity
        print("🔍 Checking internet connectivity...")
        try:
            import requests
            test_response = requests.get("https://bio.tools", timeout=10)
            print(f"✅ Bio.tools API accessible! (Status: {test_response.status_code})")
        except Exception as e:
            print(f"❌ Internet connectivity issue: {e}")
            return False
        
        # Import required modules
        from biotools_collector import BioToolsCollector
        from src.db.chroma_store import SemanticSearchStore
        
        # Start data collection
        start_time = time.time()
        
        print("\n📊 Discovering all bio.tools entries...")
        print("⏱️  This process includes:")
        print("   • Fetching from bio.tools API")
        print("   • Excluding Biopython packages")
        print("   • Excluding Bioconductor packages")
        print("   • Processing tool metadata")
        
        collector = BioToolsCollector()
        biotools_entries = await collector.collect_and_save()
        
        if not biotools_entries:
            print("❌ No bio.tools entries found!")
            return False
        
        collection_time = time.time() - start_time
        print(f"✅ Discovered {len(biotools_entries)} bio.tools entries in {collection_time:.1f}s")
        
        # Initialize ChromaDB store
        print("\n💾 Initializing ChromaDB store...")
        store = SemanticSearchStore()
        
        # Check existing data
        existing_count = store.collection.count()
        print(f"📊 Existing tools in database: {existing_count}")
        
        # Add all bio.tools entries
        print("🔄 Adding bio.tools entries to ChromaDB...")
        integration_start = time.time()
        
        # Load tools from multiple JSON files
        all_tools = []
        data_dir = Path("data/biotools_collection")
        tool_files = sorted(data_dir.glob("complete_biotools_tools_*.json"))
        
        if tool_files:
            print(f"📁 Found {len(tool_files)} tool files to load")
            for file_path in tool_files:
                try:
                    with open(file_path, 'r') as f:
                        file_tools = json.load(f)
                        all_tools.extend(file_tools)
                        print(f"  ✅ Loaded {len(file_tools)} tools from {file_path.name}")
                except Exception as e:
                    print(f"  ❌ Error loading {file_path.name}: {e}")
            
            biotools_entries = all_tools
        
        # Process in batches to respect ChromaDB limits
        batch_size = 1000  # Safe batch size for ChromaDB
        total_batches = (len(biotools_entries) + batch_size - 1) // batch_size
        
        print(f"🔄 Processing {len(biotools_entries)} tools in {total_batches} batches...")
        
        success = True
        added_count = 0
        
        for i in range(0, len(biotools_entries), batch_size):
            batch = biotools_entries[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            try:
                batch_success = await store.add_tools(batch)
                if batch_success:
                    added_count += len(batch)
                    print(f"  ✅ Batch {batch_num}/{total_batches}: Added {len(batch)} tools")
                else:
                    print(f"  ❌ Batch {batch_num}/{total_batches}: Failed")
                    success = False
            except Exception as e:
                print(f"  ❌ Batch {batch_num}/{total_batches}: Error - {e}")
                success = False
        
        integration_time = time.time() - integration_start
        
        if success:
            new_count = store.collection.count()
            
            print(f"✅ Successfully added {added_count} tools!")
            print(f"⏱️  Integration completed in {integration_time:.1f} seconds")
            print(f"📊 Total tools in database: {new_count}")
            print(f"🚀 Tools per second: {added_count / integration_time:.1f}")
            
            # Test search quality
            await test_biotools_search(store)
            
            # Show success summary
            show_success_summary(biotools_entries, collection_time, integration_time)
            
            return True
        else:
            print("❌ Failed to integrate tools into ChromaDB")
            return False
            
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_biotools_search(store):
    """Test search quality with bio.tools-specific queries."""
    print("\n🧪 Testing search quality...")
    
    test_queries = [
        ("genome assembly tools", 3),
        ("mass spectrometry analysis", 3),
        ("CRISPR gene editing", 3),
        ("single cell RNA sequencing", 3),
        ("protein structure prediction", 3),
        ("variant calling pipeline", 3)
    ]
    
    all_passed = True
    
    for query, expected_min in test_queries:
        try:
            results = await store.semantic_search(query, n_results=5)
            result_count = len(results)
            
            if result_count >= expected_min:
                top_score = results[0]['relevance_score'] if results else 0
                print(f"  ✅ '{query}' → {result_count} results")
                if results:
                    print(f"      Top: {results[0]['name']} (Score: {top_score:.2f})")
            else:
                print(f"  ⚠️  '{query}' → Only {result_count} results (expected {expected_min}+)")
                all_passed = False
        except Exception as e:
            print(f"  ❌ '{query}' → Error: {e}")
            all_passed = False
    
    if all_passed:
        print("\n✅ All search quality tests passed!")
    else:
        print("\n⚠️  Some searches returned fewer results than expected")
        print("   This is normal if you have a filtered dataset")

def show_success_summary(tools, collection_time, integration_time):
    """Show detailed success summary."""
    total_time = collection_time + integration_time
    
    print(f"\n🎉 Bio.tools integration completed successfully!")
    print(f"📊 Summary:")
    print(f"   • Bio.tools entries collected: {len(tools)}")
    print(f"   • Collection time: {collection_time:.1f} seconds ({collection_time/60:.1f} minutes)")
    print(f"   • Integration time: {integration_time:.1f} seconds") 
    print(f"   • Total time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    print(f"   • Performance: {len(tools) / total_time:.1f} tools/second")
    
    # Count categories
    categories = {}
    for tool in tools:
        cat = tool.get('category', 'Unknown')
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"\n🏷️  Categories discovered: {len(categories)}")
    top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:8]
    for cat, count in top_categories:
        print(f"   • {cat}: {count} tools")
    
    # Count programming languages
    languages = {}
    for tool in tools:
        lang = tool.get('programming_language', 'Not specified')
        for l in lang.split(', '):
            if l and l != 'Not specified':
                languages[l] = languages.get(l, 0) + 1
    
    if languages:
        print(f"\n💻 Top programming languages:")
        top_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)[:5]
        for lang, count in top_langs:
            print(f"   • {lang}: {count} tools")
    
    # Show sample tools
    print(f"\n📦 Sample tools:")
    for i, tool in enumerate(tools[:5]):
        print(f"   {i+1}. {tool['name']}: {tool['description'][:60]}...")
    
    print(f"\n🎯 Next Steps:")
    print("1. Test with your agent: Results now include bio.tools entries")
    print("2. Search for specific tools: Try 'BLAST', 'Cytoscape', 'GATK'")
    print("3. Run update checker: python src/scripts/check_and_update_packages.py")
    print("4. Check detailed report: data/biotools_collection/")
    print("\n🚀 Your ChromaDB now contains tools from:")
    print("   • Biopython (Python packages)")
    print("   • Bioconductor (R packages)")
    print("   • Bio.tools (30,000+ diverse tools)")

def check_prerequisites():
    """Check if all required dependencies are available."""
    missing_deps = []
    
    try:
        import requests
    except ImportError:
        missing_deps.append("requests")
    
    try:
        import chromadb
    except ImportError:
        missing_deps.append("chromadb")
    
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
    except ImportError:
        missing_deps.append("langchain-community")
    
    if missing_deps:
        print("❌ Missing dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\nInstall missing dependencies with:")
        print(f"  pip install {' '.join(missing_deps)}")
        return False
    
    return True

def check_file_structure():
    """Check if required files are in the correct locations."""
    script_dir = Path(__file__).parent
    collector_file = script_dir / "biotools_collector.py"
    
    if not collector_file.exists():
        print("❌ Missing file: biotools_collector.py")
        print(f"   Expected location: {collector_file}")
        print("   Please ensure the collector is in the scripts folder.")
        return False
    
    # Check if ChromaDB store exists
    db_file = Path(__file__).parent.parent / "db" / "chroma_store.py"
    if not db_file.exists():
        print("❌ Missing file: src/db/chroma_store.py")
        print("   This is required for ChromaDB integration")
        return False
    
    return True

def show_integration_info():
    """Show information about the integration and get user confirmation."""
    print("\n📋 Bio.tools Integration Information")
    print("-" * 50)
    print("This script will:")
    print("1. Fetch ALL tools from bio.tools API (~30,000+ entries)")
    print("2. EXCLUDE Biopython packages (already in your DB)")
    print("3. EXCLUDE Bioconductor packages (already in your DB)")
    print("4. Add remaining tools to your ChromaDB")
    print("\n⏱️  Estimated time: 30-60 minutes")
    print("💾 Disk space needed: ~200-500 MB")
    print("\n⚠️  Note: The script saves progress every 50 pages")
    print("   If interrupted, data is not lost")
    
    response = input("\nProceed with bio.tools integration? (y/N): ").strip().lower()
    return response in ['y', 'yes']

if __name__ == "__main__":
    print("🔍 Checking prerequisites and file structure...")
    
    if not check_prerequisites():
        print("\n💡 Install missing dependencies first")
        sys.exit(1)
    
    if not check_file_structure():
        print("\n📁 Ensure all required files are in place")
        sys.exit(1)
    
    print("✅ All prerequisites and files found!")
    
    # Show integration information and get user confirmation
    if not show_integration_info():
        print("❌ Integration cancelled by user.")
        sys.exit(0)
    
    print("\n🚀 Starting bio.tools integration...")
    
    # Run the integration
    success = asyncio.run(main())
    
    if not success:
        print("\n⚠️  Integration failed. Check the error messages above.")
        sys.exit(1)
    else:
        print("\n🌟 SUCCESS: Bio.tools entries successfully integrated!")