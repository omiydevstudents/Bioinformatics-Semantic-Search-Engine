# src/scripts/load_biopython_tools.py

"""
Simple Biopython Integration Script
Loads ALL 200+ Biopython tools into your existing ChromaDB.

Usage:
    python src/scripts/load_biopython_tools.py

This will:
1. Discover all Biopython modules, functions, and classes
2. Load them into your existing ChromaDB using SemanticSearchStore
3. Test search quality with Biopython-specific queries
4. Generate a comprehensive report

Author: Nitanshu (ChromaDB & RAG Pipeline)
"""

import asyncio
import sys
import os
from pathlib import Path
import time

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

async def main():
    """Main function to load Biopython tools."""
    
    print("🧬 Biopython Tools Integration for ChromaDB")
    print("=" * 50)
    print("Loading ALL Biopython tools into your ChromaDB...")
    print("This will take 30-60 seconds to complete.\n")
    
    try:
        # Check Biopython availability
        print("🔍 Checking Biopython availability...")
        try:
            import Bio
            bio_version = getattr(Bio, '__version__', 'unknown')
            print(f"✅ Biopython {bio_version} found!")
        except ImportError:
            print("❌ Biopython not found!")
            print("Install it with: pip install biopython")
            return False
        
        # Import required modules (now from scripts folder)
        from biopython_tools_collector import CompleteBiopythonCollector
        from src.db.chroma_store import SemanticSearchStore
        
        # Start data collection
        start_time = time.time()
        
        print("\n📊 Discovering all Biopython tools...")
        collector = CompleteBiopythonCollector()
        biopython_tools = await collector.collect_and_save()
        
        if not biopython_tools:
            print("❌ No Biopython tools found!")
            return False
        
        collection_time = time.time() - start_time
        print(f"✅ Discovered {len(biopython_tools)} Biopython tools in {collection_time:.1f}s")
        
        # Initialize ChromaDB store
        print("\n💾 Initializing ChromaDB store...")
        store = SemanticSearchStore()
        
        # Check existing data
        existing_count = store.collection.count()
        print(f"📊 Existing tools in database: {existing_count}")
        
        # Add all Biopython tools
        print("🔄 Adding Biopython tools to ChromaDB...")
        integration_start = time.time()
        
        success = await store.add_tools(biopython_tools)
        
        integration_time = time.time() - integration_start
        
        if success:
            new_count = store.collection.count()
            added_count = new_count - existing_count
            
            print(f"✅ Successfully added {added_count} new tools!")
            print(f"⏱️  Integration completed in {integration_time:.1f} seconds")
            print(f"📊 Total tools in database: {new_count}")
            print(f"🚀 Tools per second: {len(biopython_tools) / integration_time:.1f}")
            
            # Test search quality
            await test_biopython_search(store)
            
            # Show success summary
            show_success_summary(biopython_tools, collection_time, integration_time)
            
            return True
        else:
            print("❌ Failed to integrate tools into ChromaDB")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the project root directory.")
        print("Also ensure biopython_tools_collector.py is in the scripts folder.")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_biopython_search(store):
    """Test search quality with Biopython-specific queries."""
    print("\n🧪 Testing search quality...")
    
    test_queries = [
        ("Bio.Seq sequence manipulation", "Core sequence tools"),
        ("sequence alignment pairwise", "Alignment tools"),
        ("BLAST sequence search", "BLAST tools"),
        ("protein structure PDB", "Structure analysis"),
        ("phylogenetic tree", "Phylogenetics"),
        ("file format conversion", "I/O tools"),
        ("restriction enzyme", "Molecular biology"),
        ("entrez database", "Database access")
    ]
    
    excellent_count = 0
    
    for query, description in test_queries:
        results = await store.semantic_search(query, n_results=3)
        
        if results and len(results) >= 2:
            # Check if results are Biopython-related
            bio_results = [r for r in results if 'biopython' in r.get('source', '').lower()]
            avg_score = sum(r['relevance_score'] for r in results[:2]) / 2
            
            if len(bio_results) >= 1 and avg_score > 0.5:
                status = "✅"
                excellent_count += 1
            else:
                status = "✔️ "
        else:
            status = "⚠️ "
        
        print(f"  {status} '{query}' → {len(results)} results")
        if results:
            top = results[0]
            print(f"      Top: {top['name']} (Score: {top['relevance_score']:.2f})")
    
    quality_pct = (excellent_count / len(test_queries)) * 100
    print(f"\n📈 Search Quality: {excellent_count}/{len(test_queries)} excellent ({quality_pct:.0f}%)")

def show_success_summary(tools, collection_time, integration_time):
    """Show final success summary."""
    total_time = collection_time + integration_time
    
    print(f"\n🎉 Integration completed successfully!")
    print(f"📊 Summary:")
    print(f"   • Biopython tools collected: {len(tools)}")
    print(f"   • Collection time: {collection_time:.1f} seconds")
    print(f"   • Integration time: {integration_time:.1f} seconds") 
    print(f"   • Total time: {total_time:.1f} seconds")
    print(f"   • Performance: {len(tools) / total_time:.1f} tools/second")
    
    # Count categories
    categories = {}
    for tool in tools:
        cat = tool.get('category', 'Unknown')
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"\n🏷️  Categories discovered: {len(categories)}")
    top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
    for cat, count in top_categories:
        print(f"   • {cat}: {count} tools")
    
    print(f"\n🎯 Next Steps:")
    print("1. Test with your agent: Results now include all Biopython tools")
    print("2. Run performance tests: python src/scripts/comprehensive_test.py") 
    print("3. Check detailed report: data/biopython_collection/")
    print("\n🚀 Your ChromaDB now contains the complete Biopython toolkit!")

def check_prerequisites():
    """Check if all required dependencies are available."""
    missing_deps = []
    
    try:
        import Bio
    except ImportError:
        missing_deps.append("biopython")
    
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
    collector_file = script_dir / "biopython_tools_collector.py"
    
    if not collector_file.exists():
        print("❌ Missing file: biopython_tools_collector.py")
        print(f"   Expected location: {collector_file}")
        print("   Please ensure the collector is in the scripts folder.")
        return False
    
    return True

if __name__ == "__main__":
    print("🔍 Checking prerequisites and file structure...")
    
    if not check_prerequisites():
        sys.exit(1)
    
    if not check_file_structure():
        print("\n📁 File Structure Help:")
        print("Your scripts folder should contain:")
        print("  src/scripts/")
        print("  ├── load_biopython_tools.py        # This file")
        print("  ├── biopython_tools_collector.py   # The collector")
        print("  ├── initialize_store.py            # Your existing file")
        print("  └── test_chroma_setup.py          # Your existing file")
        sys.exit(1)
    
    print("✅ All prerequisites and files found!")
    
    # Run the integration
    success = asyncio.run(main())
    
    if not success:
        print("\n⚠️  Integration failed. Check the error messages above.")
        sys.exit(1)
    