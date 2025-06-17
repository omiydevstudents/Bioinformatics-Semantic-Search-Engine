import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

from ..data.ingestion import RepositoryIngestion
from ..db.chroma_store import SemanticSearchStore

load_dotenv()

async def initialize_store():
    """Initialize and populate the semantic search store."""
    print("🚀 Initializing semantic search store...")
    
    # Create data directories
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Initialize components
    ingestion = RepositoryIngestion()
    store = SemanticSearchStore()
    
    # Ingest repositories
    print("📚 Ingesting bioinformatics repositories...")
    results = await ingestion.ingest_all_repositories()
    
    # Count total tools
    total_tools = sum(len(tools) for tools in results.values())
    print(f"📊 Found {total_tools} tools across {len(results)} repositories")
    
    # Add tools to semantic search store
    print("💾 Adding tools to semantic search store...")
    for repo_name, tools in results.items():
        print(f"  - Processing {repo_name}: {len(tools)} tools")
        success = await store.add_tools(tools)
        if success:
            print(f"  ✅ Successfully added {repo_name} tools")
        else:
            print(f"  ❌ Failed to add {repo_name} tools")
    
    # Test semantic search
    print("\n🔍 Testing semantic search...")
    test_queries = [
        "sequence alignment",
        "RNA-seq analysis",
        "protein structure prediction",
        "variant calling"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        results = await store.semantic_search(query, n_results=3)
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['name']} (Score: {result['relevance_score']:.2f})")
    
    print("\n✨ Semantic search store initialization complete!")

if __name__ == "__main__":
    asyncio.run(initialize_store()) 