# File: test_client_mcp.py

import requests
import os
from dotenv import load_dotenv

load_dotenv()

MCP_URL = os.getenv("BIO_MCP_URL")  # Updated .env to point to PubMed-MCP
API_KEY = os.getenv("SMITHERY_API_KEY")

def run_mcp_workflow(user_query: str):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {"input": user_query}

    print(f"🔁 Sending request to: {MCP_URL}")
    response = requests.post(MCP_URL, json=payload, headers=headers)

    print("🔎 Status Code:", response.status_code)
    print("🧾 Content-Type:", response.headers.get("Content-Type"))
    print("📦 Response Preview:\n", response.text[:500])

    content_type = response.headers.get("Content-Type", "")
    if "text/html" in content_type:
        print("⚠️ HTML received instead of JSON. Likely a frontend page.")
        return {"error": "Invalid endpoint (HTML instead of JSON)."}

    try:
        return response.json()
    except Exception as e:
        print(f"❌ JSON decode failed: {e}")
        return {"error": "Invalid JSON response from server"}

def test_mcp_workflow():
    query = "Cancer gene interactions"
    result = run_mcp_workflow(query)
    print("✅ Final Result:")
    print(result)

if __name__ == "__main__":
    test_mcp_workflow()
