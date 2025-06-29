#!/usr/bin/env python3
"""
Test script for the Bioinformatics Tool Discovery Web Application
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path (tests folder is inside the project)
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

async def test_web_app():
    """Test the web application components."""
    
    print("🧪 Testing Bioinformatics Tool Discovery Web App")
    print("=" * 50)
    
    try:
        # Test 1: Check if main.py exists
        print("1. Checking main.py...")
        if Path("main.py").exists():
            print("   ✅ main.py found")
        else:
            print("   ❌ main.py not found")
            return False
        
        # Test 2: Check if templates exist
        print("2. Checking templates...")
        if Path("templates/index.html").exists():
            print("   ✅ templates/index.html found")
        else:
            print("   ❌ templates/index.html not found")
            return False
        
        # Test 3: Check if static files exist
        print("3. Checking static files...")
        static_files = [
            "static/css/style.css",
            "static/js/app.js"
        ]
        for file_path in static_files:
            if Path(file_path).exists():
                print(f"   ✅ {file_path} found")
            else:
                print(f"   ❌ {file_path} not found")
                return False
        
        # Test 4: Test SelfRAGAgent import (main.py now uses this)
        print("4. Testing SelfRAGAgent import...")
        try:
            from src.agents.self_rag_agent import SelfRAGAgent
            print("   ✅ SelfRAGAgent imported successfully")
        except ImportError as e:
            print(f"   ❌ Failed to import SelfRAGAgent: {e}")
            return False
        
        # Test 5: Test ChromaDB store
        print("5. Testing ChromaDB store...")
        try:
            from src.db.chroma_store import SemanticSearchStore
            store = SemanticSearchStore()
            print("   ✅ SemanticSearchStore initialized successfully")
        except Exception as e:
            print(f"   ❌ Failed to initialize SemanticSearchStore: {e}")
            return False
        
        # Test 6: Test MCP client
        print("6. Testing MCP client...")
        try:
            from src.mcp.enhanced_mcp_client import EnhancedMCPClient
            print("   ✅ EnhancedMCPClient imported successfully")
        except ImportError as e:
            print(f"   ❌ Failed to import EnhancedMCPClient: {e}")
            return False
        
        # Test 7: Test base ToolDiscoveryAgent (used by SelfRAGAgent)
        print("7. Testing base ToolDiscoveryAgent...")
        try:
            from src.agents.tool_discovery_agent import ToolDiscoveryAgent
            print("   ✅ ToolDiscoveryAgent imported successfully")
        except ImportError as e:
            print(f"   ❌ Failed to import ToolDiscoveryAgent: {e}")
            return False
        
        print("\n🎉 All tests passed! Web app is ready to run.")
        print("\n📱 To start the web application:")
        print("   python main.py")
        print("\n🌐 Then open your browser to: http://localhost:8000")
        print("\n🧠 Features: Self-RAG quality control, query refinement, tool grading")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_web_app())
    sys.exit(0 if success else 1) 