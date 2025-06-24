"""
Mock implementations for testing MCP client functionality.
"""
from typing import Dict, Any


class MockMCPClient:
    """Mock MCP client for testing purposes."""
    
    def __init__(self):
        """Initialize mock client."""
        pass
    
    async def query_code_executor(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Mock code executor query."""
        return {
            "success": True,
            "data": {
                "result": "Mock Code Executor Result"
            }
        }
    
    async def query_bio_mcp(self, query: str) -> Dict[str, Any]:
        """Mock bio MCP query."""
        return {
            "success": True,
            "data": {
                "tools": ["Mock MCP Tool"]
            }
        }
    
    async def query_pubmed_mcp(self, query: str) -> Dict[str, Any]:
        """Mock PubMed MCP query."""
        return {
            "success": True,
            "data": {
                "tools": ["Mock PubMed Tool"]
            }
        }
    
    async def query_bio_context(self, query: str) -> Dict[str, Any]:
        """Mock BioContext query."""
        return {
            "success": True,
            "data": {
                "tools": ["Mock BioContext Tool"]
            }
        }
    
    async def close(self):
        """Mock close method."""
        pass


class MockSmitheryClient:
    """Mock Smithery client for testing purposes."""
    
    def __init__(self):
        """Initialize mock Smithery client."""
        pass
    
    async def search_tools(self, query: str) -> Dict[str, Any]:
        """Mock tool search."""
        return {
            "success": True,
            "data": {
                "tools": [
                    {
                        "id": "mock-tool-1",
                        "name": "Mock Bioinformatics Tool",
                        "description": "A mock tool for testing",
                        "category": "sequence_analysis"
                    }
                ]
            }
        }
    
    async def get_tool_details(self, tool_id: str) -> Dict[str, Any]:
        """Mock tool details."""
        return {
            "success": True,
            "data": {
                "id": tool_id,
                "name": "Mock Tool",
                "description": "Detailed mock tool information",
                "parameters": ["input_file", "threshold"],
                "usage": "mock usage instructions"
            }
        }
    
    async def execute_workflow(self, workflow_id: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Mock workflow execution."""
        return {
            "success": True,
            "data": {
                "workflow_id": workflow_id,
                "status": "completed",
                "results": "Mock workflow execution results"
            }
        }
    
    async def close(self):
        """Mock close method."""
        pass
