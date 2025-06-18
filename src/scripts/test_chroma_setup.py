import os
from dotenv import load_dotenv
from pathlib import Path
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
    
    # Test semantic search
    print("\nTesting semantic search...")
    results = await store.semantic_search("sequence alignment tool")
    print(f"Found {len(results)} results:")
    for result in results:
        print(f"- {result['name']} (Score: {result['relevance_score']:.2f})")
    
    # Test category search
    print("\nTesting category search...")
    category_results = await store.search_by_category("Sequence Analysis", "alignment")
    print(f"Found {len(category_results)} results in Sequence Analysis category:")
    for result in category_results:
        print(f"- {result['name']} (Score: {result['relevance_score']:.2f})")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 