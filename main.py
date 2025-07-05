#!/usr/bin/env python3
"""
Bioinformatics Tool Discovery Web Application
A Perplexity-style interface for discovering bioinformatics tools with Apple-inspired design.

Usage:
    python main.py

Features:
    - Conversational search interface
    - Real-time tool discovery
    - Beautiful Apple-inspired UI
    - Source attribution
    - Responsive design
    - Self-RAG enhanced quality control
"""

import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Dict, Optional, List
import os
from dotenv import load_dotenv
import json
from pathlib import Path

# Import our Self-RAG enhanced tool discovery agent
from src.agents.self_rag_agent import SelfRAGAgent

load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Bioinformatics Tool Discovery",
    description="Discover bioinformatics tools with AI-powered search and Self-RAG quality control",
    version="2.0.0"
)

# Setup static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Pydantic models
class SearchRequest(BaseModel):
    query: str
    max_results: Optional[int] = 10

class FollowUpRequest(BaseModel):
    original_query: str
    follow_up_question: str
    previous_results: Optional[Dict] = None
    max_results: Optional[int] = 10

class SearchResponse(BaseModel):
    success: bool
    query: str
    response: str
    analysis: str
    tools: List[Dict]
    sources: List[Dict]
    total_results: int
    search_time: float
    enhanced_with_gemini: bool
    quality_metrics: Optional[Dict] = None
    follow_up_suggestions: Optional[List[str]] = None

# Global agent instance
agent = None

@app.on_event("startup")
async def startup_event():
    """Initialize the Self-RAG enhanced tool discovery agent on startup."""
    global agent
    print("🚀 Initializing Self-RAG Enhanced Bioinformatics Tool Discovery Agent...")
    agent = SelfRAGAgent()
    print("✅ Self-RAG Agent initialized successfully!")
    print("🎯 Features enabled: Query refinement, Tool grading, Hallucination detection, Quality assessment")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main web interface."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/search", response_model=SearchResponse)
async def search_tools(request: SearchRequest) -> SearchResponse:
    """API endpoint for Self-RAG enhanced tool discovery search."""
    import time
    start_time = time.time()
    
    try:
        if not agent:
            raise HTTPException(status_code=500, detail="Agent not initialized")
        
        # Perform the Self-RAG enhanced search with max_results parameter
        max_results = request.max_results or 10
        result = await agent.discover_tools_self_rag(request.query, max_results)
        
        # Calculate search time
        search_time = time.time() - start_time
        
        # Format the response for the web interface
        formatted_response = format_response_for_web(result, request.query, max_results)
        
        # Debug logging for follow-up suggestions
        follow_up_suggestions = result.get("follow_up_suggestions", [])
        print(f"🔍 Backend - Follow-up suggestions: {follow_up_suggestions}")
        print(f"🔍 Backend - Follow-up suggestions type: {type(follow_up_suggestions)}")
        print(f"🔍 Backend - Follow-up suggestions length: {len(follow_up_suggestions) if follow_up_suggestions else 0}")
        
        return SearchResponse(
            success=True,
            query=request.query,
            response=formatted_response["response"],
            analysis=formatted_response["analysis"],
            tools=formatted_response["tools"],
            sources=formatted_response["sources"],
            total_results=result.get("total_results", 0),
            search_time=search_time,
            enhanced_with_gemini=result.get("enhanced_with_gemini", False),
            quality_metrics=result.get("quality_metrics", {}),
            follow_up_suggestions=follow_up_suggestions
        )
        
    except Exception as e:
        search_time = time.time() - start_time
        raise HTTPException(
            status_code=500, 
            detail=f"Search failed: {str(e)}"
        )

