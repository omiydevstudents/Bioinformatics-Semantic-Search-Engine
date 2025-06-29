#!/usr/bin/env python3
"""
Test script for the Self-RAG enhanced ToolDiscoveryAgent.
Tests intelligent self-reflection and quality control features.
"""

import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from agents.self_rag_agent import SelfRAGAgent

async def test_self_rag_agent():
    """Test the Self-RAG enhanced agent with intelligent self-reflection."""
    print("🤖 Testing Self-RAG Enhanced ToolDiscoveryAgent")
    print("=" * 60)
    
    # Initialize agent
    agent = SelfRAGAgent()
    
    print(f"✅ Agent initialized")
    print(f"🔧 Self-RAG enabled: {agent.use_gemini}")
    print(f"🔄 Max iterations: {agent.max_iterations}")
    print()
    
    # Test queries
    test_queries = [
        "I need tools for DNA sequence alignment",
        "Looking for software to do multiple sequence alignment", 
        "I'm working on RNA-seq data and need analysis tools",
        "Looking for variant calling software for my NGS data",
        "I need tools for protein structure prediction",
        "Looking for tools to identify protein domains",
        "What software is good for phylogenetic inference",
        "Looking for statistical analysis tools for my RNA-seq results"
        "What software can parse FASTA files?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"🧪 Test {i}: '{query}'")
        print("-" * 40)
        
        try:
            # Test Self-RAG enhanced discovery
            results = await agent.discover_tools_self_rag(query)
            
            print(f"📊 Results Summary:")
            print(f"   Original query: {results.get('original_query', query)}")
            print(f"   Final query: {results.get('query_used', query)}")
            print(f"   Total iterations: {results.get('total_iterations', 0)}")
            print(f"   Total results: {results.get('total_results', 0)}")
            print(f"   Self-RAG enhanced: {results.get('self_rag_enhanced', False)}")
            
            # Show quality grades
            quality_grades = results.get('quality_grades', {})
            if quality_grades:
                print(f"   🔍 Quality Assessment:")
                print(f"      Grounded: {quality_grades.get('grounded', 'unknown')}")
                print(f"      Addresses Query: {quality_grades.get('addresses_query', 'unknown')}")
                print(f"      Overall Quality: {quality_grades.get('overall_quality', 'unknown')}")
            
            # Show graded tools
            chroma_tools = results.get('chroma_tools', [])
            if chroma_tools:
                print(f"   🔍 Graded ChromaDB Tools:")
                for j, tool in enumerate(chroma_tools[:3], 1):
                    grade = tool.get('relevance_grade', 'unknown')
                    reasoning = tool.get('relevance_reasoning', 'No reasoning provided')
                    print(f"      {j}. {tool['name']} - Grade: {grade}")
                    if grade == 'no':
                        print(f"         Reason: {reasoning[:100]}...")
            
            # Show iteration history
            iteration_history = results.get('iteration_history', [])
            if len(iteration_history) > 1:
                print(f"   📈 Iteration History:")
                for k, iteration in enumerate(iteration_history, 1):
                    quality = iteration.get('quality_grades', {}).get('overall_quality', 'unknown')
                    query_used = iteration.get('query_used', 'unknown')
                    print(f"      Iteration {k}: Quality={quality}, Query='{query_used[:50]}...'")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
    
    await agent.close()
    print("✅ Self-RAG test completed!")

async def test_quality_grading():
    """Test the quality grading functionality specifically."""
    print("🔍 Testing Quality Grading Components")
    print("=" * 60)
    
    agent = SelfRAGAgent()
    
    if not agent.use_gemini:
        print("⚠️  Gemini AI not available for quality grading")
        return
    
    # Test query transformation
    print("🔄 Testing Query Transformation...")
    original_query = "ML for bio"
    improved_query = await agent.transform_query(original_query)
    print(f"   Original: {original_query}")
    print(f"   Improved: {improved_query}")
    print()
    
    # Test tool relevance grading
    print("📊 Testing Tool Relevance Grading...")
    mock_tools = [
        {
            "name": "MLSeq",
            "category": "Machine Learning",
            "content": "Machine learning package for RNA-seq data analysis"
        },
        {
            "name": "BLAST",
            "category": "Sequence Analysis", 
            "content": "Basic Local Alignment Search Tool for sequence comparison"
        }
    ]
    
    graded_tools = await agent.grade_tool_relevance("machine learning for biology", mock_tools)
    print(f"   Graded {len(graded_tools)} tools")
    for tool in graded_tools:
        print(f"   - {tool['name']}: {tool.get('relevance_grade', 'unknown')}")
    print()
    
    await agent.close()

async def main():
    """Main function."""
    print("🚀 Self-RAG Agent Test Suite")
    print("=" * 60)
    
    # Check environment
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("⚠️  GOOGLE_API_KEY not found")
        print("   Self-RAG grading will be disabled")
        print("   To enable Self-RAG features, add to your .env file:")
        print("   GOOGLE_API_KEY=your-google-api-key-here")
        print()
    else:
        print(f"✅ GOOGLE_API_KEY found: {google_api_key[:10]}...")
        print("   Self-RAG features will be active!")
        print()
    
    # Run tests
    await test_quality_grading()
    await test_self_rag_agent()

if __name__ == "__main__":
    asyncio.run(main()) 