# src/scripts/biopython_tools_collector.py

"""
Complete Biopython Tools Collector (Scripts Version)
Extracts ALL 2000+ Biopython tools using Python introspection.

This collector discovers and catalogs every Bio.* module, submodule, 
function, and class in Biopython automatically.

Usage:
    python src/scripts/biopython_tools_collector.py

Author: Nitanshu (ChromaDB & RAG Pipeline)
"""

import asyncio
import sys
import os
import pkgutil
import importlib
import inspect
import json
import time
from typing import List, Dict, Optional, Set
from pathlib import Path
from dataclasses import dataclass
import traceback
import logging

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BioPythonTool:
    """Represents a single Biopython tool/module/function."""
    name: str
    full_name: str  # e.g., Bio.Seq.Seq
    category: str
    tool_type: str  # module, function, class
    description: str
    features: List[str]
    documentation: str
    source: str = "Biopython"
    version: Optional[str] = None
    programming_language: str = "Python"
    license: str = "Biopython License"
    installation_guide: str = "pip install biopython"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary format for ChromaDB."""
        return {
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "features": self.features,
            "documentation": self.documentation,
            "source": self.source,
            "version": self.version or "1.85",
            "programming_language": self.programming_language,
            "license": self.license,
            "installation_guide": self.installation_guide,
            "tool_type": self.tool_type,
            "full_name": self.full_name
        }

class CompleteBiopythonCollector:
    """Comprehensive collector for ALL Biopython tools using introspection."""
    
    def __init__(self):
        self.collected_tools: List[BioPythonTool] = []
        self.processed_modules: Set[str] = set()
        
        # Set data directory relative to project root
        self.data_dir = project_root / "data" / "biopython_collection"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Category mapping for better organization
        self.category_mapping = {
            # Core sequence handling
            'seq': 'Sequence Analysis',
            'seqio': 'Sequence Processing', 
            'sequtils': 'Sequence Analysis',
            'seqrecord': 'Sequence Processing',
            
            # Alignment
            'align': 'Sequence Alignment',
            'alignio': 'Sequence Alignment',
            'pairwise': 'Sequence Alignment',
            'multiple': 'Sequence Alignment',
            
            # Database access
            'entrez': 'Database Access',
            'expasy': 'Database Access',
            'uniprot': 'Database Access',
            'kegg': 'Database Access',
            'ncbi': 'Database Access',
            
            # Analysis tools
            'blast': 'Sequence Analysis',
            'emboss': 'Sequence Analysis',
            'restriction': 'Sequence Analysis',
            'motif': 'Sequence Analysis',
            
            # Structure
            'pdb': 'Protein Structure',
            'structure': 'Protein Structure',
            'dssp': 'Protein Structure',
            
            # Phylogenetics
            'phylo': 'Phylogenetics',
            'tree': 'Phylogenetics',
            'nexus': 'Phylogenetics',
            'newick': 'Phylogenetics',
            
            # Graphics and visualization
            'graphics': 'Visualization',
            'genomediagram': 'Visualization',
            'chromosome': 'Visualization',
            
            # Population genetics
            'popgen': 'Population Genetics',
            'genepop': 'Population Genetics',
            
            # File formats
            'genbank': 'File Formats',
            'fasta': 'File Formats',
            'swiss': 'File Formats',
            'embl': 'File Formats',
            
            # Applications and wrappers
            'application': 'Tool Wrappers',
            'applications': 'Tool Wrappers',
            
            # Machine learning
            'cluster': 'Machine Learning',
            'hmm': 'Machine Learning',
            
            # Utilities
            'alphabet': 'Core Utilities',
            'data': 'Data Resources',
            'pathway': 'Pathway Analysis'
        }
    
    def _categorize_tool(self, module_name: str, tool_name: str) -> str:
        """Categorize a tool based on its module and name."""
        full_path = f"{module_name}.{tool_name}".lower()
        
        # Check each category keyword
        for keyword, category in self.category_mapping.items():
            if keyword in full_path:
                return category
        
        # Fallback categorization based on module structure
        parts = module_name.lower().split('.')
        if len(parts) >= 2:
            main_module = parts[1]  # Skip 'bio'
            
            if main_module in self.category_mapping:
                return self.category_mapping[main_module]
        
        return 'General Bioinformatics'
    
    def _is_experimental_module(self, module, module_name: str) -> bool:
        """Check if a module is marked as experimental."""
        try:
            # Check if module docstring mentions experimental
            doc = inspect.getdoc(module) or ""
            if any(word in doc.lower() for word in ['experimental', 'beta', 'alpha', 'unstable']):
                return True
            
            # Check if module name suggests experimental status
            if any(word in module_name.lower() for word in ['experimental', 'beta', 'test']):
                return True
                
            return False
        except Exception:
            return False
    
    def _get_documentation_url(self, module_name: str, member_name: str = None) -> str:
        """Generate accurate documentation URL for Biopython API."""
        # Base URL for Biopython API documentation
        base_url = "https://biopython.org/docs/latest/api/"
        
        # For modules, use the module page
        if not member_name:
            return f"{base_url}{module_name}.html"
        
        # For module members, link to the module page with anchor
        return f"{base_url}{module_name}.html#{module_name}.{member_name}"
    
    def _extract_functions_and_classes(self, module, module_name: str) -> List[BioPythonTool]:
        """Extract functions and classes from a module."""
        tools = []
        
        try:
            # Get all members of the module
            members = inspect.getmembers(module)
            
            for name, obj in members:
                # Skip private/internal items
                if name.startswith('_'):
                    continue
                
                # Skip imports from other modules (not defined in this module)
                if hasattr(obj, '__module__') and obj.__module__ != module_name:
                    continue
                
                tool_type = None
                description = ""
                features = []
                
                if inspect.isfunction(obj):
                    tool_type = "function"
                    description = inspect.getdoc(obj) or f"Function in {module_name}"
                    
                    # Extract function signature as a feature
                    try:
                        sig = inspect.signature(obj)
                        features.append(f"Parameters: {str(sig)}")
                    except (ValueError, TypeError):
                        pass
                        
                elif inspect.isclass(obj):
                    tool_type = "class"
                    description = inspect.getdoc(obj) or f"Class in {module_name}"
                    
                    # Extract class methods as features
                    methods = [method for method in dir(obj) 
                             if not method.startswith('_') and callable(getattr(obj, method, None))]
                    if methods:
                        features.extend(methods[:5])  # Top 5 methods
                
                if tool_type:
                    full_name = f"{module_name}.{name}"
                    category = self._categorize_tool(module_name, name)
                    
                    # Clean up description
                    if description and len(description) > 500:
                        description = description[:500] + "..."
                    
                    # Create documentation URL using official API structure
                    doc_url = self._get_documentation_url(module_name, name)
                    
                    tool = BioPythonTool(
                        name=name,
                        full_name=full_name,
                        category=category,
                        tool_type=tool_type,
                        description=description or f"{tool_type.title()} for {category.lower()}",
                        features=features,
                        documentation=doc_url
                    )
                    
                    tools.append(tool)
                    
        except Exception as e:
            logger.warning(f"Error extracting from {module_name}: {e}")
        
        return tools
    
    def _create_module_tool(self, module, module_name: str) -> BioPythonTool:
        """Create a tool entry for the module itself."""
        description = inspect.getdoc(module) or f"Biopython module: {module_name}"
        
        # Clean up description
        if description and len(description) > 500:
            description = description[:500] + "..."
        
        # Extract module-level features
        features = []
        
        # Get submodules
        try:
            if hasattr(module, '__path__'):
                submodules = [name for _, name, _ in pkgutil.iter_modules(module.__path__)]
                if submodules:
                    features.extend([f"submodule: {sub}" for sub in submodules[:5]])
        except (AttributeError, TypeError):
            pass
        
        # Get main classes/functions
        try:
            members = inspect.getmembers(module)
            classes = [name for name, obj in members if inspect.isclass(obj) and not name.startswith('_')]
            functions = [name for name, obj in members if inspect.isfunction(obj) and not name.startswith('_')]
            
            if classes:
                features.extend([f"class: {cls}" for cls in classes[:3]])
            if functions:
                features.extend([f"function: {func}" for func in functions[:3]])
        except Exception:
            pass
        
        category = self._categorize_tool(module_name, "")
        doc_url = self._get_documentation_url(module_name)
        
        return BioPythonTool(
            name=module_name.split('.')[-1],  # Just the last part
            full_name=module_name,
            category=category,
            tool_type="module",
            description=description,
            features=features,
            documentation=doc_url
        )
    
    async def discover_all_biopython_tools(self) -> List[BioPythonTool]:
        """Discover ALL Biopython tools using introspection."""
        logger.info("Starting comprehensive Biopython discovery...")
        
        try:
            # Import Bio package
            import Bio
            
            # Get Biopython version and check compatibility
            bio_version = getattr(Bio, '__version__', '1.85')
            logger.info(f"Discovered Biopython version: {bio_version}")
            
            # Check for warnings about experimental code
            try:
                from Bio import BiopythonExperimentalWarning
                import warnings
                # We'll collect experimental modules but mark them
                warnings.simplefilter('ignore', BiopythonExperimentalWarning)
            except ImportError:
                logger.info("No experimental warning system detected")
            
            # Walk through all Bio modules
            discovered_modules = []
            
            for importer, modname, ispkg in pkgutil.walk_packages(
                path=Bio.__path__, 
                prefix=Bio.__name__ + '.',
                onerror=lambda x: logger.debug(f"Cannot import {x} - likely missing optional dependency")
            ):
                discovered_modules.append((modname, ispkg))
            
            logger.info(f"Found {len(discovered_modules)} total Bio modules")
            
            # Filter out known problematic/deprecated modules
            deprecated_modules = {
                'Bio.Fasta',  # Removed in 1.55
                'Bio.Prosite',  # Deprecated
                'Bio.Wise',  # Deprecated
            }
            
            # Process each module
            successful_imports = 0
            failed_imports = 0
            
            for module_name, is_package in discovered_modules:
                if module_name in self.processed_modules:
                    continue
                    
                # Skip known deprecated modules
                if module_name in deprecated_modules:
                    logger.debug(f"Skipping deprecated module: {module_name}")
                    continue
                
                try:
                    logger.debug(f"Processing {module_name}...")
                    
                    # Import the module with timeout for problematic modules
                    module = importlib.import_module(module_name)
                    self.processed_modules.add(module_name)
                    successful_imports += 1
                    
                    # Check if module is experimental
                    is_experimental = self._is_experimental_module(module, module_name)
                    
                    # Create tool for the module itself
                    module_tool = self._create_module_tool(module, module_name)
                    module_tool.version = bio_version
                    if is_experimental:
                        module_tool.description = f"[EXPERIMENTAL] {module_tool.description}"
                    
                    self.collected_tools.append(module_tool)
                    
                    # Extract functions and classes from the module
                    member_tools = self._extract_functions_and_classes(module, module_name)
                    for tool in member_tools:
                        tool.version = bio_version
                        if is_experimental:
                            tool.description = f"[EXPERIMENTAL] {tool.description}"
                    
                    self.collected_tools.extend(member_tools)
                    
                    # Small delay to be respectful
                    await asyncio.sleep(0.001)
                    
                except ImportError as e:
                    failed_imports += 1
                    logger.debug(f"Could not import {module_name}: {e} (likely missing optional dependency)")
                    continue
                except Exception as e:
                    failed_imports += 1
                    logger.warning(f"Error processing {module_name}: {e}")
                    continue
            
            logger.info(f"Successfully imported: {successful_imports} modules")
            logger.info(f"Failed imports: {failed_imports} modules (expected for optional dependencies)")
            logger.info(f"Total tools discovered: {len(self.collected_tools)}")
            
            return self.collected_tools
            
        except ImportError as e:
            logger.error(f"Biopython not installed or not accessible: {e}")
            return []
        except Exception as e:
            logger.error(f"Error during Biopython discovery: {e}")
            return []
    
    def _generate_collection_report(self, tools: List[Dict]):
        """Generate comprehensive collection report."""
        categories = {}
        tool_types = {}
        
        for tool in tools:
            # Count by category
            category = tool.get('category', 'Unknown')
            categories[category] = categories.get(category, 0) + 1
            
            # Count by tool type
            tool_type = tool.get('tool_type', 'Unknown')
            tool_types[tool_type] = tool_types.get(tool_type, 0) + 1
        
        report = {
            "collection_summary": {
                "total_tools": len(tools),
                "biopython_version": tools[0].get('version', '1.85') if tools else 'Unknown',
                "collection_timestamp": time.time(),
                "source": "Biopython Complete Collection"
            },
            "categories": categories,
            "tool_types": tool_types,
            "top_categories": sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10]
        }
        
        # Save report
        report_file = self.data_dir / "biopython_collection_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Collection report saved to: {report_file}")
        
        # Print summary
        logger.info("Biopython Collection Summary:")
        logger.info(f"  Total tools: {report['collection_summary']['total_tools']}")
        logger.info(f"  Categories: {len(categories)}")
        logger.info(f"  Tool types: {len(tool_types)}")
        
        logger.info("\nTop Categories:")
        for category, count in report["top_categories"]:
            percentage = (count / len(tools)) * 100
            logger.info(f"  {category:25} {count:3d} tools ({percentage:5.1f}%)")
        
        logger.info("\nTool Types:")
        for tool_type, count in sorted(tool_types.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(tools)) * 100
            logger.info(f"  {tool_type:15} {count:3d} tools ({percentage:5.1f}%)")
    
    async def collect_and_save(self) -> List[Dict]:
        """Main method to collect all Biopython tools and save them."""
        start_time = time.time()
        
        # Discover all tools
        tools = await self.discover_all_biopython_tools()
        
        if not tools:
            logger.error("No Biopython tools discovered!")
            return []
        
        # Convert to dictionary format
        tools_dict = [tool.to_dict() for tool in tools]
        
        # Save collected data
        output_file = self.data_dir / "complete_biopython_tools.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(tools_dict, f, indent=2, ensure_ascii=False)
        
        collection_time = time.time() - start_time
        
        # Generate report
        self._generate_collection_report(tools_dict)
        
        logger.info(f"Collection completed in {collection_time:.1f} seconds")
        logger.info(f"Data saved to: {output_file}")
        logger.info(f"Tools per second: {len(tools_dict) / collection_time:.1f}")
        
        return tools_dict


async def standalone_collection():
    """Standalone function to run collection from scripts folder."""
    print("🧬 Standalone Biopython Tools Collection")
    print("=" * 50)
    
    # Check if Biopython is available
    try:
        import Bio
        print(f"✅ Biopython {getattr(Bio, '__version__', 'unknown')} detected")
    except ImportError:
        print("❌ Biopython not found! Install with: pip install biopython")
        return False
    
    # Run collection
    collector = CompleteBiopythonCollector()
    print("🔍 Starting comprehensive Biopython collection...")
    
    start_time = time.time()
    tools = await collector.collect_and_save()
    total_time = time.time() - start_time
    
    if tools:
        print(f"\n🎉 Collection completed successfully!")
        print(f"📊 Collected {len(tools)} Biopython tools")
        print(f"⏱️  Total time: {total_time:.1f} seconds")
        print(f"🚀 Performance: {len(tools) / total_time:.1f} tools/second")
        print(f"💾 Data saved to: {collector.data_dir}")
        
        # Show top categories
        categories = {}
        for tool in tools:
            cat = tool.get('category', 'Unknown')
            categories[cat] = categories.get(cat, 0) + 1
        
        print(f"\n🏷️  Top Categories:")
        top_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
        for cat, count in top_cats:
            print(f"   {cat}: {count} tools")
        
        return True
    else:
        print("❌ Collection failed!")
        return False


if __name__ == "__main__":
    """Run as standalone script from scripts folder."""
    print("🧪 Running Biopython Collector from Scripts Folder")
    success = asyncio.run(standalone_collection())
    
    if success:
        print("\n✅ Collection completed! Files saved to data/biopython_collection/")
        print("🔗 Ready to integrate with load_biopython_tools.py script")
    else:
        print("\n❌ Collection failed. Check error messages above.")
        sys.exit(1)