# src/agents/tool_discovery_agent.py

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.chroma_store import SemanticSearchStore
from mcp.mcp_client import MCPClient

try:
    from langchain_community.memory import ConversationBufferMemory
except ImportError:
    # Fallback for older versions
    from langchain.memory import ConversationBufferMemory


class ToolDiscoveryAgent:
    """
    Agent for discovering bioinformatics tools using real ChromaDB and MCP components.
    Extend this class to add EXA, Smithery, or other integrations as needed.
    """

    def __init__(self):
        self.mcp_client = MCPClient()  # Real MCP client
        self.chroma_store = SemanticSearchStore()  # Real ChromaDB store
        self.memory = ConversationBufferMemory()

    async def discover_tools(self, query: str) -> dict:
        """
        Discover tools for a given query by combining results from MCP and ChromaDB.
        Returns a dictionary with a formatted response and analysis.
        """
        # Query all MCP servers
        mcp_bio_response = await self.mcp_client.query_bio_mcp(query)
        mcp_pubmed_response = await self.mcp_client.query_pubmed_mcp(query)
        mcp_context_response = await self.mcp_client.query_bio_context(query)

        # Query ChromaDB
        chroma_results = await self.chroma_store.semantic_search(query)

        # Process MCP results
        mcp_tools = []
        mcp_messages = []
        mcp_warnings = []

        for name, response in [
            ("Bio MCP", mcp_bio_response),
            ("PubMed MCP", mcp_pubmed_response),
            ("BioContext", mcp_context_response),
        ]:
            if response.success:
                tools = response.data.get("tools", [])
                if tools:
                    mcp_tools.extend(tools)

                # Check if this is an HTML page (documentation)
                if response.data.get("status") == "html_page":
                    mcp_warnings.append(
                        f"{name}: {response.data.get('note', 'HTML page received')}"
                    )
                    if response.data.get("description"):
                        mcp_messages.append(
                            f"{name}: {response.data.get('description')}"
                        )
                else:
                    message = response.data.get("message", "")
                    if message and message != "Empty response from server":
                        mcp_messages.append(f"{name}: {message}")
            else:
                mcp_messages.append(f"{name}: Error - {response.error}")

        # Format response
        chroma_tool_names = [t["name"] for t in chroma_results[:5]]  # Top 5 results

        response_parts = []
        if mcp_tools:
            response_parts.append(f"MCP Tools: {mcp_tools}")
        if chroma_tool_names:
            response_parts.append(f"ChromaDB Tools: {chroma_tool_names}")
        if mcp_warnings:
            response_parts.append(f"MCP Warnings: {'; '.join(mcp_warnings)}")
        if mcp_messages:
            response_parts.append(f"MCP Info: {'; '.join(mcp_messages)}")

        response = "; ".join(response_parts) if response_parts else "No tools found"

        # Enhanced analysis
        analysis_parts = []
        if mcp_tools:
            analysis_parts.append(f"Found {len(mcp_tools)} tools from MCP servers")
        if chroma_tool_names:
            analysis_parts.append(f"Found {len(chroma_tool_names)} tools from ChromaDB")
        if mcp_warnings:
            analysis_parts.append(
                "MCP URLs appear to be documentation pages, not API endpoints"
            )
        if mcp_messages:
            analysis_parts.append("MCP servers provided additional context")

        analysis = (
            "; ".join(analysis_parts)
            if analysis_parts
            else "No results from any source"
        )

        return {
            "response": response,
            "analysis": analysis,
            "mcp_tools": mcp_tools,
            "chroma_tools": chroma_results[:5],
            "mcp_messages": mcp_messages,
            "mcp_warnings": mcp_warnings,
        }

    # Optionally, add more methods for advanced workflows, EXA, Smithery, etc.
