# MCP - EXA Web Search using Smithery

## Overview

This project demonstrates how to use the Smithery MCP (Model Context Protocol) client to perform web searches through the `web_search_exa` tool. It queries a knowledge base for answers to user-defined questions and processes the structured or semi-structured results.

The example is written in Python using asynchronous programming (async/await) and showcases how to:

- Initialize an MCP client session
- List available tools
- Call a specific tool with input parameters
- Parse and display the tool's response

---

## Features

- Connects to Smithery MCP server using an API key
- Dynamically lists available tools from the server
- Queries the `web_search_exa` tool for web search results
- Parses JSON content returned by the tool
- Handles edge cases such as missing tools or empty results
- Provides test suite to validate behavior under various scenarios

---

## Prerequisites

- Python 3.8+
- An active Smithery API key
- MCP Python client library installed

Install required packages (example):

```bash
pip install mcp asyncio
```

## Configuration

Set your Smithery API key in the script:

```python
smithery_api_key = "YOUR_API_KEY_HERE"
```

## How It Works

- Encode configuration:
Basic debug config is encoded as a base64 JSON string and passed in the request URL.

- Connect to MCP server:
Using the streamablehttp_client for HTTP streaming.

- Initialize session:
Open an MCP ClientSession for RPC communication.

- List tools:
Retrieve all available tools from the server to verify web_search_exa availability.

- Call tool:
Call web_search_exa with query inputs (e.g., "What is protein synthesis?").

- Parse results:
The tool returns JSON content inside TextContent objects, which is parsed and formatted

## Usage

Run the main script:

```bash
python example2.py
```

- Expected output includes:

Available tools on the MCP server

Search query and results with titles, URLs, and snippets

Graceful error messages for missing tools or malformed results

## Testing

The project includes an async test suite with pytest that covers:

- Tool availability (test_tool_not_available)

- Empty result sets (test_empty_results)

- Results with missing fields (test_missing_fields)

Run tests with:

```bash
pytest test_example.py
```

Tests mock MCP client behavior to avoid external dependencies and ensure reliable CI/CD runs.

## Next Steps

Now Piyush can integrate different MCP's tools into this project, and the code is ready to be extended with more tools and features.

## Contributer

Name - Gautam Chugh
Github - https://github.com/Gautam05Chugh