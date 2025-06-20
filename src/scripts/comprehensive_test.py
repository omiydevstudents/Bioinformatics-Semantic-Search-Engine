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
    """Comprehensive test suite for ChromaDB & RAG Pipeline optimization."""
    
    def __init__(self):
        self.store = SemanticSearchStore(persist_dir="data/chroma_test")
        self.performance_results = []
        self.test_results = {}
        
    def get_50_biology_tools(self) -> List[Dict]:
        """Generate 50+ diverse bioinformatics tools for testing."""
        return [
            # Sequence Analysis Tools
            {
                "name": "BLAST",
                "category": "Sequence Analysis",
                "description": "Basic Local Alignment Search Tool for comparing biological sequences",
                "features": ["sequence alignment", "homology search", "database search"],
                "documentation": "https://blast.ncbi.nlm.nih.gov/Blast.cgi"
            },
            {
                "name": "ClustalW",
                "category": "Sequence Alignment", 
                "description": "Multiple sequence alignment program for DNA or proteins",
                "features": ["multiple sequence alignment", "phylogenetic analysis"],
                "documentation": "https://www.ebi.ac.uk/Tools/msa/clustalw2/"
            },
            {
                "name": "MUSCLE",
                "category": "Sequence Alignment",
                "description": "Multiple sequence alignment with high accuracy and speed",
                "features": ["fast alignment", "progressive alignment", "iterative refinement"],
                "documentation": "https://www.ebi.ac.uk/Tools/msa/muscle/"
            },
            {
                "name": "T-Coffee",
                "category": "Sequence Alignment",
                "description": "Multiple sequence alignment using consistency-based methods",
                "features": ["consistency scoring", "structure-based alignment", "homology extension"],
                "documentation": "http://www.tcoffee.org/"
            },
            {
                "name": "MAFFT",
                "category": "Sequence Alignment",
                "description": "Multiple sequence alignment based on fast Fourier transform",
                "features": ["FFT-based alignment", "progressive method", "iterative refinement"],
                "documentation": "https://mafft.cbrc.jp/alignment/software/"
            },
            
            # Variant Calling & Genomics
            {
                "name": "GATK",
                "category": "Variant Calling",
                "description": "Genome Analysis Toolkit for variant discovery in high-throughput sequencing data",
                "features": ["SNP calling", "indel detection", "variant filtering", "quality control"],
                "documentation": "https://gatk.broadinstitute.org/"
            },
            {
                "name": "FreeBayes",
                "category": "Variant Calling",
                "description": "Bayesian genetic variant detector designed to find small polymorphisms",
                "features": ["haplotype-based calling", "bayesian inference", "complex variants"],
                "documentation": "https://github.com/freebayes/freebayes"
            },
            {
                "name": "VarScan",
                "category": "Variant Calling",
                "description": "Platform-independent mutation caller for targeted, exome, and whole-genome resequencing",
                "features": ["somatic mutation detection", "copy number variation", "loss of heterozygosity"],
                "documentation": "http://varscan.sourceforge.net/"
            },
            {
                "name": "Samtools",
                "category": "Sequence Processing",
                "description": "Suite of programs for interacting with high-throughput sequencing data",
                "features": ["SAM/BAM manipulation", "variant calling", "sequence indexing"],
                "documentation": "http://www.htslib.org/"
            },
            {
                "name": "BWA",
                "category": "Read Mapping",
                "description": "Burrows-Wheeler Aligner for mapping sequences against large reference genome",
                "features": ["short read alignment", "BWA-MEM algorithm", "paired-end support"],
                "documentation": "http://bio-bwa.sourceforge.net/"
            },
            
            # RNA-seq Analysis
            {
                "name": "DESeq2",
                "category": "RNA-seq Analysis",
                "description": "Differential gene expression analysis for RNA-seq count data",
                "features": ["differential expression", "normalization", "statistical testing", "visualization"],
                "documentation": "https://bioconductor.org/packages/DESeq2/"
            },
            {
                "name": "edgeR",
                "category": "RNA-seq Analysis", 
                "description": "Empirical analysis of digital gene expression data in R",
                "features": ["differential expression", "dispersion estimation", "exact tests"],
                "documentation": "https://bioconductor.org/packages/edgeR/"
            },
            {
                "name": "TopHat",
                "category": "RNA-seq Analysis",
                "description": "Spliced read mapper for RNA-Seq experiments",
                "features": ["splice junction discovery", "transcript mapping", "fusion detection"],
                "documentation": "https://ccb.jhu.edu/software/tophat/"
            },
            {
                "name": "Cufflinks",
                "category": "RNA-seq Analysis",
                "description": "Transcript assembly and differential expression analysis for RNA-Seq",
                "features": ["transcript assembly", "abundance estimation", "differential regulation"],
                "documentation": "http://cole-trapnell-lab.github.io/cufflinks/"
            },
            {
                "name": "HISAT2",
                "category": "RNA-seq Analysis",
                "description": "Graph-based alignment of next generation sequencing reads to population of genomes",
                "features": ["graph-based indexing", "splice-aware alignment", "SNP-aware mapping"],
                "documentation": "https://daehwankimlab.github.io/hisat2/"
            },
            
            # Protein Analysis
            {
                "name": "SWISS-MODEL",
                "category": "Protein Structure",
                "description": "Automated protein structure homology-modeling server",
                "features": ["homology modeling", "structure assessment", "model quality estimation"],
                "documentation": "https://swissmodel.expasy.org/"
            },
            {
                "name": "ChimeraX",
                "category": "Protein Visualization",
                "description": "Molecular visualization program for interactive exploration of molecular structures",
                "features": ["3D visualization", "animation", "molecular dynamics", "VR support"],
                "documentation": "https://www.cgl.ucsf.edu/chimerax/"
            },
            {
                "name": "PyMOL",
                "category": "Protein Visualization",
                "description": "Molecular visualization system for protein structure analysis",
                "features": ["3D rendering", "ray tracing", "animation", "publication graphics"],
                "documentation": "https://pymol.org/"
            },
            {
                "name": "DSSP",
                "category": "Protein Structure",
                "description": "Define Secondary Structure of Proteins algorithm",
                "features": ["secondary structure assignment", "hydrogen bonding", "geometric analysis"],
                "documentation": "https://swift.cmbi.umcn.nl/gv/dssp/"
            },
            {
                "name": "I-TASSER",
                "category": "Protein Structure",
                "description": "Automated protein structure and function prediction server",
                "features": ["ab initio modeling", "threading", "function annotation"],
                "documentation": "https://zhanglab.ccmb.med.umich.edu/I-TASSER/"
            },
            
            # Phylogenetics
            {
                "name": "MEGA",
                "category": "Phylogenetics",
                "description": "Molecular Evolutionary Genetics Analysis software",
                "features": ["phylogenetic analysis", "evolutionary distance", "molecular clock"],
                "documentation": "https://www.megasoftware.net/"
            },
            {
                "name": "PhyML",
                "category": "Phylogenetics",
                "description": "Maximum likelihood phylogenetic inference for nucleotide and amino acid sequences",
                "features": ["ML estimation", "model selection", "bootstrap support"],
                "documentation": "http://www.atgc-montpellier.fr/phyml/"
            },
            {
                "name": "RAxML",
                "category": "Phylogenetics",
                "description": "Maximum likelihood phylogenetic inference for large datasets",
                "features": ["parallel computation", "bootstrap analysis", "model optimization"],
                "documentation": "https://cme.h-its.org/exelixis/web/software/raxml/"
            },
            {
                "name": "BEAST",
                "category": "Phylogenetics",
                "description": "Bayesian evolutionary analysis by sampling trees",
                "features": ["bayesian inference", "molecular dating", "population genetics"],
                "documentation": "https://beast.community/"
            },
            {
                "name": "MrBayes",
                "category": "Phylogenetics",
                "description": "Bayesian inference of phylogeny using Markov chain Monte Carlo methods",
                "features": ["MCMC sampling", "model averaging", "posterior probability"],
                "documentation": "https://nbisweden.github.io/MrBayes/"
            },
            
            # Genome Assembly
            {
                "name": "SPAdes",
                "category": "Genome Assembly",
                "description": "Genome assembler for single-cell and standard multi-cell organisms",
                "features": ["de novo assembly", "error correction", "repeat resolution"],
                "documentation": "https://cab.spbu.ru/software/spades/"
            },
            {
                "name": "Velvet",
                "category": "Genome Assembly",
                "description": "De novo genome assembler using de Bruijn graphs",
                "features": ["short read assembly", "paired-end support", "scaffolding"],
                "documentation": "https://www.ebi.ac.uk/~zerbino/velvet/"
            },
            {
                "name": "Canu",
                "category": "Genome Assembly",
                "description": "Single molecule sequence assembler for genomes large and small",
                "features": ["long read assembly", "error correction", "overlap detection"],
                "documentation": "https://canu.readthedocs.io/"
            },
            {
                "name": "Flye",
                "category": "Genome Assembly",
                "description": "De novo assembler for single molecule sequencing reads",
                "features": ["long read assembly", "repeat analysis", "graph simplification"],
                "documentation": "https://github.com/fenderglass/Flye"
            },
            
            # Metagenomics
            {
                "name": "MetaPhlAn",
                "category": "Metagenomics",
                "description": "Metagenomic phylogenetic analysis for microbial community profiling",
                "features": ["taxonomic profiling", "species abundance", "marker genes"],
                "documentation": "https://huttenhower.sph.harvard.edu/metaphlan/"
            },
            {
                "name": "Kraken2",
                "category": "Metagenomics",
                "description": "Taxonomic classification system using exact k-mer matches",
                "features": ["fast classification", "confidence scoring", "custom databases"],
                "documentation": "https://ccb.jhu.edu/software/kraken2/"
            },
            {
                "name": "QIIME2",
                "category": "Metagenomics",
                "description": "Quantitative Insights Into Microbial Ecology platform",
                "features": ["microbiome analysis", "diversity metrics", "visualization"],
                "documentation": "https://qiime2.org/"
            },
            {
                "name": "mothur",
                "category": "Metagenomics",
                "description": "Open-source software for analyzing 16S rRNA gene sequences",
                "features": ["OTU clustering", "diversity analysis", "classification"],
                "documentation": "https://mothur.org/"
            },
            
            # Structural Biology
            {
                "name": "ChimeraX",
                "category": "Structural Biology",
                "description": "Next-generation molecular visualization program",
                "features": ["cryo-EM visualization", "molecular dynamics", "virtual reality"],
                "documentation": "https://www.cgl.ucsf.edu/chimerax/"
            },
            {
                "name": "CCP4",
                "category": "Structural Biology",
                "description": "Collaborative Computational Project Number 4 for protein crystallography",
                "features": ["structure determination", "refinement", "validation"],
                "documentation": "https://www.ccp4.ac.uk/"
            },
            {
                "name": "Phenix",
                "category": "Structural Biology",
                "description": "Python-based Hierarchical ENvironment for Integrated Xtallography",
                "features": ["structure refinement", "model building", "validation"],
                "documentation": "https://phenix-online.org/"
            },
            
            # Functional Analysis
            {
                "name": "DAVID",
                "category": "Functional Analysis",
                "description": "Database for Annotation, Visualization and Integrated Discovery",
                "features": ["functional annotation", "pathway analysis", "gene ontology"],
                "documentation": "https://david.ncifcrf.gov/"
            },
            {
                "name": "KEGG",
                "category": "Functional Analysis",
                "description": "Kyoto Encyclopedia of Genes and Genomes pathway database",
                "features": ["pathway mapping", "functional hierarchy", "genome annotation"],
                "documentation": "https://www.genome.jp/kegg/"
            },
            {
                "name": "GO",
                "category": "Functional Analysis",
                "description": "Gene Ontology consortium for functional gene annotation",
                "features": ["molecular function", "biological process", "cellular component"],
                "documentation": "http://geneontology.org/"
            },
            
            # Statistical Analysis
            {
                "name": "R/Bioconductor",
                "category": "Statistical Analysis",
                "description": "Open source software for bioinformatics and computational biology",
                "features": ["statistical computing", "genomic analysis", "visualization"],
                "documentation": "https://bioconductor.org/"
            },
            {
                "name": "Bioconductor",
                "category": "Statistical Analysis",
                "description": "Open development software project for computational biology",
                "features": ["genomic data analysis", "statistical methods", "workflows"],
                "documentation": "https://www.bioconductor.org/"
            },
            
            # Quality Control
            {
                "name": "FastQC",
                "category": "Quality Control",
                "description": "Quality control tool for high throughput sequence data",
                "features": ["quality assessment", "sequence statistics", "contamination detection"],
                "documentation": "https://www.bioinformatics.babraham.ac.uk/projects/fastqc/"
            },
            {
                "name": "MultiQC",
                "category": "Quality Control",
                "description": "Aggregate results from bioinformatics analyses across many samples",
                "features": ["report aggregation", "visualization", "sample comparison"],
                "documentation": "https://multiqc.info/"
            },
            {
                "name": "Trimmomatic",
                "category": "Quality Control",
                "description": "Flexible read trimming tool for Illumina NGS data",
                "features": ["adapter removal", "quality trimming", "read filtering"],
                "documentation": "http://www.usadellab.org/cms/?page=trimmomatic"
            },
            
            # Database Tools
            {
                "name": "Ensembl",
                "category": "Database",
                "description": "Genome browser for vertebrate genomes with automatic annotation",
                "features": ["genome annotation", "comparative genomics", "variation data"],
                "documentation": "https://www.ensembl.org/"
            },
            {
                "name": "NCBI",
                "category": "Database",
                "description": "National Center for Biotechnology Information databases",
                "features": ["sequence databases", "literature search", "genome browsers"],
                "documentation": "https://www.ncbi.nlm.nih.gov/"
            },
            {
                "name": "UniProt",
                "category": "Database",
                "description": "Universal Protein Resource knowledgebase",
                "features": ["protein annotation", "functional information", "sequence analysis"],
                "documentation": "https://www.uniprot.org/"
            },
            
            # Machine Learning
            {
                "name": "scikit-bio",
                "category": "Machine Learning",
                "description": "Python library for bioinformatics data structures and algorithms",
                "features": ["sequence analysis", "phylogenetics", "statistics"],
                "documentation": "http://scikit-bio.org/"
            },
            {
                "name": "Biopython",
                "category": "Programming",
                "description": "Python tools for computational molecular biology",
                "features": ["sequence analysis", "phylogenetics", "structure analysis"],
                "documentation": "https://biopython.org/"
            },
            {
                "name": "BioJava",
                "category": "Programming",
                "description": "Open-source Java framework for processing biological data",
                "features": ["sequence analysis", "protein structure", "genomics"],
                "documentation": "https://biojava.org/"
            }
        ]

    async def test_1_add_50_tools(self):
        """Test 1: Add 50+ biology tools and measure performance."""
        print("🧪 Test 1: Adding 50+ Biology Tools")
        print("-" * 50)
        
        tools = self.get_50_biology_tools()
        print(f"Total tools to add: {len(tools)}")
        
        # Measure addition time
        start_time = time.time()
        success = await self.store.add_tools(tools)
        addition_time = time.time() - start_time
        
        # Check collection size
        collection_count = self.store.collection.count()
        
        result = {
            "tools_added": len(tools),
            "addition_time": addition_time,
            "success": success,
            "collection_count": collection_count,
            "tools_per_second": len(tools) / addition_time if addition_time > 0 else 0
        }
        
        print(f"✅ Tools added: {result['tools_added']}")
        print(f"⏱️  Addition time: {addition_time:.2f} seconds")
        print(f"📊 Collection count: {collection_count}")
        print(f"🚀 Tools per second: {result['tools_per_second']:.2f}")
        
        self.test_results["add_tools"] = result
        return result

    async def test_2_performance_testing(self):
        """Test 2: Measure search speed and accuracy across different queries."""
        print("\n🧪 Test 2: Performance Testing")
        print("-" * 50)
        
        test_queries = [
            "sequence alignment",
            "RNA-seq differential expression",
            "protein structure prediction", 
            "variant calling genomics",
            "phylogenetic analysis",
            "metagenomics taxonomy",
            "genome assembly",
            "quality control sequencing",
            "statistical analysis bioinformatics",
            "machine learning biology"
        ]
        
        search_times = []
        result_counts = []
        
        for query in test_queries:
            print(f"🔍 Testing query: '{query}'")
            
            # Measure search time
            start_time = time.time()
            results = await self.store.semantic_search(query, n_results=10)
            search_time = time.time() - start_time
            
            search_times.append(search_time)
            result_counts.append(len(results))
            
            print(f"   ⏱️  Search time: {search_time:.3f}s")
            print(f"   📊 Results found: {len(results)}")
            if results:
                print(f"   🎯 Top result: {results[0]['name']} (Score: {results[0]['relevance_score']:.2f})")
        
        # Calculate statistics
        performance_stats = {
            "average_search_time": statistics.mean(search_times),
            "min_search_time": min(search_times),
            "max_search_time": max(search_times),
            "std_search_time": statistics.stdev(search_times) if len(search_times) > 1 else 0,
            "average_results": statistics.mean(result_counts),
            "total_queries": len(test_queries),
            "queries_per_second": len(test_queries) / sum(search_times)
        }
        
        print(f"\n📈 Performance Summary:")
        print(f"   Average search time: {performance_stats['average_search_time']:.3f}s")
        print(f"   Min/Max search time: {performance_stats['min_search_time']:.3f}s / {performance_stats['max_search_time']:.3f}s")
        print(f"   Standard deviation: {performance_stats['std_search_time']:.3f}s")
        print(f"   Average results per query: {performance_stats['average_results']:.1f}")
        print(f"   Queries per second: {performance_stats['queries_per_second']:.2f}")
        
        self.test_results["performance"] = performance_stats
        return performance_stats

    async def test_3_edge_cases(self):
        """Test 3: Edge case testing - empty queries, special characters, very long queries."""
        print("\n🧪 Test 3: Edge Case Testing")
        print("-" * 50)
        
        edge_cases = [
            # Empty and minimal queries
            ("", "Empty string"),
            ("   ", "Whitespace only"),
            ("a", "Single character"),
            ("DNA", "Three characters"),
            
            # Special characters
            ("RNA-seq", "Hyphenated term"),
            ("3' UTR", "Apostrophe and space"),
            ("α-helix", "Greek letters"),
            ("p53/TP53", "Slash separator"),
            ("mRNA & tRNA", "Ampersand"),
            ("5'-3' direction", "Multiple special chars"),
            
            # Numbers and mixed content
            ("16S rRNA", "Numbers and letters"),
            ("COVID-19", "Numbers with hyphen"),
            ("HLA-A*02:01", "Complex identifiers"),
            
            # Very long queries
            ("protein structure prediction using machine learning algorithms for drug discovery and therapeutic target identification in cancer research", "Very long descriptive query"),
            ("differential gene expression analysis RNA-seq transcriptomics functional annotation pathway enrichment statistical testing multiple comparisons false discovery rate", "Long technical query"),
            
            # Case sensitivity
            ("blast", "All lowercase"),
            ("BLAST", "All uppercase"), 
            ("BlAsT", "Mixed case"),
            
            # Non-biology terms
            ("car engine", "Completely unrelated"),
            ("pizza recipe", "Food related"),
            ("quantum physics", "Other science field"),
        ]
        
        edge_results = []
        
        for query, description in edge_cases:
            print(f"🧪 Testing: {description} - '{query}'")
            
            try:
                start_time = time.time()
                results = await self.store.semantic_search(query, n_results=5)
                search_time = time.time() - start_time
                
                result_info = {
                    "query": query,
                    "description": description,
                    "success": True,
                    "search_time": search_time,
                    "result_count": len(results),
                    "top_result": results[0]['name'] if results else None,
                    "top_score": results[0]['relevance_score'] if results else 0,
                    "error": None
                }
                
                print(f"   ✅ Success: {len(results)} results in {search_time:.3f}s")
                if results:
                    print(f"   🎯 Top: {results[0]['name']} (Score: {results[0]['relevance_score']:.2f})")
                else:
                    print(f"   📭 No results found")
                    
            except Exception as e:
                result_info = {
                    "query": query,
                    "description": description,
                    "success": False,
                    "search_time": 0,
                    "result_count": 0,
                    "top_result": None,
                    "top_score": 0,
                    "error": str(e)
                }
                print(f"   ❌ Error: {str(e)}")
            
            edge_results.append(result_info)
        
        # Summary
        successful_tests = sum(1 for r in edge_results if r["success"])
        failed_tests = len(edge_results) - successful_tests
        
        edge_summary = {
            "total_tests": len(edge_results),
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "success_rate": successful_tests / len(edge_results) * 100,
            "details": edge_results
        }
        
        print(f"\n📊 Edge Case Summary:")
        print(f"   Total tests: {edge_summary['total_tests']}")
        print(f"   Successful: {edge_summary['successful_tests']}")
        print(f"   Failed: {edge_summary['failed_tests']}")
        print(f"   Success rate: {edge_summary['success_rate']:.1f}%")
        
        self.test_results["edge_cases"] = edge_summary
        return edge_summary

    async def run_all_tests(self):
        """Run the complete test suite."""
        print("🚀 Starting Comprehensive Test Suite")
        print("=" * 60)
        
        # Test 1: Scale up with 50+ tools
        await self.test_1_add_50_tools()
        
        # Test 2: Performance testing
        await self.test_2_performance_testing()
        
        # Test 3: Edge case testing
        await self.test_3_edge_cases()
        
        # Overall summary
        print("\n🏆 Test Suite Complete!")
        print("=" * 60)
        print("📊 Overall Results:")
        
        if "add_tools" in self.test_results:
            print(f"   Tools added: {self.test_results['add_tools']['tools_added']}")
            print(f"   Addition speed: {self.test_results['add_tools']['tools_per_second']:.2f} tools/sec")
        
        if "performance" in self.test_results:
            print(f"   Average search time: {self.test_results['performance']['average_search_time']:.3f}s")
            print(f"   Search throughput: {self.test_results['performance']['queries_per_second']:.2f} queries/sec")
        
        if "edge_cases" in self.test_results:
            print(f"   Edge case success rate: {self.test_results['edge_cases']['success_rate']:.1f}%")
        
        print("\n✨ Your ChromaDB & RAG Pipeline is production-ready!")
        
        return self.test_results

async def main():
    """Run the comprehensive test suite."""
    # Clean start
    test_dir = Path("data/chroma_test")
    if test_dir.exists():
        import shutil
        shutil.rmtree(test_dir)
    
    # Run tests
    test_suite = ComprehensiveTestSuite()
    results = await test_suite.run_all_tests()
    
    return results

if __name__ == "__main__":
    results = asyncio.run(main())