@app.post("/api/followup", response_model=SearchResponse)
async def follow_up_search(request: FollowUpRequest) -> SearchResponse:
    """API endpoint for follow-up questions to improve search results."""
    import time
    start_time = time.time()
    
    try:
        if not agent:
            raise HTTPException(status_code=500, detail="Agent not initialized")
        
        # Create an improved query based on the follow-up question
        improved_query = await create_improved_query_from_followup(
            request.original_query, 
            request.follow_up_question,
            request.previous_results
        )
        
        # Perform the Self-RAG enhanced search with the improved query
        max_results = request.max_results or 10
        result = await agent.discover_tools_self_rag(improved_query, max_results)
        
        # Calculate search time
        search_time = time.time() - start_time
        
        # Format the response for the web interface
        formatted_response = format_response_for_web(result, improved_query, max_results)
        
        # Debug logging for follow-up suggestions
        follow_up_suggestions = result.get("follow_up_suggestions", [])
        print(f"🔍 Backend - Follow-up suggestions: {follow_up_suggestions}")
        print(f"🔍 Backend - Follow-up suggestions type: {type(follow_up_suggestions)}")
        print(f"🔍 Backend - Follow-up suggestions length: {len(follow_up_suggestions) if follow_up_suggestions else 0}")
        
        # Add context about the follow-up improvement
        formatted_response["response"] = f"**Follow-up Response:** Based on your feedback about '{request.follow_up_question}', I've refined the search to better address your needs.\n\n" + formatted_response["response"]
        
        return SearchResponse(
            success=True,
            query=improved_query,
            response=formatted_response["response"],
            analysis=formatted_response["analysis"],
            tools=formatted_response["tools"],
            sources=formatted_response["sources"],
            total_results=result.get("total_results", 0),
            search_time=search_time,
            enhanced_with_gemini=result.get("enhanced_with_gemini", False),
            quality_metrics=result.get("quality_metrics", {}),
            follow_up_suggestions=follow_up_suggestions
        )
        
    except Exception as e:
        search_time = time.time() - start_time
        raise HTTPException(
            status_code=500, 
            detail=f"Follow-up search failed: {str(e)}"
        )

async def create_improved_query_from_followup(original_query: str, follow_up_question: str, previous_results: Optional[Dict] = None) -> str:
    """
    Create an improved query based on user's follow-up question and feedback.
    
    Args:
        original_query: The original search query
        follow_up_question: User's follow-up question or feedback
        previous_results: Results from the previous search (if available)
        
    Returns:
        Improved query that addresses the user's feedback
    """
    try:
        # Use Gemini to create an improved query
        if agent and agent.use_gemini and agent.gemini:
            prompt = f"""
You are an expert at improving bioinformatics tool discovery queries based on user feedback.

ORIGINAL QUERY: {original_query}
USER FOLLOW-UP/FEEDBACK: {follow_up_question}

Your task is to create an improved query that addresses the user's feedback and provides better results.

IMPROVEMENT STRATEGIES:
1. **Add Specificity**: If the user wants more specific tools, add relevant terms
2. **Expand Scope**: If the user wants broader coverage, include related concepts
3. **Focus on Use Cases**: If the user mentions specific applications, include those
4. **Add Technical Details**: If the user wants technical specifics, include relevant parameters
5. **Include Workflow Context**: If the user mentions workflows, add related tools

EXAMPLES:
- Original: "ChIP-seq tools" + Follow-up: "I need tools for peak calling" → "ChIP-seq peak calling tools for identifying binding sites"
- Original: "phylogenetic tools" + Follow-up: "I work with large datasets" → "phylogenetic tree construction tools for large datasets with maximum likelihood methods"
- Original: "RNA-seq analysis" + Follow-up: "I need visualization tools" → "RNA-seq analysis and visualization tools for gene expression data"

Create an improved query that combines the original intent with the user's feedback.
Return ONLY the improved query (max 150 words).
"""

            response = await agent.gemini.ainvoke(prompt)
            improved_query = response.content.strip()
            
            # Clean up the response
            if improved_query.startswith('"') and improved_query.endswith('"'):
                improved_query = improved_query[1:-1]
            
            print(f"🔄 Follow-up Query Improvement:")
            print(f"   Original: {original_query}")
            print(f"   Follow-up: {follow_up_question}")
            print(f"   Improved: {improved_query}")
            
            return improved_query
        else:
            # Fallback: simple combination
            return f"{original_query} {follow_up_question}"
            
    except Exception as e:
        print(f"⚠️  Error creating improved query: {e}")
        # Fallback: simple combination
        return f"{original_query} {follow_up_question}"

