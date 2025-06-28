# scripts/check_and_update_packages.py
"""
Package Update Checker
Checks for new BioPython and Bioconductor packages and updates the system.

Usage:
    python src/scripts/check_and_update_packages.py

What it does:
1. Uses existing scrapers to get current packages
2. Compares with existing JSON data files  
3. Shows new packages found
4. Asks user to update JSON files
5. Asks user to load new packages into ChromaDB

"""

import json
import os
import sys
import asyncio
from pathlib import Path

# Add project root and src to path for imports
project_root = Path(__file__).parent.parent.parent
scripts_dir = Path(__file__).parent
sys.path.append(str(project_root))
sys.path.append(str(scripts_dir))
sys.path.append(str(project_root / "src"))

def load_existing_data(file_path):
    """Load existing package data from JSON file."""
    if not os.path.exists(file_path):
        print(f"📄 No existing data found at {file_path}")
        return []
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        print(f"✅ Loaded {len(data)} existing packages from {file_path}")
        return data
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return []

def save_updated_data(data, file_path):
    """Save updated package data to JSON file."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ Saved {len(data)} packages to {file_path}")
        return True
    except Exception as e:
        print(f"❌ Error saving to {file_path}: {e}")
        return False

def update_report_file(tools_data, report_path, source_name):
    """Update the collection report file with new statistics."""
    try:
        # Create basic report statistics
        categories = {}
        for tool in tools_data:
            category = tool.get('category', 'Unknown')
            categories[category] = categories.get(category, 0) + 1
        
        # Sort categories by count
        top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
        
        report = {
            "collection_summary": {
                "total_tools": len(tools_data),
                "source": source_name,
                "categories_count": len(categories)
            },
            "top_categories": top_categories[:15],  # Top 15 categories
            "category_breakdown": categories
        }
        
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✅ Updated report file: {report_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating report {report_path}: {e}")
        return False

def ask_user(question):
    """Ask user a yes/no question."""
    while True:
        answer = input(f"{question} (y/n): ").lower().strip()
        if answer in ['y', 'yes']:
            return True
        elif answer in ['n', 'no']:
            return False
        else:
            print("Please answer 'y' or 'n'")

async def check_biopython_packages():
    """Check for new BioPython packages."""
    print("\n🐍 Checking BioPython packages...")
    print("-" * 40)
    
    # Path to existing BioPython data
    biopython_file = "data/biopython_collection/complete_biopython_tools.json"
    
    # Load existing data
    existing_tools = load_existing_data(biopython_file)
    existing_names = set(tool['name'] for tool in existing_tools)
    
    # Get current packages using existing scraper
    try:
        from biopython_tools_collector import CompleteBiopythonCollector
        
        print("🔍 Scanning current BioPython packages...")
        collector = CompleteBiopythonCollector()
        current_tools = await collector.collect_and_save()
        
        if not current_tools:
            print("❌ No current BioPython packages found")
            return [], []
        
        print(f"✅ Found {len(current_tools)} current BioPython packages")
        
        # Find new packages
        current_names = set(tool['name'] for tool in current_tools)
        new_names = current_names - existing_names
        
        new_tools = [tool for tool in current_tools if tool['name'] in new_names]
        
        if new_tools:
            print(f"🆕 Found {len(new_tools)} new BioPython packages:")
            for tool in new_tools[:10]:  # Show first 10
                print(f"   • {tool['name']}")
            if len(new_tools) > 10:
                print(f"   ... and {len(new_tools) - 10} more")
        else:
            print("✅ No new BioPython packages found")
        
        return new_tools, current_tools
        
    except Exception as e:
        print(f"❌ Error checking BioPython packages: {e}")
        return [], []

async def check_bioconductor_packages():
    """Check for new Bioconductor packages."""
    print("\n🧬 Checking Bioconductor packages...")
    print("-" * 40)
    
    # Path to existing Bioconductor data
    bioconductor_file = "data/bioconductor_collection/complete_bioconductor_tools.json"
    
    # Load existing data
    existing_tools = load_existing_data(bioconductor_file)
    existing_names = set(tool['name'] for tool in existing_tools)
    
    # Get current packages using existing scraper
    try:
        from bioconductor_tools_collector import FixedBioconductorCollector
        
        print("🔍 Scanning current Bioconductor packages...")
        print("⏱️  This may take a few minutes...")
        
        collector = FixedBioconductorCollector()
        current_tools = await collector.collect_and_save()
        
        if not current_tools:
            print("❌ No current Bioconductor packages found")
            return [], []
        
        print(f"✅ Found {len(current_tools)} current Bioconductor packages")
        
        # Find new packages
        current_names = set(tool['name'] for tool in current_tools)
        new_names = current_names - existing_names
        
        new_tools = [tool for tool in current_tools if tool['name'] in new_names]
        
        if new_tools:
            print(f"🆕 Found {len(new_tools)} new Bioconductor packages:")
            for tool in new_tools[:10]:  # Show first 10
                print(f"   • {tool['name']}")
            if len(new_tools) > 10:
                print(f"   ... and {len(new_tools) - 10} more")
        else:
            print("✅ No new Bioconductor packages found")
        
        return new_tools, current_tools
        
    except Exception as e:
        print(f"❌ Error checking Bioconductor packages: {e}")
        return [], []

async def update_chromadb(new_biopython_tools, new_bioconductor_tools):
    """Load new tools into ChromaDB."""
    total_new_tools = len(new_biopython_tools) + len(new_bioconductor_tools)
    
    if total_new_tools == 0:
        print("ℹ️  No new tools to load into ChromaDB")
        return
    
    print(f"\n💾 Loading {total_new_tools} new tools into ChromaDB...")
    print("-" * 40)
    
    try:
        from db.chroma_store import SemanticSearchStore
        
        store = SemanticSearchStore()
        
        # Convert tools to the right format for ChromaDB
        all_new_tools = []
        
        # Add BioPython tools
        for tool in new_biopython_tools:
            tool_dict = tool.to_dict() if hasattr(tool, 'to_dict') else tool
            all_new_tools.append(tool_dict)
        
        # Add Bioconductor tools
        for tool in new_bioconductor_tools:
            tool_dict = tool.to_dict() if hasattr(tool, 'to_dict') else tool
            all_new_tools.append(tool_dict)
        
        if all_new_tools:
            print(f"🔄 Adding {len(all_new_tools)} new tools to ChromaDB...")
            success = await store.add_tools(all_new_tools)
            
            if success:
                print(f"✅ Successfully loaded {len(all_new_tools)} new tools into ChromaDB")
            else:
                print("❌ Failed to load tools into ChromaDB")
        
    except Exception as e:
        print(f"❌ Error loading into ChromaDB: {e}")

async def main():
    """Main function to check and update packages."""
    print("🔍 Package Update Checker")
    print("=" * 50)
    print("This script checks for new BioPython and Bioconductor packages")
    print("and updates your data files, reports, and ChromaDB if even 1 new package is found.\n")
    
    # Check BioPython packages
    new_biopython_tools, all_biopython_tools = await check_biopython_packages()
    
    # Check Bioconductor packages  
    new_bioconductor_tools, all_bioconductor_tools = await check_bioconductor_packages()
    
    # Summary
    print("\n📊 Summary")
    print("-" * 20)
    print(f"New BioPython packages: {len(new_biopython_tools)}")
    print(f"New Bioconductor packages: {len(new_bioconductor_tools)}")
    total_new = len(new_biopython_tools) + len(new_bioconductor_tools)
    
    if total_new >= 1:
        print(f"🔔 TOTAL NEW PACKAGES FOUND: {total_new}")
        print("📝 Updates available for JSON files and reports")
    else:
        print("✅ No new packages found - everything is up to date")
    
    # Update JSON files if any new packages found (even just 1)
    if len(new_biopython_tools) >= 1 or len(new_bioconductor_tools) >= 1:
        print("\n📝 Update JSON Data Files & Reports")
        print("-" * 40)
        
        # Update BioPython JSON and report
        if len(new_biopython_tools) >= 1:
            if ask_user(f"Update BioPython JSON file and report with {len(new_biopython_tools)} new package(s)?"):
                biopython_file = "data/biopython_collection/complete_biopython_tools.json"
                biopython_report = "data/biopython_collection/biopython_collection_report.json"
                
                # Convert tools to dict format
                all_tools_dict = []
                for tool in all_biopython_tools:
                    tool_dict = tool.to_dict() if hasattr(tool, 'to_dict') else tool
                    all_tools_dict.append(tool_dict)
                
                # Save data and update report
                if save_updated_data(all_tools_dict, biopython_file):
                    update_report_file(all_tools_dict, biopython_report, "Biopython")
        
        # Update Bioconductor JSON and report
        if len(new_bioconductor_tools) >= 1:
            if ask_user(f"Update Bioconductor JSON file and report with {len(new_bioconductor_tools)} new package(s)?"):
                bioconductor_file = "data/bioconductor_collection/complete_bioconductor_tools.json"
                bioconductor_report = "data/bioconductor_collection/bioconductor_collection_report.json"
                
                # Convert tools to dict format
                all_tools_dict = []
                for tool in all_bioconductor_tools:
                    tool_dict = tool.to_dict() if hasattr(tool, 'to_dict') else tool
                    all_tools_dict.append(tool_dict)
                
                # Save data and update report
                if save_updated_data(all_tools_dict, bioconductor_file):
                    update_report_file(all_tools_dict, bioconductor_report, "Bioconductor")
        
        # Load into ChromaDB
        print("\n💾 ChromaDB Update")
        print("-" * 20)
        if ask_user("Load newly found tools into ChromaDB?"):
            await update_chromadb(new_biopython_tools, new_bioconductor_tools)
    
    else:
        print("\n✅ All packages are up to date!")
        print("No new packages found - your data and reports are current.")
    
    print("\n🎉 Package check complete!")

if __name__ == "__main__":
    asyncio.run(main())