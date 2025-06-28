# tests/test_query.py
"""
Interactive Query Testing Tool for RAG Pipeline
=============================================

This tool lets you test your own search queries from the terminal and see
exactly what your ChromaDB contains for each bioinformatics tool.

🚀 HOW TO USE:
python tests/test_query.py "your search query here"

📊 WHAT YOU'LL SEE:
- Relevance score (0.0 to 1.0, higher = more relevant)
- Source (Biopython, Bioconductor, etc.)
- Complete JSON data for each tool (everything stored in ChromaDB)

💡 EXAMPLES:
python tests/test_query.py "protein structure prediction"
python tests/test_query.py "RNA-seq analysis tools"
python tests/test_query.py "sequence alignment"
python tests/test_query.py "Bio.Seq" --max-results 10
python tests/test_query.py "DESeq2" --detailed
python tests/test_query.py "alignment" --source Biopython
"""

import sys
import os
import asyncio
import argparse
import json
import time
from typing import Dict, List

# Add project root to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

class QueryTester:
    """Simple query testing tool for beginners."""
    
    def __init__(self):
        """Initialize the query tester."""
        self.store = None
        self.total_tools = 0
        
    async def connect_to_database(self):
        """Connect to ChromaDB and check what's available."""
        try:
            from src.db.chroma_store import SemanticSearchStore
            self.store = SemanticSearchStore()
            self.total_tools = self.store.collection.count()
            
            print(f"✅ Connected to ChromaDB")
            print(f"📊 Database contains: {self.total_tools:,} bioinformatics tools")
            print()
            
        except Exception as e:
            print(f"❌ Error connecting to ChromaDB: {e}")
            print("💡 Make sure you've run the pipeline setup first")
            sys.exit(1)
    
    async def search_tools(self, query: str, max_results: int = 5, source_filter: str = None) -> List[Dict]:
        """Search for tools using your query."""
        
        print(f"🔍 Searching for: '{query}'")
        print("⏱️  Searching...")
        
        # Measure search speed
        start_time = time.time()
        results = await self.store.semantic_search(query, n_results=max_results)
        search_time = time.time() - start_time
        
        # Filter by source if requested
        if source_filter:
            results = [r for r in results if r.get('source', '').lower() == source_filter.lower()]
        
        print(f"⚡ Search completed in {search_time:.3f} seconds")
        print(f"📊 Found {len(results)} results")
        print("=" * 60)
        
        return results
    
    def display_result(self, index: int, result: Dict, show_full_json: bool = False):
        """Display a single search result with all details."""
        
        # Extract basic info
        name = result.get('name', 'Unknown Tool')
        relevance = result.get('relevance_score', 0.0)
        source = result.get('source', 'Unknown')
        category = result.get('category', 'Unknown')
        content = result.get('content', 'No description available')
        
        # Display header
        print(f"\n🧬 RESULT #{index}")
        print(f"Name: {name}")
        print(f"🎯 Relevance Score: {relevance:.3f} (higher = more relevant)")
        print(f"📦 Source: {source}")
        print(f"📂 Category: {category}")
        print()
        
        # Show description (truncated)
        if len(content) > 200:
            print(f"📝 Description: {content[:200]}...")
            print(f"    (... {len(content)-200} more characters)")
        else:
            print(f"📝 Description: {content}")
        print()
        
        # Show complete JSON data if requested
        if show_full_json:
            print("📄 COMPLETE JSON DATA:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            print()
        
        print("-" * 60)
    
    def show_summary(self, results: List[Dict], query: str):
        """Show summary of search results."""
        
        if not results:
            print("🚫 NO RESULTS FOUND")
            print()
            print("💡 Try these tips:")
            print("   • Use simpler terms: 'protein' instead of 'protein structure prediction'")
            print("   • Try module names: 'Bio.Seq', 'Bio.Align', 'Bio.PDB'")
            print("   • Search for functions: 'alignment', 'format', 'parse'")
            print("   • Use general terms: 'sequence', 'analysis', 'tools'")
            return
        
        # Count by source
        sources = {}
        total_relevance = 0
        
        for result in results:
            source = result.get('source', 'Unknown')
            sources[source] = sources.get(source, 0) + 1
            total_relevance += result.get('relevance_score', 0)
        
        avg_relevance = total_relevance / len(results)
        
        print("\n📈 SEARCH SUMMARY")
        print(f"Query: '{query}'")
        print(f"Results found: {len(results)}")
        print(f"Average relevance: {avg_relevance:.3f}")
        print()
        
        print("📊 Results by source:")
        for source, count in sources.items():
            percentage = (count / len(results)) * 100
            print(f"   • {source}: {count} tools ({percentage:.1f}%)")
        print()
    
    async def get_database_stats(self):
        """Show what's in the database."""
        print("📊 DATABASE STATISTICS")
        print("=" * 30)
        
        # Get sample of tools to analyze
        sample = self.store.collection.get(limit=100)
        
        if sample['metadatas']:
            sources = {}
            categories = {}
            
            for metadata in sample['metadatas']:
                if metadata:
                    source = metadata.get('source', 'Unknown')
                    category = metadata.get('category', 'Unknown')
                    
                    sources[source] = sources.get(source, 0) + 1
                    categories[category] = categories.get(category, 0) + 1
            
            print(f"Total tools in database: {self.total_tools:,}")
            print()
            
            print("🔬 Available sources:")
            for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
                print(f"   • {source}")
            print()
            
            print("📂 Top categories:")
            for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"   • {category}")
            print()

