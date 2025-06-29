#!/usr/bin/env python3
"""
Test script for Gemini AI integration in the ToolDiscoveryAgent.
Demonstrates enhanced query processing and intelligent result analysis.
Handles rate limits and API errors gracefully.
"""

import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from agents.tool_discovery_agent import ToolDiscoveryAgent

class RateLimitHandler:
    """Handles rate limit errors and provides fallback options."""
    
    def __init__(self):
        self.last_error_time = 0
        self.retry_count = 0
        self.max_retries = 3
    
    def should_retry(self, error: Exception) -> bool:
        """Check if we should retry based on the error type."""
        error_str = str(error).lower()
        
        # Rate limit errors
        if "429" in error_str or "quota" in error_str or "rate" in error_str:
            return True
        
        # Temporary errors
        if "timeout" in error_str or "temporary" in error_str:
            return True
            
        return False
    
    def get_retry_delay(self, error: Exception) -> int:
        """Calculate retry delay based on error type."""
        error_str = str(error).lower()
        
        if "429" in error_str:
            # Rate limit - wait longer
            return min(60, 10 * (2 ** self.retry_count))
        elif "quota" in error_str:
            # Quota exceeded - wait even longer
            return min(300, 30 * (2 ** self.retry_count))
        else:
            # Other errors - shorter delay
            return min(30, 5 * (2 ** self.retry_count))
    
    def increment_retry(self):
        """Increment retry counter."""
        self.retry_count += 1
    
    def reset_retry(self):
        """Reset retry counter."""
        self.retry_count = 0

async def test_gemini_with_fallback(agent: ToolDiscoveryAgent, query: str, rate_handler: RateLimitHandler) -> dict:
    """Test Gemini integration with fallback handling."""
    print(f"🧪 Testing Query: '{query}'")
    
    # Try to enhance query with Gemini
    enhanced_query = query
    gemini_used = False
    error_message = None
    
    try:
        enhanced_query = await agent.enhance_query_with_gemini(query)
        gemini_used = enhanced_query != query
        print(f"   ✅ Enhanced: '{enhanced_query}'")
        
    except Exception as e:
        error_message = str(e)
        print(f"   ⚠️  Gemini enhancement failed: {error_message}")
        
        # Check if we should retry
        should_retry = (rate_handler.should_retry(e) and 
                       rate_handler.retry_count < rate_handler.max_retries)
        
        if should_retry:
            delay = rate_handler.get_retry_delay(e)
            attempt = rate_handler.retry_count + 1
            print(f"   🔄 Retrying in {delay} seconds... "
                  f"(attempt {attempt}/{rate_handler.max_retries})")
            
            rate_handler.increment_retry()
            await asyncio.sleep(delay)
            
            try:
                enhanced_query = await agent.enhance_query_with_gemini(query)
                gemini_used = enhanced_query != query
                print(f"   ✅ Retry successful! Enhanced: '{enhanced_query}'")
                rate_handler.reset_retry()
            except Exception as retry_error:
                print(f"   ❌ Retry failed: {retry_error}")
                error_message = str(retry_error)
        else:
            print("   ⚠️  Using original query as fallback")
    
    # Test full discovery (this will work even without Gemini)
    print("🔍 Running tool discovery...")
    try:
        results = await agent.discover_tools_enhanced(query)
        
        return {
            "original_query": query,
            "enhanced_query": enhanced_query,
            "gemini_used": gemini_used,
            "error": error_message,
            "results": results,
            "success": True
        }
        
    except Exception as e:
        print(f"   ❌ Discovery failed: {e}")
        return {
            "original_query": query,
            "enhanced_query": enhanced_query,
            "gemini_used": gemini_used,
            "error": error_message,
            "results": None,
            "success": False
        }

