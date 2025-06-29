#!/usr/bin/env python3
"""
Test script to verify Pro Gemini account limits and billing status.
"""

import os
import asyncio
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_pro_account_limits():
    """Test Pro account limits and billing status."""
    print("🔍 Testing Pro Gemini Account Limits")
    print("=" * 50)
    
    # Check API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not found")
        return
    
    print(f"✅ API Key found: {api_key[:10]}...")
    
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        # Initialize Gemini with Pro settings
        gemini = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            api_key=api_key,
            temperature=0.1,
            max_tokens=1000
        )
        
        print("🤖 Testing Pro account capabilities...")
        print()
        
        # Test 1: Basic functionality
        print("📋 Test 1: Basic Query")
        try:
            response = await gemini.ainvoke("Say 'Pro account test successful' in one sentence.")
            print(f"   ✅ Success: {response.content}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return
        
        # Test 2: Multiple rapid requests (to test rate limits)
        print("\n📋 Test 2: Multiple Rapid Requests")
        print("   Testing 5 requests in quick succession...")
        
        success_count = 0
        for i in range(5):
            try:
                response = await gemini.ainvoke(f"Count to {i+1} in one sentence.")
                print(f"   ✅ Request {i+1}: {response.content}")
                success_count += 1
                # Small delay between requests
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"   ❌ Request {i+1} failed: {e}")
                if "429" in str(e):
                    print("   ⚠️  Rate limit hit - this suggests free tier limits")
                break
        
        print(f"\n📊 Results: {success_count}/5 requests successful")
        
        if success_count == 5:
            print("🎉 Pro account working with high rate limits!")
        elif success_count > 0:
            print("⚠️  Partial success - may be hitting some limits")
        else:
            print("❌ All requests failed - check account status")
        
        # Test 3: Longer response (to test token limits)
        print("\n📋 Test 3: Longer Response Test")
        try:
            long_prompt = """
            Write a detailed paragraph about bioinformatics tools for sequence analysis.
            Include information about BLAST, HMMER, and other popular tools.
            Make it comprehensive and informative.
            """
            response = await gemini.ainvoke(long_prompt)
            print(f"   ✅ Long response successful: {len(response.content)} characters")
            print(f"   📝 Preview: {response.content[:100]}...")
        except Exception as e:
            print(f"   ❌ Long response failed: {e}")
        
        # Test 4: Check billing status
        print("\n📋 Test 4: Billing Status Check")
        try:
            billing_prompt = """
            You are a helpful assistant. Please respond with just "Billing check successful" 
            if you can process this request. This will help verify your account status.
            """
            response = await gemini.ainvoke(billing_prompt)
            print(f"   ✅ Billing check: {response.content}")
        except Exception as e:
            print(f"   ❌ Billing check failed: {e}")
            
    except ImportError:
        print("❌ langchain_google_genai not installed")
        return

async def test_quota_limits():
    """Test to see what limits we're actually hitting."""
    print("\n🔍 Testing Quota Limits")
    print("=" * 30)
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return
    
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        gemini = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            api_key=api_key,
            temperature=0.1,
            max_tokens=100
        )
        
        print("🔄 Testing rapid requests to identify limits...")
        
        # Try to make many requests quickly
        for i in range(20):
            try:
                start_time = time.time()
                response = await gemini.ainvoke(f"Quick test {i+1}")
                end_time = time.time()
                print(f"   ✅ Request {i+1}: {end_time - start_time:.2f}s")
                
                if i % 5 == 4:  # Every 5 requests
                    print(f"   ⏳ Pausing 2 seconds...")
                    await asyncio.sleep(2)
                    
            except Exception as e:
                error_str = str(e)
                print(f"   ❌ Request {i+1} failed: {error_str}")
                
                if "429" in error_str:
                    print(f"   🎯 Rate limit hit at request {i+1}")
                    if "per minute" in error_str.lower():
                        print("   📊 This appears to be a per-minute limit")
                    elif "per day" in error_str.lower():
                        print("   📊 This appears to be a daily limit")
                    break
                else:
                    print(f"   🔍 Other error: {error_str}")
                    break
                    
    except Exception as e:
        print(f"❌ Quota test failed: {e}")

async def main():
    """Main function."""
    await test_pro_account_limits()
    await test_quota_limits()
    
    print("\n" + "=" * 50)
    print("📋 Summary:")
    print("• If you see rate limits at 15 requests/minute, you're on free tier")
    print("• If you can make 20+ requests quickly, you're on Pro tier")
    print("• Check your Google AI Studio billing dashboard for confirmation")
    print("• Pro accounts should have much higher limits")

if __name__ == "__main__":
    asyncio.run(main()) 