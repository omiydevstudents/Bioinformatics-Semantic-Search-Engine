#!/usr/bin/env python3
"""
Simple script to check Gemini API quota status and test basic functionality.
"""

import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_gemini_quota():
    """Test Gemini API quota and basic functionality."""
    print("🔍 Checking Gemini API Quota Status")
    print("=" * 50)
    
    # Check API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not found")
        return
    
    print(f"✅ API Key found: {api_key[:10]}...")
    
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        # Initialize Gemini
        gemini = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            api_key=api_key,
            temperature=0.1,
            max_tokens=100
        )
        
        print("🤖 Testing basic Gemini functionality...")
        
        # Simple test query
        test_prompt = "Say 'Hello, Gemini is working!' in one sentence."
        
        try:
            response = await gemini.ainvoke(test_prompt)
            print(f"✅ Success: {response.content}")
            print("🎉 Your Gemini API is working and has quota available!")
            
        except Exception as e:
            error_str = str(e)
            print(f"❌ Error: {error_str}")
            
            if "429" in error_str or "quota" in error_str.lower():
                print("\n📊 Rate Limit Analysis:")
                print("   • You've hit the rate limit")
                print("   • Free tier limits: 15 requests/minute, 1500 requests/day")
                print("   • Wait a few minutes and try again")
                
                if "per minute" in error_str.lower():
                    print("   • This is a per-minute limit - wait 60 seconds")
                elif "per day" in error_str.lower():
                    print("   • This is a daily limit - wait until tomorrow")
                    
            elif "401" in error_str or "unauthorized" in error_str.lower():
                print("   • API key might be invalid or expired")
                print("   • Check your Google AI Studio settings")
            else:
                print("   • Unknown error - check your internet connection")
                
    except ImportError:
        print("❌ langchain_google_genai not installed")
        print("   Run: pip install langchain-google-genai")

async def main():
    """Main function."""
    await test_gemini_quota()

if __name__ == "__main__":
    asyncio.run(main()) 