#!/usr/bin/env python3
"""
Test script for the enhanced ToolDiscoveryAgent with Gemini AI integration.
"""

import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from agents.tool_discovery_agent import ToolDiscoveryAgent

async def test_enhanced_agent():
    """Test the enhanced agent with Gemini integration."""
    print("🤖 Testing Enhanced ToolDiscoveryAgent with Gemini AI")
    print("=" * 60)
    
    # Initialize agent
    agent = ToolDiscoveryAgent()
    
    print(f"✅ Agent initialized")
    print(f"🔧 Gemini AI enabled: {agent.use_gemini}")
    print()
    
    # Test queries
    test_queries = [
        "machine learning for biology",
        "sequence alignment tools",
        "protein structure prediction",
        "RNA-seq analysis pipeline",
        "phylogenetic tree construction",
        "variant calling tools",
        "gene expression analysis",
        "drug discovery bioinformatics"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"🧪 Test {i}: '{query}'")
        print("-" * 40)
        
        try:
            # Test enhanced discovery (with Gemini query enhancement)
            results = await agent.discover_tools_enhanced(query)
            
            print(f"📊 Results Summary:")
            print(f"   Original query: {results.get('original_query', query)}")
            print(f"   Enhanced query: {results.get('enhanced_query', query)}")
            print(f"   Query enhanced: {results.get('query_enhanced', False)}")
            print(f"   Total results: {results.get('total_results', 0)}")
            print(f"   Gemini enhanced: {results.get('enhanced_with_gemini', False)}")
            
            # Show analysis
            analysis = results.get('analysis', '')
            if analysis:
                if '=== ENHANCED AGENT RESPONSE ===' in analysis:
                    print("   ✅ Using Gemini-enhanced analysis")
                    # Show first part of Gemini analysis
                    gemini_part = analysis.split('=== ENHANCED AGENT RESPONSE ===')[1].strip()
                    print(f"   📝 Analysis: {gemini_part[:150]}...")
                else:
                    print("   ⚠️  Using basic analysis")
                    print(f"   📝 Analysis: {analysis[:150]}...")
            
            # Show top results
            chroma_tools = results.get('chroma_tools', [])
            if chroma_tools:
                print(f"   🔍 Top ChromaDB tools:")
                for j, tool in enumerate(chroma_tools[:3], 1):
                    print(f"      {j}. {tool['name']} (Score: {tool.get('relevance_score', 0):.3f})")
            
            web_tools = results.get('web_tools', [])
            if web_tools:
                print(f"   🌐 Top web tools:")
                for j, tool in enumerate(web_tools[:2], 1):
                    print(f"      {j}. {tool.get('name', 'Unknown')}")
            
            papers = results.get('papers', [])
            if papers:
                print(f"   📚 Top papers:")
                for j, paper in enumerate(papers[:2], 1):
                    title = paper.get('title', 'Unknown')[:50]
                    print(f"      {j}. {title}...")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
    
    await agent.close()
    print("✅ Test completed!")

async def main():
    """Main function."""
    print("🚀 Enhanced Agent Test Suite")
    print("=" * 60)
    
    # Check environment
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("⚠️  GOOGLE_API_KEY not found")
        print("   The agent will work without Gemini AI enhancement")
        print("   To enable Gemini AI, add to your .env file:")
        print("   GOOGLE_API_KEY=your-google-api-key-here")
        print()
    else:
        print(f"✅ GOOGLE_API_KEY found: {google_api_key[:10]}...")
        print("   Gemini AI enhancement will be active!")
        print()
    
    await test_enhanced_agent()

if __name__ == "__main__":
    asyncio.run(main()) 