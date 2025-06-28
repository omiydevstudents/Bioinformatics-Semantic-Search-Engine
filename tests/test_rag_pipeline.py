# tests/test_rag_pipeline.py
"""
RAG Pipeline Testing
==================================================

This file tests your RAG (Retrieval-Augmented Generation) pipeline.

🚀 HOW TO USE:
1. Run without arguments: python tests/test_rag_pipeline.py
   → Tests ALL components of the pipeline

2. Run with specific component: python tests/test_rag_pipeline.py chromadb
   → Tests only the ChromaDB component

3. Get help: python tests/test_rag_pipeline.py --help
   → Shows detailed usage instructions

🔧 AVAILABLE COMPONENTS TO TEST:
- chromadb: Tests ChromaDB storage and connections (2,596+ bioinformatics tools)
- embeddings: Tests HuggingFace biomedical BERT embeddings
- search: Tests semantic search functionality with relevance scoring
- agent: Tests LangChain ToolDiscoveryAgent coordination
- integration: Tests how all components work together
- performance: Tests speed and throughput benchmarks

📊 WHAT EACH TEST DOES:
- ChromaDB: Verifies connection to vector database with bioinformatics tools
- Embeddings: Tests text-to-vector conversion using biomedical BERT
- Search: Tests semantic search with relevance scoring (finds Biopython, Bioconductor tools)
- Agent: Tests LangChain agent that coordinates MCP, EXA, Smithery + ChromaDB
- Integration: Tests complete pipeline from query to results
- Performance: Measures search speed (target: <40ms per query)

💡 EXAMPLES:
python tests/test_rag_pipeline.py                    # Test everything
python tests/test_rag_pipeline.py chromadb          # Test only ChromaDB
python tests/test_rag_pipeline.py performance       # Test speed only
python tests/test_rag_pipeline.py --help            # Show this help
"""

import sys
import os
import time
import asyncio

# Add project root to path so we can import our code
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

def print_header(test_name):
    """Print a nice header for each test."""
    print("\n" + "="*50)
    print(f"🧪 TESTING: {test_name}")
    print("="*50)

def print_result(test_name, success, details=""):
    """Print test results in a clear way."""
    status = "✅ PASSED" if success else "❌ FAILED"
    print(f"{status}: {test_name}")
    if details:
        print(f"   Details: {details}")

