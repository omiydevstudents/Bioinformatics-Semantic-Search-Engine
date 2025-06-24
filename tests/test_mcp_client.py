import pytest
import asyncio
import sys

sys.path.insert(0, "./src")
from mocks import MockMCPClient


@pytest.mark.asyncio
async def test_query_code_executor():
    client = MockMCPClient()
    payload = {"code": "print('Hello, world!')"}
    response = await client.query_code_executor(payload)
    assert response["success"] is True
    assert response["data"]["result"] == "Mock Code Executor Result"


@pytest.mark.asyncio
async def test_query_bio_mcp():
    client = MockMCPClient()
    response = await client.query_bio_mcp("Find tools for RNA-seq analysis")
    assert response["success"] is True
    assert response["data"]["tools"] == ["Mock MCP Tool"]


@pytest.mark.asyncio
async def test_query_pubmed_mcp():
    client = MockMCPClient()
    response = await client.query_pubmed_mcp("Find tools for literature mining")
    assert response["success"] is True
    assert response["data"]["tools"] == ["Mock PubMed Tool"]


@pytest.mark.asyncio
async def test_query_bio_context():
    client = MockMCPClient()
    response = await client.query_bio_context("Find context-aware tools")
    assert response["success"] is True
    assert response["data"]["tools"] == ["Mock BioContext Tool"]
