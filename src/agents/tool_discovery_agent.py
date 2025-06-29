# src/agents/tool_discovery_agent.py

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.chroma_store import SemanticSearchStore
from mcp.enhanced_mcp_client import EnhancedMCPClient

try:
    from langchain_community.memory import ConversationBufferMemory
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    # Fallback for older versions
    from langchain.memory import ConversationBufferMemory
    from langchain_google_genai import ChatGoogleGenerativeAI

import os
from dotenv import load_dotenv

load_dotenv()

class ToolDiscoveryAgent:
    """
    Agent for discovering bioinformatics tools using real ChromaDB and MCP components.
    Enhanced with Google Gemini for intelligent analysis and ranking.
    """

    def __init__(self):
        self.mcp_client = EnhancedMCPClient()  # Enhanced MCP client with all fixes
        self.chroma_store = SemanticSearchStore()  # Real ChromaDB store
        self.memory = ConversationBufferMemory()
        
        # Initialize Gemini for intelligent analysis
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if google_api_key:
            self.gemini = ChatGoogleGenerativeAI(
                model="gemini-1.5-pro",
                google_api_key=google_api_key,
                temperature=0.3,
                max_tokens=1000
            )
            self.use_gemini = True
        else:
            self.gemini = None
            self.use_gemini = False
            print("⚠️  GOOGLE_API_KEY not found. Running without Gemini AI enhancement.")

    async def discover_tools(self, query: str) -> dict:
        """
        Discover tools for a given query by combining results from Enhanced MCP and ChromaDB.
        Uses all available sources: Original MCP, Exa Search, Tavily, PubMed E-utilities, Europe PMC.
        Enhanced with Gemini AI for intelligent analysis and ranking.
        Returns a dictionary with a formatted response and analysis.
        """
        # Query ChromaDB first (fastest)
        chroma_results = await self.chroma_store.semantic_search(query)

        # Query all MCP sources concurrently using the enhanced client
        all_mcp_results = await self.mcp_client.query_all_sources(query)

        # Process all MCP results
        mcp_tools = []
        web_tools = []
        papers = []
        mcp_messages = []
        mcp_warnings = []

        for source_name, response in all_mcp_results.items():
            if response.success:
                # Handle different types of results
                tools = response.data.get("tools", [])
                source_papers = response.data.get("papers", [])

                if tools:
                    if source_name in ["exa_search", "tavily_search"]:
                        web_tools.extend(tools[:3])  # Top 3 from each web source
                    else:
                        mcp_tools.extend(tools)

                if source_papers:
                    papers.extend(source_papers[:3])  # Top 3 papers from each source

                # Handle documentation pages and messages
                if response.data.get("status") == "html_page":
                    mcp_warnings.append(
                        f"{source_name}: {response.data.get('note', 'HTML page received')}"
                    )
                    if response.data.get("description"):
                        mcp_messages.append(
                            f"{source_name}: {response.data.get('description')}"
                        )
                else:
                    message = response.data.get("message", "")
                    if message and message != "Empty response from server":
                        mcp_messages.append(f"{source_name}: {message}")

                # Add hit count info for literature sources
                hit_count = response.data.get("hit_count", 0)
                if hit_count > 0:
                    mcp_messages.append(
                        f"{source_name}: {hit_count:,} total hits available"
                    )

            else:
                mcp_messages.append(f"{source_name}: Error - {response.error}")

        # Format comprehensive response
        chroma_tool_names = [
            t["name"] for t in chroma_results[:5]
        ]  # Top 5 ChromaDB results
        web_tool_names = [t["name"] for t in web_tools]
        paper_titles = [p["title"][:50] + "..." for p in papers]

        response_parts = []

        # Add ChromaDB results (local tools)
        if chroma_tool_names:
            response_parts.append(f"ChromaDB Tools: {chroma_tool_names}")

        # Add web search results
        if web_tool_names:
            response_parts.append(f"Web Search Tools: {web_tool_names}")

        # Add scientific papers
        if paper_titles:
            response_parts.append(f"Scientific Papers: {paper_titles}")

        # Add original MCP tools (if any)
        if mcp_tools:
            response_parts.append(f"MCP Tools: {mcp_tools}")

        # Add warnings and info
        if mcp_warnings:
            response_parts.append(
                f"MCP Warnings: {'; '.join(mcp_warnings[:2])}"
            )  # Limit warnings

        response = "; ".join(response_parts) if response_parts else "No tools found"

        # Enhanced analysis with Gemini AI if available
        if self.use_gemini and (chroma_results or web_tools or papers or mcp_tools):
            analysis = await self._enhanced_analysis_with_gemini(
                query, chroma_results, web_tools, papers, mcp_tools
            )
        else:
            # Fallback to basic analysis
            analysis = self._basic_analysis(
                chroma_tool_names, web_tool_names, papers, mcp_tools, mcp_warnings
            )

        return {
            "response": response,
            "analysis": analysis,
            "chroma_tools": chroma_results[:5],
            "web_tools": web_tools,
            "papers": papers,
            "mcp_tools": mcp_tools,
            "mcp_messages": mcp_messages,
            "mcp_warnings": mcp_warnings,
            "total_results": len(chroma_tool_names) + len(web_tool_names) + len(papers) + len(mcp_tools),
            "enhanced_with_gemini": self.use_gemini
        }

    async def _enhanced_analysis_with_gemini(self, query: str, chroma_results: list, web_tools: list, papers: list, mcp_tools: list) -> str:
        """
        Use Gemini AI to provide intelligent analysis and recommendations.
        """
        try:
            # Prepare data for Gemini analysis
            analysis_data = {
                "query": query,
                "chroma_tools": [
                    {
                        "name": tool["name"],
                        "category": tool.get("category", "Unknown"),
                        "relevance_score": tool.get("relevance_score", 0),
                        "description": tool.get("content", "")[:200]
                    }
                    for tool in chroma_results[:5]
                ],
                "web_tools": [
                    {
                        "name": tool.get("name", "Unknown"),
                        "url": tool.get("url", ""),
                        "description": tool.get("description", "")[:200]
                    }
                    for tool in web_tools[:5]
                ],
                "papers": [
                    {
                        "title": paper.get("title", "Unknown"),
                        "authors": paper.get("authors", []),
                        "abstract": paper.get("abstract", "")[:300]
                    }
                    for paper in papers[:3]
                ],
                "mcp_tools": mcp_tools[:5]
            }

            # Create prompt for Gemini
            prompt = f"""
You are a bioinformatics expert analyzing tool discovery results. Please provide an intelligent analysis of the following results for the query: "{query}"

Results Summary:
- ChromaDB Tools: {len(analysis_data['chroma_tools'])} local tools
- Web Tools: {len(analysis_data['web_tools'])} web-discovered tools  
- Scientific Papers: {len(analysis_data['papers'])} relevant papers
- MCP Tools: {len(analysis_data['mcp_tools'])} MCP server tools

Please provide:
1. A brief analysis of result quality and relevance
2. Top 3 most relevant tools/papers with brief explanations
3. Any notable gaps or recommendations
4. Overall assessment (excellent/good/fair/poor)

Keep your response concise but insightful (max 300 words).
"""

            # Get Gemini analysis
            gemini_response = await self.gemini.ainvoke(prompt)
            return f"=== ENHANCED AGENT RESPONSE ===\n{gemini_response.content}"

        except Exception as e:
            print(f"⚠️  Gemini analysis failed: {e}")
            return self._basic_analysis(
                [t["name"] for t in chroma_results[:5]],
                [t.get("name", "Unknown") for t in web_tools],
                papers,
                mcp_tools,
                []
            )

    def _basic_analysis(self, chroma_tool_names: list, web_tool_names: list, papers: list, mcp_tools: list, mcp_warnings: list) -> str:
        """
        Fallback basic analysis without Gemini.
        """
        analysis_parts = []

        if chroma_tool_names:
            analysis_parts.append(f"Found {len(chroma_tool_names)} tools from ChromaDB")
        if web_tool_names:
            analysis_parts.append(f"Found {len(web_tool_names)} tools from web search")
        if papers:
            analysis_parts.append(f"Found {len(papers)} scientific papers")
        if mcp_tools:
            analysis_parts.append(
                f"Found {len(mcp_tools)} tools from original MCP servers"
            )
        if mcp_warnings:
            analysis_parts.append("Some MCP URLs are documentation pages")

        total_results = (
            len(chroma_tool_names) + len(web_tool_names) + len(papers) + len(mcp_tools)
        )
        analysis_parts.append(
            f"Total results from {len([p for p in [chroma_tool_names, web_tool_names, papers, mcp_tools] if p])} sources: {total_results}"
        )

        return (
            "; ".join(analysis_parts)
            if analysis_parts
            else "No results from any source"
        )

    async def close(self):
        """Close the MCP client and clean up resources."""
        await self.mcp_client.close()

    async def enhance_query_with_gemini(self, user_query: str) -> str:
        """
        Use Gemini to enhance user queries with bioinformatics context and related terms.
        """
        if not self.use_gemini:
            return user_query

        try:
            prompt = f"""
You are a bioinformatics expert. The user is searching for bioinformatics tools with this query: "{user_query}"

Please enhance this query by:
1. Adding relevant bioinformatics terminology
2. Including related scientific terms
3. Suggesting alternative phrasings
4. Adding specific tool categories if applicable

Return ONLY the enhanced query (max 100 words). Make it more specific and comprehensive for tool discovery.
"""

            response = await self.gemini.ainvoke(prompt)
            enhanced_query = response.content.strip()
            
            # Clean up the response (remove quotes if present)
            if enhanced_query.startswith('"') and enhanced_query.endswith('"'):
                enhanced_query = enhanced_query[1:-1]
            
            print(f"🔍 Original query: {user_query}")
            print(f"🚀 Enhanced query: {enhanced_query}")
            
            return enhanced_query

        except Exception as e:
            print(f"⚠️  Query enhancement failed: {e}")
            return user_query

    async def discover_tools_enhanced(self, query: str) -> dict:
        """
        Enhanced tool discovery with Gemini query enhancement.
        """
        # Enhance query with Gemini if available
        enhanced_query = await self.enhance_query_with_gemini(query)
        
        # Use enhanced query for discovery
        results = await self.discover_tools(enhanced_query)
        
        # Add original query info
        results["original_query"] = query
        results["enhanced_query"] = enhanced_query
        results["query_enhanced"] = enhanced_query != query
        
        return results

    async def generate_workflow_with_gemini(self, task_description: str) -> dict:
        """
        Use Gemini to generate a complete bioinformatics workflow for a given task.
        """
        if not self.use_gemini:
            return {
                "success": False,
                "error": "Gemini AI not available",
                "workflow": None
            }

        try:
            # First, discover relevant tools
            tool_results = await self.discover_tools_enhanced(task_description)
            
            # Prepare tool data for workflow generation
            available_tools = []
            
            # Add ChromaDB tools
            for tool in tool_results.get('chroma_tools', []):
                available_tools.append({
                    "name": tool["name"],
                    "category": tool.get("category", "Unknown"),
                    "description": tool.get("content", "")[:200],
                    "source": "ChromaDB"
                })
            
            # Add web tools
            for tool in tool_results.get('web_tools', []):
                available_tools.append({
                    "name": tool.get("name", "Unknown"),
                    "category": "Web Tool",
                    "description": tool.get("description", "")[:200],
                    "source": "Web Search"
                })

            # Create workflow generation prompt
            prompt = f"""
You are a bioinformatics expert. Generate a complete workflow for this task: "{task_description}"

Available tools from our search:
{chr(10).join([f"- {tool['name']} ({tool['category']}): {tool['description']}" for tool in available_tools[:10]])}

Please create a detailed workflow with:
1. **Input Requirements**: What data/files are needed
2. **Preprocessing Steps**: Data cleaning and preparation
3. **Analysis Pipeline**: Step-by-step analysis using available tools
4. **Quality Control**: Validation and assessment steps
5. **Output Generation**: Results and visualization
6. **Alternative Approaches**: If different tools are available

Format as a structured workflow with clear steps, tool recommendations, and expected outputs.
Keep it practical and actionable (max 500 words).
"""

            # Generate workflow with Gemini
            workflow_response = await self.gemini.ainvoke(prompt)
            
            return {
                "success": True,
                "task": task_description,
                "workflow": workflow_response.content,
                "available_tools": len(available_tools),
                "enhanced_with_gemini": True
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "workflow": None
            }

    async def get_tool_recommendations_with_gemini(self, specific_task: str, constraints: str = "") -> dict:
        """
        Use Gemini to provide intelligent tool recommendations for a specific task.
        """
        if not self.use_gemini:
            return {
                "success": False,
                "error": "Gemini AI not available",
                "recommendations": None
            }

        try:
            # Discover tools for the task
            tool_results = await self.discover_tools_enhanced(specific_task)
            
            # Prepare comprehensive tool list
            all_tools = []
            
            # Add ChromaDB tools with scores
            for tool in tool_results.get('chroma_tools', []):
                all_tools.append({
                    "name": tool["name"],
                    "category": tool.get("category", "Unknown"),
                    "relevance_score": tool.get("relevance_score", 0),
                    "description": tool.get("content", "")[:300],
                    "source": "ChromaDB"
                })
            
            # Add web tools
            for tool in tool_results.get('web_tools', []):
                all_tools.append({
                    "name": tool.get("name", "Unknown"),
                    "category": "Web Tool",
                    "relevance_score": 0.5,  # Default score for web tools
                    "description": tool.get("description", "")[:300],
                    "source": "Web Search"
                })

            # Create recommendation prompt
            prompt = f"""
You are a bioinformatics expert providing tool recommendations for: "{specific_task}"

Constraints: {constraints if constraints else "None specified"}

Available tools:
{chr(10).join([f"- {tool['name']} (Score: {tool['relevance_score']:.2f}, Category: {tool['category']}): {tool['description']}" for tool in all_tools[:15]])}

Please provide:
1. **Top 3 Recommended Tools** with explanations for why they're best for this task
2. **Tool Comparison** highlighting strengths and weaknesses
3. **Usage Recommendations** for each tool
4. **Alternative Options** if the top tools don't meet constraints
5. **Integration Tips** for combining multiple tools

Focus on practical, actionable recommendations (max 400 words).
"""

            # Get recommendations from Gemini
            recommendations_response = await self.gemini.ainvoke(prompt)
            
            return {
                "success": True,
                "task": specific_task,
                "constraints": constraints,
                "recommendations": recommendations_response.content,
                "total_tools_analyzed": len(all_tools),
                "enhanced_with_gemini": True
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "recommendations": None
            }

    # Optionally, add more methods for advanced workflows, EXA, Smithery, etc.
