# File: mcp_agent.py

import os
import requests
from langchain.agents import Tool, initialize_agent
from langchain_community.chat_models import ChatOpenAI

# ✅ Your OpenAI API key (required)
os.environ["OPENAI_API_KEY"] = "your-openai-key-here"  # 🔁 replace this

# ✅ Your real MCP tool endpoint (replace with actual if running locally or remotely)
MCP_ENDPOINT = "http://localhost:3000/mcp/longevity-genie"

# ✅ Function that calls the MCP tool (real HTTP call)
def query_mcp(input_str: str) -> str:
    try:
        response = requests.post(
            MCP_ENDPOINT,
            json={"input": input_str},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json().get("output", "No output key found in MCP response.")
    except Exception as e:
        return f"❌ MCP call failed: {str(e)}"

# ✅ Define tool for LangChain agent
mcp_tool = Tool.from_function(
    func=query_mcp,
    name="longevity-genie",
    description="Use this tool to get gene associations with longevity. Input should be a natural language question."
)

# ✅ Initialize LLM and agent
llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
agent = initialize_agent(
    tools=[mcp_tool],
    llm=llm,
    agent_type="zero-shot-react-description",
    verbose=True
)

# ✅ CLI Execution
def ask_mcp(query: str):
    return agent.run(query)

if __name__ == "__main__":
    question = "What genes are associated with longevity?"
    print("🔍 Asking MCP:", question)
    result = ask_mcp(question)
    print("🧠 Result:\n", result)
