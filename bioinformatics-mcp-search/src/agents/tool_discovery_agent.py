from typing import List, Dict, Optional
import google.generativeai as genai
from langchain.graphs import StateGraph
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
import os
from dotenv import load_dotenv

from ..mcp.mcp_client import MCPClient, MCPResponse
from ..search.exa_search import ExaSearchClient, SearchResult
from ..db.chroma_store import ChromaToolStore

load_dotenv()

# Initialize Google Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-pro')

class ToolDiscoveryAgent:
    """Agent for discovering bioinformatics tools using MCP, EXA search, and ChromaDB."""
    
    def __init__(self):
        self.mcp_client = MCPClient()
        self.exa_client = ExaSearchClient()
        self.chroma_store = ChromaToolStore()
        self.workflow = self._create_workflow()
        self.memory = ConversationBufferMemory()

    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow for tool discovery."""
        workflow = StateGraph(name="tool_discovery")

        # Define nodes
        workflow.add_node("process_query", self._process_query)
        workflow.add_node("search_tools", self._search_tools)
        workflow.add_node("analyze_results", self._analyze_results)
        workflow.add_node("generate_response", self._generate_response)

        # Define edges
        workflow.add_edge("process_query", "search_tools")
        workflow.add_edge("search_tools", "analyze_results")
        workflow.add_edge("analyze_results", "generate_response")

        # Set entry point
        workflow.set_entry_point("process_query")

        return workflow

    async def _process_query(self, state: Dict) -> Dict:
        """Process and enhance the user query."""
        query = state["query"]
        
        # Create a prompt template for query enhancement
        prompt_template = PromptTemplate(
            input_variables=["query"],
            template="""
            Given the following bioinformatics query, enhance it to better capture the user's intent:
            Query: {query}
            
            Provide an enhanced query that includes:
            1. Specific techniques or methods mentioned
            2. Type of analysis needed
            3. Any specific requirements or constraints
            """
        )
        
        # Use Gemini to enhance the query
        response = model.generate_content(prompt_template.format(query=query))
        enhanced_query = response.text.strip()
        
        return {
            **state,
            "enhanced_query": enhanced_query
        }

    async def _search_tools(self, state: Dict) -> Dict:
        """Search for tools using MCP, EXA, and ChromaDB."""
        query = state["enhanced_query"]
        
        # Query MCP servers
        bio_mcp_response = await self.mcp_client.query_bio_mcp(query)
        pubmed_mcp_response = await self.mcp_client.query_pubmed_mcp(query)
        bio_context_response = await self.mcp_client.query_bio_context(query)
        
        # Search with EXA
        exa_results = await self.exa_client.search_tools(query)
        
        # Search in ChromaDB
        chroma_results = await self.chroma_store.search_tools(query)
        
        return {
            **state,
            "mcp_results": {
                "bio_mcp": bio_mcp_response,
                "pubmed_mcp": pubmed_mcp_response,
                "bio_context": bio_context_response
            },
            "exa_results": exa_results,
            "chroma_results": chroma_results
        }

    async def _analyze_results(self, state: Dict) -> Dict:
        """Analyze and rank the search results."""
        mcp_results = state["mcp_results"]
        exa_results = state["exa_results"]
        chroma_results = state["chroma_results"]
        
        # Create a prompt template for result analysis
        prompt_template = PromptTemplate(
            input_variables=["mcp_results", "exa_results", "chroma_results"],
            template="""
            Analyze the following tool discovery results and rank them by relevance:
            
            MCP Results:
            {mcp_results}
            
            EXA Search Results:
            {exa_results}
            
            ChromaDB Results:
            {chroma_results}
            
            Provide a ranked list of tools with:
            1. Tool name
            2. Brief description
            3. Relevance score
            4. Key features
            5. Source (MCP/EXA/ChromaDB)
            """
        )
        
        # Use Gemini to analyze results
        response = model.generate_content(
            prompt_template.format(
                mcp_results=mcp_results,
                exa_results=exa_results,
                chroma_results=chroma_results
            )
        )
        analysis = response.text.strip()
        
        return {
            **state,
            "analysis": analysis
        }

    async def _generate_response(self, state: Dict) -> Dict:
        """Generate a natural language response."""
        query = state["query"]
        analysis = state["analysis"]
        
        # Create a prompt template for response generation
        prompt_template = PromptTemplate(
            input_variables=["query", "analysis"],
            template="""
            Given the user's query and the tool analysis, generate a helpful response:
            
            User Query: {query}
            
            Tool Analysis:
            {analysis}
            
            Provide a response that:
            1. Directly addresses the user's needs
            2. Recommends the most relevant tools
            3. Explains why each tool is recommended
            4. Includes any important considerations or limitations
            5. Suggests potential next steps or related tools
            """
        )
        
        # Use Gemini to generate response
        response = model.generate_content(
            prompt_template.format(
                query=query,
                analysis=analysis
            )
        )
        final_response = response.text.strip()
        
        # Store the interaction in memory
        self.memory.save_context(
            {"input": query},
            {"output": final_response}
        )
        
        return {
            **state,
            "response": final_response
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

    async def add_tool(self, tool_data: Dict) -> bool:
        """Add a new tool to the ChromaDB store."""
        return await self.chroma_store.add_tool(tool_data)

    async def get_tool(self, name: str) -> Optional[Dict]:
        """Retrieve a specific tool from the ChromaDB store."""
        return await self.chroma_store.get_tool_by_name(name) 