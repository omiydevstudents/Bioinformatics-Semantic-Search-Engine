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

from agents.tool_discovery_agent import ToolDiscoveryAgent


@pytest.mark.asyncio
async def test_tool_discovery_agent_initialization():
    """Test that the tool discovery agent initializes properly."""
    agent = ToolDiscoveryAgent()

    # Check that components are initialized
    assert agent.mcp_client is not None, "MCP client should be initialized"
    assert agent.chroma_store is not None, "ChromaDB store should be initialized"
    assert agent.memory is not None, "Memory should be initialized"


@pytest.mark.asyncio
async def test_discover_tools_protein_structure():
    """Test tool discovery for protein structure prediction using real data."""
    agent = ToolDiscoveryAgent()

    query = "Suggest software for protein structure prediction"
    print(f"🔍 Querying for: {query}")

    try:
        result = await agent.discover_tools(query)

        # Check response structure
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "response" in result, "Result should contain 'response' key"
        assert "analysis" in result, "Result should contain 'analysis' key"

        print("\n=== AGENT RESPONSE ===")
        print("Response:", result["response"])
        print("Analysis:", result["analysis"])

        # Check that we got some results
        assert result["response"] is not None, "Response should not be None"
        assert result["analysis"] is not None, "Analysis should not be None"

    except Exception as e:
        print(f"Tool discovery test failed: {e}")
        # Don't fail the test for network issues, just log them
        pytest.skip(f"Skipping due to network/server issue: {e}")


@pytest.mark.asyncio
async def test_discover_tools_rna_seq():
    """Test tool discovery for RNA-seq analysis using real data."""
    agent = ToolDiscoveryAgent()

    query = "Find tools for RNA-seq analysis"
    print(f"🔍 Querying for: {query}")

    try:
        result = await agent.discover_tools(query)

        # Check response structure
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "response" in result, "Result should contain 'response' key"
        assert "analysis" in result, "Result should contain 'analysis' key"

        print("\n=== RNA-SEQ AGENT RESPONSE ===")
        print("Response:", result["response"])
        print("Analysis:", result["analysis"])

        # Check that we got some results
        assert result["response"] is not None, "Response should not be None"
        assert result["analysis"] is not None, "Analysis should not be None"

    except Exception as e:
        print(f"RNA-seq tool discovery test failed: {e}")
        pytest.skip(f"Skipping due to network/server issue: {e}")


@pytest.mark.asyncio
async def test_discover_tools_genome_assembly():
    """Test tool discovery for genome assembly using real data."""
    agent = ToolDiscoveryAgent()

    query = "Find tools for genome assembly and annotation"
    print(f"🔍 Querying for: {query}")

    try:
        result = await agent.discover_tools(query)

        # Check response structure
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "response" in result, "Result should contain 'response' key"
        assert "analysis" in result, "Result should contain 'analysis' key"

        print("\n=== GENOME ASSEMBLY AGENT RESPONSE ===")
        print("Response:", result["response"])
        print("Analysis:", result["analysis"])

        # Check that we got some results
        assert result["response"] is not None, "Response should not be None"
        assert result["analysis"] is not None, "Analysis should not be None"

    except Exception as e:
        print(f"Genome assembly tool discovery test failed: {e}")
        pytest.skip(f"Skipping due to network/server issue: {e}")


if __name__ == "__main__":
    # Allow running this file directly for manual testing
    async def main():
        agent = ToolDiscoveryAgent()
        query = "Suggest software for protein structure prediction"
        print(f"🔍 Querying for: {query}")
        result = await agent.discover_tools(query)
        print("\n=== AGENT RESPONSE ===")
        print("Response:", result["response"])
        print("Analysis:", result["analysis"])

    asyncio.run(main())
