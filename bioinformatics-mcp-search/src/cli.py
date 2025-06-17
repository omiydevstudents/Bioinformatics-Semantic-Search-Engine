import asyncio
import argparse
from agents.tool_discovery_agent import ToolDiscoveryAgent

async def main():
    parser = argparse.ArgumentParser(description="Bioinformatics Tool Discovery CLI")
    parser.add_argument("query", help="Your bioinformatics query")
    args = parser.parse_args()

    print(f"\n🔍 Processing query: {args.query}\n")
    
    agent = ToolDiscoveryAgent()
    result = await agent.discover_tools(args.query)
    
    if result["success"]:
        print("\n📊 Analysis:")
        print(result["analysis"])
        print("\n💡 Recommendation:")
        print(result["response"])
    else:
        print(f"\n❌ Error: {result['error']}")

if __name__ == "__main__":
    asyncio.run(main()) 