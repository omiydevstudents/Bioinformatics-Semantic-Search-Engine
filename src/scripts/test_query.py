# src/scripts/test_query.py

"""
Interactive Query Tester for ChromaDB Biopython Integration
Test your own queries against the comprehensive Biopython tools database.

Usage:
    python src/scripts/test_query.py "your search query"
    python src/scripts/test_query.py "Bio.Seq" --max-results 10
    python src/scripts/test_query.py "sequence alignment" --search-type semantic
    python src/scripts/test_query.py "alignment" --search-type category --category "Sequence Analysis"

Examples:
    python src/scripts/test_query.py "protein structure"
    python src/scripts/test_query.py "Bio.Blast" --detailed
    python src/scripts/test_query.py "file format" --max-results 5 --show-scores

Author: Nitanshu (ChromaDB & RAG Pipeline)
"""

import asyncio
import sys
import os
import argparse
import time
from pathlib import Path
from typing import List, Dict, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.db.chroma_store import SemanticSearchStore

class QueryTester:
    """Interactive query testing for ChromaDB Biopython integration."""
    
    def __init__(self):
        """Initialize the query tester."""
        print("🔍 ChromaDB Query Tester")
        print("=" * 40)
        
        try:
            self.store = SemanticSearchStore()
            self.db_count = self.store.collection.count()
            
            if self.db_count == 0:
                print("❌ No tools found in database!")
                print("🔧 Run: python src/scripts/load_biopython_tools.py")
                sys.exit(1)
            
            print(f"✅ Connected to database with {self.db_count:,} tools")
            print()
            
        except Exception as e:
            print(f"❌ Error connecting to database: {e}")
            sys.exit(1)
    
    async def test_semantic_search(self, query: str, max_results: int = 5, detailed: bool = False) -> Dict:
        """Test semantic search with performance metrics."""
        print(f"🔍 Semantic Search: '{query}'")
        print("-" * 50)
        
        # Measure search performance
        start_time = time.time()
        results = await self.store.semantic_search(query, n_results=max_results)
        search_time = time.time() - start_time
        
        # Display results
        if results:
            print(f"📊 Found {len(results)} results in {search_time:.3f} seconds")
            print(f"⚡ Performance: {1/search_time:.1f} queries/second")
            print()
            
            for i, result in enumerate(results, 1):
                self._display_result(i, result, detailed)
                
            # Calculate average relevance
            avg_relevance = sum(r['relevance_score'] for r in results) / len(results)
            print(f"📈 Average relevance score: {avg_relevance:.3f}")
            
        else:
            print("📭 No results found")
            print("💡 Try:")
            print("   - More general terms: 'sequence' instead of 'DNA sequence analysis'")
            print("   - Biopython modules: 'Bio.Seq', 'Bio.Align', 'Bio.PDB'")
            print("   - Function names: 'alignment', 'structure', 'format'")
        
        return {
            "query": query,
            "results_count": len(results),
            "search_time": search_time,
            "average_relevance": sum(r['relevance_score'] for r in results) / len(results) if results else 0
        }
    
    async def test_category_search(self, query: str, category: str, max_results: int = 5, detailed: bool = False) -> Dict:
        """Test category-based search."""
        print(f"📂 Category Search: '{query}' in '{category}'")
        print("-" * 50)
        
        try:
            start_time = time.time()
            results = await self.store.search_by_category(category, query, n_results=max_results)
            search_time = time.time() - start_time
            
            if results:
                print(f"📊 Found {len(results)} results in {search_time:.3f} seconds")
                print()
                
                for i, result in enumerate(results, 1):
                    self._display_result(i, result, detailed)
                    
                avg_relevance = sum(r['relevance_score'] for r in results) / len(results)
                print(f"📈 Average relevance score: {avg_relevance:.3f}")
                
            else:
                print(f"📭 No results found in category '{category}'")
                await self._suggest_categories()
                
        except Exception as e:
            print(f"❌ Error in category search: {e}")
            print("💡 Make sure the category name is correct")
            await self._suggest_categories()
            
        return {
            "query": query,
            "category": category,
            "results_count": len(results) if 'results' in locals() else 0,
            "search_time": search_time if 'search_time' in locals() else 0
        }
    
    async def test_similar_tools(self, tool_name: str, max_results: int = 5, detailed: bool = False) -> Dict:
        """Test similar tools functionality."""
        print(f"🔗 Similar Tools to: '{tool_name}'")
        print("-" * 50)
        
        try:
            # First check if the tool exists
            tool_info = await self.store.get_tool_by_name(tool_name)
            
            if not tool_info:
                print(f"❌ Tool '{tool_name}' not found in database")
                print("💡 Try searching first to find the exact tool name:")
                
                # Suggest similar tools by doing a semantic search
                suggestions = await self.store.semantic_search(tool_name, n_results=3)
                if suggestions:
                    print("🔍 Did you mean one of these?")
                    for i, suggestion in enumerate(suggestions, 1):
                        print(f"   {i}. {suggestion['name']} (Score: {suggestion['relevance_score']:.2f})")
                
                return {"error": "Tool not found"}
            
            start_time = time.time()
            results = await self.store.get_similar_tools(tool_name, n_results=max_results)
            search_time = time.time() - start_time
            
            if results:
                print(f"📊 Found {len(results)} similar tools in {search_time:.3f} seconds")
                print()
                
                for i, result in enumerate(results, 1):
                    # Similar tools have similarity_score instead of relevance_score
                    similarity = result.get('similarity_score', result.get('relevance_score', 0))
                    print(f"{i}. 🧬 {result['name']}")
                    print(f"   📂 Category: {result['category']}")
                    print(f"   🎯 Similarity: {similarity:.3f}")
                    if detailed:
                        content = result['content'][:150] + "..." if len(result['content']) > 150 else result['content']
                        print(f"   📝 Description: {content}")
                    print()
                    
            else:
                print("📭 No similar tools found")
                
        except Exception as e:
            print(f"❌ Error finding similar tools: {e}")
            
        return {
            "tool_name": tool_name,
            "results_count": len(results) if 'results' in locals() else 0,
            "search_time": search_time if 'search_time' in locals() else 0
        }
    
    def _display_result(self, index: int, result: Dict, detailed: bool = False):
        """Display a single search result."""
        name = result['name']
        category = result['category']
        score = result['relevance_score']
        source = result.get('source', 'Unknown')
        
        print(f"{index}. 🧬 {name}")
        print(f"   📂 Category: {category}")
        print(f"   🎯 Relevance: {score:.3f}")
        print(f"   📦 Source: {source}")
        
        if detailed:
            # Show more details
            content = result['content']
            if len(content) > 200:
                content = content[:200] + "..."
            print(f"   📝 Description: {content}")
            
            # Show additional metadata if available
            if 'tool_type' in result:
                print(f"   🔧 Type: {result['tool_type']}")
            if 'full_name' in result:
                print(f"   📋 Full Name: {result['full_name']}")
        
        print()
    
    async def _suggest_categories(self):
        """Suggest available categories."""
        print("\n💡 Available categories:")
        
        # Get sample of data to find categories
        sample = self.store.collection.get(limit=20)
        if sample['metadatas']:
            categories = set()
            for metadata in sample['metadatas']:
                if metadata and 'category' in metadata:
                    categories.add(metadata['category'])
            
            for cat in sorted(list(categories)):
                print(f"   • {cat}")
        print()
    
    async def quick_database_stats(self):
        """Show quick database statistics."""
        print("📊 Database Statistics")
        print("-" * 30)
        print(f"Total tools: {self.db_count:,}")
        
        # Get sample for analysis
        sample = self.store.collection.get(limit=50)
        if sample['metadatas']:
            categories = {}
            sources = {}
            
            for metadata in sample['metadatas']:
                if metadata:
                    cat = metadata.get('category', 'Unknown')
                    src = metadata.get('source', 'Unknown')
                    categories[cat] = categories.get(cat, 0) + 1
                    sources[src] = sources.get(src, 0) + 1
            
            print(f"Categories found: {len(categories)}")
            print(f"Top categories:")
            for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"   • {cat}: {count} tools")
            
            print(f"\nSources: {', '.join(sources.keys())}")
        
        print()

