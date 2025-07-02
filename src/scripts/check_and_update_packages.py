#!/usr/bin/env python3
"""
Package Update Checker - Updated with Bio.tools Support
Checks for new BioPython, Bioconductor, and Bio.tools packages and updates the system.

Usage:
    python src/scripts/check_and_update_packages.py

What it does:
1. Uses existing scrapers to get current packages
2. Compares with existing JSON data files  
3. Shows new packages found
4. Asks user to update JSON files
5. Asks user to load new packages into ChromaDB

Now includes bio.tools support!
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
        
        # Add source-specific info
        if source_name == "bio.tools":
            # Count programming languages for bio.tools
            languages = {}
            for tool in tools_data:
                lang = tool.get('programming_language', 'Not specified')
                for l in lang.split(', '):
                    if l:
                        languages[l] = languages.get(l, 0) + 1
            report["top_languages"] = sorted(languages.items(), key=lambda x: x[1], reverse=True)[:10]
        
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

async def check_biotools_packages():
    """Check for new bio.tools entries (complete check)."""
    print("\n🔧 Checking bio.tools entries...")
    print("-" * 40)
    
    # Path to bio.tools data directory
    biotools_dir = Path("data/biotools_collection")
    
    # Load existing data from multiple files
    existing_tools = []
    existing_ids = set()
    
    if biotools_dir.exists():
        tool_files = sorted(biotools_dir.glob("complete_biotools_tools_*.json"))
        if tool_files:
            print(f"📁 Found {len(tool_files)} existing bio.tools files")
            for file_path in tool_files:
                try:
                    with open(file_path, 'r') as f:
                        file_tools = json.load(f)
                        existing_tools.extend(file_tools)
                        print(f"✅ Loaded {len(file_tools)} tools from {file_path.name}")
                except Exception as e:
                    print(f"❌ Error reading {file_path.name}: {e}")
            
            existing_ids = set(tool.get('biotoolsID', tool['name']) for tool in existing_tools)
            print(f"📊 Total existing bio.tools entries: {len(existing_tools)}")
        else:
            print("📄 No existing bio.tools data found")
    else:
        print("📄 Bio.tools data directory not found")
    
    # Check all pages for new tools
    print("🔍 Checking for new bio.tools entries...")
    print("   (Checking all pages - this may take a while)")
    
    try:
        import requests
        
        new_tools = []
        checked_ids = set()
        
        # Check all pages
        page = 1
        while True:
            try:
                print(f"   Checking page {page}...")
                response = requests.get(
                    f"https://bio.tools/api/tool/?page={page}&format=json",
                    timeout=30
                )
                if response.status_code == 200:
                    data = response.json()
                    tools_list = data.get('list', [])
                    
                    for tool_data in tools_list:
                        tool_id = tool_data.get('biotoolsID', '')
                        if tool_id and tool_id not in existing_ids and tool_id not in checked_ids:
                            # Check if it's not Biopython or Bioconductor
                            name = tool_data.get('name', '').lower()
                            homepage = tool_data.get('homepage', '').lower()
                            
                            if ('biopython' not in name and 'bio.' not in name and
                                'bioconductor' not in name and 'bioconductor.org' not in homepage):
                                
                                new_tools.append({
                                    'name': tool_data.get('name', ''),
                                    'biotoolsID': tool_id,
                                    'description': tool_data.get('description', '')[:100] + '...'
                                })
                                checked_ids.add(tool_id)
                    
                    if not data.get('next'):
                        break
                    
                    page += 1
                else:
                    break
                    
            except Exception as e:
                print(f"   Warning: Error checking page {page}: {e}")
                break
        
        if new_tools:
            print(f"🆕 Found {len(new_tools)} new bio.tools entries:")
            for tool in new_tools[:10]:
                print(f"   • {tool['name']} ({tool['biotoolsID']})")
            if len(new_tools) > 10:
                print(f"   ... and {len(new_tools) - 10} more")
        else:
            print("✅ No new bio.tools entries found")
        
        # For bio.tools, we return a flag to indicate if full update is needed
        needs_full_update = len(new_tools) > 20  # If many new tools, suggest full update
        
        return new_tools, needs_full_update
        
    except Exception as e:
        print(f"❌ Error checking bio.tools: {e}")
        return [], False

async def update_chromadb(new_biopython_tools, new_bioconductor_tools, new_biotools=None):
    """Load new tools into ChromaDB."""
    total_new_tools = len(new_biopython_tools) + len(new_bioconductor_tools)
    if new_biotools:
        total_new_tools += len(new_biotools)
    
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
        
        # Add bio.tools entries if provided
        if new_biotools:
            for tool in new_biotools:
                all_new_tools.append(tool)
        
        if all_new_tools:
            print(f"🔄 Adding {len(all_new_tools)} new tools to ChromaDB...")
            success = await store.add_tools(all_new_tools)
            
            if success:
                print(f"✅ Successfully loaded {len(all_new_tools)} new tools into ChromaDB")
            else:
                print("❌ Failed to load tools into ChromaDB")
        
    except Exception as e:
        print(f"❌ Error loading into ChromaDB: {e}")

async def run_full_biotools_update():
    """Run a full bio.tools update."""
    print("\n🔄 Running full bio.tools update...")
    print("This will take 30-60 minutes for 30,000+ tools")
    
    try:
        from biotools_collector import BioToolsCollector
        
        collector = BioToolsCollector()
        tools = await collector.collect_and_save()
        
        if tools:
            print(f"✅ Successfully collected {len(tools)} bio.tools entries")
            
            # Update report (data is already saved in chunks by the collector)
            biotools_report = "data/biotools_collection/biotools_collection_report.json"
            update_report_file(tools, biotools_report, "bio.tools")
            
            return tools
        else:
            print("❌ Failed to collect bio.tools entries")
            return []
            
    except Exception as e:
        print(f"❌ Error during bio.tools update: {e}")
        return []

async def main():
    """Main function to check and update packages."""
    print("🔍 Package Update Checker")
    print("=" * 50)
    print("This script checks for new packages from:")
    print("  • BioPython")
    print("  • Bioconductor")
    print("  • Bio.tools (partial check)")
    print("and updates your data files, reports, and ChromaDB.\n")
    
    # Check BioPython packages
    new_biopython_tools, all_biopython_tools = await check_biopython_packages()
    
    # Check Bioconductor packages  
    new_bioconductor_tools, all_bioconductor_tools = await check_bioconductor_packages()
    
    # Check bio.tools (partial)
    new_biotools_sample, needs_biotools_full_update = await check_biotools_packages()
    
    # Summary
    print("\n📊 Summary")
    print("-" * 20)
    print(f"New BioPython packages: {len(new_biopython_tools)}")
    print(f"New Bioconductor packages: {len(new_bioconductor_tools)}")
    print(f"New bio.tools entries detected: {len(new_biotools_sample)} (partial check)")
    
    total_new = len(new_biopython_tools) + len(new_bioconductor_tools)
    
    if total_new >= 1 or new_biotools_sample:
        print(f"🔔 Updates available!")
    else:
        print("✅ No new packages found - everything is up to date")
    
    # Update JSON files if any new packages found
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
        if ask_user("Load newly found packages into ChromaDB?"):
            await update_chromadb(new_biopython_tools, new_bioconductor_tools)
    
    # Handle bio.tools updates separately
    if new_biotools_sample or needs_biotools_full_update:
        print("\n🔧 Bio.tools Updates")
        print("-" * 40)
        
        if needs_biotools_full_update:
            print("⚠️  Many new bio.tools entries detected!")
            print("   A full update is recommended to get all new tools.")
            
            if ask_user("Run full bio.tools update (30-60 minutes)?"):
                new_biotools = await run_full_biotools_update()
                
                if new_biotools and ask_user("Load new bio.tools entries into ChromaDB?"):
                    await update_chromadb([], [], new_biotools)
        else:
            print(f"ℹ️  {len(new_biotools_sample)} new bio.tools entries found in partial check")
            print("   Run 'python src/scripts/load_biotools_tools.py' for a complete update")
    
    print("\n🎉 Package check complete!")
    print("\n💡 Tips:")
    print("  • Run this script weekly to stay up-to-date")
    print("  • For full bio.tools update: python src/scripts/load_biotools_tools.py")
    print("  • Check reports in data/*/collection_report.json for statistics")

if __name__ == "__main__":
    asyncio.run(main())