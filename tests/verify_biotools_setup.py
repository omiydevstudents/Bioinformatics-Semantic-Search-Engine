#!/usr/bin/env python3
"""
Verify Bio.tools Setup
Quick script to verify all bio.tools components are properly configured.
"""

import os
import sys
from pathlib import Path
import json

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def check_file_exists(file_path, description):
    """Check if a file exists."""
    if Path(file_path).exists():
        print(f"{GREEN}✓{RESET} {description} found at: {file_path}")
        return True
    else:
        print(f"{RED}✗{RESET} {description} NOT FOUND at: {file_path}")
        return False

def check_data_files():
    """Check if bio.tools data files exist."""
    print(f"\n{BLUE}Checking Bio.tools Data Files:{RESET}")
    
    data_dir = Path("data/biotools_collection")
    files_ok = True
    
    if data_dir.exists():
        print(f"{GREEN}✓{RESET} Bio.tools data directory exists: {data_dir}")
        
        # Check for data files (multiple JSON files)
        tool_files = sorted(data_dir.glob("complete_biotools_tools_*.json"))
        report_file = data_dir / "biotools_collection_report.json"
        
        if tool_files:
            print(f"{GREEN}✓{RESET} Found {len(tool_files)} tool data files")
            total_tools = 0
            biopython_count = 0
            bioconductor_count = 0
            
            for file_path in tool_files:
                try:
                    with open(file_path, 'r') as f:
                        tools = json.load(f)
                        total_tools += len(tools)
                        print(f"  → {file_path.name}: {len(tools)} tools")
                        
                        # Check for excluded tools
                        for t in tools:
                            if 'biopython' in t.get('name', '').lower():
                                biopython_count += 1
                            if 'bioconductor' in t.get('name', '').lower():
                                bioconductor_count += 1
                        
                except Exception as e:
                    print(f"{RED}✗{RESET} Error reading {file_path.name}: {e}")
                    files_ok = False
            
            print(f"  → Total tools across all files: {total_tools}")
            
            if biopython_count > 0 or bioconductor_count > 0:
                print(f"{YELLOW}⚠{RESET}  Warning: Found {biopython_count} Biopython and {bioconductor_count} Bioconductor tools")
                print(f"  These should have been excluded!")
        else:
            print(f"{YELLOW}⚠{RESET}  Tool data files not found - run load_biotools_tools.py first")
            files_ok = False
        
        if report_file.exists():
            print(f"{GREEN}✓{RESET} Report file exists")
            try:
                with open(report_file, 'r') as f:
                    report = json.load(f)
                    summary = report.get('collection_summary', {})
                    print(f"  → Total tools: {summary.get('total_tools', 0)}")
                    print(f"  → Excluded Biopython: {summary.get('excluded_biopython', 0)}")
                    print(f"  → Excluded Bioconductor: {summary.get('excluded_bioconductor', 0)}")
            except Exception as e:
                print(f"{RED}✗{RESET} Error reading report file: {e}")
        else:
            print(f"{YELLOW}⚠{RESET}  Report file not found")
    else:
        print(f"{YELLOW}⚠{RESET}  Bio.tools data directory does not exist yet")
        print(f"  → Run load_biotools_tools.py to create it")
        files_ok = False
    
    return files_ok

def check_scripts():
    """Check if all required scripts exist."""
    print(f"\n{BLUE}Checking Required Scripts:{RESET}")
    
    scripts_dir = Path("src/scripts")
    all_ok = True
    
    required_scripts = [
        ("biotools_collector.py", "Bio.tools collector"),
        ("load_biotools_tools.py", "Bio.tools loader"),
        ("check_and_update_packages.py", "Update checker")
    ]
    
    # Check test script separately (in tests folder)
    test_script_path = Path("tests/test_biotools_api.py")
    if not check_file_exists(test_script_path, "Bio.tools API test"):
        all_ok = False
    
    for script_name, description in required_scripts:
        script_path = scripts_dir / script_name
        if not check_file_exists(script_path, description):
            all_ok = False
    
    return all_ok

def check_other_collections():
    """Check status of other collections."""
    print(f"\n{BLUE}Checking Other Collections:{RESET}")
    
    collections = [
        ("data/biopython_collection", "Biopython"),
        ("data/bioconductor_collection", "Bioconductor")
    ]
    
    for collection_dir, name in collections:
        if Path(collection_dir).exists():
            tools_file = Path(collection_dir) / f"complete_{name.lower()}_tools.json"
            if tools_file.exists():
                try:
                    with open(tools_file, 'r') as f:
                        tools = json.load(f)
                        print(f"{GREEN}✓{RESET} {name} collection: {len(tools)} tools")
                except:
                    print(f"{YELLOW}⚠{RESET}  {name} collection exists but couldn't read data")
            else:
                print(f"{YELLOW}⚠{RESET}  {name} collection directory exists but no data file")
        else:
            print(f"{YELLOW}⚠{RESET}  {name} collection not found")

def check_chromadb():
    """Check if ChromaDB is accessible."""
    print(f"\n{BLUE}Checking ChromaDB:{RESET}")
    
    try:
        # Add paths
        project_root = Path(__file__).parent.parent
        sys.path.append(str(project_root))
        
        from src.db.chroma_store import SemanticSearchStore
        
        store = SemanticSearchStore()
        count = store.collection.count()
        print(f"{GREEN}✓{RESET} ChromaDB accessible - contains {count} tools")
        return True
    except Exception as e:
        print(f"{RED}✗{RESET} ChromaDB error: {e}")
        return False

def main():
    """Run all checks."""
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Bio.tools Setup Verification{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    # Check scripts
    scripts_ok = check_scripts()
    
    # Check data files
    data_ok = check_data_files()
    
    # Check other collections
    check_other_collections()
    
    # Check ChromaDB
    chromadb_ok = check_chromadb()
    
    # Summary
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Summary:{RESET}")
    
    if scripts_ok and chromadb_ok:
        if data_ok:
            print(f"{GREEN}✓ All systems ready!{RESET} Bio.tools integration is complete.")
            print("\nNext steps:")
            print("1. Run test queries to verify search quality")
            print("2. Use check_and_update_packages.py to keep data current")
        else:
            print(f"{YELLOW}⚠ Setup incomplete.{RESET} Run these commands:")
            print("\n1. First, test the API:")
            print("   python tests/test_biotools_api.py")
            print("\n2. Then load bio.tools data:")
            print("   python src/scripts/load_biotools_tools.py")
    else:
        print(f"{RED}✗ Setup issues detected.{RESET} Please check the errors above.")
        
        if not scripts_ok:
            print("\nMake sure all scripts are in the correct locations:")
            print("  src/scripts/:")
            print("    - biotools_collector.py")
            print("    - load_biotools_tools.py")
            print("  tests/:")
            print("    - test_biotools_api.py")

if __name__ == "__main__":
    main()