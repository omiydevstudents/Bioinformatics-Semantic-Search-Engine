# src/scripts/biopython_tools_collector.py

"""
Complete Biopython Tools Collector (Updated Web Scraping Version)
Extracts Biopython package information from official documentation.

This collector scrapes the official Biopython documentation to get
accurate, up-to-date package information instead of using introspection.

Usage:
    python src/scripts/biopython_tools_collector.py

Author: Nitanshu (ChromaDB & RAG Pipeline)
"""

import asyncio
import sys
import os
import json
import time
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Set
from pathlib import Path
from dataclasses import dataclass
import traceback
import logging
import re
from urllib.parse import urljoin, urlparse

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BioPythonTool:
    """Represents a single Biopython package/tool."""
    name: str
    full_name: str  # e.g., Bio.Seq
    category: str
    tool_type: str  # Always "package" for this version
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
    """Web scraping collector for Biopython packages from official documentation."""
    
    def __init__(self):
        self.collected_tools: List[BioPythonTool] = []
        self.processed_packages: Set[str] = set()
        
        # Set data directory relative to project root
        self.data_dir = project_root / "data" / "biopython_collection"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Base URLs for Biopython documentation
        self.base_url = "https://biopython.org/docs/latest/api/"
        self.main_bio_url = "https://biopython.org/docs/latest/api/Bio.html"
        
        # Session for HTTP requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; BioinformaticsSearchEngine/1.0; +https://github.com/bioinformatics-search)'
        })
        
        # Category mapping for better organization
        self.category_mapping = {
            'affy': 'Microarray Analysis',
            'align': 'Sequence Alignment',
            'alignio': 'Alignment I/O',
            'application': 'External Applications',
            'blast': 'Sequence Search',
            'cluster': 'Clustering Analysis',
            'compass': 'Sequence Compass',
            'data': 'Data Resources',
            'entrez': 'Database Access',
            'expasy': 'ExPASy Tools',
            'genbank': 'GenBank Format',
            'graphics': 'Visualization',
            'kegg': 'KEGG Database',
            'markovmodel': 'Markov Models',
            'medline': 'Literature Search',
            'motifs': 'Sequence Motifs',
            'nexus': 'Nexus Format',
            'pairwise2': 'Pairwise Alignment',
            'pathway': 'Pathway Analysis',
            'pdb': 'Protein Structure',
            'phenotype': 'Phenotype Analysis',
            'phylo': 'Phylogenetics',
            'popgen': 'Population Genetics',
            'restriction': 'Restriction Analysis',
            'scop': 'SCOP Database',
            'seq': 'Sequence Objects',
            'seqio': 'Sequence I/O',
            'sequtils': 'Sequence Utilities',
            'sequencing': 'Sequencing Analysis',
            'swisssample': 'Swiss-Prot Samples',
            'uniprot': 'UniProt Database',
            'biosql': 'Database Storage'
        }
    
    def _categorize_package(self, package_name: str) -> str:
        """Categorize a package based on its name."""
        # Remove Bio. prefix for categorization
        clean_name = package_name.replace('Bio.', '').lower()
        
        # Check for exact matches first
        if clean_name in self.category_mapping:
            return self.category_mapping[clean_name]
        
        # Check for partial matches
        for keyword, category in self.category_mapping.items():
            if keyword in clean_name:
                return category
        
        # Default category
        return 'General Bioinformatics'
    
    def _clean_description(self, description: str) -> str:
        """Clean and format the description text."""
        if not description:
            return "Biopython package for bioinformatics analysis"
        
        # Remove extra whitespace and normalize
        description = ' '.join(description.split())
        
        # Remove HTML tags if any
        description = re.sub(r'<[^>]+>', '', description)
        
        # Limit length
        if len(description) > 1000:
            description = description[:1000] + "..."
        
        return description
    
    def _extract_features_from_description(self, description: str) -> List[str]:
        """Extract key features from the description."""
        features = []
        
        # Common patterns to extract features
        feature_patterns = [
            r'provides?\s+([^.]+)',
            r'includes?\s+([^.]+)',
            r'supports?\s+([^.]+)',
            r'implements?\s+([^.]+)',
            r'handles?\s+([^.]+)',
            r'for\s+([^.]+)',
            r'to\s+([^.]+)'
        ]
        
        for pattern in feature_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            for match in matches:
                if len(match.strip()) > 5 and len(match.strip()) < 100:
                    features.append(match.strip())
                    if len(features) >= 5:  # Limit to 5 features
                        break
            if len(features) >= 5:
                break
        
        # If no features found, create generic ones
        if not features:
            features = [
                "bioinformatics analysis",
                "data processing",
                "sequence analysis"
            ]
        
        return features[:5]  # Limit to 5 features
    
    def _fetch_page_content(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a web page."""
        try:
            logger.debug(f"Fetching: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            return soup
            
        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return None
    
    def _extract_package_links(self, soup: BeautifulSoup) -> List[tuple]:
        """Extract package links from the main Bio page."""
        package_links = []
        
        try:
            # Look for package links in the documentation
            # Pattern: Bio.PackageName package
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                text = link.get_text().strip()
                
                # Check if this is a package link (not module)
                if ('Bio.' in text and 
                    'package' in text and 
                    '.html' in href and
                    '#' not in href):  # Avoid fragment links
                    
                    # Extract package name
                    package_match = re.search(r'Bio\.(\w+)', text)
                    if package_match:
                        package_name = f"Bio.{package_match.group(1)}"
                        full_url = urljoin(self.base_url, href)
                        package_links.append((package_name, full_url))
                        logger.debug(f"Found package: {package_name} -> {full_url}")
        
        except Exception as e:
            logger.error(f"Error extracting package links: {e}")
        
        return package_links
    
    def _extract_package_description(self, soup: BeautifulSoup, package_name: str) -> str:
        """Extract package description from the package page."""
        try:
            # Construct URL as requested: self.base_url{package_name}.html#module-{package_name}
            url = f"{self.base_url}{package_name}.html#module-{package_name}"
            
            # Fetch the webpage
            page_soup = self._fetch_page_content(url)
            if not page_soup:
                return self._clean_description("")
            
            # Find section with id="module-{package_name}"
            section = page_soup.find('section', id=f'module-{package_name}')
            if not section:
                return self._clean_description("")
            
            # Extract all text content from the section
            description_text = section.get_text()
            
            # Remove "Module contents" heading
            description_text = description_text.replace("Module contents", "").strip()
            
            return self._clean_description(description_text)
            
        except Exception:
            return self._clean_description("")
    
    def _create_package_tool(self, package_name: str, package_url: str, description: str) -> BioPythonTool:
        """Create a BioPythonTool object for a package."""
        category = self._categorize_package(package_name)
        features = self._extract_features_from_description(description)
        
        return BioPythonTool(
            name=package_name.split('.')[-1],  # Just the package name (e.g., "Blast")
            full_name=package_name,            # Full name (e.g., "Bio.Blast")
            category=category,
            tool_type="package",
            description=description,
            features=features,
            documentation=package_url
        )
    
    def _add_biosql_manually(self):
        """Add BioSQL package manually with provided information."""
        biosql_tool = BioPythonTool(
            name="BioSQL",
            full_name="BioSQL",
            category="Database Storage",
            tool_type="package",
            description="Storing and retrieve biological sequences in a BioSQL relational database.",
            features=[
                "relational database storage",
                "biological sequence management",
                "database schema",
                "SQL interface",
                "sequence retrieval"
            ],
            documentation="https://biopython.org/docs/latest/api/BioSQL.html"
        )
        
        self.collected_tools.append(biosql_tool)
        logger.info("Added BioSQL package manually")
    
    async def discover_all_biopython_packages(self) -> List[BioPythonTool]:
        """Discover all Biopython packages by scraping the official documentation."""
        logger.info("Starting Biopython package discovery via web scraping...")
        
        try:
            # Check if Biopython is available (for version info)
            try:
                import Bio
                bio_version = getattr(Bio, '__version__', '1.85')
                logger.info(f"Detected Biopython version: {bio_version}")
            except ImportError:
                bio_version = "1.85"
                logger.info("Biopython not installed locally - using version 1.85 as default")
            
            # Step 1: Fetch the main Bio page
            logger.info(f"Fetching main Bio documentation page: {self.main_bio_url}")
            main_soup = self._fetch_page_content(self.main_bio_url)
            
            if not main_soup:
                logger.error("Failed to fetch main Bio page")
                return []
            
            # Step 2: Extract package links
            logger.info("Extracting package links...")
            package_links = self._extract_package_links(main_soup)
            
            if not package_links:
                logger.warning("No package links found - trying alternative extraction method")
                # Alternative: look for any Bio.* links
                for link in main_soup.find_all('a', href=True):
                    href = link.get('href', '')
                    text = link.get_text().strip()
                    
                    if ('Bio.' in href and 
                        '.html' in href and
                        '#' not in href):
                        
                        # Extract package name from URL
                        url_match = re.search(r'Bio\.(\w+)\.html', href)
                        if url_match:
                            package_name = f"Bio.{url_match.group(1)}"
                            full_url = urljoin(self.base_url, href)
                            package_links.append((package_name, full_url))
            
            logger.info(f"Found {len(package_links)} package links")
            
            # Step 3: Process each package
            successful_extractions = 0
            failed_extractions = 0
            
            for package_name, package_url in package_links:
                if package_name in self.processed_packages:
                    continue
                
                try:
                    logger.info(f"Processing package: {package_name}")
                    
                    # Fetch package page
                    package_soup = self._fetch_page_content(package_url)
                    
                    if package_soup:
                        # Extract description
                        description = self._extract_package_description(package_soup, package_name)
                        
                        # Create tool object
                        tool = self._create_package_tool(package_name, package_url, description)
                        tool.version = bio_version
                        
                        self.collected_tools.append(tool)
                        self.processed_packages.add(package_name)
                        successful_extractions += 1
                        
                        logger.debug(f"Successfully processed {package_name}")
                        
                        # Small delay to be respectful
                        await asyncio.sleep(0.1)
                    else:
                        failed_extractions += 1
                        logger.warning(f"Failed to fetch page for {package_name}")
                        
                except Exception as e:
                    failed_extractions += 1
                    logger.error(f"Error processing {package_name}: {e}")
                    continue
            
            # Step 4: Add BioSQL manually
            self._add_biosql_manually()
            successful_extractions += 1
            
            logger.info(f"Package discovery completed:")
            logger.info(f"  Successfully processed: {successful_extractions}")
            logger.info(f"  Failed extractions: {failed_extractions}")
            logger.info(f"  Total tools collected: {len(self.collected_tools)}")
            
            return self.collected_tools
            
        except Exception as e:
            logger.error(f"Error during package discovery: {e}")
            traceback.print_exc()
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
                "source": "Biopython Documentation Scraping",
                "method": "Web scraping from biopython.org/docs/latest/api/"
            },
            "categories": categories,
            "tool_types": tool_types,
            "top_categories": sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10],
            "extraction_method": "Official Biopython Documentation",
            "base_url": self.base_url
        }
        
        # Save report
        report_file = self.data_dir / "biopython_collection_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Collection report saved to: {report_file}")
        
        # Print summary
        logger.info("Biopython Web Scraping Collection Summary:")
        logger.info(f"  Total packages: {report['collection_summary']['total_tools']}")
        logger.info(f"  Categories: {len(categories)}")
        logger.info(f"  Method: {report['extraction_method']}")
        
        logger.info("\nTop Categories:")
        for category, count in report["top_categories"]:
            percentage = (count / len(tools)) * 100
            logger.info(f"  {category:25} {count:3d} packages ({percentage:5.1f}%)")
    
    async def collect_and_save(self) -> List[Dict]:
        """Main method to collect all Biopython packages and save them."""
        start_time = time.time()
        
        logger.info("Starting Biopython documentation scraping...")
        
        # Discover all packages
        tools = await self.discover_all_biopython_packages()
        
        if not tools:
            logger.error("No Biopython packages discovered!")
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
        
        logger.info(f"Web scraping collection completed in {collection_time:.1f} seconds")
        logger.info(f"Data saved to: {output_file}")
        logger.info(f"Packages per second: {len(tools_dict) / collection_time:.1f}")
        
        return tools_dict


async def standalone_collection():
    """Standalone function to run collection from scripts folder."""
    print("🧬 Biopython Documentation Web Scraping Collection")
    print("=" * 60)
    print("Extracting packages from https://biopython.org/docs/latest/api/")
    
    # Check internet connectivity
    try:
        test_response = requests.get("https://biopython.org", timeout=5)
        print(f"✅ Internet connectivity verified (Status: {test_response.status_code})")
    except Exception as e:
        print(f"❌ Internet connectivity issue: {e}")
        print("Please check your internet connection and try again.")
        return False
    
    # Run collection
    collector = CompleteBiopythonCollector()
    print("🔍 Starting comprehensive Biopython package collection...")
    
    start_time = time.time()
    tools = await collector.collect_and_save()
    total_time = time.time() - start_time
    
    if tools:
        print(f"\n🎉 Collection completed successfully!")
        print(f"📊 Collected {len(tools)} Biopython packages")
        print(f"⏱️  Total time: {total_time:.1f} seconds")
        print(f"🚀 Performance: {len(tools) / total_time:.1f} packages/second")
        print(f"💾 Data saved to: {collector.data_dir}")
        
        # Show sample packages
        print(f"\n📦 Sample Packages:")
        for tool in tools[:5]:
            print(f"   • {tool['full_name']}: {tool['description'][:60]}...")
        
        # Show top categories
        categories = {}
        for tool in tools:
            cat = tool.get('category', 'Unknown')
            categories[cat] = categories.get(cat, 0) + 1
        
        print(f"\n🏷️  Top Categories:")
        top_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
        for cat, count in top_cats:
            print(f"   {cat}: {count} packages")
        
        print(f"\n✨ Key Advantages of Web Scraping Approach:")
        print("   • Always up-to-date with official documentation")
        print("   • No import dependencies or version conflicts")
        print("   • Includes official package descriptions")
        print("   • Follows Biopython's official package structure")
        print("   • Works even without Biopython installed locally")
        
        return True
    else:
        print("❌ Collection failed!")
        return False


if __name__ == "__main__":
    """Run as standalone script from scripts folder."""
    print("🧪 Running Biopython Web Scraper from Scripts Folder")
    success = asyncio.run(standalone_collection())
    
    if success:
        print("\n✅ Web scraping collection completed! Files saved to data/biopython_collection/")
        print("🔗 Ready to integrate with load_biopython_tools.py script")
        print("🎯 This new approach provides official, accurate package information!")
    else:
        print("\n❌ Web scraping collection failed. Check error messages above.")
        sys.exit(1)