from typing import Dict, List, Optional
import httpx
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()


class MCPResponse(BaseModel):
    """Model for MCP server responses."""

    success: bool
    data: Dict
    error: Optional[str] = None


class MCPClient:
    """Client for interacting with MCP servers."""

    def __init__(self):
        self.bio_mcp_url = os.getenv("BIO_MCP_URL")
        self.pubmed_mcp_url = os.getenv("PUBMED_MCP_URL")
        self.bio_context_url = os.getenv("BIO_CONTEXT_URL")
        self.code_executor_url = os.getenv("MCP_CODE_EXECUTOR_URL")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def query_bio_mcp(self, query: str) -> MCPResponse:
        """Query the bioinformatics MCP server."""
        if not self.bio_mcp_url:
            raise ValueError("BIO_MCP_URL environment variable is not set")
        try:
            response = await self.client.post(self.bio_mcp_url, json={"query": query})
            response.raise_for_status()
            return MCPResponse(success=True, data=response.json())
        except Exception as e:
            return MCPResponse(success=False, data={}, error=str(e))

    async def query_pubmed_mcp(self, query: str) -> MCPResponse:
        """Query the PubMed MCP server."""
        if not self.pubmed_mcp_url:
            raise ValueError("PUBMED_MCP_URL environment variable is not set")
        try:
            response = await self.client.post(
                self.pubmed_mcp_url, json={"query": query}
            )
            response.raise_for_status()
            return MCPResponse(success=True, data=response.json())
        except Exception as e:
            return MCPResponse(success=False, data={}, error=str(e))

    async def query_bio_context(self, query: str) -> MCPResponse:
        """Query the BioContext MCP server."""
        if not self.bio_context_url:
            raise ValueError("BIO_CONTEXT_URL environment variable is not set")
        try:
            response = await self.client.post(
                self.bio_context_url, json={"query": query}
            )
            response.raise_for_status()
            return MCPResponse(success=True, data=response.json())
        except Exception as e:
            return MCPResponse(success=False, data={}, error=str(e))

    async def query_code_executor(self, payload: dict) -> MCPResponse:
        """
        Query the MCP Code Executor server. This endpoint does NOT append /query.
        The payload should be a dict with the required fields for code execution.
        """
        if not self.code_executor_url:
            raise ValueError("MCP_CODE_EXECUTOR_URL environment variable is not set")
        try:
            response = await self.client.post(self.code_executor_url, json=payload)
            response.raise_for_status()
            return MCPResponse(success=True, data=response.json())
        except Exception as e:
            return MCPResponse(success=False, data={}, error=str(e))

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
