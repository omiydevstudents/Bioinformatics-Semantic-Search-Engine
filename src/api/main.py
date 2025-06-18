from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
import uvicorn
import os
from dotenv import load_dotenv

from ..agents.tool_discovery_agent import ToolDiscoveryAgent

load_dotenv()

app = FastAPI(
    title="Bioinformatics Tool Discovery API",
    description="API for discovering bioinformatics tools using MCP and EXA search",
    version="1.0.0"
)

class QueryRequest(BaseModel):
    """Model for tool discovery query requests."""
    query: str
    max_results: Optional[int] = 5

class QueryResponse(BaseModel):
    """Model for tool discovery query responses."""
    success: bool
    response: Optional[str] = None
    analysis: Optional[str] = None
    error: Optional[str] = None

@app.post("/discover", response_model=QueryResponse)
async def discover_tools(request: QueryRequest) -> QueryResponse:
    """Endpoint for discovering bioinformatics tools."""
    try:
        agent = ToolDiscoveryAgent()
        result = await agent.discover_tools(request.query)
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return QueryResponse(
            success=True,
            response=result["response"],
            analysis=result["analysis"]
        )
    except Exception as e:
        return QueryResponse(
            success=False,
            error=str(e)
        )

@app.get("/health")
async def health_check() -> Dict:
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True) 