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
        
        # Perform the Self-RAG enhanced search
        result = await agent.discover_tools_self_rag(request.query)
        
        # Calculate search time
        search_time = time.time() - start_time
        
        # Format the response for the web interface
        formatted_response = format_response_for_web(result, request.query)
        
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
            quality_metrics=result.get("quality_metrics", {})
        )
        
    except Exception as e:
        search_time = time.time() - start_time
        raise HTTPException(
            status_code=500, 
            detail=f"Search failed: {str(e)}"
        )

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
            
        # Check for section headers
        if line.startswith("**Top") or line.startswith("**Notable Gaps:") or line.startswith("**Recommendations:") or line.startswith("**Overall Assessment:"):
            current_section = "analysis"
            analysis_parts.append(f"\n### {line.strip('*')}")
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


def format_response_for_web(result: Dict, query: str) -> Dict:
    """Format the Self-RAG agent response for web display."""
    
    # Extract tools from different sources
    tools = []
    
    # Add ChromaDB tools (now with quality grades)
    for tool in result.get("chroma_tools", []):
        relevance_grade = tool.get("relevance_grade", "unknown")
        relevance_reasoning = tool.get("relevance_reasoning", "")
        
        tools.append({
            "name": tool.get("name", "Unknown"),
            "category": tool.get("category", "Unknown"),
            "description": tool.get("content", "")[:200] + "...",
            "source": "ChromaDB (Local Database)",
            "relevance_score": tool.get("relevance_score", 0),
            "type": "local_tool",
            "url": None,
            "quality_grade": relevance_grade,
            "quality_reasoning": relevance_reasoning
        })
    
    # Add web tools
    for tool in result.get("web_tools", []):
        tools.append({
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
        tools.append({
            "name": paper.get("title", "Unknown Paper"),
            "category": "Scientific Literature",
            "description": paper.get("abstract", "")[:200] + "...",
            "source": "PubMed/Europe PMC",
            "relevance_score": 0.7,  # Default score for papers
            "type": "scientific_paper",
            "url": paper.get("url"),
            "quality_grade": "scientific_paper",
            "quality_reasoning": "Peer-reviewed scientific literature"
        })
    
    # Sort tools by relevance score (Self-RAG may have reordered based on quality)
    tools.sort(key=lambda x: x["relevance_score"], reverse=True)
    
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
    response_text = f"I found several tools and resources that might help with your query about '{query}'. "
    
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
        response_text += f"Here are the most relevant options I discovered:"
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
            response_text = structured_response["summary"]
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
        "tools": tools[:10],  # Limit to top 10
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