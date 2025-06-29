import httpx
from smithery_client.config import API_BASE_URL, API_KEY

class SmitheryClient:
    def __init__(self, api_key=API_KEY):
        self.base_url = API_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def query_mcp(self, query: str) -> dict:
        print(f"🔍 Sending query to Smithery MCP: {query}")
        try:
            response = httpx.post(
                self.base_url,
                json={"query": query},
                headers=self.headers,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP error: {e.response.status_code} - {e.response.text}")
            return {"error": str(e)}
        except httpx.RequestError as e:
            print(f"❌ Request failed: {e}")
            return {"error": str(e)}

if __name__ == "__main__":
    client = SmitheryClient()
    result = client.query_mcp("example query")
    print("Result:", result)