async def main():
    """Main function with command-line argument parsing."""
    
    parser = argparse.ArgumentParser(
        description="Test queries against ChromaDB Biopython tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/scripts/test_query.py "Bio.Seq"
  python src/scripts/test_query.py "protein structure" --max-results 10
  python src/scripts/test_query.py "alignment" --search-type category --category "Sequence Analysis"
  python src/scripts/test_query.py "BLAST" --search-type similar
  python src/scripts/test_query.py "sequence" --detailed --show-scores
        """
    )
    
    parser.add_argument("query", help="Search query to test")
    parser.add_argument("--max-results", "-n", type=int, default=5, 
                       help="Maximum number of results to show (default: 5)")
    parser.add_argument("--search-type", "-t", choices=["semantic", "category", "similar"], 
                       default="semantic", help="Type of search to perform (default: semantic)")
    parser.add_argument("--category", "-c", help="Category for category search")
    parser.add_argument("--detailed", "-d", action="store_true", 
                       help="Show detailed information for each result")
    parser.add_argument("--show-scores", "-s", action="store_true", 
                       help="Always show relevance scores")
    parser.add_argument("--stats", action="store_true", 
                       help="Show database statistics before search")
    
    args = parser.parse_args()
    
    # Initialize tester
    tester = QueryTester()
    
    # Show stats if requested
    if args.stats:
        await tester.quick_database_stats()
    
    # Perform the requested search
    try:
        if args.search_type == "semantic":
            result = await tester.test_semantic_search(
                args.query, 
                max_results=args.max_results, 
                detailed=args.detailed
            )
            
        elif args.search_type == "category":
            if not args.category:
                print("❌ Category search requires --category argument")
                print("💡 Use --stats to see available categories")
                sys.exit(1)
            
            result = await tester.test_category_search(
                args.query, 
                args.category, 
                max_results=args.max_results, 
                detailed=args.detailed
            )
            
        elif args.search_type == "similar":
            result = await tester.test_similar_tools(
                args.query, 
                max_results=args.max_results, 
                detailed=args.detailed
            )
        
        # Show final summary
        if 'error' not in result:
            print("✅ Query test completed successfully!")
            
    except KeyboardInterrupt:
        print("\n🛑 Query test interrupted by user")
    except Exception as e:
        print(f"❌ Error during query test: {e}")
        sys.exit(1)

def interactive_mode():
    """Interactive mode for multiple queries."""
    print("🎯 Interactive Query Mode")
    print("Type queries to test them. Type 'quit' to exit.")
    print("Commands: 'stats' for database info, 'help' for options")
    print("-" * 50)
    
    async def run_interactive():
        tester = QueryTester()
        
        while True:
            try:
                query = input("\n🔍 Enter query (or 'quit'): ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                elif query.lower() == 'stats':
                    await tester.quick_database_stats()
                    continue
                elif query.lower() == 'help':
                    print("\n💡 Available commands:")
                    print("   • Any text: Semantic search")
                    print("   • stats: Show database statistics") 
                    print("   • help: Show this help")
                    print("   • quit: Exit interactive mode")
                    continue
                elif not query:
                    continue
                
                await tester.test_semantic_search(query, max_results=3)
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    asyncio.run(run_interactive())

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No arguments - run in interactive mode
        interactive_mode()
    else:
        # Run with command line arguments
        asyncio.run(main())