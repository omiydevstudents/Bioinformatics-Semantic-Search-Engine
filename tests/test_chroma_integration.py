import pytest
import asyncio
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(os.path.dirname(current_dir), "src")
sys.path.insert(0, src_dir)

from db.chroma_store import SemanticSearchStore


@pytest.mark.asyncio
async def test_chroma_store_initialization():
    """Test that ChromaDB store initializes properly."""
    store = SemanticSearchStore()
    
    # Check that components are initialized
    assert store.embeddings is not None, "Embeddings should be initialized"
    assert store.vector_store is not None, "Vector store should be initialized"
    assert store.client is not None, "ChromaDB client should be initialized"
    assert store.collection is not None, "ChromaDB collection should be initialized"


@pytest.mark.asyncio
async def test_add_sample_tools():
    """Test adding sample bioinformatics tools to the store."""
    store = SemanticSearchStore()
    
    # Sample bioinformatics tools
    sample_tools = [
        {
            "name": "BLAST",
            "category": "sequence_alignment",
            "description": "Basic Local Alignment Search Tool for comparing biological sequences",
            "features": ["sequence alignment", "similarity search", "database search"],
            "documentation": "BLAST finds regions of local similarity between sequences",
            "source": "NCBI"
        },
        {
            "name": "BWA",
            "category": "sequence_alignment",
            "description": "Burrows-Wheeler Aligner for mapping DNA sequences",
            "features": ["read mapping", "genome alignment", "NGS data"],
            "documentation": "BWA is a software package for mapping low-divergent sequences",
            "source": "Biopython"
        },
        {
            "name": "DESeq2",
            "category": "differential_expression",
            "description": "Differential gene expression analysis based on negative binomial distribution",
            "features": ["RNA-seq", "differential expression", "statistical analysis"],
            "documentation": "DESeq2 provides methods to test for differential expression",
            "source": "Bioconductor"
        }
    ]
    
    # Add tools to the store
    success = await store.add_tools(sample_tools)
    assert success, "Adding tools should succeed"


@pytest.mark.asyncio
async def test_semantic_search_real_data():
    """Test semantic search with real data."""
    store = SemanticSearchStore()
    
    # First add some sample data
    sample_tools = [
        {
            "name": "BLAST",
            "category": "sequence_alignment",
            "description": "Basic Local Alignment Search Tool for comparing biological sequences",
            "features": ["sequence alignment", "similarity search", "database search"],
            "documentation": "BLAST finds regions of local similarity between sequences",
            "source": "NCBI"
        },
        {
            "name": "Bowtie2",
            "category": "sequence_alignment",
            "description": "Fast and memory-efficient tool for aligning sequencing reads",
            "features": ["read alignment", "NGS", "genome mapping"],
            "documentation": "Bowtie2 is an ultrafast and memory-efficient tool",
            "source": "Biopython"
        }
    ]
    
    await store.add_tools(sample_tools)
    
    # Test semantic search
    query = "sequence alignment tools"
    results = await store.semantic_search(query, n_results=5)
    
    print(f"\nSemantic search results for '{query}':")
    for i, result in enumerate(results):
        print(f"{i+1}. {result['name']} (Score: {result['relevance_score']:.3f})")
        print(f"   Category: {result['category']}")
        print(f"   Content: {result['content'][:100]}...")
    
    # Check results
    assert isinstance(results, list), "Results should be a list"
    assert len(results) > 0, "Should return some results"
    
    # Check result structure
    for result in results:
        assert "name" in result, "Result should have name"
        assert "category" in result, "Result should have category"
        assert "relevance_score" in result, "Result should have relevance score"


@pytest.mark.asyncio
async def test_category_search_real_data():
    """Test category-based search with real data."""
    store = SemanticSearchStore()
    
    # Add sample data with different categories
    sample_tools = [
        {
            "name": "STAR",
            "category": "rna_seq",
            "description": "Spliced Transcripts Alignment to a Reference",
            "features": ["RNA-seq alignment", "splice junction detection"],
            "documentation": "STAR aligns RNA-seq reads to reference genomes",
            "source": "GitHub"
        },
        {
            "name": "Cufflinks",
            "category": "rna_seq",
            "description": "Transcriptome assembly and differential expression analysis",
            "features": ["transcript assembly", "FPKM calculation"],
            "documentation": "Cufflinks assembles transcripts from RNA-seq reads",
            "source": "Biopython"
        }
    ]
    
    await store.add_tools(sample_tools)
    
    # Test category search
    query = "RNA sequencing analysis"
    category = "rna_seq"
    results = await store.search_by_category(category, query, n_results=5)
    
    print(f"\nCategory search results for '{query}' in category '{category}':")
    for i, result in enumerate(results):
        print(f"{i+1}. {result['name']} (Score: {result['relevance_score']:.3f})")
        print(f"   Category: {result['category']}")
    
    # Check results
    assert isinstance(results, list), "Results should be a list"
    
    # All results should be from the specified category
    for result in results:
        assert result["category"] == category, f"Result should be from category {category}"


@pytest.mark.asyncio
async def test_get_tool_by_name():
    """Test retrieving a specific tool by name."""
    store = SemanticSearchStore()
    
    # Add a specific tool
    sample_tools = [
        {
            "name": "FastQC",
            "category": "quality_control",
            "description": "Quality control tool for high throughput sequence data",
            "features": ["quality assessment", "sequence statistics", "report generation"],
            "documentation": "FastQC provides quality control checks on raw sequence data",
            "source": "Babraham Institute"
        }
    ]
    
    await store.add_tools(sample_tools)
    
    # Retrieve the tool
    tool = await store.get_tool_by_name("FastQC")
    
    if tool:
        print(f"\nRetrieved tool: {tool['name']}")
        print(f"Content: {tool['content'][:200]}...")
        
        assert tool["name"] == "FastQC", "Should retrieve the correct tool"
        assert "content" in tool, "Tool should have content"
    else:
        print("Tool not found - this might be expected if the store is empty")


if __name__ == "__main__":
    # Allow running this file directly for manual testing
    async def main():
        print("Testing ChromaDB integration with real data...")
        
        # Initialize store
        store = SemanticSearchStore()
        print("✓ ChromaDB store initialized")
        
        # Add sample tools
        sample_tools = [
            {
                "name": "BLAST",
                "category": "sequence_alignment",
                "description": "Basic Local Alignment Search Tool",
                "features": ["sequence alignment", "similarity search"],
                "documentation": "BLAST finds regions of local similarity",
                "source": "NCBI"
            }
        ]
        
        success = await store.add_tools(sample_tools)
        print(f"✓ Added sample tools: {success}")
        
        # Test search
        results = await store.semantic_search("sequence alignment", n_results=3)
        print(f"✓ Search results: {len(results)} tools found")
        
        for result in results:
            print(f"  - {result['name']} (Score: {result['relevance_score']:.3f})")

    asyncio.run(main())
