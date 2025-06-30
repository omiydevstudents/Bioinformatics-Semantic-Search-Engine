import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import json

# Fake TextContent-like object
class MockTextContent:
    def __init__(self, text):
        self.text = text

@pytest.mark.asyncio
async def test_tool_not_available():
    with patch("mcp.ClientSession") as MockClientSession, \
         patch("mcp.client.streamable_http.streamablehttp_client") as MockStreamClient:

        mock_stream_context = AsyncMock()
        mock_stream_context.__aenter__.return_value = (AsyncMock(), AsyncMock(), None)
        MockStreamClient.return_value = mock_stream_context

        mock_session = AsyncMock()
        mock_session.initialize.return_value = None
        # Return tools list WITHOUT the desired tool
        mock_session.list_tools.return_value = MagicMock(tools=[MagicMock(name="some_other_tool")])
        MockClientSession.return_value.__aenter__.return_value = mock_session

        from exa_sample import main

        # Run main() and check output manually, or you can capture stdout if needed
        await main()


@pytest.mark.asyncio
async def test_empty_results():
    with patch("mcp.ClientSession") as MockClientSession, \
         patch("mcp.client.streamable_http.streamablehttp_client") as MockStreamClient:

        mock_stream_context = AsyncMock()
        mock_stream_context.__aenter__.return_value = (AsyncMock(), AsyncMock(), None)
        MockStreamClient.return_value = mock_stream_context

        mock_session = AsyncMock()
        mock_session.initialize.return_value = None
        mock_session.list_tools.return_value = MagicMock(tools=[MagicMock(name="web_search_exa")])

        # Return content with empty results array
        empty_results_json = json.dumps({"results": []})
        mock_session.call_tool.return_value = MagicMock(
            content=[MockTextContent(text=empty_results_json)]
        )

        MockClientSession.return_value.__aenter__.return_value = mock_session

        from exa_sample import main

        await main()


@pytest.mark.asyncio
async def test_missing_fields():
    with patch("mcp.ClientSession") as MockClientSession, \
         patch("mcp.client.streamable_http.streamablehttp_client") as MockStreamClient:

        mock_stream_context = AsyncMock()
        mock_stream_context.__aenter__.return_value = (AsyncMock(), AsyncMock(), None)
        MockStreamClient.return_value = mock_stream_context

        mock_session = AsyncMock()
        mock_session.initialize.return_value = None
        mock_session.list_tools.return_value = MagicMock(tools=[MagicMock(name="web_search_exa")])

        # JSON with some entries missing title, url or text fields
        incomplete_json = json.dumps({
            "results": [
                {"title": "Title Only"},
                {"url": "https://example.com"},
                {"text": "Just some snippet text"},
                {}  # completely empty
            ]
        })

        mock_session.call_tool.return_value = MagicMock(
            content=[MockTextContent(text=incomplete_json)]
        )

        MockClientSession.return_value.__aenter__.return_value = mock_session

        from exa_search import main

        await main()
