import os
from dotenv import load_dotenv
from pathlib import Path
import asyncio

# Add the project root to Python path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.db.chroma_store import SemanticSearchStore

async def main():
    # Load environment variables
    load_dotenv()
    
    # Get configuration from environment
    chroma_db_dir = os.getenv('CHROMA_DB_DIR', 'data/chroma')
    embedding_model = os.getenv('EMBEDDING_MODEL', 'microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext')
    
    print(f"Initializing ChromaDB with:")
    print(f"- Database directory: {chroma_db_dir}")
    print(f"- Embedding model: {embedding_model}")
    
    # Create data directory if it doesn't exist
    Path(chroma_db_dir).mkdir(parents=True, exist_ok=True)
    
    # Initialize the store
    store = SemanticSearchStore(persist_dir=chroma_db_dir)
    
    # Test data
    test_tools = [
        {
            "name": "BLAST",
            "category": "Sequence Analysis",
            "description": "Basic Local Alignment Search Tool for comparing biological sequences",
            "features": ["sequence alignment", "homology search", "database search"],
            "documentation": "https://blast.ncbi.nlm.nih.gov/Blast.cgi"
        },
        {
            "name": "ClustalW",
            "category": "Sequence Alignment",
            "description": "Multiple sequence alignment program for DNA or proteins",
            "features": ["multiple sequence alignment", "phylogenetic analysis"],
            "documentation": "https://www.ebi.ac.uk/Tools/msa/clustalw2/"
        }
    ]
    
    # Test adding tools
    print("\nTesting tool addition...")
    success = await store.add_tools(test_tools)
    print(f"Tool addition {'successful' if success else 'failed'}")
    
    # Check what's in the collection
    print(f"\nChecking collection contents...")
    collection_count = store.collection.count()
    print(f"Collection has {collection_count} items")
    
    # Get all items to see what's there
    if collection_count > 0:
        all_items = store.collection.get()
        print(f"Sample documents in collection:")
        for i, doc in enumerate(all_items['documents'][:3]):  # Show first 3
            print(f"  {i+1}. {doc[:100]}...")  # Show first 100 chars
    
    # Test semantic search
    print("\nTesting semantic search...")
    search_query = "sequence alignment tool"
    print(f"Searching for: '{search_query}'")
    results = await store.semantic_search(search_query)
    print(f"Found {len(results)} results:")
    for result in results:
        print(f"- {result['name']} (Score: {result['relevance_score']:.2f})")
    
    # Test category search
    print("\nTesting category search...")
    category_query = "alignment"
    category = "Sequence Analysis"
    print(f"Searching for: '{category_query}' in category '{category}'")
    category_results = await store.search_by_category(category, category_query)
    print(f"Found {len(category_results)} results in {category} category:")
    for result in category_results:
        print(f"- {result['name']} (Score: {result['relevance_score']:.2f})")

if __name__ == "__main__":
    asyncio.run(main())