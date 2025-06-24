class MockMCPClient:
    async def query_bio_mcp(self, query):
        return {"success": True, "data": {"tools": ["Mock MCP Tool"]}}

    async def query_pubmed_mcp(self, query):
        return {"success": True, "data": {"tools": ["Mock PubMed Tool"]}}

    async def query_bio_context(self, query):
        return {"success": True, "data": {"tools": ["Mock BioContext Tool"]}}

    async def query_code_executor(self, payload):
        return {"success": True, "data": {"result": "Mock Code Executor Result"}}

    async def close(self):
        pass


class MockExaSearchClient:
    async def search_tools(self, query, num_results=5):
        return [{"title": "Mock EXA Tool", "score": 0.9}]


class MockChromaToolStore:
    async def semantic_search(self, query, n_results=5):
        return [{"name": "Mock Chroma Tool", "relevance_score": 0.8}]

    async def add_tool(self, tool_data):
        return True

    async def get_tool_by_name(self, name):
        return {"name": name, "content": "Mock content"}


class MockSmitheryClient:
    async def search_tools(self, query):
        return {"success": True, "data": {"tools": ["Mock Smithery Tool"]}}

    async def execute_workflow(self, workflow_id, inputs):
        return {"success": True, "data": {"result": "Mock Workflow Result"}}

    async def get_workflow_templates(self):
        return {"success": True, "data": {"templates": [{"id": "mock_workflow"}]}}

    async def close(self):
        pass
