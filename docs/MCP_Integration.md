# MCP Integration Guide

## Overview
The MCP (Modular Computational Platform) client enables querying multiple bioinformatics tool discovery and analysis servers (BioMCP, PubMed MCP, BioContext, and Code Executor) from within the project. It is designed to help the agent suggest the right tool for a user's analysis goal.

## Environment Variables
Set these in your `.env` file:

- `BIO_MCP_URL`: e.g., https://mcp.so/server/bio-mcp/longevity-genie
- `PUBMED_MCP_URL`: e.g., https://mcp.so/server/PubMed-MCP/BioContext
- `BIO_CONTEXT_URL`: e.g., https://mcp.so/server/BioContext/EazyAl
- `MCP_CODE_EXECUTOR_URL`: e.g., http://localhost:8000 (dummy or local server)

## Using the MCP Client

```
from mcp.mcp_client import MCPClient
import asyncio

async def main():
    mcp = MCPClient()
    response = await mcp.query_bio_mcp("Find tools for RNA-seq analysis")
    print(response)
    # For code executor:
    payload = {"code": "print('Hello, world!')"}
    exec_response = await mcp.query_code_executor(payload)
    print(exec_response)
    await mcp.close()

asyncio.run(main())
```

## Adding New MCP Endpoints
- Add a new environment variable for the endpoint URL.
- Add a new async method to `MCPClient` following the pattern of existing methods.
- Update mocks and tests as needed.

## Integration Notes (for colleagues)
- Ensure all required environment variables are set.
- Use the provided async methods for querying each MCP.
- The code executor does not append `/query` to its URL; all others do.
- See `src/mocks.py` for mock client examples.
- See `src/test_agent.py` for usage/testing patterns. 