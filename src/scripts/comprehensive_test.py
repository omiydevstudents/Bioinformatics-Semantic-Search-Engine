# src/scripts/comprehensive_test.py

import os
import time
import asyncio
from pathlib import Path
from typing import List, Dict
import statistics
import sys

# Add the project root to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.db.chroma_store import SemanticSearchStore

class ComprehensiveTestSuite:
    """Comprehensive test suite for ChromaDB & RAG Pipeline with Biopython integration."""
    
    def __init__(self, use_main_db: bool = True):
        """Initialize test suite.
        
        Args:
            use_main_db: If True, use main ChromaDB with Biopython tools.
                        If False, create separate test database.
        """
        if use_main_db:
            # Use the main database with 2,390 Biopython tools
            self.store = SemanticSearchStore()
            print("🔬 Testing with main ChromaDB (includes 2,390+ Biopython tools)")
        else:
            # Create separate test database
            self.store = SemanticSearchStore(persist_dir="data/chroma_test")
            print("🔬 Testing with separate test database")
            
        self.performance_results = []
        self.test_results = {}
        self.use_main_db = use_main_db

    async def test_1_database_validation(self):
        """Test 1: Validate the Biopython integration and database state."""
        print("🧪 Test 1: Database Validation & Biopython Integration")
        print("-" * 60)
        
        # Check database size
        collection_count = self.store.collection.count()
        print(f"📊 Total tools in database: {collection_count}")
        
        if self.use_main_db:
            # Validate Biopython integration
            if collection_count >= 2000:
                print("✅ Database contains expected number of tools (2000+)")
                integration_status = "SUCCESS"
            else:
                print(f"⚠️  Database has fewer tools than expected ({collection_count} < 2000)")
                integration_status = "PARTIAL"
        else:
            integration_status = "TEST_DB"
        
        # Test sample Biopython queries
        biopython_queries = [
            "Bio.Seq",
            "Bio.Align",
            "Bio.Blast",
            "Bio.PDB",
            "Bio.Phylo"
        ]
        
        biopython_results = {}
        for query in biopython_queries:
            results = await self.store.semantic_search(query, n_results=3)
            biopython_results[query] = {
                "found": len(results),
                "top_score": results[0]['relevance_score'] if results else 0,
                "top_name": results[0]['name'] if results else "None"
            }
            print(f"🔍 '{query}': {len(results)} results, top: {results[0]['name'] if results else 'None'}")
        
        # Calculate Biopython coverage
        total_bio_results = sum(r["found"] for r in biopython_results.values())
        avg_bio_score = statistics.mean([r["top_score"] for r in biopython_results.values() if r["top_score"] > 0])
        
        result = {
            "collection_count": collection_count,
            "integration_status": integration_status,
            "biopython_queries_tested": len(biopython_queries),
            "total_biopython_results": total_bio_results,
            "average_biopython_score": avg_bio_score,
            "biopython_coverage": "EXCELLENT" if avg_bio_score > 0.8 else "GOOD" if avg_bio_score > 0.6 else "NEEDS_IMPROVEMENT"
        }
        
        print(f"📈 Biopython Integration Summary:")
        print(f"   Status: {integration_status}")
        print(f"   Average relevance score: {avg_bio_score:.3f}")
        print(f"   Coverage assessment: {result['biopython_coverage']}")
        
        self.test_results["database_validation"] = result
        return result

    async def test_2_enhanced_performance_testing(self):
        """Test 2: Enhanced performance testing with Biopython-focused queries."""
        print("\n🧪 Test 2: Enhanced Performance Testing")
        print("-" * 60)
        
        # Bioinformatics-focused test queries
        test_queries = [
            # Core Biopython functionality
            ("Bio.Seq sequence manipulation", "Core sequence operations"),
            ("Bio.Align pairwise alignment", "Sequence alignment"),
            ("Bio.Blast sequence search", "Database searching"),
            ("Bio.PDB protein structure", "Structural analysis"),
            ("Bio.Phylo phylogenetic trees", "Phylogenetic analysis"),
            
            # General bioinformatics queries
            ("sequence alignment algorithms", "Alignment methods"),
            ("RNA-seq differential expression analysis", "Transcriptomics"),
            ("protein structure prediction modeling", "Structural biology"),
            ("variant calling genomics pipeline", "Genomics analysis"),
            ("phylogenetic tree construction methods", "Evolutionary analysis"),
            ("metagenomics taxonomic classification", "Microbial analysis"),
            ("genome assembly de novo algorithms", "Genome assembly"),
            ("quality control sequencing data", "Data quality"),
            ("statistical analysis bioinformatics", "Computational analysis"),
            ("machine learning computational biology", "AI applications"),
            
            # Specific tool searches
            ("restriction enzyme analysis", "Molecular cloning"),
            ("motif discovery sequences", "Pattern recognition"),
            ("database access NCBI Entrez", "Data retrieval"),
            ("file format conversion biology", "Data processing"),
            ("visualization molecular graphics", "Data visualization")
        ]
        
        search_times = []
        result_counts = []
        relevance_scores = []
        
        print("🔍 Testing search performance with bioinformatics queries...")
        
        for query, description in test_queries:
            print(f"   Testing: '{query[:30]}{'...' if len(query) > 30 else ''}'")
            
            # Measure search time
            start_time = time.time()
            results = await self.store.semantic_search(query, n_results=5)
            search_time = time.time() - start_time
            
            search_times.append(search_time)
            result_counts.append(len(results))
            
            if results:
                avg_score = statistics.mean([r['relevance_score'] for r in results[:3]])
                relevance_scores.append(avg_score)
                print(f"      ⏱️  {search_time:.3f}s | 📊 {len(results)} results | 🎯 {avg_score:.2f} avg score")
            else:
                relevance_scores.append(0)
                print(f"      ⏱️  {search_time:.3f}s | 📊 {len(results)} results | 🎯 No results")
        
        # Calculate enhanced statistics
        performance_stats = {
            "total_queries": len(test_queries),
            "average_search_time": statistics.mean(search_times),
            "min_search_time": min(search_times),
            "max_search_time": max(search_times),
            "std_search_time": statistics.stdev(search_times) if len(search_times) > 1 else 0,
            "median_search_time": statistics.median(search_times),
            "average_results": statistics.mean(result_counts),
            "average_relevance_score": statistics.mean([s for s in relevance_scores if s > 0]),
            "queries_per_second": len(test_queries) / sum(search_times),
            "high_quality_results": sum(1 for s in relevance_scores if s > 0.8),
            "performance_grade": self._calculate_performance_grade(search_times, relevance_scores)
        }
        
        print(f"\n📈 Enhanced Performance Summary:")
        print(f"   Average search time: {performance_stats['average_search_time']:.3f}s")
        print(f"   Median search time: {performance_stats['median_search_time']:.3f}s")
        print(f"   Min/Max search time: {performance_stats['min_search_time']:.3f}s / {performance_stats['max_search_time']:.3f}s")
        print(f"   Search time std dev: {performance_stats['std_search_time']:.3f}s")
        print(f"   Average results per query: {performance_stats['average_results']:.1f}")
        print(f"   Average relevance score: {performance_stats['average_relevance_score']:.3f}")
        print(f"   Queries per second: {performance_stats['queries_per_second']:.2f}")
        print(f"   High-quality results (>0.8): {performance_stats['high_quality_results']}/{len(test_queries)}")
        print(f"   Overall performance grade: {performance_stats['performance_grade']}")
        
        self.test_results["enhanced_performance"] = performance_stats
        return performance_stats
    
    def _calculate_performance_grade(self, search_times: List[float], relevance_scores: List[float]) -> str:
        """Calculate overall performance grade."""
        avg_time = statistics.mean(search_times)
        avg_relevance = statistics.mean([s for s in relevance_scores if s > 0])
        
        # Speed criteria (lower is better)
        speed_score = 100 if avg_time < 0.05 else 80 if avg_time < 0.1 else 60 if avg_time < 0.2 else 40
        
        # Relevance criteria (higher is better)
        relevance_score = 100 if avg_relevance > 0.85 else 80 if avg_relevance > 0.75 else 60 if avg_relevance > 0.65 else 40
        
        # Combined score
        combined_score = (speed_score + relevance_score) / 2
        
        if combined_score >= 90:
            return "A+ (EXCELLENT)"
        elif combined_score >= 80:
            return "A (VERY_GOOD)"
        elif combined_score >= 70:
            return "B+ (GOOD)"
        elif combined_score >= 60:
            return "B (ACCEPTABLE)"
        else:
            return "C (NEEDS_IMPROVEMENT)"

    async def test_3_biopython_specific_testing(self):
        """Test 3: Biopython-specific functionality testing."""
        print("\n🧪 Test 3: Biopython-Specific Testing")
        print("-" * 60)
        
        # Test major Biopython modules
        biopython_modules = [
            ("Bio.Seq", "Core sequence class for DNA, RNA, and protein sequences"),
            ("Bio.SeqIO", "Reading and writing sequence files in various formats"),
            ("Bio.Align.PairwiseAligner", "Pairwise sequence alignment algorithms"),
            ("Bio.Blast.NCBIWWW", "Running BLAST searches over the internet"),
            ("Bio.Entrez", "Access to NCBI databases through Entrez"),
            ("Bio.PDB", "Working with protein structures from PDB files"),
            ("Bio.Phylo", "Working with phylogenetic trees"),
            ("Bio.Restriction", "Restriction enzyme analysis"),
            ("Bio.motifs", "Sequence motif analysis"),
            ("Bio.Graphics.GenomeDiagram", "Creating genome diagrams")
        ]
        
        module_results = []
        
        for module_name, expected_description in biopython_modules:
            print(f"🔍 Testing module: {module_name}")
            
            # Search for the specific module
            results = await self.store.semantic_search(module_name, n_results=5)
            
            # Analyze results
            exact_match = any(module_name.lower() in r['name'].lower() or 
                             module_name.lower() in r.get('full_name', '').lower() 
                             for r in results)
            
            bio_related = sum(1 for r in results if 'bio' in r['name'].lower() or 
                             'bio' in r.get('source', '').lower())
            
            avg_score = statistics.mean([r['relevance_score'] for r in results]) if results else 0
            
            result = {
                "module": module_name,
                "found_results": len(results),
                "exact_match_found": exact_match,
                "bio_related_results": bio_related,
                "average_score": avg_score,
                "top_result": results[0]['name'] if results else None,
                "status": "EXCELLENT" if exact_match and avg_score > 0.8 else 
                         "GOOD" if bio_related >= 3 and avg_score > 0.6 else 
                         "NEEDS_IMPROVEMENT"
            }
            
            module_results.append(result)
            print(f"   📊 {len(results)} results | 🎯 {avg_score:.2f} avg | ✅ {result['status']}")
            if results:
                print(f"   🏆 Top: {results[0]['name']} (score: {results[0]['relevance_score']:.2f})")
        
        # Calculate summary statistics
        excellent_modules = sum(1 for r in module_results if r["status"] == "EXCELLENT")
        good_modules = sum(1 for r in module_results if r["status"] == "GOOD")
        total_modules = len(module_results)
        
        biopython_summary = {
            "total_modules_tested": total_modules,
            "excellent_modules": excellent_modules,
            "good_modules": good_modules,
            "success_rate": (excellent_modules + good_modules) / total_modules * 100,
            "average_module_score": statistics.mean([r["average_score"] for r in module_results]),
            "module_details": module_results
        }
        
        print(f"\n📊 Biopython Module Testing Summary:")
        print(f"   Modules tested: {total_modules}")
        print(f"   Excellent results: {excellent_modules}")
        print(f"   Good results: {good_modules}")
        print(f"   Success rate: {biopython_summary['success_rate']:.1f}%")
        print(f"   Average module score: {biopython_summary['average_module_score']:.3f}")
        
        self.test_results["biopython_specific"] = biopython_summary
        return biopython_summary

    async def test_4_edge_cases(self):
        """Test 4: Edge case testing with scientific terminology."""
        print("\n🧪 Test 4: Scientific Edge Cases & Terminology")
        print("-" * 60)
        
        edge_cases = [
            # Empty and minimal queries
            ("", "Empty string"),
            ("   ", "Whitespace only"),
            ("DNA", "Three characters"),
            ("RNA", "Three characters"),
            
            # Scientific notation and special characters
            ("RNA-seq", "Hyphenated scientific term"),
            ("3' UTR", "Apostrophe and numbers"),
            ("5'-3' direction", "Multiple apostrophes"),
            ("α-helix", "Greek letters"),
            ("β-sheet", "Greek letters"),
            ("p53/TP53", "Gene name variations"),
            ("mRNA & tRNA", "Multiple abbreviations"),
            ("16S rRNA", "Numbers and abbreviations"),
            ("COVID-19", "Recent scientific term"),
            ("HLA-A*02:01", "Complex genetic identifier"),
            ("CpG islands", "Molecular biology term"),
            
            # Long scientific queries
            ("protein structure prediction using machine learning algorithms for drug discovery", "Long technical query"),
            ("differential gene expression analysis RNA-seq transcriptomics pathway enrichment", "Multi-domain query"),
            ("next generation sequencing quality control adapter trimming", "NGS workflow"),
            
            # Case sensitivity with scientific terms
            ("blast", "All lowercase tool"),
            ("BLAST", "All uppercase tool"),
            ("BioPython", "Mixed case library"),
            ("genbank", "Database name lowercase"),
            ("GenBank", "Database name proper case"),
            
            # Non-biology terms (should still work gracefully)
            ("machine learning", "General CS term"),
            ("data analysis", "General analytics"),
            ("visualization", "General term"),
            ("statistics", "General math term"),
            
            # Completely unrelated (should handle gracefully)
            ("car engine", "Completely unrelated"),
            ("cooking recipe", "Unrelated domain"),
        ]
        
        edge_results = []
        scientific_term_count = 0
        
        for query, description in edge_cases:
            print(f"🧪 Testing: {description} - '{query}'")
            
            try:
                start_time = time.time()
                results = await self.store.semantic_search(query, n_results=5)
                search_time = time.time() - start_time
                
                # Check if results are relevant for scientific terms
                is_scientific = any(word in description.lower() for word in 
                                  ['scientific', 'technical', 'abbreviation', 'gene', 'molecular', 'ngs'])
                if is_scientific:
                    scientific_term_count += 1
                
                # Analyze result quality
                bio_related_results = sum(1 for r in results if 
                                        any(bio_word in r.get('source', '').lower() or 
                                           bio_word in r['name'].lower() for bio_word in 
                                           ['bio', 'sequence', 'protein', 'dna', 'rna']))
                
                result_info = {
                    "query": query,
                    "description": description,
                    "success": True,
                    "search_time": search_time,
                    "result_count": len(results),
                    "bio_related_count": bio_related_results,
                    "top_result": results[0]['name'] if results else None,
                    "top_score": results[0]['relevance_score'] if results else 0,
                    "is_scientific_term": is_scientific,
                    "quality": "HIGH" if results and results[0]['relevance_score'] > 0.7 else
                              "MEDIUM" if results and results[0]['relevance_score'] > 0.5 else
                              "LOW" if results else "NO_RESULTS",
                    "error": None
                }
                
                print(f"   ✅ {len(results)} results in {search_time:.3f}s")
                if results:
                    print(f"   🎯 Top: {results[0]['name']} (Score: {results[0]['relevance_score']:.2f})")
                    
            except Exception as e:
                result_info = {
                    "query": query,
                    "description": description,
                    "success": False,
                    "search_time": 0,
                    "result_count": 0,
                    "bio_related_count": 0,
                    "top_result": None,
                    "top_score": 0,
                    "is_scientific_term": False,
                    "quality": "ERROR",
                    "error": str(e)
                }
                print(f"   ❌ Error: {str(e)}")
            
            edge_results.append(result_info)
        
        # Calculate enhanced statistics
        successful_tests = sum(1 for r in edge_results if r["success"])
        failed_tests = len(edge_results) - successful_tests
        high_quality_results = sum(1 for r in edge_results if r["quality"] == "HIGH")
        scientific_high_quality = sum(1 for r in edge_results if r["is_scientific_term"] and r["quality"] == "HIGH")
        
        edge_summary = {
            "total_tests": len(edge_results),
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "success_rate": successful_tests / len(edge_results) * 100,
            "high_quality_results": high_quality_results,
            "scientific_terms_tested": scientific_term_count,
            "scientific_high_quality": scientific_high_quality,
            "scientific_success_rate": (scientific_high_quality / scientific_term_count * 100) if scientific_term_count > 0 else 0,
            "details": edge_results
        }
        
        print(f"\n📊 Edge Case Testing Summary:")
        print(f"   Total tests: {edge_summary['total_tests']}")
        print(f"   Successful: {edge_summary['successful_tests']}")
        print(f"   Failed: {edge_summary['failed_tests']}")
        print(f"   Success rate: {edge_summary['success_rate']:.1f}%")
        print(f"   High-quality results: {edge_summary['high_quality_results']}")
        print(f"   Scientific terms tested: {edge_summary['scientific_terms_tested']}")
        print(f"   Scientific term success rate: {edge_summary['scientific_success_rate']:.1f}%")
        
        self.test_results["edge_cases"] = edge_summary
        return edge_summary

    async def run_all_tests(self):
        """Run the complete enhanced test suite."""
        print("🚀 Starting Enhanced Comprehensive Test Suite")
        print("=" * 70)
        
        if self.use_main_db:
            print("🧬 Testing with Biopython-integrated ChromaDB (2,390+ tools)")
        else:
            print("🧪 Testing with separate test database")
        print("=" * 70)
        
        # Test 1: Database validation and Biopython integration
        await self.test_1_database_validation()
        
        # Test 2: Enhanced performance testing
        await self.test_2_enhanced_performance_testing()
        
        # Test 3: Biopython-specific testing
        await self.test_3_biopython_specific_testing()
        
        # Test 4: Enhanced edge case testing
        await self.test_4_edge_cases()
        
        # Generate final comprehensive summary
        await self._generate_final_summary()
        
        return self.test_results
    
    async def _generate_final_summary(self):
        """Generate comprehensive final summary."""
        print("\n🏆 COMPREHENSIVE TEST RESULTS")
        print("=" * 70)
        
        # Database Status
        if "database_validation" in self.test_results:
            db_results = self.test_results["database_validation"]
            print(f"📊 Database Status:")
            print(f"   Total tools: {db_results['collection_count']:,}")
            print(f"   Biopython integration: {db_results['integration_status']}")
            print(f"   Biopython coverage: {db_results['biopython_coverage']}")
        
        # Performance Results
        if "enhanced_performance" in self.test_results:
            perf_results = self.test_results["enhanced_performance"]
            print(f"\n⚡ Performance Results:")
            print(f"   Average search time: {perf_results['average_search_time']:.3f}s")
            print(f"   Queries per second: {perf_results['queries_per_second']:.2f}")
            print(f"   Average relevance: {perf_results['average_relevance_score']:.3f}")
            print(f"   Performance grade: {perf_results['performance_grade']}")
        
        # Biopython Results
        if "biopython_specific" in self.test_results:
            bio_results = self.test_results["biopython_specific"]
            print(f"\n🧬 Biopython Module Testing:")
            print(f"   Modules tested: {bio_results['total_modules_tested']}")
            print(f"   Success rate: {bio_results['success_rate']:.1f}%")
            print(f"   Average score: {bio_results['average_module_score']:.3f}")
        
        # Edge Case Results
        if "edge_cases" in self.test_results:
            edge_results = self.test_results["edge_cases"]
            print(f"\n🧪 Edge Case Testing:")
            print(f"   Overall success rate: {edge_results['success_rate']:.1f}%")
            print(f"   Scientific term success: {edge_results['scientific_success_rate']:.1f}%")
            print(f"   High-quality results: {edge_results['high_quality_results']}")
        
        # Final Assessment
        overall_grade = self._calculate_overall_grade()
        print(f"\n🎯 OVERALL SYSTEM ASSESSMENT: {overall_grade}")
        
        if "A" in overall_grade:
            print("🌟 Your ChromaDB system is performing excellently with the Biopython integration!")
        elif "B" in overall_grade:
            print("👍 Your ChromaDB system is performing well with room for minor improvements.")
        else:
            print("⚠️  Your ChromaDB system may need some optimization.")
        
        print("\n✨ Test suite completed successfully!")
    
    def _calculate_overall_grade(self) -> str:
        """Calculate overall system grade."""
        scores = []
        
        # Performance score
        if "enhanced_performance" in self.test_results:
            perf = self.test_results["enhanced_performance"]
            if "A" in perf["performance_grade"]:
                scores.append(90)
            elif "B" in perf["performance_grade"]:
                scores.append(75)
            else:
                scores.append(60)
        
        # Biopython score
        if "biopython_specific" in self.test_results:
            bio = self.test_results["biopython_specific"]
            scores.append(bio["success_rate"])
        
        # Edge case score
        if "edge_cases" in self.test_results:
            edge = self.test_results["edge_cases"]
            scores.append(edge["success_rate"])
        
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
    """Run the comprehensive test suite."""
    print("🔬 Enhanced Comprehensive Test Suite for Biopython Integration")
    print("=" * 70)
    
    # Ask user which database to test
    import sys
    use_main = True  # Default to main database with Biopython tools
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test-db":
        use_main = False
        print("🧪 Creating separate test database...")
        # Clean start for test database
        test_dir = Path("data/chroma_test")
        if test_dir.exists():
            import shutil
            shutil.rmtree(test_dir)
    
    # Run tests
    test_suite = ComprehensiveTestSuite(use_main_db=use_main)
    results = await test_suite.run_all_tests()
    
    return results


if __name__ == "__main__":
    results = asyncio.run(main())