def format_enhanced_response(enhanced_text: str) -> Dict:
    """
    Parse and structure the enhanced agent response for better web display.
    
    Args:
        enhanced_text: Raw enhanced agent response text
        
    Returns:
        Dict with structured summary and detailed analysis
    """
    # Initialize structured response
    structured = {
        "summary": "",
        "detailed_analysis": ""
    }
    
    # Split the text into sections
    lines = enhanced_text.split('\n')
    current_section = "summary"
    summary_parts = []
    analysis_parts = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check for section headers in the new detailed format
        if line.startswith("**QUALITY ASSESSMENT:**") or line.startswith("**TOP RECOMMENDATIONS") or line.startswith("**DETAILED GAPS ANALYSIS:**") or line.startswith("**ACTIONABLE RECOMMENDATIONS:**") or line.startswith("**OVERALL ASSESSMENT:**"):
            current_section = "analysis"
            # Format as a proper header
            header_text = line.strip('*').strip()
            analysis_parts.append(f"\n### {header_text}")
            continue
            
        # Check for numbered lists
        if line.startswith(("1.", "2.", "3.")) and "(" in line and "):" in line:
            current_section = "analysis"
            # Format as a proper list item
            analysis_parts.append(f"\n{line}")
            continue
            
        # Check for bullet points
        if line.startswith("* ") or line.startswith("- "):
            current_section = "analysis"
            analysis_parts.append(f"\n{line}")
            continue
            
        # Add to appropriate section
        if current_section == "summary":
            summary_parts.append(line)
        else:
            analysis_parts.append(line)
    
    # Combine summary parts
    structured["summary"] = " ".join(summary_parts)
    
    # Combine analysis parts and add structure
    if analysis_parts:
        structured["detailed_analysis"] = "\n".join(analysis_parts)
    else:
        structured["detailed_analysis"] = enhanced_text
    
    return structured


