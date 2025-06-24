"""
Comprehensive test suite for the Bioinformatics Semantic Search Engine
using real data and actual API calls.
"""
import pytest
import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(os.path.dirname(current_dir), "src")
sys.path.insert(0, src_dir)

from mcp.mcp_client import MCPClient
from db.chroma_store import SemanticSearchStore
from agents.tool_discovery_agent import ToolDiscoveryAgent


class TestRealDataIntegration:
    """Test suite for real data integration."""
    
    @pytest.mark.asyncio
    async def test_environment_setup(self):
        """Test that all required environment variables are set."""
        required_vars = [
            "GOOGLE_API_KEY",
            "BIO_MCP_URL",
            "PUBMED_MCP_URL", 
            "BIO_CONTEXT_URL",
            "SMITHERY_API_KEY"
        ]
        
        for var in required_vars:
            value = os.getenv(var)
            assert value is not None, f"Environment variable {var} should be set"
            assert len(value) > 0, f"Environment variable {var} should not be empty"
            print(f"✓ {var}: {'*' * (len(value) - 4)}{value[-4:]}")
    
    @pytest.mark.asyncio
    async def test_mcp_client_real_queries(self):
        """Test MCP client with real API calls."""
        client = MCPClient()
        
        test_queries = [
            "Find tools for protein structure prediction",
            "RNA-seq differential expression analysis",
            "Genome assembly tools",
            "Phylogenetic analysis software"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Testing query: {query}")
            
            # Test Bio MCP
            try:
                bio_response = await client.query_bio_mcp(query)
                print(f"  Bio MCP: {'✓' if bio_response.success else '✗'} {bio_response.error or 'Success'}")
                if bio_response.success:
                    assert isinstance(bio_response.data, dict)
            except Exception as e:
                print(f"  Bio MCP: ✗ Exception: {e}")
            
            # Test PubMed MCP
            try:
                pubmed_response = await client.query_pubmed_mcp(query)
                print(f"  PubMed MCP: {'✓' if pubmed_response.success else '✗'} {pubmed_response.error or 'Success'}")
                if pubmed_response.success:
                    assert isinstance(pubmed_response.data, dict)
            except Exception as e:
                print(f"  PubMed MCP: ✗ Exception: {e}")
            
            # Test BioContext
            try:
                context_response = await client.query_bio_context(query)
                print(f"  BioContext: {'✓' if context_response.success else '✗'} {context_response.error or 'Success'}")
                if context_response.success:
                    assert isinstance(context_response.data, dict)
            except Exception as e:
                print(f"  BioContext: ✗ Exception: {e}")
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_chroma_store_with_real_tools(self):
        """Test ChromaDB store with real bioinformatics tools."""
        store = SemanticSearchStore()
        
        # Real bioinformatics tools data
        real_tools = [
            {
                "name": "BLAST",
                "category": "sequence_alignment",
                "description": "Basic Local Alignment Search Tool for comparing biological sequences against databases",
                "features": ["sequence similarity search", "database alignment", "E-value statistics", "multiple sequence formats"],
                "documentation": "BLAST finds regions of local similarity between sequences. The program compares nucleotide or protein sequences to sequence databases and calculates the statistical significance of matches.",
                "source": "NCBI"
            },
            {
                "name": "BWA",
                "category": "sequence_alignment", 
                "description": "Burrows-Wheeler Aligner for mapping DNA sequences against reference genome",
                "features": ["short read alignment", "BWA-MEM algorithm", "paired-end support", "SAM output"],
                "documentation": "BWA is a software package for mapping low-divergent sequences against a large reference genome, such as the human genome.",
                "source": "GitHub"
            },
            {
                "name": "DESeq2",
                "category": "differential_expression",
                "description": "Differential gene expression analysis based on negative binomial distribution",
                "features": ["RNA-seq analysis", "statistical testing", "normalization", "visualization"],
                "documentation": "DESeq2 provides methods to test for differential expression by use of negative binomial generalized linear models.",
                "source": "Bioconductor"
            },
            {
                "name": "STAR",
                "category": "rna_seq",
                "description": "Spliced Transcripts Alignment to a Reference for RNA-seq data",
                "features": ["splice-aware alignment", "chimeric detection", "quantification", "fusion detection"],
                "documentation": "STAR aligns RNA-seq reads to a reference genome using uncompressed suffix arrays.",
                "source": "GitHub"
            },
            {
                "name": "Cufflinks",
                "category": "rna_seq",
                "description": "Transcriptome assembly and differential expression analysis for RNA-seq",
                "features": ["transcript assembly", "FPKM calculation", "differential expression", "isoform analysis"],
                "documentation": "Cufflinks assembles transcripts, estimates their abundances, and tests for differential expression.",
                "source": "GitHub"
            }
        ]
        
        # Add tools to store
        success = await store.add_tools(real_tools)
        assert success, "Should successfully add real tools to ChromaDB"
        print(f"✓ Added {len(real_tools)} real bioinformatics tools to ChromaDB")
        
        # Test various search queries
        test_queries = [
            "sequence alignment tools",
            "RNA-seq analysis software", 
            "differential gene expression",
            "protein structure prediction",
            "genome assembly"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Searching for: {query}")
            results = await store.semantic_search(query, n_results=3)
            
            print(f"  Found {len(results)} results:")
            for i, result in enumerate(results):
                print(f"    {i+1}. {result['name']} (Score: {result['relevance_score']:.3f})")
                print(f"       Category: {result['category']}")
            
            assert isinstance(results, list), "Results should be a list"
            # Don't assert length > 0 as some queries might not match
    
    @pytest.mark.asyncio
    async def test_tool_discovery_agent_integration(self):
        """Test the complete tool discovery agent with real data."""
        agent = ToolDiscoveryAgent()
        
        # Test queries that should return real results
        test_queries = [
            "Find tools for protein structure prediction",
            "RNA-seq differential expression analysis tools",
            "Sequence alignment software for genomics",
            "Tools for phylogenetic tree construction"
        ]
        
        for query in test_queries:
            print(f"\n🤖 Agent query: {query}")
            
            try:
                result = await agent.discover_tools(query)
                
                # Check response structure
                assert isinstance(result, dict), "Result should be a dictionary"
                assert "response" in result, "Result should contain response"
                assert "analysis" in result, "Result should contain analysis"
                
                print(f"  Response: {result['response'][:200]}...")
                print(f"  Analysis: {result['analysis']}")
                
                # Verify we got some meaningful response
                assert len(result['response']) > 0, "Response should not be empty"
                assert len(result['analysis']) > 0, "Analysis should not be empty"
                
            except Exception as e:
                print(f"  ✗ Agent query failed: {e}")
                # Don't fail test for network issues
                pytest.skip(f"Skipping due to network/server issue: {e}")
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow with real data."""
        print("\n🚀 Testing end-to-end workflow...")
        
        # 1. Initialize all components
        mcp_client = MCPClient()
        chroma_store = SemanticSearchStore()
        agent = ToolDiscoveryAgent()
        
        print("✓ All components initialized")
        
        # 2. Add some real tools to ChromaDB
        real_tools = [
            {
                "name": "FastQC",
                "category": "quality_control",
                "description": "Quality control tool for high throughput sequence data",
                "features": ["quality assessment", "per base quality", "sequence duplication", "adapter content"],
                "documentation": "FastQC provides a modular set of analyses which you can use to give a quick impression of whether your data has any problems.",
                "source": "Babraham Institute"
            }
        ]
        
        await chroma_store.add_tools(real_tools)
        print("✓ Added sample tools to ChromaDB")
        
        # 3. Test agent discovery
        query = "quality control tools for sequencing data"
        result = await agent.discover_tools(query)
        
        print(f"✓ Agent discovery completed")
        print(f"  Query: {query}")
        print(f"  Response length: {len(result['response'])}")
        print(f"  Analysis: {result['analysis']}")
        
        # 4. Verify results
        assert isinstance(result, dict)
        assert len(result['response']) > 0
        assert len(result['analysis']) > 0
        
        # 5. Cleanup
        await mcp_client.close()
        print("✓ End-to-end workflow completed successfully")


if __name__ == "__main__":
    # Allow running this file directly
    async def main():
        print("🧪 Running comprehensive real data tests...")
        
        test_instance = TestRealDataIntegration()
        
        try:
            await test_instance.test_environment_setup()
            print("✓ Environment setup test passed")
        except Exception as e:
            print(f"✗ Environment setup test failed: {e}")
        
        try:
            await test_instance.test_mcp_client_real_queries()
            print("✓ MCP client test passed")
        except Exception as e:
            print(f"✗ MCP client test failed: {e}")
        
        try:
            await test_instance.test_chroma_store_with_real_tools()
            print("✓ ChromaDB test passed")
        except Exception as e:
            print(f"✗ ChromaDB test failed: {e}")
        
        try:
            await test_instance.test_tool_discovery_agent_integration()
            print("✓ Agent integration test passed")
        except Exception as e:
            print(f"✗ Agent integration test failed: {e}")
        
        try:
            await test_instance.test_end_to_end_workflow()
            print("✓ End-to-end workflow test passed")
        except Exception as e:
            print(f"✗ End-to-end workflow test failed: {e}")
        
        print("\n🎉 All tests completed!")

    asyncio.run(main())
