# src/scripts/test_bioconductor_integration.py

"""
Test Bioconductor Integration - Adjusted for FixedBioconductorCollector
Comprehensive testing for Bioconductor packages in ChromaDB.

Usage:
    python src/scripts/test_bioconductor_integration.py

This tests:
1. Database connectivity with Bioconductor packages
2. Search functionality with R/Bioconductor-specific queries
3. Performance and accuracy with real Bioconductor data
4. Package-specific searches for popular Bioconductor tools

Author: Nitanshu (ChromaDB & RAG Pipeline)
"""

import asyncio
import sys
import os
from pathlib import Path
import time
import statistics

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.db.chroma_store import SemanticSearchStore

class BioconductorTestSuite:
    """Comprehensive test suite for Bioconductor integration using FixedBioconductorCollector."""
    
    def __init__(self):
        self.store = SemanticSearchStore()
        self.test_results = {}
    
    async def test_1_database_state(self):
        """Test 1: Check database state and Bioconductor presence."""
        print("🧪 Test 1: Database State & Bioconductor Presence")
        print("-" * 60)
        
        # Check total count
        total_count = self.store.collection.count()
        print(f"📊 Total tools in database: {total_count}")
        
        # Check for Bioconductor packages - updated to match our collector
        sample_data = self.store.collection.get(limit=200)  # Larger sample for better detection
        bioconductor_count = 0
        bioconductor_packages = []
        
        if sample_data['metadatas']:
            for metadata in sample_data['metadatas']:
                if metadata:
                    source = metadata.get('source', '').lower()
                    # Match the exact source format from our collector
                    if source == 'bioconductor':
                        bioconductor_count += 1
                        bioconductor_packages.append(metadata.get('name', 'Unknown'))
        
        # Estimate total Bioconductor packages
        sample_size = len(sample_data['metadatas']) if sample_data['metadatas'] else 0
        estimated_bioc_total = (bioconductor_count / sample_size) * total_count if sample_size > 0 else 0
        
        print(f"📦 Bioconductor packages in sample: {bioconductor_count}/{sample_size}")
        print(f"📈 Estimated total Bioconductor packages: {estimated_bioc_total:.0f}")
        
        if bioconductor_packages:
            print(f"🌟 Sample Bioconductor packages found:")
            for pkg in bioconductor_packages[:8]:
                print(f"   • {pkg}")
        
        # Determine integration status - adjusted thresholds
        if bioconductor_count >= 20:
            integration_status = "EXCELLENT"
        elif bioconductor_count >= 10:
            integration_status = "GOOD"
        elif bioconductor_count >= 3:
            integration_status = "PARTIAL"
        else:
            integration_status = "NOT_FOUND"
        
        result = {
            "total_count": total_count,
            "bioconductor_sample_count": bioconductor_count,
            "estimated_bioc_total": estimated_bioc_total,
            "integration_status": integration_status,
            "sample_packages": bioconductor_packages[:15]
        }
        
        print(f"📈 Integration Status: {integration_status}")
        
        self.test_results["database_state"] = result
        return result
    
    async def test_2_popular_bioconductor_packages(self):
        """Test 2: Search for popular Bioconductor packages."""
        print("\n🧪 Test 2: Popular Bioconductor Packages Search")
        print("-" * 60)
        
        # Popular Bioconductor packages - realistic expectations
        popular_packages = [
            ("DESeq2", "Differential gene expression analysis"),
            ("limma", "Linear models for microarray analysis"),
            ("edgeR", "Empirical analysis of DGE in RNA-seq"),
            ("Biostrings", "String objects representing biological sequences"),
            ("GenomicRanges", "Representation and manipulation of genomic intervals"),
            ("ComplexHeatmap", "Make complex heatmaps"),
            ("ChIPseeker", "ChIP peak Annotation, Comparison and Visualization"),
            ("clusterProfiler", "Statistical analysis and visualization of functional profiles"),
            ("GSVA", "Gene set variation analysis for microarray and RNA-seq"),
            ("BiocGenerics", "S4 generic functions for Bioconductor"),
            ("S4Vectors", "S4 implementation of vector-like and list-like objects"),
            ("IRanges", "Infrastructure for manipulating intervals on sequences"),
            ("SummarizedExperiment", "Container for representing genomic experiments"),
            ("SingleCellExperiment", "S4 classes for single cell experiments"),
            ("AnnotationDbi", "Manipulation of SQLite-based annotations")
        ]
        
        package_results = []
        found_packages = 0
        
        print("🔍 Searching for popular Bioconductor packages...")
        
        for package_name, description in popular_packages:
            print(f"\n   Testing: {package_name}")
            
            # Search for the package
            results = await self.store.semantic_search(package_name, n_results=5)
            
            # Check if we found the actual package - more flexible matching
            exact_match = any(r['name'].lower() == package_name.lower() for r in results)
            partial_match = any(package_name.lower() in r['name'].lower() for r in results)
            bioc_source = any(r.get('source', '').lower() == 'bioconductor' for r in results)
            
            avg_score = statistics.mean([r['relevance_score'] for r in results[:3]]) if results else 0
            
            # More lenient success criteria
            if exact_match and bioc_source:
                found_packages += 1
                status = "✅ FOUND (Exact)"
            elif partial_match and bioc_source and avg_score > 0.5:
                found_packages += 1
                status = "✅ FOUND (Partial)"
            elif results and avg_score > 0.6:
                status = "✔️  RELATED"
            else:
                status = "❌ MISSING"
            
            result_info = {
                "package": package_name,
                "description": description,
                "found": len(results),
                "exact_match": exact_match,
                "partial_match": partial_match,
                "bioc_source": bioc_source,
                "avg_score": avg_score,
                "status": status,
                "top_result": results[0]['name'] if results else None
            }
            
            package_results.append(result_info)
            
            print(f"      {status} - {len(results)} results, avg score: {avg_score:.2f}")
            if results:
                print(f"      Top: {results[0]['name']} (Score: {results[0]['relevance_score']:.2f})")
                print(f"      Source: {results[0].get('source', 'Unknown')}")
        
        success_rate = (found_packages / len(popular_packages)) * 100
        
        summary = {
            "total_tested": len(popular_packages),
            "found_packages": found_packages,
            "success_rate": success_rate,
            "package_details": package_results
        }
        
        print(f"\n📊 Popular Package Search Summary:")
        print(f"   Packages tested: {len(popular_packages)}")
        print(f"   Packages found: {found_packages}")
        print(f"   Success rate: {success_rate:.1f}%")
        
        self.test_results["popular_packages"] = summary
        return summary
    
    async def test_3_bioconductor_categories(self):
        """Test 3: Test searches by Bioconductor categories."""
        print("\n🧪 Test 3: Bioconductor Category Searches")
        print("-" * 60)
        
        # Bioconductor-specific search queries - adjusted for our categorization
        category_queries = [
            ("RNA-seq differential expression", "RNA-seq Analysis"),
            ("microarray analysis", "Microarray Analysis"),
            ("genomic ranges", "Genomics"),
            ("sequence analysis", "Sequence Analysis"),
            ("gene set enrichment", "Pathway Analysis"),
            ("single cell", "Single Cell Analysis"),
            ("ChIP-seq analysis", "Epigenomics"),
            ("data visualization", "Visualization"),
            ("protein analysis", "Proteomics"),
            ("quality control", "Quality Control"),
            ("statistical analysis", "Statistical Analysis"),
            ("data preprocessing", "Data Preprocessing"),
            ("clustering analysis", "Clustering"),
            ("annotation data", "Annotation"),
            ("workflow analysis", "Workflow")
        ]
        
        category_results = []
        successful_searches = 0
        
        print("🔍 Testing category-based searches...")
        
        for query, expected_category in category_queries:
            print(f"\n   Query: '{query}' (Expected: {expected_category})")
            
            start_time = time.time()
            results = await self.store.semantic_search(query, n_results=5)
            search_time = time.time() - start_time
            
            # Analyze results - focus on Bioconductor packages
            bioc_results = [r for r in results if r.get('source', '').lower() == 'bioconductor']
            avg_score = statistics.mean([r['relevance_score'] for r in results[:3]]) if results else 0
            
            # Check for category matches
            category_matches = 0
            for result in results[:3]:
                result_category = result.get('category', '')
                if any(word in result_category.lower() for word in expected_category.lower().split()):
                    category_matches += 1
            
            # Adjusted success criteria
            if len(bioc_results) >= 1 and avg_score > 0.5:
                successful_searches += 1
                status = "✅"
            elif len(results) >= 3 and avg_score > 0.4:
                status = "✔️ "
            else:
                status = "⚠️ "
            
            result_info = {
                "query": query,
                "expected_category": expected_category,
                "total_results": len(results),
                "bioc_results": len(bioc_results),
                "avg_score": avg_score,
                "search_time": search_time,
                "category_matches": category_matches,
                "status": status
            }
            
            category_results.append(result_info)
            
            print(f"      {status} {len(results)} results ({len(bioc_results)} Bioc), "
                  f"avg score: {avg_score:.2f}, time: {search_time:.3f}s")
            
            if results:
                print(f"      Top: {results[0]['name']} (Score: {results[0]['relevance_score']:.2f})")
                print(f"      Source: {results[0].get('source', 'Unknown')}")
        
        category_success_rate = (successful_searches / len(category_queries)) * 100
        avg_search_time = statistics.mean([r['search_time'] for r in category_results])
        
        summary = {
            "total_queries": len(category_queries),
            "successful_searches": successful_searches,
            "success_rate": category_success_rate,
            "avg_search_time": avg_search_time,
            "category_details": category_results
        }
        
        print(f"\n📊 Category Search Summary:")
        print(f"   Queries tested: {len(category_queries)}")
        print(f"   Successful searches: {successful_searches}")
        print(f"   Success rate: {category_success_rate:.1f}%")
        print(f"   Average search time: {avg_search_time:.3f}s")
        
        self.test_results["category_searches"] = summary
        return summary
    
    async def test_4_installation_and_metadata(self):
        """Test 4: Check if installation guides and metadata are properly stored."""
        print("\n🧪 Test 4: Installation Guides & Metadata")
        print("-" * 60)
        
        # Get a sample of tools to check metadata
        sample_data = self.store.collection.get(limit=50)
        
        bioconductor_tools = []
        if sample_data['metadatas']:
            for i, metadata in enumerate(sample_data['metadatas']):
                if metadata and metadata.get('source', '').lower() == 'bioconductor':
                    # Combine metadata with document content
                    tool_info = metadata.copy()
                    if i < len(sample_data['documents']):
                        tool_info['content'] = sample_data['documents'][i]
                    bioconductor_tools.append(tool_info)
        
        if not bioconductor_tools:
            print("❌ No Bioconductor tools found in sample")
            return {"metadata_check": "FAILED", "sample_tools": []}
        
        print(f"📦 Found {len(bioconductor_tools)} Bioconductor tools in sample")
        
        # Check metadata completeness
        metadata_stats = {
            "has_installation_guide": 0,
            "has_author": 0,
            "has_maintainer": 0,
            "has_version": 0,
            "has_license": 0,
            "has_programming_language": 0,
            "has_proper_category": 0
        }
        
        sample_tools_info = []
        
        for tool in bioconductor_tools[:10]:  # Check first 10 tools
            name = tool.get('name', 'Unknown')
            
            # Check metadata fields
            installation = tool.get('installation_guide', '')
            author = tool.get('author', '')
            maintainer = tool.get('maintainer', '')
            version = tool.get('version', '')
            license_info = tool.get('license', '')
            prog_lang = tool.get('programming_language', '')
            category = tool.get('category', '')
            
            # Count non-empty fields
            if installation and 'BiocManager::install' in installation:
                metadata_stats["has_installation_guide"] += 1
            if author:
                metadata_stats["has_author"] += 1
            if maintainer:
                metadata_stats["has_maintainer"] += 1
            if version and version != '3.21':  # Not just default
                metadata_stats["has_version"] += 1
            if license_info:
                metadata_stats["has_license"] += 1
            if prog_lang == 'R':
                metadata_stats["has_programming_language"] += 1
            if category and category != 'General Bioinformatics':
                metadata_stats["has_proper_category"] += 1
            
            tool_summary = {
                "name": name,
                "author": author[:50] + "..." if len(author) > 50 else author,
                "version": version,
                "category": category,
                "installation": installation[:50] + "..." if len(installation) > 50 else installation
            }
            sample_tools_info.append(tool_summary)
            
            print(f"\n   📦 {name}:")
            print(f"      Author: {author[:50]}{'...' if len(author) > 50 else ''}")
            print(f"      Version: {version}")
            print(f"      Category: {category}")
            print(f"      Installation: {installation[:50]}{'...' if len(installation) > 50 else ''}")
        
        # Calculate completeness percentages
        tool_count = len(bioconductor_tools[:10])
        completeness_percentages = {
            field: (count / tool_count) * 100 
            for field, count in metadata_stats.items()
        }
        
        print(f"\n📊 Metadata Completeness (sample of {tool_count} tools):")
        for field, percentage in completeness_percentages.items():
            status = "✅" if percentage >= 70 else "✔️" if percentage >= 40 else "⚠️"
            print(f"   {status} {field.replace('_', ' ').title()}: {percentage:.0f}%")
        
        avg_completeness = statistics.mean(completeness_percentages.values())
        
        summary = {
            "sample_size": tool_count,
            "metadata_stats": metadata_stats,
            "completeness_percentages": completeness_percentages,
            "avg_completeness": avg_completeness,
            "sample_tools": sample_tools_info,
            "metadata_check": "EXCELLENT" if avg_completeness >= 80 else 
                             "GOOD" if avg_completeness >= 60 else
                             "NEEDS_IMPROVEMENT"
        }
        
        print(f"\n📈 Average metadata completeness: {avg_completeness:.1f}%")
        print(f"🎯 Metadata quality: {summary['metadata_check']}")
        
        self.test_results["metadata_quality"] = summary
        return summary
    
    async def run_all_tests(self):
        """Run the complete Bioconductor test suite."""
        print("🚀 Starting Bioconductor Integration Test Suite")
        print("=" * 70)
        print("Testing ChromaDB integration with FixedBioconductorCollector packages")
        print("=" * 70)
        
        # Test 1: Database state
        await self.test_1_database_state()
        
        # Test 2: Popular packages
        await self.test_2_popular_bioconductor_packages()
        
        # Test 3: Category searches
        await self.test_3_bioconductor_categories()
        
        # Test 4: Metadata quality
        await self.test_4_installation_and_metadata()
        
        # Generate final summary
        await self._generate_final_summary()
        
        return self.test_results
    
    async def _generate_final_summary(self):
        """Generate comprehensive final summary."""
        print("\n🏆 BIOCONDUCTOR INTEGRATION TEST RESULTS")
        print("=" * 70)
        
        # Database Status
        if "database_state" in self.test_results:
            db_results = self.test_results["database_state"]
            print(f"📊 Database Status:")
            print(f"   Total tools: {db_results['total_count']:,}")
            print(f"   Estimated Bioconductor packages: {db_results['estimated_bioc_total']:.0f}")
            print(f"   Integration status: {db_results['integration_status']}")
        
        # Popular Packages
        if "popular_packages" in self.test_results:
            pop_results = self.test_results["popular_packages"]
            print(f"\n🌟 Popular Packages:")
            print(f"   Packages tested: {pop_results['total_tested']}")
            print(f"   Packages found: {pop_results['found_packages']}")
            print(f"   Success rate: {pop_results['success_rate']:.1f}%")
        
        # Category Searches
        if "category_searches" in self.test_results:
            cat_results = self.test_results["category_searches"]
            print(f"\n📂 Category Searches:")
            print(f"   Queries tested: {cat_results['total_queries']}")
            print(f"   Successful searches: {cat_results['successful_searches']}")
            print(f"   Success rate: {cat_results['success_rate']:.1f}%")
            print(f"   Average search time: {cat_results['avg_search_time']:.3f}s")
        
        # Metadata Quality
        if "metadata_quality" in self.test_results:
            meta_results = self.test_results["metadata_quality"]
            print(f"\n📋 Metadata Quality:")
            print(f"   Sample size: {meta_results['sample_size']} tools")
            print(f"   Average completeness: {meta_results['avg_completeness']:.1f}%")
            print(f"   Quality assessment: {meta_results['metadata_check']}")
        
        # Overall Assessment
        overall_grade = self._calculate_overall_grade()
        print(f"\n🎯 OVERALL BIOCONDUCTOR INTEGRATION: {overall_grade}")
        
        if "A" in overall_grade:
            print("🌟 Excellent! Bioconductor packages are well integrated with proper metadata!")
        elif "B" in overall_grade:
            print("👍 Good integration with room for minor improvements.")
        else:
            print("⚠️  Integration may need optimization or more time to collect packages.")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if "database_state" in self.test_results:
            db_status = self.test_results["database_state"]["integration_status"]
            if db_status == "NOT_FOUND":
                print("   - Run the Bioconductor collector: python src/scripts/load_bioconductor_tools.py")
            elif db_status == "PARTIAL":
                print("   - Check if collection was interrupted; may need to re-run collector")
        
        if "popular_packages" in self.test_results:
            pop_rate = self.test_results["popular_packages"]["success_rate"]
            if pop_rate < 50:
                print("   - Popular packages not found; verify package names in collector")
        
        if "metadata_quality" in self.test_results:
            meta_quality = self.test_results["metadata_quality"]["avg_completeness"]
            if meta_quality < 70:
                print("   - Improve metadata extraction in the collector's _extract_package_info method")
        
        print("\n🎉 Bioconductor test suite completed successfully!")
    
    def _calculate_overall_grade(self) -> str:
        """Calculate overall integration grade."""
        scores = []
        
        # Database state score
        if "database_state" in self.test_results:
            db = self.test_results["database_state"]
            if db["integration_status"] == "EXCELLENT":
                scores.append(95)
            elif db["integration_status"] == "GOOD":
                scores.append(80)
            elif db["integration_status"] == "PARTIAL":
                scores.append(60)
            else:
                scores.append(20)
        
        # Popular packages score
        if "popular_packages" in self.test_results:
            pop = self.test_results["popular_packages"]
            scores.append(pop["success_rate"])
        
        # Category searches score
        if "category_searches" in self.test_results:
            cat = self.test_results["category_searches"]
            scores.append(cat["success_rate"])
        
        # Metadata quality score
        if "metadata_quality" in self.test_results:
            meta = self.test_results["metadata_quality"]
            scores.append(meta["avg_completeness"])
        
        if not scores:
            return "INCOMPLETE"
        
        avg_score = statistics.mean(scores)
        
        if avg_score >= 90:
            return "A+ (EXCEPTIONAL)"
        elif avg_score >= 85:
            return "A (EXCELLENT)"
        elif avg_score >= 80:
            return "A- (VERY_GOOD)"
        elif avg_score >= 75:
            return "B+ (GOOD)"
        elif avg_score >= 70:
            return "B (SATISFACTORY)"
        else:
            return "C (NEEDS_IMPROVEMENT)"


async def main():
    """Run the Bioconductor integration test suite."""
    print("🔬 Bioconductor Integration Test Suite")
    print("Testing integration with FixedBioconductorCollector")
    print("=" * 50)
    
    # Initialize test suite
    test_suite = BioconductorTestSuite()
    
    # Check if ChromaDB is available
    try:
        total_count = test_suite.store.collection.count()
        if total_count == 0:
            print("❌ No tools found in ChromaDB!")
            print("🔧 Run: python src/scripts/load_bioconductor_tools.py")
            return False
        
        print(f"✅ ChromaDB connected with {total_count:,} tools")
        print("🔍 Testing Bioconductor integration...\n")
        
        # Run all tests
        results = await test_suite.run_all_tests()
        
        return True
        
    except Exception as e:
        print(f"❌ Error connecting to ChromaDB: {e}")
        print("🔧 Check if ChromaDB is properly initialized")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    
    if success:
        print("\n✅ Bioconductor integration tests completed!")
        print("📋 Results show how well the FixedBioconductorCollector integration is working")
    else:
        print("\n⚠️  Tests could not be completed - check ChromaDB setup.")
        sys.exit(1)