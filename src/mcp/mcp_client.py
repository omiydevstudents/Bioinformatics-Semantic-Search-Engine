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
        self.client = httpx.AsyncClient(timeout=30.0)

    async def query_bio_mcp(self, query: str) -> MCPResponse:
        """Query the bioinformatics MCP server."""
        try:
            response = await self.client.post(
                f"{self.bio_mcp_url}/query",
                json={"query": query}
            )
            response.raise_for_status()
            return MCPResponse(success=True, data=response.json())
        except Exception as e:
            return MCPResponse(success=False, data={}, error=str(e))

    async def query_pubmed_mcp(self, query: str) -> MCPResponse:
        """Query the PubMed MCP server."""
        try:
            response = await self.client.post(
                f"{self.pubmed_mcp_url}/query",
                json={"query": query}
            )
            response.raise_for_status()
            return MCPResponse(success=True, data=response.json())
        except Exception as e:
            return MCPResponse(success=False, data={}, error=str(e))

    async def query_bio_context(self, query: str) -> MCPResponse:
        """Query the BioContext MCP server."""
        try:
            response = await self.client.post(
                f"{self.bio_context_url}/query",
                json={"query": query}
            )
            response.raise_for_status()
            return MCPResponse(success=True, data=response.json())
        except Exception as e:
            return MCPResponse(success=False, data={}, error=str(e))

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose() 