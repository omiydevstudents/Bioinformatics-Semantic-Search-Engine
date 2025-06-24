from typing import Dict, List, Optional, Any
import httpx
from pydantic import BaseModel
import os
import json
import re
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

            # Handle different response types
            response_data = await self._parse_response(response)
            return MCPResponse(success=True, data=response_data)
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

            # Handle different response types
            response_data = await self._parse_response(response)
            return MCPResponse(success=True, data=response_data)
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

            # Handle different response types
            response_data = await self._parse_response(response)
            return MCPResponse(success=True, data=response_data)
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

            # Handle different response types
            response_data = await self._parse_response(response)
            return MCPResponse(success=True, data=response_data)
        except Exception as e:
            return MCPResponse(success=False, data={}, error=str(e))

    async def _parse_response(self, response: httpx.Response) -> Dict[str, Any]:
        """
        Parse response from MCP server, handling various response formats.
        """
        try:
            # First try to parse as JSON
            return response.json()
        except (json.JSONDecodeError, ValueError):
            # If JSON parsing fails, try to extract content
            content = response.text.strip()

            if not content:
                # Empty response
                return {
                    "message": "Empty response from server",
                    "status": "no_content",
                    "tools": []
                }

            # Check if this is an HTML page (likely a documentation page)
            if content.startswith('<!DOCTYPE html>') or '<html' in content[:100]:
                # Extract title and description from HTML
                title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
                desc_match = re.search(r'<meta name="description" content="(.*?)"', content, re.IGNORECASE)

                title = title_match.group(1) if title_match else "Unknown Page"
                description = desc_match.group(1) if desc_match else "No description available"

                return {
                    "message": f"Received HTML page: {title}",
                    "description": description,
                    "status": "html_page",
                    "tools": [],
                    "note": "This appears to be a documentation page, not an active MCP server endpoint",
                    "suggestion": "Check if this URL points to an actual MCP server API endpoint"
                }

            # Try to find JSON-like content in the response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

            # Try to find array-like content
            array_match = re.search(r'\[.*\]', content, re.DOTALL)
            if array_match:
                try:
                    parsed_array = json.loads(array_match.group())
                    return {"tools": parsed_array, "message": "Parsed from array format"}
                except json.JSONDecodeError:
                    pass

            # If all else fails, return the raw content as a message
            return {
                "message": content[:500] + "..." if len(content) > 500 else content,
                "status": "raw_text",
                "tools": [],
                "raw_response_length": len(content)
            }

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
