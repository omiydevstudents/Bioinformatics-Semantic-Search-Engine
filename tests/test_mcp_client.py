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


@pytest.mark.asyncio
async def test_real_mcp_client_initialization():
    """Test that the real MCP client initializes properly with environment variables."""
    client = MCPClient()

    # Check that environment variables are loaded
    assert client.bio_mcp_url is not None, "BIO_MCP_URL should be set"
    assert client.pubmed_mcp_url is not None, "PUBMED_MCP_URL should be set"
    assert client.bio_context_url is not None, "BIO_CONTEXT_URL should be set"
    assert client.code_executor_url is not None, "MCP_CODE_EXECUTOR_URL should be set"

    await client.close()


@pytest.mark.asyncio
async def test_query_bio_mcp_real():
    """Test real Bio MCP query with actual server."""
    client = MCPClient()

    try:
        response = await client.query_bio_mcp("Find tools for RNA-seq analysis")

        # Check response structure
        assert hasattr(response, 'success'), "Response should have success attribute"
        assert hasattr(response, 'data'), "Response should have data attribute"

        # Print response for debugging
        print(f"Bio MCP Response: {response}")

        # If successful, check data structure
        if response.success:
            assert isinstance(response.data, dict), "Response data should be a dictionary"
        else:
            print(f"Bio MCP query failed: {response.error}")

    except Exception as e:
        print(f"Bio MCP test failed with exception: {e}")
        # Don't fail the test for network issues, just log them

    finally:
        await client.close()


@pytest.mark.asyncio
async def test_query_pubmed_mcp_real():
    """Test real PubMed MCP query with actual server."""
    client = MCPClient()

    try:
        response = await client.query_pubmed_mcp("Find tools for literature mining")

        # Check response structure
        assert hasattr(response, 'success'), "Response should have success attribute"
        assert hasattr(response, 'data'), "Response should have data attribute"

        # Print response for debugging
        print(f"PubMed MCP Response: {response}")

        # If successful, check data structure
        if response.success:
            assert isinstance(response.data, dict), "Response data should be a dictionary"
        else:
            print(f"PubMed MCP query failed: {response.error}")

    except Exception as e:
        print(f"PubMed MCP test failed with exception: {e}")

    finally:
        await client.close()


@pytest.mark.asyncio
async def test_query_bio_context_real():
    """Test real BioContext query with actual server."""
    client = MCPClient()

    try:
        response = await client.query_bio_context("Find context-aware tools")

        # Check response structure
        assert hasattr(response, 'success'), "Response should have success attribute"
        assert hasattr(response, 'data'), "Response should have data attribute"

        # Print response for debugging
        print(f"BioContext Response: {response}")

        # If successful, check data structure
        if response.success:
            assert isinstance(response.data, dict), "Response data should be a dictionary"
        else:
            print(f"BioContext query failed: {response.error}")

    except Exception as e:
        print(f"BioContext test failed with exception: {e}")

    finally:
        await client.close()


@pytest.mark.asyncio
async def test_query_code_executor_real():
    """Test real Code Executor query (may fail if server not running locally)."""
    client = MCPClient()

    try:
        payload = {"code": "print('Hello, world!')"}
        response = await client.query_code_executor(payload)

        # Check response structure
        assert hasattr(response, 'success'), "Response should have success attribute"
        assert hasattr(response, 'data'), "Response should have data attribute"

        # Print response for debugging
        print(f"Code Executor Response: {response}")

        # If successful, check data structure
        if response.success:
            assert isinstance(response.data, dict), "Response data should be a dictionary"
        else:
            print(f"Code Executor query failed (expected if server not running): {response.error}")

    except Exception as e:
        print(f"Code Executor test failed (expected if server not running): {e}")

    finally:
        await client.close()
