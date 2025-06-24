import sys
import asyncio
from mcp.mcp_client import MCPClient


def print_usage():
    print("Usage: python src/cli.py <your query>")
    print("Or for code execution: python src/cli.py exec: <python code>")


async def main():
    if len(sys.argv) < 2:
        print_usage()
        return
    query = " ".join(sys.argv[1:])
    mcp = MCPClient()
    if query.startswith("exec:"):
        code = query[len("exec:") :].strip()
        payload = {"code": code}
        response = await mcp.query_code_executor(payload)
        print("\n[Code Executor Result]")
        print(response)
    else:
        print(f"\n[Bio MCP Result for: {query}]")
        print(await mcp.query_bio_mcp(query))
        print(f"\n[PubMed MCP Result for: {query}]")
        print(await mcp.query_pubmed_mcp(query))
        print(f"\n[BioContext MCP Result for: {query}]")
        print(await mcp.query_bio_context(query))
    await mcp.close()


if __name__ == "__main__":
    asyncio.run(main())
