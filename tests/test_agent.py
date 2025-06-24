# src/test_agent.py

import asyncio
from src.agents.tool_discovery_agent import ToolDiscoveryAgent


async def main():
    agent = ToolDiscoveryAgent()
    # query = "Find context-aware tools"
    query = "Suggest software for protein structure prediction"
    print(f"🔍 Querying for: {query}")
    result = await agent.discover_tools(query)
    print("\n=== AGENT RESPONSE ===")
    print("Response:", result["response"])
    print("Analysis:", result["analysis"])


if __name__ == "__main__":
    asyncio.run(main())
