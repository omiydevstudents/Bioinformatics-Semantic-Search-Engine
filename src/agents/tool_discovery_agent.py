from typing import List, Dict, Optional
import google.generativeai as genai
from langchain.graphs import StateGraph
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.agents import Tool, AgentExecutor
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
import os
from dotenv import load_dotenv

from ..mcp.mcp_client import MCPClient, MCPResponse
from ..search.exa_search import ExaSearchClient, SearchResult
from ..db.chroma_store import ChromaToolStore
from ..smithery.smithery_client import SmitheryClient, SmitheryResponse

load_dotenv()

# Initialize Google Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-pro')

class ToolDiscoveryAgent:
    """Agent for discovering bioinformatics tools using MCP, EXA search, ChromaDB, and Smithery."""
    
    def __init__(self):
        self.mcp_client = MCPClient()
        self.exa_client = ExaSearchClient()
        self.chroma_store = ChromaToolStore()
        self.smithery_client = SmitheryClient()
        self.workflow = self._create_workflow()
        self.memory = ConversationBufferMemory()
        self.tools = self._create_tools()
        self.agent_executor = self._create_agent_executor()

    def _create_tools(self) -> List[Tool]:
        """Create LangChain tools for the agent."""
        return [
            Tool(
                name="mcp_search",
                func=self.mcp_client.query_bio_mcp,
                description="Search for bioinformatics tools using MCP servers"
            ),
            Tool(
                name="exa_search",
                func=self.exa_client.search_tools,
                description="Search for bioinformatics tools using EXA"
            ),
            Tool(
                name="chroma_search",
                func=self.chroma_store.semantic_search,
                description="Search for bioinformatics tools in the local database"
            ),
            Tool(
                name="smithery_search",
                func=self.smithery_client.search_tools,
                description="Search for bioinformatics tools using Smithery"
            ),
            Tool(
                name="smithery_workflow",
                func=self.smithery_client.execute_workflow,
                description="Execute a workflow using Smithery"
            )
        ]

    def _create_agent_executor(self) -> AgentExecutor:
        """Create a LangChain agent executor."""
        prompt = PromptTemplate.from_template(
            """You are a bioinformatics tool discovery assistant. Use the following tools to help users find the right tools for their needs:

            {tools}

            Use the following format:
            Question: the input question you must answer
            Thought: you should always think about what to do
            Action: the action to take, should be one of [{tool_names}]
            Action Input: the input to the action
            Observation: the result of the action
            ... (this Thought/Action/Action Input/Observation can repeat N times)
            Thought: I now know the final answer
            Final Answer: the final answer to the original input question

            Begin!

            Question: {input}
            {agent_scratchpad}"""
        )

        agent = (
            {
                "input": lambda x: x["input"],
                "agent_scratchpad": lambda x: format_to_openai_function_messages(x["intermediate_steps"]),
                "tools": lambda x: x["tools"],
                "tool_names": lambda x: x["tool_names"],
            }
            | prompt
            | model
            | OpenAIFunctionsAgentOutputParser()
        )

        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True
        )

    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow for tool discovery."""
        workflow = StateGraph(name="tool_discovery")

        # Define nodes
        workflow.add_node("process_query", self._process_query)
        workflow.add_node("search_tools", self._search_tools)
        workflow.add_node("analyze_results", self._analyze_results)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("execute_workflow", self._execute_workflow)

        # Define edges
        workflow.add_edge("process_query", "search_tools")
        workflow.add_edge("search_tools", "analyze_results")
        workflow.add_edge("analyze_results", "execute_workflow")
        workflow.add_edge("execute_workflow", "generate_response")

        # Set entry point
        workflow.set_entry_point("process_query")

        return workflow

    async def _process_query(self, state: Dict) -> Dict:
        """Process and enhance the user query."""
        query = state["query"]
        
        # Use LangChain agent to process query
        result = await self.agent_executor.ainvoke({"input": query})
        enhanced_query = result["output"]
        
        return {
            **state,
            "enhanced_query": enhanced_query
        }

    async def _search_tools(self, state: Dict) -> Dict:
        """Search for tools using MCP, EXA, ChromaDB, and Smithery."""
        query = state["enhanced_query"]
        
        # Query MCP servers
        bio_mcp_response = await self.mcp_client.query_bio_mcp(query)
        pubmed_mcp_response = await self.mcp_client.query_pubmed_mcp(query)
        bio_context_response = await self.mcp_client.query_bio_context(query)
        
        # Search with EXA
        exa_results = await self.exa_client.search_tools(query)
        
        # Search in ChromaDB
        chroma_results = await self.chroma_store.semantic_search(query)
        
        # Search with Smithery
        smithery_results = await self.smithery_client.search_tools(query)
        
        return {
            **state,
            "mcp_results": {
                "bio_mcp": bio_mcp_response,
                "pubmed_mcp": pubmed_mcp_response,
                "bio_context": bio_context_response
            },
            "exa_results": exa_results,
            "chroma_results": chroma_results,
            "smithery_results": smithery_results
        }

    async def _analyze_results(self, state: Dict) -> Dict:
        """Analyze and rank the search results."""
        mcp_results = state["mcp_results"]
        exa_results = state["exa_results"]
        chroma_results = state["chroma_results"]
        smithery_results = state["smithery_results"]
        
        # Use LangChain agent to analyze results
        result = await self.agent_executor.ainvoke({
            "input": f"Analyze these tool discovery results and rank them by relevance: MCP: {mcp_results}, EXA: {exa_results}, ChromaDB: {chroma_results}, Smithery: {smithery_results}"
        })
        
        return {
            **state,
            "analysis": result["output"]
        }

    async def _execute_workflow(self, state: Dict) -> Dict:
        """Execute a workflow using Smithery."""
        analysis = state["analysis"]
        
        # Get workflow templates
        templates = await self.smithery_client.get_workflow_templates()
        
        if templates.success:
            # Execute the most relevant workflow
            workflow_id = templates.data["templates"][0]["id"]  # Simplified selection
            workflow_result = await self.smithery_client.execute_workflow(
                workflow_id,
                {"analysis": analysis}
            )
            
            return {
                **state,
                "workflow_result": workflow_result
            }
        
        return state

    async def _generate_response(self, state: Dict) -> Dict:
        """Generate a natural language response."""
        query = state["query"]
        analysis = state["analysis"]
        workflow_result = state.get("workflow_result")
        
        # Use LangChain agent to generate response
        result = await self.agent_executor.ainvoke({
            "input": f"Generate a response for the user query: {query}. Analysis: {analysis}. Workflow result: {workflow_result}"
        })
        
        # Store the interaction in memory
        self.memory.save_context(
            {"input": query},
            {"output": result["output"]}
        )
        
        return {
            **state,
            "response": result["output"]
        }

    async def discover_tools(self, query: str) -> Dict:
        """Main method to discover tools for a given query."""
        try:
            # Initialize state
            state = {"query": query}
            
            # Run the workflow
            final_state = await self.workflow.arun(state)
            
            return {
                "success": True,
                "response": final_state["response"],
                "analysis": final_state["analysis"]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            await self.mcp_client.close()
            await self.smithery_client.close()

    async def add_tool(self, tool_data: Dict) -> bool:
        """Add a new tool to the ChromaDB store."""
        return await self.chroma_store.add_tool(tool_data)

    async def get_tool(self, name: str) -> Optional[Dict]:
        """Retrieve a specific tool from the ChromaDB store."""
        return await self.chroma_store.get_tool_by_name(name) 