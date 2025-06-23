# src/scripts/test_chroma_setup.py

"""
Updated ChromaDB Setup Test - Now with Real Biopython Tools
Tests the ChromaDB integration with the comprehensive Biopython collection.

Usage:
    python src/scripts/test_chroma_setup.py

This tests:
1. Database connectivity with existing Biopython tools
2. Search functionality with real bioinformatics queries
3. Performance and accuracy with actual data
4. Biopython-specific module searches

Author: Nitanshu (ChromaDB & RAG Pipeline)
"""

import os
from dotenv import load_dotenv
from pathlib import Path
import asyncio
import time

# Add the project root to Python path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.db.chroma_store import SemanticSearchStore

async def test_database_connection():
    """Test 1: Database connection and current state."""
    print("🔧 Test 1: Database Connection & Current State")
    print("-" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Get configuration from environment
    chroma_db_dir = os.getenv('CHROMA_DB_DIR', 'data/chroma')
    embedding_model = os.getenv('EMBEDDING_MODEL', 'microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext')
    
    print(f"📁 Database directory: {chroma_db_dir}")
    print(f"🤖 Embedding model: {embedding_model}")
    
    # Create data directory if it doesn't exist
    Path(chroma_db_dir).mkdir(parents=True, exist_ok=True)
    
    # Initialize the store
    store = SemanticSearchStore(persist_dir=chroma_db_dir)
    
    # Check current collection state
    collection_count = store.collection.count()
    print(f"📊 Total tools in database: {collection_count}")
    
    if collection_count == 0:
        print("⚠️  Database is empty!")
        print("   Run: python src/scripts/load_biopython_tools.py")
        return store, False
    elif collection_count < 100:
        print("⚠️  Database has limited data (< 100 tools)")
        print("   Consider running: python src/scripts/load_biopython_tools.py")
    else:
        print("✅ Database has substantial data - ready for testing!")
    
    # Show sample of current data
    if collection_count > 0:
        sample_data = store.collection.get(limit=5)
        print(f"\n📋 Sample entries (first 5):")
        for i, doc in enumerate(sample_data['documents'][:5]):
            metadata = sample_data['metadatas'][i] if sample_data['metadatas'] else {}
            name = metadata.get('name', 'Unknown')
            source = metadata.get('source', 'Unknown')
            print(f"  {i+1}. {name} (Source: {source})")
    
    return store, True

async def test_biopython_specific_searches(store):
    """Test 2: Biopython-specific search functionality."""
    print("\n🧬 Test 2: Biopython-Specific Searches")
    print("-" * 50)
    
    # Test with actual Biopython module queries
    biopython_queries = [
        ("Bio.Seq", "Core sequence class"),
        ("Bio.Align", "Sequence alignment"),
        ("Bio.Blast", "BLAST search tools"),
        ("Bio.PDB", "Protein structure analysis"),
        ("Bio.Phylo", "Phylogenetic analysis"),
        ("Bio.SeqIO", "Sequence file I/O"),
        ("Bio.Entrez", "NCBI database access"),
        ("Bio.Restriction", "Restriction enzyme analysis")
    ]
    
    print("🔍 Testing Biopython module searches...")
    successful_searches = 0
    
    for query, description in biopython_queries:
        print(f"\n🧪 Testing: {query} ({description})")
        
        start_time = time.time()
        results = await store.semantic_search(query, n_results=3)
        search_time = time.time() - start_time
        
        print(f"   ⏱️  Search time: {search_time:.3f}s")
        print(f"   📊 Results found: {len(results)}")
        
        if results:
            # Check if we found relevant Biopython tools
            bio_related = sum(1 for r in results if 'bio' in r.get('source', '').lower() or 
                             'bio' in r['name'].lower() or 
                             query.lower() in r['name'].lower())
            
            if bio_related > 0:
                successful_searches += 1
                print(f"   ✅ Found {bio_related} relevant Biopython tools")
                
                # Show top result
                top = results[0]
                print(f"   🎯 Top: {top['name']} (Score: {top['relevance_score']:.2f})")
            else:
                print(f"   ⚠️  No Biopython-specific results found")
        else:
            print(f"   ❌ No results found")
    
    success_rate = (successful_searches / len(biopython_queries)) * 100
    print(f"\n📈 Biopython Search Success Rate: {success_rate:.1f}% ({successful_searches}/{len(biopython_queries)})")
    
    return success_rate > 60  # Consider successful if > 60% of searches work

async def test_general_bioinformatics_searches(store):
    """Test 3: General bioinformatics search functionality."""
    print("\n🔬 Test 3: General Bioinformatics Searches")
    print("-" * 50)
    
    # Test with general bioinformatics terms
    general_queries = [
        ("sequence alignment", "Alignment algorithms"),
        ("protein structure", "Structural biology"),
        ("phylogenetic tree", "Evolutionary analysis"),
        ("file format conversion", "Data processing"),
        ("database access", "Data retrieval"),
        ("restriction enzyme", "Molecular cloning"),
        ("sequence analysis", "General sequence work"),
        ("motif discovery", "Pattern recognition")
    ]
    
    print("🔍 Testing general bioinformatics searches...")
    search_results = []
    
    for query, description in general_queries:
        print(f"\n🧪 Testing: '{query}' ({description})")
        
        start_time = time.time()
        results = await store.semantic_search(query, n_results=5)
        search_time = time.time() - start_time
        
        result_info = {
            "query": query,
            "description": description,
            "search_time": search_time,
            "result_count": len(results),
            "avg_score": sum(r['relevance_score'] for r in results[:3]) / min(3, len(results)) if results else 0,
            "top_result": results[0]['name'] if results else None
        }
        
        search_results.append(result_info)
        
        print(f"   ⏱️  Search time: {search_time:.3f}s")
        print(f"   📊 Results: {len(results)}")
        if results:
            print(f"   🎯 Top: {results[0]['name']} (Score: {results[0]['relevance_score']:.2f})")
            print(f"   📈 Avg score (top 3): {result_info['avg_score']:.2f}")
    
    # Calculate overall performance
    avg_search_time = sum(r['search_time'] for r in search_results) / len(search_results)
    avg_score = sum(r['avg_score'] for r in search_results if r['avg_score'] > 0) / len([r for r in search_results if r['avg_score'] > 0])
    queries_with_results = sum(1 for r in search_results if r['result_count'] > 0)
    
    print(f"\n📊 General Search Performance:")
    print(f"   Average search time: {avg_search_time:.3f}s")
    print(f"   Average relevance score: {avg_score:.3f}")
    print(f"   Queries with results: {queries_with_results}/{len(general_queries)}")
    print(f"   Success rate: {(queries_with_results/len(general_queries))*100:.1f}%")
    
    return avg_search_time < 0.1 and avg_score > 0.5  # Good if fast and relevant

async def test_category_search(store):
    """Test 4: Category-based search functionality."""
    print("\n📂 Test 4: Category-Based Search")
    print("-" * 50)
    
    # Test category searches
    category_tests = [
        ("Sequence Analysis", "alignment"),
        ("Protein Structure", "structure"),
        ("Database Access", "entrez"),
        ("File Formats", "format"),
        ("Sequence Alignment", "multiple")
    ]
    
    print("🔍 Testing category-based searches...")
    category_success = 0
    
    for category, query in category_tests:
        print(f"\n🧪 Testing category: '{category}' with query: '{query}'")
        
        try:
            results = await store.search_by_category(category, query, n_results=3)
            
            if results:
                category_success += 1
                print(f"   ✅ Found {len(results)} results in {category}")
                for result in results[:2]:  # Show top 2
                    print(f"   • {result['name']} (Score: {result['relevance_score']:.2f})")
            else:
                print(f"   ⚠️  No results found in {category}")
                
        except Exception as e:
            print(f"   ❌ Error searching category {category}: {e}")
    
    category_success_rate = (category_success / len(category_tests)) * 100
    print(f"\n📈 Category Search Success Rate: {category_success_rate:.1f}%")
    
    return category_success_rate > 50

async def test_performance_benchmarks(store):
    """Test 5: Performance benchmarks."""
    print("\n⚡ Test 5: Performance Benchmarks")
    print("-" * 50)
    
    # Performance test queries
    perf_queries = [
        "sequence",
        "protein",
        "alignment",
        "structure",
        "analysis"
    ]
    
    print("🏃‍♂️ Running performance tests...")
    search_times = []
    
    for query in perf_queries:
        start_time = time.time()
        results = await store.semantic_search(query, n_results=10)
        search_time = time.time() - start_time
        search_times.append(search_time)
        
        print(f"   '{query}': {search_time:.3f}s ({len(results)} results)")
    
    # Calculate performance metrics
    avg_time = sum(search_times) / len(search_times)
    min_time = min(search_times)
    max_time = max(search_times)
    queries_per_second = len(search_times) / sum(search_times)
    
    print(f"\n📊 Performance Results:")
    print(f"   Average search time: {avg_time:.3f}s")
    print(f"   Min/Max search time: {min_time:.3f}s / {max_time:.3f}s")
    print(f"   Queries per second: {queries_per_second:.2f}")
    
    # Performance benchmarks
    is_fast = avg_time < 0.1  # Should be under 100ms
    is_consistent = (max_time - min_time) < 0.05  # Consistent timing
    
    if is_fast and is_consistent:
        print("   ✅ Performance: EXCELLENT")
        return True
    elif is_fast:
        print("   ✅ Performance: GOOD (fast but some variation)")
        return True
    else:
        print("   ⚠️  Performance: NEEDS IMPROVEMENT")
        return False

async def main():
    """Main test function."""
    print("🧪 ChromaDB Setup Test - Biopython Integration")
    print("=" * 60)
    print("Testing ChromaDB with real Biopython tools")
    print("=" * 60)
    
    # Test 1: Database connection
    store, has_data = await test_database_connection()
    
    if not has_data:
        print("\n❌ Cannot run comprehensive tests without data!")
        print("🔧 Please run: python src/scripts/load_biopython_tools.py")
        return False
    
    # Run all tests
    test_results = []
    
    # Test 2: Biopython searches
    bio_success = await test_biopython_specific_searches(store)
    test_results.append(("Biopython Searches", bio_success))
    
    # Test 3: General searches  
    general_success = await test_general_bioinformatics_searches(store)
    test_results.append(("General Searches", general_success))
    
    # Test 4: Category searches
    category_success = await test_category_search(store)
    test_results.append(("Category Searches", category_success))
    
    # Test 5: Performance
    perf_success = await test_performance_benchmarks(store)
    test_results.append(("Performance", perf_success))
    
    # Final summary
    print("\n🏆 TEST SUMMARY")
    print("=" * 30)
    
    passed_tests = sum(1 for _, success in test_results if success)
    total_tests = len(test_results)
    
    for test_name, success in test_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {test_name:20} {status}")
    
    success_rate = (passed_tests / total_tests) * 100
    print(f"\n📊 Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
    
    if success_rate >= 80:
        print("🎉 ChromaDB is working excellently with Biopython tools!")
        print("🚀 Ready for production use with agent integration!")
    elif success_rate >= 60:
        print("👍 ChromaDB is working well with some areas for improvement")
        print("🔧 Consider running more comprehensive tests")
    else:
        print("⚠️  ChromaDB may need attention - multiple test failures")
        print("🔧 Check your Biopython installation and data loading")
    
    print(f"\n🤝 Integration status: {'READY' if success_rate >= 60 else 'NEEDS WORK'}")
    
    return success_rate >= 60

if __name__ == "__main__":
    success = asyncio.run(main())
    
    if success:
        print("\n✅ All tests completed successfully!")
    else:
        print("\n⚠️  Some tests failed - check output above")
        sys.exit(1)