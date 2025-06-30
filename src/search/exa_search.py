import mcp
from mcp.client.streamable_http import streamablehttp_client
import json
import base64
import asyncio

config = {
    "debug": False
}
smithery_api_key = "62f78669-16cd-48b3-98ea-d35c377be2b2"  # Replace with your real API key
config_b64 = base64.b64encode(json.dumps(config).encode()).decode()
url = f"https://server.smithery.ai/exa/mcp?config={config_b64}&api_key={smithery_api_key}"

async def main():
    async with streamablehttp_client(url) as (read_stream, write_stream, _):
        async with mcp.ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            tools_result = await session.list_tools()
            tool_names = [t.name for t in tools_result.tools]
            print("✅ Available tools:", tool_names)

            tool_name = "web_search_exa"
            if tool_name not in tool_names:
                print(f"❌ Tool {tool_name} not available.")
                return

            inputs = {
                "query": "What is protein synthesis?",
                "num_results": 3
            }

            print(f"🔍 Calling `{tool_name}` with inputs: {inputs}")
            result = await session.call_tool(tool_name, inputs)
            print("✅ Tool response received.")

            # ✅ Try parsing content from TextContent.text
            if result.content and isinstance(result.content, list):
                for i, item in enumerate(result.content, 1):
                    if hasattr(item, 'text'):
                        try:
                            parsed = json.loads(item.text)
                            for j, res in enumerate(parsed.get("results", []), 1):
                                print(f"\n🔹 Result {j}")
                                print("Title  :", res.get("title", "N/A"))
                                print("URL    :", res.get("url", res.get("id", "N/A")))
                                print("Snippet:", res.get("text", "N/A"))
                        except Exception as e:
                            print(f"⚠️ Error parsing item {i}: {e}")
                    else:
                        print(f"⚠️ Unexpected item format in result.content[{i}]")
            else:
                print("⚠️ No content or unexpected format in result.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print("❌ Unhandled exception:")
        import traceback
        traceback.print_exc()
