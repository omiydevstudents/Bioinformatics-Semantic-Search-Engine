# src/scripts/load_bioconductor_tools.py

"""
Bioconductor Tools Integration Script - Fixed Version
Loads ALL 2300+ Bioconductor packages into your existing ChromaDB.
Follows the exact plan specified by the user.

Usage:
    python src/scripts/load_bioconductor_tools.py

This will:
1. Follow user's exact plan to scrape Bioconductor packages
2. Load them into your existing ChromaDB using SemanticSearchStore
3. Test search quality with Bioconductor-specific queries
4. Generate a comprehensive report

Author: Nitanshu (ChromaDB & RAG Pipeline)
"""

import asyncio
import sys
import os
from pathlib import Path
import time

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

async def main():
    """Main function to load Bioconductor tools."""
    
    print("🧬 Bioconductor Tools Integration for ChromaDB")
    print("=" * 55)
    print("Following user's exact plan:")
    print("1. Use official PACKAGES file for accurate package discovery")
    print("2. Visit each package page to extract detailed info")
    print("3. Load all packages into ChromaDB")
    print("This will take 5-10 minutes to complete (2300+ packages).\n")
    
    try:
        # Check internet connectivity first
        print("🔍 Checking internet connectivity...")
        try:
            import requests
            test_response = requests.get("https://bioconductor.org", timeout=10)
            if test_response.status_code == 200:
                print(f"✅ Bioconductor website accessible!")
            else:
                print(f"⚠️  Bioconductor website returned status {test_response.status_code}")
        except Exception as e:
            print(f"❌ Internet connectivity issue: {e}")
            print("Please check your internet connection and try again.")
            return False
        
        # Import required modules - FIXED: Use correct class name
        try:
            from bioconductor_tools_collector import FixedBioconductorCollector
            print("✅ Bioconductor collector imported successfully")
        except ImportError as e:
            print(f"❌ Failed to import Bioconductor collector: {e}")
            print("Make sure bioconductor_tools_collector.py is in the scripts folder")
            return False
        
        try:
            from src.db.chroma_store import SemanticSearchStore
            print("✅ ChromaDB store imported successfully")
        except ImportError as e:
            print(f"❌ Failed to import ChromaDB store: {e}")
            print("Make sure your ChromaDB dependencies are installed")
            return False
        
        # Start data collection
        start_time = time.time()
        
        print("\n📊 Starting Bioconductor package discovery...")
        print("🕐 Following FIXED method:")
        print("   Step 1: Fetching official PACKAGES file from Bioconductor...")
        print("   Step 2: Extracting all package names (reliable approach)...")
        print("   Step 3: Visiting individual package pages...")
        print("   Step 4: Extracting version, description, author, maintainer...")
        print("   Step 5: Processing all packages...")
        print("\n⏱️  This may take 5-10 minutes due to respectful rate limiting...")
        
        collector = FixedBioconductorCollector()  # FIXED: Use correct class name
        bioconductor_tools = await collector.collect_and_save()
        
        if not bioconductor_tools:
            print("❌ No Bioconductor packages found!")
            print("🔍 Debugging information:")
            print("   - Check if bioconductor.org is accessible")
            print("   - Verify the PACKAGES file is available")
            print("   - Try running the collector standalone for more details")
            return False
        
        collection_time = time.time() - start_time
        print(f"✅ Discovered {len(bioconductor_tools)} Bioconductor packages in {collection_time:.1f}s")
        
        # Initialize ChromaDB store
        print("\n💾 Initializing ChromaDB store...")
        try:
            store = SemanticSearchStore()
            print("✅ ChromaDB store initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize ChromaDB store: {e}")
            return False
        
        # Check existing data
        try:
            existing_count = store.collection.count()
            print(f"📊 Existing tools in database: {existing_count}")
        except Exception as e:
            print(f"⚠️  Could not check existing data: {e}")
            existing_count = 0
        
        # Add all Bioconductor tools
        print("🔄 Adding Bioconductor packages to ChromaDB...")
        integration_start = time.time()
        
        try:
            success = await store.add_tools(bioconductor_tools)
        except Exception as e:
            print(f"❌ Error during ChromaDB integration: {e}")
            return False
        
        integration_time = time.time() - integration_start
        
        if success:
            try:
                new_count = store.collection.count()
                added_count = new_count - existing_count
            except:
                added_count = len(bioconductor_tools)
                new_count = existing_count + added_count
            
            print(f"✅ Successfully added {added_count} new packages!")
            print(f"⏱️  Integration completed in {integration_time:.1f} seconds")
            print(f"📊 Total tools in database: {new_count}")
            print(f"🚀 Packages per second: {len(bioconductor_tools) / integration_time:.1f}")
            
            # Test search quality
            await test_bioconductor_search(store)
            
            # Show success summary
            show_success_summary(bioconductor_tools, collection_time, integration_time)
            
            return True
        else:
            print("❌ Failed to integrate packages into ChromaDB")
            return False
            
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_bioconductor_search(store):
    """Test search quality with Bioconductor-specific queries."""
    print("\n🧪 Testing search quality with Bioconductor packages...")
    
    test_queries = [
        ("DESeq2 differential expression", "RNA-seq analysis"),
        ("limma microarray analysis", "Statistical analysis"),  
        ("Biostrings sequence manipulation", "Sequence tools"),
        ("ggplot2 visualization", "Plotting tools"),
        ("GenomicRanges genomic intervals", "Genomics infrastructure"),
        ("edgeR differential expression", "RNA-seq analysis"),
        ("ComplexHeatmap visualization", "Heatmap tools"),
        ("ChIPseeker peak annotation", "ChIP-seq analysis"),
        ("clusterProfiler enrichment", "Pathway analysis"),
        ("GSVA gene set analysis", "Gene set tools")
    ]
    
    excellent_count = 0
    total_results = 0
    
    for query, description in test_queries:
        try:
            results = await store.semantic_search(query, n_results=3)
            total_results += len(results)
            
            if results and len(results) >= 1:
                # Check if results are Bioconductor-related
                bioc_results = [r for r in results if 'bioconductor' in r.get('source', '').lower()]
                top_score = results[0]['relevance_score']
                
                if len(bioc_results) >= 1 and top_score > 0.3:
                    status = "✅"
                    excellent_count += 1
                elif len(results) >= 2:
                    status = "✔️ "
                else:
                    status = "⚠️ "
            else:
                status = "❌"
            
            print(f"  {status} '{query}' → {len(results)} results")
            if results:
                top = results[0]
                print(f"      Top: {top['name']} (Score: {top['relevance_score']:.2f})")
        except Exception as e:
            print(f"  ❌ '{query}' → Error: {e}")
    
    quality_pct = (excellent_count / len(test_queries)) * 100
    print(f"\n📈 Search Quality: {excellent_count}/{len(test_queries)} excellent ({quality_pct:.0f}%)")
    print(f"📊 Total results found: {total_results}")

