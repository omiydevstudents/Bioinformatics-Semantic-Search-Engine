# src/agents/tool_discovery_agent.py

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.chroma_store import SemanticSearchStore
from mcp.enhanced_mcp_client import EnhancedMCPClient

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
        self.mcp_client = EnhancedMCPClient()  # Enhanced MCP client with all fixes
        self.chroma_store = SemanticSearchStore()  # Real ChromaDB store
        self.memory = ConversationBufferMemory()

    async def discover_tools(self, query: str) -> dict:
        """
        Discover tools for a given query by combining results from Enhanced MCP and ChromaDB.
        Uses all available sources: Original MCP, Exa Search, Tavily, PubMed E-utilities, Europe PMC.
        Returns a dictionary with a formatted response and analysis.
        """
        # Query ChromaDB first (fastest)
        chroma_results = await self.chroma_store.semantic_search(query)

        # Query all MCP sources concurrently using the enhanced client
        all_mcp_results = await self.mcp_client.query_all_sources(query)

        # Process all MCP results
        mcp_tools = []
        web_tools = []
        papers = []
        mcp_messages = []
        mcp_warnings = []

        for source_name, response in all_mcp_results.items():
            if response.success:
                # Handle different types of results
                tools = response.data.get("tools", [])
                source_papers = response.data.get("papers", [])

                if tools:
                    if source_name in ["exa_search", "tavily_search"]:
                        web_tools.extend(tools[:3])  # Top 3 from each web source
                    else:
                        mcp_tools.extend(tools)

                if source_papers:
                    papers.extend(source_papers[:3])  # Top 3 papers from each source

                # Handle documentation pages and messages
                if response.data.get("status") == "html_page":
                    mcp_warnings.append(
                        f"{source_name}: {response.data.get('note', 'HTML page received')}"
                    )
                    if response.data.get("description"):
                        mcp_messages.append(
                            f"{source_name}: {response.data.get('description')}"
                        )
                else:
                    message = response.data.get("message", "")
                    if message and message != "Empty response from server":
                        mcp_messages.append(f"{source_name}: {message}")

                # Add hit count info for literature sources
                hit_count = response.data.get("hit_count", 0)
                if hit_count > 0:
                    mcp_messages.append(
                        f"{source_name}: {hit_count:,} total hits available"
                    )

            else:
                mcp_messages.append(f"{source_name}: Error - {response.error}")

        # Format comprehensive response
        chroma_tool_names = [
            t["name"] for t in chroma_results[:5]
        ]  # Top 5 ChromaDB results
        web_tool_names = [t["name"] for t in web_tools]
        paper_titles = [p["title"][:50] + "..." for p in papers]

        response_parts = []

        # Add ChromaDB results (local tools)
        if chroma_tool_names:
            response_parts.append(f"ChromaDB Tools: {chroma_tool_names}")

        # Add web search results
        if web_tool_names:
            response_parts.append(f"Web Search Tools: {web_tool_names}")

        # Add scientific papers
        if paper_titles:
            response_parts.append(f"Scientific Papers: {paper_titles}")

        # Add original MCP tools (if any)
        if mcp_tools:
            response_parts.append(f"MCP Tools: {mcp_tools}")

        # Add warnings and info
        if mcp_warnings:
            response_parts.append(
                f"MCP Warnings: {'; '.join(mcp_warnings[:2])}"
            )  # Limit warnings

        response = "; ".join(response_parts) if response_parts else "No tools found"

        # Enhanced analysis with all sources
        analysis_parts = []

        if chroma_tool_names:
            analysis_parts.append(f"Found {len(chroma_tool_names)} tools from ChromaDB")
        if web_tool_names:
            analysis_parts.append(f"Found {len(web_tool_names)} tools from web search")
        if papers:
            analysis_parts.append(f"Found {len(papers)} scientific papers")
        if mcp_tools:
            analysis_parts.append(
                f"Found {len(mcp_tools)} tools from original MCP servers"
            )
        if mcp_warnings:
            analysis_parts.append("Some MCP URLs are documentation pages")

        total_results = (
            len(chroma_tool_names) + len(web_tool_names) + len(papers) + len(mcp_tools)
        )
        analysis_parts.append(
            f"Total results from {len([p for p in response_parts if p])} sources: {total_results}"
        )

        analysis = (
            "; ".join(analysis_parts)
            if analysis_parts
            else "No results from any source"
        )

        return {
            "response": response,
            "analysis": analysis,
            "chroma_tools": chroma_results[:5],
            "web_tools": web_tools,
            "papers": papers,
            "mcp_tools": mcp_tools,
            "mcp_messages": mcp_messages,
            "mcp_warnings": mcp_warnings,
            "total_results": total_results,
        }

    async def close(self):
        """Close the MCP client and clean up resources."""
        await self.mcp_client.close()

    # Optionally, add more methods for advanced workflows, EXA, Smithery, etc.