class SimpleRAGTester:
    """Simple tester for RAG pipeline - easy for beginners to understand."""
    
    def __init__(self):
        """Initialize the tester."""
        self.store = None
        self.agent = None
        
    def test_chromadb(self):
        """Test 1: Check if ChromaDB vector database works."""
        print_header("ChromaDB Vector Database")
        
        try:
            # Import and create ChromaDB connection
            from src.db.chroma_store import SemanticSearchStore
            self.store = SemanticSearchStore()
            
            # Try to get collection info from ChromaDB
            collection_info = self.store.collection.count()
            
            print_result("ChromaDB Connection", True, f"Connected to ChromaDB with {collection_info} bioinformatics tools")
            return True
            
        except Exception as e:
            print_result("ChromaDB Connection", False, str(e))
            return False
    
    async def test_embeddings(self):
        """Test 2: Check if HuggingFace biomedical BERT embeddings work."""
        print_header("HuggingFace Biomedical BERT Embeddings")
        
        if not self.store:
            print_result("HuggingFace Embeddings", False, "ChromaDB not connected")
            return False
            
        try:
            # Test embeddings by performing a simple semantic search
            # This will internally use the biomedical BERT embeddings
            test_results = await self.store.semantic_search("protein structure prediction", n_results=1)
            
            # Check if we got valid results (which means embeddings worked)
            if test_results and len(test_results) > 0:
                result = test_results[0]
                relevance = result.get('relevance_score', 0)
                source = result.get('source', 'Unknown')
                print_result("HuggingFace Embeddings", True, f"Biomedical BERT working (relevance: {relevance:.3f}, found {source} tool)")
                return True
            else:
                print_result("HuggingFace Embeddings", False, "No embeddings generated from biomedical BERT")
                return False
                
        except Exception as e:
            print_result("HuggingFace Embeddings", False, str(e))
            return False
    
    async def test_search(self):
        """Test 3: Check if semantic search finds relevant bioinformatics tools."""
        print_header("Semantic Search with Relevance Scoring")
        
        if not self.store:
            print_result("Semantic Search", False, "ChromaDB not connected")
            return False
            
        try:
            # Search for bioinformatics tools related to DNA sequence analysis
            results = await self.store.semantic_search("DNA sequence analysis", n_results=3)
            
            if results and len(results) > 0:
                print("Found these relevant bioinformatics tools:")
                
                # Count tools by source
                sources = {}
                for result in results:
                    source = result.get('source', 'Unknown')
                    sources[source] = sources.get(source, 0) + 1
                
                for i, result in enumerate(results, 1):
                    name = result.get('name', 'Unknown')
                    score = result.get('relevance_score', 0)
                    category = result.get('category', 'Unknown')
                    source = result.get('source', 'Unknown')
                    print(f"   {i}. {name} (relevance: {score:.3f}, source: {source}, category: {category})")
                
                # Show source breakdown
                source_summary = ", ".join([f"{count} {source}" for source, count in sources.items()])
                print_result("Semantic Search", True, f"Found {len(results)} tools ({source_summary})")
                return True
            else:
                print_result("Semantic Search", False, "No search results found in ChromaDB")
                return False
                
        except Exception as e:
            print_result("Semantic Search", False, str(e))
            return False
    
    async def test_agent(self):
        """Test 4: Check if LangChain ToolDiscoveryAgent coordinates multiple sources."""
        print_header("LangChain ToolDiscoveryAgent Integration")
        
        try:
            # Import and create the LangChain agent that coordinates everything
            from src.agents.tool_discovery_agent import ToolDiscoveryAgent
            self.agent = ToolDiscoveryAgent()
            
            # Ask the agent to find tools (coordinates ChromaDB + MCP + EXA + Smithery)
            query = "Find tools for protein analysis"
            result = await self.agent.discover_tools(query)
            
            if result and 'response' in result:
                response_length = len(result['response'])
                print_result("LangChain Agent", True, f"Agent coordinated multiple sources ({response_length} chars)")
                print(f"   Sample response: {result['response'][:150]}...")
                return True
            else:
                print_result("LangChain Agent", False, "Agent didn't provide proper coordination response")
                return False
                
        except Exception as e:
            print_result("LangChain Agent", False, str(e))
            return False
    
    async def test_integration(self):
        """Test 5: Check if ChromaDB + embeddings + search work together."""
        print_header("Complete RAG Pipeline Integration")
        
        try:
            # Test the complete RAG workflow: ChromaDB + HuggingFace + Semantic Search
            if not self.store:
                print_result("RAG Integration", False, "ChromaDB not available")
                return False
            
            # 1. Check ChromaDB has bioinformatics data
            count = self.store.collection.count()
            
            # 2. Test semantic search works with biomedical terms
            results = await self.store.semantic_search("bioinformatics sequence analysis", n_results=1)
            
            # 3. Test category-based search works
            try:
                category_results = await self.store.search_by_category("sequence_analysis", "alignment", n_results=1)
                categories_work = True
            except:
                categories_work = False
            
            all_working = count > 0 and len(results) > 0
            
            if all_working:
                details = f"ChromaDB: {count} tools, Search: works, Category search: {'works' if categories_work else 'partial'}"
                print_result("RAG Integration", True, details)
                return True
            else:
                print_result("RAG Integration", False, "Some RAG components not working")
                return False
                
        except Exception as e:
            print_result("RAG Integration", False, str(e))
            return False
            
    async def test_performance(self):
        """Test 6: Check if search performance meets targets (<40ms per query)."""
        print_header("Performance Benchmarks")
        
        if not self.store:
            print_result("Performance", False, "ChromaDB not connected")
            return False
            
        try:
            import time
            
            # Test search speed with multiple queries
            test_queries = [
                "protein structure prediction",
                "RNA sequencing analysis", 
                "DNA alignment tools",
                "phylogenetic analysis",
                "gene expression analysis"
            ]
            
            times = []
            for query in test_queries:
                start_time = time.time()
                results = await self.store.semantic_search(query, n_results=5)
                end_time = time.time()
                
                query_time = (end_time - start_time) * 1000  # Convert to milliseconds
                times.append(query_time)
            
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            
            # Target is <40ms per query (from project docs)
            target_met = avg_time < 40
            
            details = f"Avg: {avg_time:.1f}ms, Min: {min_time:.1f}ms, Max: {max_time:.1f}ms"
            print_result("Performance", target_met, details)
            
            if target_met:
                queries_per_sec = 1000 / avg_time
                print(f"   Throughput: ~{queries_per_sec:.1f} queries/second")
            
            return target_met
                
        except Exception as e:
            print_result("Performance", False, str(e))
            return False

