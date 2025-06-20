# src/test_agent.py

import asyncio
from mocks import MockMCPClient, MockExaSearchClient, MockChromaToolStore, MockSmitheryClient
from agents.tool_discovery_agent import ToolDiscoveryAgent

async def main():
    agent = ToolDiscoveryAgent(
        mcp_client=MockMCPClient(),
        exa_client=MockExaSearchClient(),
        chroma_store=MockChromaToolStore(),
        smithery_client=MockSmitheryClient()
    )
    result = await agent.discover_tools("Find tools for RNA-seq analysis")
    print("Response:", result["response"])
    print("Analysis:", result["analysis"])

if __name__ == "__main__":
    asyncio.run(main())