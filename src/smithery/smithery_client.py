from typing import Dict, List, Optional
import httpx
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

class SmitheryResponse(BaseModel):
    """Model for Smithery platform responses."""
    success: bool
    data: Dict
    error: Optional[str] = None

class SmitheryClient:
    """Client for interacting with the Smithery platform."""
    
    def __init__(self):
        self.api_key = os.getenv("SMITHERY_API_KEY")
        if not self.api_key:
            raise ValueError("SMITHERY_API_KEY environment variable is not set")
        
        self.base_url = os.getenv("SMITHERY_API_URL", "https://api.smithery.ai")
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=30.0
        )

    async def search_tools(self, query: str) -> SmitheryResponse:
        """Search for bioinformatics tools using Smithery."""
        try:
            response = await self.client.post(
                "/v1/tools/search",
                json={"query": query}
            )
            response.raise_for_status()
            return SmitheryResponse(success=True, data=response.json())
        except Exception as e:
            return SmitheryResponse(success=False, data={}, error=str(e))

    async def get_tool_details(self, tool_id: str) -> SmitheryResponse:
        """Get detailed information about a specific tool."""
        try:
            response = await self.client.get(f"/v1/tools/{tool_id}")
            response.raise_for_status()
            return SmitheryResponse(success=True, data=response.json())
        except Exception as e:
            return SmitheryResponse(success=False, data={}, error=str(e))

    async def get_workflow_templates(self) -> SmitheryResponse:
        """Get available workflow templates from Smithery."""
        try:
            response = await self.client.get("/v1/workflows/templates")
            response.raise_for_status()
            return SmitheryResponse(success=True, data=response.json())
        except Exception as e:
            return SmitheryResponse(success=False, data={}, error=str(e))

    async def execute_workflow(self, workflow_id: str, inputs: Dict) -> SmitheryResponse:
        """Execute a workflow with given inputs."""
        try:
            response = await self.client.post(
                f"/v1/workflows/{workflow_id}/execute",
                json={"inputs": inputs}
            )
            response.raise_for_status()
            return SmitheryResponse(success=True, data=response.json())
        except Exception as e:
            return SmitheryResponse(success=False, data={}, error=str(e))

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose() 