def show_success_summary(tools, collection_time, integration_time):
    """Show final success summary."""
    total_time = collection_time + integration_time
    
    print(f"\n🎉 Bioconductor integration completed successfully!")
    print(f"📊 Summary:")
    print(f"   • Bioconductor packages collected: {len(tools)}")
    print(f"   • Collection time: {collection_time:.1f} seconds ({collection_time/60:.1f} minutes)")
    print(f"   • Integration time: {integration_time:.1f} seconds") 
    print(f"   • Total time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    print(f"   • Performance: {len(tools) / total_time:.1f} packages/second")
    
    # Count categories
    categories = {}
    for tool in tools:
        cat = tool.get('category', 'Unknown')
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"\n🏷️  Categories discovered: {len(categories)}")
    top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:8]
    for cat, count in top_categories:
        print(f"   • {cat}: {count} packages")
    
    # Show examples of popular packages that might be found
    popular_patterns = ['DESeq2', 'limma', 'edgeR', 'Biostrings', 'GenomicRanges', 'ggplot2', 'dplyr']
    found_popular = []
    for tool in tools:
        tool_name = tool['name']
        if any(pattern.lower() in tool_name.lower() for pattern in popular_patterns):
            found_popular.append(tool_name)
    
    if found_popular:
        print(f"\n🌟 Popular packages found: {', '.join(found_popular[:8])}")
    
    # Show sample packages
    print(f"\n📦 Sample packages:")
    for i, tool in enumerate(tools[:5]):
        print(f"   {i+1}. {tool['name']}: {tool['description'][:50]}...")
    
    print(f"\n🎯 Next Steps:")
    print("1. Test with your agent: Results now include all Bioconductor packages")
    print("2. Search for R packages: Try 'DESeq2', 'limma', 'Biostrings'")
    print("3. Run performance tests: python src/scripts/comprehensive_test.py") 
    print("4. Check detailed report: data/bioconductor_collection/")
    print("\n🚀 Your ChromaDB now contains the complete Bioconductor ecosystem!")
    print("💡 You can search for both Python (Biopython) and R (Bioconductor) tools!")

def check_prerequisites():
    """Check if all required dependencies are available."""
    missing_deps = []
    
    # Check core dependencies
    dependencies = [
        ("requests", "requests"),
        ("beautifulsoup4", "bs4"),
        ("chromadb", "chromadb"),
        ("langchain-community", "langchain_community")
    ]
    
    for dep_name, import_name in dependencies:
        try:
            __import__(import_name)
        except ImportError:
            missing_deps.append(dep_name)
    
    if missing_deps:
        print("❌ Missing dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\nInstall missing dependencies with:")
        print(f"  pip install {' '.join(missing_deps)}")
        return False
    
    return True