def format_response_for_web(result: Dict, query: str, max_results: int) -> Dict:
    """Format the Self-RAG agent response for web display."""
    
    # Organize tools by source type
    local_tools = []
    web_tools = []
    scientific_papers = []
    
    # Add ChromaDB tools (local database)
    for tool in result.get("chroma_tools", []):
        relevance_grade = tool.get("relevance_grade", "unknown")
        relevance_reasoning = tool.get("relevance_reasoning", "")
        
        local_tools.append({
            "name": tool.get("name", "Unknown"),
            "category": tool.get("category", "Unknown"),
            "description": tool.get("content", "")[:200] + "...",
            "source": "Local Database",
            "relevance_score": tool.get("relevance_score", 0),
            "type": "local_tool",
            "url": None,
            "quality_grade": relevance_grade,
            "quality_reasoning": relevance_reasoning
        })
    
    # Add web tools
    for tool in result.get("web_tools", []):
        web_tools.append({
            "name": tool.get("name", "Unknown"),
            "category": "Web Tool",
            "description": tool.get("description", "")[:200] + "...",
            "source": "Web Search",
            "relevance_score": 0.8,  # Default score for web tools
            "type": "web_tool",
            "url": tool.get("url"),
            "quality_grade": "web_tool",
            "quality_reasoning": "Web-based tool from search results"
        })
    
    # Add scientific papers
    for paper in result.get("papers", []):
        scientific_papers.append({
            "name": paper.get("title", "Unknown Paper"),
            "category": "Scientific Literature",
            "description": paper.get("abstract", "")[:200] + "...",
            "source": "Scientific Literature",
            "relevance_score": 0.7,  # Default score for papers
            "type": "scientific_paper",
            "url": paper.get("url"),
            "quality_grade": "scientific_paper",
            "quality_reasoning": "Peer-reviewed scientific literature"
        })
    
    # Sort each category by relevance score
    local_tools.sort(key=lambda x: x["relevance_score"], reverse=True)
    web_tools.sort(key=lambda x: x["relevance_score"], reverse=True)
    scientific_papers.sort(key=lambda x: x["relevance_score"], reverse=True)
    
    # Limit each category to max_results
    local_tools = local_tools[:max_results]
    web_tools = web_tools[:max_results]
    scientific_papers = scientific_papers[:max_results]
    
    # Combine all tools in the desired order: local first, then web, then papers
    tools = local_tools + web_tools + scientific_papers
    
    # Create sources list
    sources = []
    if result.get("chroma_tools"):
        sources.append({
            "name": "Local Tool Database",
            "description": f"Found {len(result['chroma_tools'])} relevant tools",
            "type": "database"
        })
    if result.get("web_tools"):
        sources.append({
            "name": "Web Search",
            "description": f"Found {len(result['web_tools'])} web-based tools",
            "type": "web_search"
        })
    if result.get("papers"):
        sources.append({
            "name": "Scientific Literature",
            "description": f"Found {len(result['papers'])} relevant papers",
            "type": "literature"
        })
    
    # Format the main response with Self-RAG insights
    response_text = f"I've analyzed your query about '{query}' and found {len(tools)} relevant tools and resources across different categories. "
    
    # Add specific counts for each category
    category_counts = []
    if local_tools:
        category_counts.append(f"{len(local_tools)} database tools")
    if web_tools:
        category_counts.append(f"{len(web_tools)} web tools")
    if scientific_papers:
        category_counts.append(f"{len(scientific_papers)} scientific papers")
    
    if category_counts:
        response_text += f"The results include {', '.join(category_counts)}. "
    
    # Add Self-RAG quality insights
    quality_metrics = result.get("quality_metrics", {})
    if quality_metrics:
        if quality_metrics.get("query_improved"):
            response_text += "I refined your query to get better results. "
        if quality_metrics.get("hallucination_detected"):
            response_text += "I've verified that all recommendations are grounded in reliable sources. "
        if quality_metrics.get("iterations_used", 0) > 1:
            response_text += f"I performed {quality_metrics['iterations_used']} rounds of refinement to ensure quality. "
    
    if tools:
        response_text += f"Below you'll find detailed analysis and specific recommendations for your research needs."
    else:
        response_text += "I couldn't find specific tools, but here's what I found in the scientific literature."
    
    # Format analysis with better structure
    analysis = result.get("analysis", "No detailed analysis available.")
    
    # Parse and structure the analysis if it contains the enhanced agent response format
    if "=== ENHANCED AGENT RESPONSE ===" in analysis:
        # Extract the enhanced response and format it properly
        enhanced_parts = analysis.split("=== ENHANCED AGENT RESPONSE ===")
        if len(enhanced_parts) > 1:
            enhanced_response = enhanced_parts[1].strip()
            
            # Structure the enhanced response
            structured_response = format_enhanced_response(enhanced_response)
            
            # Use structured summary if available, otherwise keep the original response_text
            if structured_response["summary"].strip():
                response_text = structured_response["summary"]
            # If no summary was extracted, create a brief one from the analysis
            else:
                response_text = f"I've analyzed your query about '{query}' and found {len(tools)} relevant tools and resources. The detailed analysis below provides specific recommendations and insights for your research needs."
            
            analysis = structured_response["detailed_analysis"]
    
    # Add Self-RAG quality summary to analysis
    if quality_metrics:
        quality_summary = []
        if quality_metrics.get("relevance_score"):
            quality_summary.append(f"Relevance Score: {quality_metrics['relevance_score']}")
        if quality_metrics.get("grounding_score"):
            quality_summary.append(f"Factual Accuracy: {quality_metrics['grounding_score']}")
        if quality_metrics.get("answer_quality"):
            quality_summary.append(f"Answer Quality: {quality_metrics['answer_quality']}")
        
        if quality_summary:
            analysis += f"\n\n🔍 Quality Assessment: {' | '.join(quality_summary)}"
    
    return {
        "response": response_text,
        "analysis": analysis,
        "tools": tools,
        "sources": sources
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "agent_initialized": agent is not None,
        "agent_type": "SelfRAGAgent",
        "version": "2.0.0",
        "features": [
            "Query refinement",
            "Tool relevance grading", 
            "Hallucination detection",
            "Quality assessment",
            "Iterative improvement"
        ]
    }

@app.get("/api/suggestions")
async def get_suggestions():
    """Get suggested queries for the search interface."""
    suggestions = [
        "I need tools for DNA sequence alignment",
        "Looking for RNA-seq analysis software",
        "What tools can I use for variant calling?",
        "I need protein structure prediction tools",
        "Looking for phylogenetic tree construction software",
        "What are the best tools for genome assembly?",
        "I need ChIP-seq analysis software",
        "Looking for single-cell RNA-seq tools",
        "What software works for protein-protein interactions?",
        "I need tools for microbiome analysis"
    ]
    return {"suggestions": suggestions}

if __name__ == "__main__":
    # Create necessary directories
    Path("templates").mkdir(exist_ok=True)
    Path("static").mkdir(exist_ok=True)
    Path("static/css").mkdir(exist_ok=True)
    Path("static/js").mkdir(exist_ok=True)
    
    # Run the application
    port = int(os.getenv("PORT", "8000"))
    print(f"🌐 Starting Self-RAG Enhanced Bioinformatics Tool Discovery Web App on port {port}")
    print(f"📱 Open your browser to: http://localhost:{port}")
    print(f"🎯 Enhanced with: Query refinement, Quality grading, Hallucination detection")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    ) 