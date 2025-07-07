#!/usr/bin/env python3
"""
Package Update Checker - Updated with Complete Bio.tools Support
Checks for new BioPython, Bioconductor, and Bio.tools packages and updates the system.

Usage:
    python src/scripts/check_and_update_packages.py

What it does:
1. Uses existing scrapers to get current packages
2. Compares with existing JSON data files  
3. Shows new packages found
4. Asks user to update JSON files
5. Asks user to load new packages into ChromaDB

Now includes complete bio.tools support with full API registry scanning!
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
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        # Create basic report structure
        report = {
            "collection_date": "updated",
            "source": source_name,
            "total_tools": len(tools_data),
            "collection_method": "update_checker",
            "status": "completed"
        }
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✅ Updated report file: {report_path}")
        return True
    except Exception as e:
        print(f"❌ Error updating report {report_path}: {e}")
        return False

def ask_user(question):
    """Ask user a yes/no question and return boolean result."""
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
    """Check for new bio.tools entries - FULL API SCAN."""
    print("\n🔧 Checking bio.tools entries...")
    print("-" * 40)
    
    # Check if we have existing bio.tools data
    biotools_dir = Path("data/biotools_collection")
    existing_tools = []
    existing_ids = set()
    
    if biotools_dir.exists():
        # Load from all existing JSON files
        tool_files = list(biotools_dir.glob("complete_biotools_tools_*.json"))
        if tool_files:
            print(f"📁 Loading existing data from {len(tool_files)} files...")
            for file_path in tool_files:
                try:
                    with open(file_path, 'r') as f:
                        file_tools = json.load(f)
                        existing_tools.extend(file_tools)
                        for tool in file_tools:
                            if 'biotoolsID' in tool:
                                existing_ids.add(tool['biotoolsID'])
                except Exception as e:
                    print(f"   Warning: Error loading {file_path.name}: {e}")
            
            print(f"✅ Loaded {len(existing_tools)} existing bio.tools entries")
        else:
            print("📄 No existing bio.tools data found")
    else:
        print("📄 No existing bio.tools data directory found")
    
    # FIXED: Check ENTIRE API registry using correct Bio.tools API format
    try:
        import requests
        
        print("🔍 Checking bio.tools API for new entries (FULL SCAN)...")
        print("🚨 WARNING: This will scan the ENTIRE bio.tools registry!")
        print("⏱️  This may take 10-30 minutes depending on API response time...")
        
        if not ask_user("Proceed with full bio.tools API scan?"):
            print("⏭️  Skipped full bio.tools scan (user choice)")
            return [], False
        
        # Set up proper session with correct headers (following biotools_collector pattern)
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'BioToolsAPITest/1.0 (Python; bioinformatics tool aggregator)',
            'Accept': 'application/json'
        })
        
        new_tools = []
        checked_ids = set()
        page = 1
        total_pages_scanned = 0
        
        print("🔄 Starting full API scan...")
        
        while True:
            try:
                # FIXED: Use correct Bio.tools API URL format
                url = f"https://bio.tools/api/tool/?page={page}&format=json"
                response = session.get(url, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    # FIXED: Use 'list' instead of 'results' (correct Bio.tools API response structure)
                    tools = data.get('list', [])
                    
                    if not tools:
                        print(f"   📄 Page {page}: No more tools found - End of API")
                        break
                    
                    print(f"   📄 Page {page}: Processing {len(tools)} tools...")
                    total_pages_scanned += 1
                    
                    for tool_data in tools:
                        tool_id = tool_data.get('biotoolsID', '')
                        name = tool_data.get('name', '').lower()
                        homepage = tool_data.get('homepage', '').lower()
                        
                        # Skip if we've already checked this ID
                        if tool_id in checked_ids:
                            continue
                            
                        # Skip if it's already in our database
                        if tool_id in existing_ids:
                            checked_ids.add(tool_id)
                            continue
                        
                        # Skip Biopython and Bioconductor tools (already handled separately)
                        if not ('biopython' in name or 'bio-python' in name or 
                                'bioconductor' in name or 'bioconductor.org' in homepage):
                            
                            new_tools.append({
                                'name': tool_data.get('name', ''),
                                'biotoolsID': tool_id,
                                'description': tool_data.get('description', '')[:200] + '...' if tool_data.get('description', '') else '',
                                'homepage': tool_data.get('homepage', ''),
                                'source': 'bio.tools'
                            })
                            checked_ids.add(tool_id)
                    
                    # Check if there's a next page
                    if not data.get('next'):
                        print(f"   ✅ Reached end of API at page {page}")
                        break
                    
                    page += 1
                    
                    # Progress update every 50 pages
                    if page % 50 == 0:
                        print(f"   📊 Progress: Scanned {total_pages_scanned} pages, found {len(new_tools)} new tools so far...")
                    
                    # FIXED: Add polite delay between requests (following biotools_collector pattern)
                    import time
                    time.sleep(1.0)  # 1 second delay to be respectful to Bio.tools API
                        
                else:
                    print(f"   ❌ API request failed with status {response.status_code}")
                    break
                    
            except Exception as e:
                print(f"   ⚠️  Error on page {page}: {e}")
                print(f"   🔄 Continuing scan from page {page + 1}...")
                page += 1
                continue
        
        print(f"\n📊 Full bio.tools API scan completed!")
        print(f"   • Pages scanned: {total_pages_scanned}")
        print(f"   • Total tools checked: {len(checked_ids)}")
        print(f"   • New tools found: {len(new_tools)}")
        
        if new_tools:
            print(f"🆕 Found {len(new_tools)} new bio.tools entries:")
            for tool in new_tools[:10]:
                print(f"   • {tool['name']} ({tool['biotoolsID']})")
            if len(new_tools) > 10:
                print(f"   ... and {len(new_tools) - 10} more")
        else:
            print("✅ No new bio.tools entries found")
        
        # Return new tools and indicate whether update is complete
        return new_tools, True
        
    except Exception as e:
        print(f"❌ Error checking bio.tools: {e}")
        return [], False

async def update_chromadb(new_biopython_tools, new_bioconductor_tools, new_biotools=None):
    """Load new tools into ChromaDB."""
    # FIXED: Calculate total including bio.tools
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
    """Run a full bio.tools update using the dedicated collector."""
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
    print("  • Bio.tools (FULL API registry scan)")
    print("and updates your data files, reports, and ChromaDB.\n")
    
    # Check BioPython packages
    new_biopython_tools, all_biopython_tools = await check_biopython_packages()
    
    # Check Bioconductor packages  
    new_bioconductor_tools, all_bioconductor_tools = await check_bioconductor_packages()
    
    # FIXED: Check bio.tools with full API scan
    new_biotools_sample, full_scan_completed = await check_biotools_packages()
    
    # Summary - INCLUDING BIO.TOOLS IN MAIN COUNT
    print("\n📊 Summary")
    print("-" * 20)
    print(f"New BioPython packages: {len(new_biopython_tools)}")
    print(f"New Bioconductor packages: {len(new_bioconductor_tools)}")
    print(f"New bio.tools entries: {len(new_biotools_sample)}")
    
    # FIXED: Include bio.tools in total count
    total_new = len(new_biopython_tools) + len(new_bioconductor_tools) + len(new_biotools_sample)
    
    if total_new > 0:
        print(f"🔔 {total_new} total new tools found!")
    else:
        print("✅ No new packages found - everything is up to date")
    
    # FIXED: Update JSON files for ALL package types when ANY new tools found
    if total_new > 0:
        print("\n📝 Update JSON Data Files & Reports")
        print("-" * 40)
        
        # Update BioPython JSON and report
        if len(new_biopython_tools) > 0:
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
        if len(new_bioconductor_tools) > 0:
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
        
        # FIXED: Save bio.tools findings
        if len(new_biotools_sample) > 0:
            if ask_user(f"Save {len(new_biotools_sample)} newly found bio.tools entries to JSON?"):
                biotools_file = f"data/biotools_collection/new_biotools_scan_{len(new_biotools_sample)}.json"
                biotools_report = "data/biotools_collection/scan_biotools_report.json"
                
                if save_updated_data(new_biotools_sample, biotools_file):
                    update_report_file(new_biotools_sample, biotools_report, "bio.tools (scan)")
        
        # FIXED: ChromaDB Update - Ask for ANY new tools (including single tool)
        print("\n💾 ChromaDB Update")
        print("-" * 20)
        print(f"Found {total_new} new tools total")
        
        # FIXED: Always ask to load into ChromaDB if ANY new tools found (>=1)
        if ask_user(f"Load {total_new} newly found tool(s) into ChromaDB?"):
            await update_chromadb(new_biopython_tools, new_bioconductor_tools, new_biotools_sample)
    
    # Handle bio.tools full update as alternative option
    if not full_scan_completed and total_new == 0:
        print("\n🔧 Bio.tools Full Update Option")
        print("-" * 40)
        print("💡 No quick scan was performed.")
        print("   For comprehensive bio.tools update, use the dedicated collector.")
        
        if ask_user("Run full bio.tools update (30-60 minutes) using dedicated collector?"):
            new_biotools_full = await run_full_biotools_update()
            
            # Load full bio.tools data into ChromaDB
            if new_biotools_full and ask_user(f"Load {len(new_biotools_full)} bio.tools entries into ChromaDB?"):
                await update_chromadb([], [], new_biotools_full)
    
    print("\n🎉 Package check complete!")
    print("\n💡 Tips:")
    print("  • Run this script weekly to stay up-to-date")
    print("  • For dedicated bio.tools update: python src/scripts/load_biotools_tools.py")
    print("  • Check reports in data/*/collection_report.json for statistics")
    print("  • Full bio.tools scan may take 10-30 minutes but finds ALL new tools")

if __name__ == "__main__":
    asyncio.run(main())