def check_file_structure():
    """Check if required files are in the correct locations."""
    script_dir = Path(__file__).parent
    
    required_files = [
        ("bioconductor_tools_collector.py", "The Bioconductor package collector"),
        ("../db/chroma_store.py", "ChromaDB store implementation")
    ]
    
    missing_files = []
    
    for filename, description in required_files:
        file_path = script_dir / filename
        if not file_path.exists():
            missing_files.append((filename, description))
    
    if missing_files:
        print("❌ Missing required files:")
        for filename, description in missing_files:
            print(f"  - {filename}: {description}")
        return False
    
    return True

def show_integration_info():
    """Show information about the integration process."""
    print("📋 Bioconductor Integration Information:")
    print("=" * 50)
    print("🎯 FIXED Method Being Used:")
    print("   1. Fetch official PACKAGES file from Bioconductor")
    print("   2. Extract all package names (reliable & accurate)")
    print("   3. Visit each package page following your URL pattern")
    print("   4. Extract: Bioconductor version, description, author, maintainer")
    print("   5. Process all ~2340 packages")
    
    print("\n📊 Expected Data Format (like Biopython example):")
    print("   • name: Package name (e.g., 'DESeq2')")
    print("   • category: Categorized automatically")
    print("   • description: From package page")
    print("   • features: Extracted from description")
    print("   • documentation: Package HTML page URL")
    print("   • source: 'Bioconductor'")
    print("   • version: Bioconductor version (e.g., '3.21')")
    print("   • programming_language: 'R'")
    print("   • license: 'Artistic-2.0'")
    print("   • installation_guide: 'BiocManager::install(\"PackageName\")'")
    print("   • tool_type: 'package'")
    print("   • full_name: Same as name for Bioconductor")
    
    print("\n⏱️  Expected timeline:")
    print("   • Package discovery: 8-15 minutes (2300+ packages with rate limiting)")
    print("   • ChromaDB integration: 30-60 seconds")
    print("   • Total time: 9-16 minutes")
    
    print("\n🔄 Rate limiting:")
    print("   • Respectful crawling: 0.1 seconds per request")
    print("   • Batch processing with 2-second delays")
    print("   • Server-friendly scraping practices")
    
    print("\n✨ FIXED Method Advantages:")
    print("   ✅ Uses official Bioconductor PACKAGES file")
    print("   ✅ Much more reliable than HTML table parsing")
    print("   ✅ Gets accurate package names")
    print("   ✅ Follows your exact URL pattern")
    print("   ✅ Extracts author and maintainer as requested")
    
    response = input("\n❓ Continue with integration? (y/N): ").strip().lower()
    return response in ['y', 'yes']

if __name__ == "__main__":
    print("🔍 Checking prerequisites and file structure...")
    
    if not check_prerequisites():
        print("\n💡 Install missing dependencies first:")
        print("  pip install requests beautifulsoup4 chromadb langchain-community")
        sys.exit(1)
    
    if not check_file_structure():
        print("\n📁 File Structure Help:")
        print("Your scripts folder should contain:")
        print("  src/scripts/")
        print("  ├── load_bioconductor_tools.py         # This file")
        print("  ├── bioconductor_tools_collector.py    # The fixed collector")
        print("  ├── load_biopython_tools.py            # Existing Biopython loader")
        print("  └── test_chroma_setup.py               # Existing test file")
        print("\nAnd your db folder should contain:")
        print("  src/db/")
        print("  └── chroma_store.py                     # ChromaDB implementation")
        sys.exit(1)
    
    print("✅ All prerequisites and files found!")
    
    # Show integration information and get user confirmation
    if not show_integration_info():
        print("❌ Integration cancelled by user.")
        sys.exit(0)
    
    print("\n🚀 Starting Bioconductor integration...")
    
    # Run the integration
    success = asyncio.run(main())
    
    if not success:
        print("\n⚠️  Integration failed. Check the error messages above.")
        print("\n🔧 Troubleshooting Tips:")
        print("1. Ensure internet connectivity to bioconductor.org")
        print("2. Check if the PACKAGES file is accessible")
        print("3. Try running bioconductor_tools_collector.py standalone")
        print("4. Check ChromaDB dependencies are properly installed")
        sys.exit(1)
    else:
        print("\n🌟 SUCCESS: Bioconductor packages successfully integrated!")
        print("🎯 Using FIXED method:")
        print("   ✅ Used official PACKAGES file for package discovery")
        print("   ✅ Extracted packages reliably")  
        print("   ✅ Visited individual package pages")
        print("   ✅ Extracted version, description, author, maintainer")
        print("   ✅ Added all packages to ChromaDB")
        print("\n🔍 Your ChromaDB now contains both:")
        print("   • Biopython tools (Python packages)")
        print("   • Bioconductor packages (R packages)")
        print(f"   • Total: Comprehensive bioinformatics toolkit!")