def show_help():
    """Show detailed help and examples."""
    help_text = """
🔍 Interactive Query Testing Tool - Complete Guide
================================================

WHAT THIS DOES:
Test your own search queries against the ChromaDB bioinformatics database.
See exactly what data is stored for each tool, with relevance scores and sources.

BASIC USAGE:
python tests/test_query.py "your search query"

EXAMPLES:
python tests/test_query.py "protein structure prediction"
python tests/test_query.py "RNA-seq differential expression"
python tests/test_query.py "sequence alignment tools"
python tests/test_query.py "Bio.Seq functions"

ADVANCED OPTIONS:
--max-results, -n      Number of results to show (default: 5)
--detailed             Show complete JSON data for each tool
--source               Filter by specific source (Biopython, Bioconductor, etc.)
--stats                Show database statistics before searching

ADVANCED EXAMPLES:
python tests/test_query.py "alignment" --max-results 10
python tests/test_query.py "DESeq2" --detailed
python tests/test_query.py "sequence" --source Biopython
python tests/test_query.py "analysis" --stats

WHAT YOU'LL SEE:
✅ Relevance Score: 0.0-1.0 (higher = more relevant to your query)
✅ Source: Which repository the tool comes from (Biopython, Bioconductor)
✅ Category: What type of bioinformatics tool it is
✅ Description: What the tool does
✅ Complete JSON: All metadata stored in ChromaDB (with --detailed)

SEARCH TIPS:
• Start simple: Use "protein" before "protein structure prediction"
• Try module names: "Bio.Seq", "Bio.Align", "Bio.PDB"
• Use function names: "alignment", "parse", "format"
• General categories: "sequence", "analysis", "visualization"

UNDERSTANDING RESULTS:
• Relevance 0.8-1.0: Highly relevant, exactly what you're looking for
• Relevance 0.6-0.8: Good match, related to your query
• Relevance 0.4-0.6: Somewhat related, might be useful
• Relevance 0.0-0.4: Low relevance, probably not what you want

TROUBLESHOOTING:
• No results? Try simpler, more general terms
• Want more results? Use --max-results 10
• Need details? Use --detailed to see complete tool information
• Check what's available? Use --stats
    """
    print(help_text)

async def main():
    """Main function that handles command line arguments."""
    
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(
        description="Interactive query testing for ChromaDB bioinformatics tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tests/test_query.py "protein structure"
  python tests/test_query.py "RNA-seq" --max-results 10
  python tests/test_query.py "Bio.Seq" --detailed
  python tests/test_query.py "alignment" --source Biopython
        """
    )
    
    parser.add_argument("query", nargs='?', help="Search query to test")
    parser.add_argument("--max-results", "-n", type=int, default=5,
                       help="Maximum number of results to show (default: 5)")
    parser.add_argument("--detailed", "-d", action="store_true",
                       help="Show complete JSON data for each result")
    parser.add_argument("--source", "-s", 
                       help="Filter results by source (e.g., Biopython, Bioconductor)")
    parser.add_argument("--stats", action="store_true",
                       help="Show database statistics")
    
    args = parser.parse_args()
    
    # Show help if no query provided
    if not args.query and not args.stats:
        show_help()
        return
    
    # Initialize the query tester
    print("🔬 ChromaDB Query Testing Tool")
    print("=" * 40)
    
    tester = QueryTester()
    await tester.connect_to_database()
    
    # Show database stats if requested
    if args.stats:
        await tester.get_database_stats()
        if not args.query:
            return
    
    # Perform the search
    try:
        results = await tester.search_tools(
            query=args.query,
            max_results=args.max_results,
            source_filter=args.source
        )
        
        # Display each result
        for i, result in enumerate(results, 1):
            tester.display_result(i, result, show_full_json=args.detailed)
        
        # Show summary
        tester.show_summary(results, args.query)
        
        print("✅ Query testing completed!")
        print(f"💡 Try different queries or use --help for more options")
        
    except Exception as e:
        print(f"❌ Error during search: {e}")
        print("💡 Check that your ChromaDB is properly set up")

if __name__ == "__main__":
    asyncio.run(main())