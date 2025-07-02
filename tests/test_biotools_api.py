#!/usr/bin/env python3
"""
Test bio.tools API connectivity and basic functionality.

Run this before the full loader to ensure everything is working.

Usage:
    python tests/test_biotools_api.py
"""

import requests
import json
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))


def test_biotools_api():
    """Test various bio.tools API endpoints."""
    print("=== Testing bio.tools API ===\n")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'BioToolsAPITest/1.0',
        'Accept': 'application/json'
    })
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Basic connectivity
    print("1. Testing basic API connectivity...")
    try:
        response = session.get("https://bio.tools/api/tool/?page=1&format=json", timeout=10)
        response.raise_for_status()
        data = response.json()
        print(f"   ✅ Success! Got {len(data.get('list', []))} tools on page 1")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        tests_failed += 1
        return
    
    # Test 2: Check response structure
    print("\n2. Checking API response structure...")
    try:
        if 'list' in data and isinstance(data['list'], list):
            print("   ✅ Response has expected 'list' structure")
            tests_passed += 1
        else:
            print("   ❌ Response structure is unexpected")
            tests_failed += 1
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        tests_failed += 1
    
    # Test 3: Check tool data structure
    print("\n3. Checking tool data structure...")
    try:
        if data['list']:
            tool = data['list'][0]
            required_fields = ['biotoolsID', 'name']
            missing_fields = [f for f in required_fields if f not in tool]
            
            if not missing_fields:
                print(f"   ✅ First tool has required fields")
                print(f"      - ID: {tool['biotoolsID']}")
                print(f"      - Name: {tool['name']}")
                print(f"      - Description: {tool.get('description', 'N/A')[:100]}...")
                tests_passed += 1
            else:
                print(f"   ❌ Missing required fields: {missing_fields}")
                tests_failed += 1
        else:
            print("   ⚠️  No tools in response to check structure")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        tests_failed += 1
    
    # Test 4: Check pagination
    print("\n4. Testing pagination...")
    try:
        if 'next' in data:
            print(f"   ✅ Pagination available. Next URL: {data['next'][:50]}...")
            tests_passed += 1
        else:
            print("   ⚠️  No 'next' field found (might be last page)")
            tests_passed += 1
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        tests_failed += 1
    
    # Test 5: Test page 2
    print("\n5. Testing page 2 access...")
    try:
        response = session.get("https://bio.tools/api/tool/?page=2&format=json", timeout=10)
        response.raise_for_status()
        data2 = response.json()
        print(f"   ✅ Success! Got {len(data2.get('list', []))} tools on page 2")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        tests_failed += 1
    
    # Test 6: Check specific tool access
    print("\n6. Testing specific tool access...")
    try:
        # Try to get BLAST tool as an example
        response = session.get("https://bio.tools/api/tool/blast", timeout=10)
        if response.status_code == 200:
            tool_data = response.json()
            print(f"   ✅ Successfully retrieved specific tool")
            print(f"      - Name: {tool_data.get('name', 'N/A')}")
            print(f"      - Homepage: {tool_data.get('homepage', 'N/A')}")
            tests_passed += 1
        else:
            print(f"   ⚠️  Could not retrieve specific tool (status: {response.status_code})")
            tests_passed += 1  # Not critical
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        tests_failed += 1
    
    # Test 7: Estimate total tools
    print("\n7. Estimating total number of tools...")
    try:
        # Try to get a high page number to estimate total
        response = session.get("https://bio.tools/api/tool/?page=1000&format=json", timeout=10)
        if response.status_code == 404:
            print("   ℹ️  Page 1000 not found (expected)")
            # Binary search to find approximate last page
            low, high = 1, 1000
            last_valid = 1
            
            while low <= high and high - low > 10:
                mid = (low + high) // 2
                response = session.get(f"https://bio.tools/api/tool/?page={mid}&format=json", timeout=10)
                if response.status_code == 200:
                    last_valid = mid
                    low = mid + 1
                else:
                    high = mid - 1
            
            print(f"   ℹ️  Approximately {last_valid * 10} - {(last_valid + 10) * 10} tools in registry")
        else:
            print("   ℹ️  Page 1000 exists! Registry has 10,000+ tools")
        tests_passed += 1
    except Exception as e:
        print(f"   ⚠️  Could not estimate total: {e}")
        tests_passed += 1  # Not critical
    
    # Summary
    print("\n" + "="*50)
    print(f"Tests passed: {tests_passed}")
    print(f"Tests failed: {tests_failed}")
    
    if tests_failed == 0:
        print("\n✅ All tests passed! Bio.tools API is working correctly.")
        print("You can now run load_biotools_tools.py safely.")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        print("The API might be down or there might be connectivity issues.")
    
    return tests_failed == 0


def test_search_functionality():
    """Test bio.tools search functionality."""
    print("\n\n=== Testing Search Functionality ===\n")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'BioToolsAPITest/1.0',
        'Accept': 'application/json'
    })
    
    # Test search
    print("Testing search for 'alignment' tools...")
    try:
        response = session.get(
            "https://bio.tools/api/tool/?q=alignment&format=json", 
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ Found {len(data.get('list', []))} tools matching 'alignment'")
        
        if data.get('list'):
            print("\nFirst 3 results:")
            for i, tool in enumerate(data['list'][:3], 1):
                print(f"{i}. {tool.get('name', 'N/A')} ({tool.get('biotoolsID', 'N/A')})")
                print(f"   {tool.get('description', 'No description')[:100]}...")
        
    except Exception as e:
        print(f"❌ Search test failed: {e}")


if __name__ == "__main__":
    # Run basic API tests
    success = test_biotools_api()
    
    # Run search test
    if success:
        test_search_functionality()
    
    print("\n" + "="*50)
    print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")