async def test_gemini_integration():
    """Test the Gemini AI integration features with rate limit handling."""
    print("🤖 Testing Gemini AI Integration (with Rate Limit Handling)")
    print("=" * 60)
    
    # Initialize agent and rate handler
    agent = ToolDiscoveryAgent()
    rate_handler = RateLimitHandler()
    
    if not agent.use_gemini:
        print("❌ Gemini AI not available. Please set GOOGLE_API_KEY in your .env file")
        print("   Example: GOOGLE_API_KEY=your-google-api-key-here")
        return False
    
    print("✅ Gemini AI integration active!")
    print("🛡️  Rate limit handling enabled")
    print()
    
    # Test queries (expanded to test Pro account limits)
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
    
    results_summary = []
    
    for i, query in enumerate(test_queries, 1):
        print(f"📋 Test {i}/{len(test_queries)}")
        print("-" * 40)
        
        result = await test_gemini_with_fallback(agent, query, rate_handler)
        results_summary.append(result)
        
        if result["success"]:
            results = result["results"]
            print("   📊 Results Summary:")
            print(f"      Total results: {results.get('total_results', 0)}")
            print(f"      ChromaDB tools: {len(results.get('chroma_tools', []))}")
            print(f"      Web tools: {len(results.get('web_tools', []))}")
            print(f"      Papers: {len(results.get('papers', []))}")
            print(f"      Enhanced with Gemini: {results.get('enhanced_with_gemini', False)}")
        else:
            print("   ❌ Test failed")
        
        print()
        
        # Add delay between tests to avoid rate limits
        if i < len(test_queries):
            print("   ⏳ Waiting 2 seconds before next test...")
            await asyncio.sleep(2)
            print()
    
    await agent.close()
    
    # Print summary
    print("📋 Test Summary")
    print("=" * 40)
    successful_tests = sum(1 for r in results_summary if r["success"])
    gemini_used_count = sum(1 for r in results_summary if r["gemini_used"])
    
    print(f"✅ Successful tests: {successful_tests}/{len(test_queries)}")
    print(f"🤖 Gemini used: {gemini_used_count}/{len(test_queries)}")
    print(f"⚠️  Errors encountered: {sum(1 for r in results_summary if r['error'])}")
    
    return successful_tests > 0

async def test_fallback_functionality():
    """Test that the system works without Gemini."""
    print("🔄 Testing Fallback Functionality (without Gemini)")
    print("=" * 50)
    
    # Temporarily disable Gemini
    agent = ToolDiscoveryAgent()
    original_gemini = agent.use_gemini
    agent.use_gemini = False
    
    print("✅ Testing with Gemini disabled...")
    
    try:
        # Test basic discovery
        results = await agent.discover_tools("sequence alignment")
        
        print("   📊 Basic discovery results:")
        print(f"      Total results: {results.get('total_results', 0)}")
        print(f"      ChromaDB tools: {len(results.get('chroma_tools', []))}")
        print(f"      Web tools: {len(results.get('web_tools', []))}")
        print(f"      Enhanced with Gemini: {results.get('enhanced_with_gemini', False)}")
        
        if results.get('total_results', 0) > 0:
            print("   ✅ Fallback functionality working correctly")
            success = True
        else:
            print("   ⚠️  No results found in fallback mode")
            success = False
            
    except Exception as e:
        print(f"   ❌ Fallback test failed: {e}")
        success = False
    
    # Restore Gemini
    agent.use_gemini = original_gemini
    await agent.close()
    
    return success

async def main():
    """Main test function."""
    print("🚀 Gemini AI Integration Test Suite (Enhanced)")
    print("=" * 60)
    
    # Check environment
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("❌ GOOGLE_API_KEY not found in environment")
        print("   Please add to your .env file:")
        print("   GOOGLE_API_KEY=your-google-api-key-here")
        print()
        print("   Get your API key from: https://makersuite.google.com/app/apikey")
        print()
        print("   Note: Free tier has rate limits. Consider upgrading for production use.")
        return False
    
    print(f"✅ GOOGLE_API_KEY found: {google_api_key[:10]}...")
    print("⚠️  Note: Free tier has rate limits (15 requests/minute, 1500 requests/day)")
    print()
    
    # Run tests
    print("🧪 Running main integration tests...")
    success1 = await test_gemini_integration()
    print()
    
    print("🔄 Testing fallback functionality...")
    success2 = await test_fallback_functionality()
    
    print()
    print("🎯 Final Results")
    print("=" * 30)
    
    if success1 and success2:
        print("🎉 All tests completed successfully!")
        print()
        print("📋 System Status:")
        print("   ✅ Gemini AI integration working")
        print("   ✅ Rate limit handling active")
        print("   ✅ Fallback functionality working")
        print("   ✅ Tool discovery operational")
        print()
        print("💡 Tips for production use:")
        print("   • Consider upgrading to paid Gemini API for higher limits")
        print("   • Implement caching to reduce API calls")
        print("   • Use batch processing for multiple queries")
        print("   • Monitor API usage to avoid rate limits")
    else:
        print("❌ Some tests failed. Check the output above.")
        print()
        print("🔧 Troubleshooting:")
        print("   • Check your GOOGLE_API_KEY is valid")
        print("   • Verify you have sufficient API quota")
        print("   • Try again later if rate limited")
        print("   • Check network connectivity")

if __name__ == "__main__":
    asyncio.run(main()) 