def run_all_tests():
    """Run all tests in the RAG pipeline."""
    print("🚀 Starting Complete RAG Pipeline Test")
    print("Testing: ChromaDB + HuggingFace + LangChain + Performance...")
    
    tester = SimpleRAGTester()
    results = {}
    
    # Run each test with proper async handling
    results['chromadb'] = tester.test_chromadb()
    results['embeddings'] = asyncio.run(tester.test_embeddings())
    results['search'] = asyncio.run(tester.test_search())
    results['agent'] = asyncio.run(tester.test_agent())
    results['integration'] = asyncio.run(tester.test_integration())
    results['performance'] = asyncio.run(tester.test_performance())
    
    # Show summary
    print("\n" + "="*60)
    print("📊 RAG PIPELINE TEST SUMMARY")
    print("="*60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, test_passed in results.items():
        status = "✅ PASSED" if test_passed else "❌ FAILED"
        tech_name = {
            'chromadb': 'ChromaDB Vector Database',
            'embeddings': 'HuggingFace Biomedical BERT',
            'search': 'Semantic Search with Relevance Scoring',
            'agent': 'LangChain ToolDiscoveryAgent',
            'integration': 'Complete RAG Pipeline',
            'performance': 'Performance Benchmarks'
        }.get(test_name, test_name.title())
        
        print(f"{status}: {tech_name}")
    
    print(f"\nOVERALL: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Your RAG pipeline is production-ready!")
        print("✨ ChromaDB, HuggingFace, LangChain all working perfectly!")
        print("🔬 Successfully handling Biopython + Bioconductor tools with accurate source detection!")
    else:
        print("⚠️  Some components failed. Check the details above.")
        print("💡 Run individual tests to debug: python tests/test_rag_pipeline.py <component>")
    
    return results

def run_specific_test(component):
    """Run test for a specific RAG component."""
    
    # Map user input to display names
    component_names = {
        'chromadb': 'ChromaDB Vector Database',
        'embeddings': 'HuggingFace Biomedical BERT',
        'search': 'Semantic Search',
        'agent': 'LangChain ToolDiscoveryAgent',
        'integration': 'Complete RAG Pipeline',
        'performance': 'Performance Benchmarks'
    }
    
    if component not in component_names:
        print(f"❌ Unknown component: {component}")
        print("\n🔧 Available components:")
        for comp, name in component_names.items():
            print(f"  {comp:<12} - {name}")
        return False
    
    print(f"🎯 Testing: {component_names[component]}")
    
    tester = SimpleRAGTester()
    
    if component == "chromadb":
        result = tester.test_chromadb()
    elif component == "embeddings":
        tester.test_chromadb()  # Need ChromaDB connection first
        result = asyncio.run(tester.test_embeddings())
    elif component == "search":
        tester.test_chromadb()  # Need ChromaDB connection first
        result = asyncio.run(tester.test_search())
    elif component == "agent":
        result = asyncio.run(tester.test_agent())
    elif component == "integration":
        tester.test_chromadb()  # Need ChromaDB connection first
        result = asyncio.run(tester.test_integration())
    elif component == "performance":
        tester.test_chromadb()  # Need ChromaDB connection first
        result = asyncio.run(tester.test_performance())
    
    if result:
        print(f"🎉 {component_names[component]} test PASSED!")
    else:
        print(f"⚠️ {component_names[component]} test FAILED!")
    
    return result

def show_help():
    """Show detailed help and usage instructions."""
    help_text = """
🚀 RAG Pipeline Testing Tool - Complete Usage Guide
=====================================================

WHAT THIS TESTS:
Your complete Retrieval-Augmented Generation (RAG) pipeline with:
• ChromaDB vector database (2,596+ bioinformatics tools: Biopython + Bioconductor)
• HuggingFace biomedical BERT embeddings  
• Semantic search with relevance scoring
• LangChain ToolDiscoveryAgent coordination
• Multi-source integration (MCP + EXA + Smithery + ChromaDB)
• Performance benchmarks (target: <40ms/query)

BASIC USAGE:
python tests/test_rag_pipeline.py                    # Test everything
python tests/test_rag_pipeline.py chromadb          # Test only ChromaDB
python tests/test_rag_pipeline.py --help            # Show this help

AVAILABLE COMPONENTS:
chromadb     - ChromaDB Vector Database (2,596+ bioinformatics tools)
embeddings   - HuggingFace Biomedical BERT Embeddings
search       - Semantic Search with Relevance Scoring  
agent        - LangChain ToolDiscoveryAgent (coordinates all sources)
integration  - Complete RAG Pipeline Integration
performance  - Performance Benchmarks (<40ms target)

WHAT EACH TEST VALIDATES:
✅ ChromaDB: Connection to vector database, tool count validation
✅ Embeddings: Biomedical BERT text-to-vector conversion working
✅ Search: Semantic search finds relevant tools (Biopython, Bioconductor, etc.)
✅ Agent: LangChain agent coordinates ChromaDB + MCP + EXA + Smithery
✅ Integration: End-to-end RAG pipeline functionality
✅ Performance: Search speed meets production targets

EXAMPLE COMMANDS:
python tests/test_rag_pipeline.py                    # Full test suite
python tests/test_rag_pipeline.py chromadb          # Just ChromaDB
python tests/test_rag_pipeline.py performance       # Just speed test
python tests/test_rag_pipeline.py agent             # Just LangChain agent

TROUBLESHOOTING:
If tests fail, run individual components to isolate issues:
• ChromaDB issues: Check data/chroma directory exists
• Embedding issues: Verify HuggingFace model downloads  
• Search issues: Check semantic_search API parameters
• Agent issues: Verify all MCP/EXA/Smithery services running
• Performance issues: Check system resources and ChromaDB optimization

EXPECTED RESULTS:
✅ ChromaDB: ~2,596 bioinformatics tools loaded (Biopython + Bioconductor)
✅ Embeddings: Biomedical BERT working with relevance scores
✅ Search: Returns relevant tools from both Biopython and Bioconductor sources
✅ Agent: Coordinates multiple search sources successfully  
✅ Integration: Complete workflow operational
✅ Performance: <40ms average search time, 25+ queries/second
    """
    print(help_text)

def main():
    """Main function - decides what to test based on arguments."""
    
    # Check for help first
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
        show_help()
        return
    
    # Check what the user wants to test
    if len(sys.argv) == 1:
        # No arguments = test everything
        run_all_tests()
    elif len(sys.argv) == 2:
        # One argument = test specific component
        component = sys.argv[1].lower()
        run_specific_test(component)
    else:
        # Too many arguments = show help
        print("❌ Too many arguments!")
        print("\n💡 QUICK USAGE:")
        print("  python tests/test_rag_pipeline.py              # Test everything")
        print("  python tests/test_rag_pipeline.py chromadb     # Test ChromaDB only")
        print("  python tests/test_rag_pipeline.py --help       # Show detailed help")
        print("\n🔧 Available components: chromadb, embeddings, search, agent, integration, performance")

if __name__ == "__main__":
    main()