# src/scripts/bioconductor_tools_collector.py

"""
Fixed Bioconductor Tools Collector
Uses the official Bioconductor PACKAGES file to get accurate package names.
Then extracts information from individual package pages as per user's plan.

Usage:
    python src/scripts/bioconductor_tools_collector.py

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
class BioconductorTool:
    """Represents a single Bioconductor package."""
    name: str
    category: str
    description: str
    features: List[str]
    documentation: str
    source: str = "Bioconductor"
    version: Optional[str] = None
    programming_language: str = "R"
    license: str = "Artistic-2.0"
    installation_guide: str = ""
    tool_type: str = "package"
    author: Optional[str] = None
    maintainer: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary format for ChromaDB."""
        return {
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "features": self.features,
            "documentation": self.documentation,
            "source": self.source,
            "version": self.version or "3.21",
            "programming_language": self.programming_language,
            "license": self.license,
            "installation_guide": self.installation_guide,
            "tool_type": self.tool_type,
            "full_name": self.name,  # For Bioconductor, name and full_name are the same
            "author": self.author,
            "maintainer": self.maintainer
        }

class FixedBioconductorCollector:
    """
    Fixed Bioconductor collector using the official PACKAGES file approach.
    This is much more reliable than parsing the BiocViews HTML page.
    """
    
    def __init__(self):
        self.collected_tools: List[BioconductorTool] = []
        self.processed_packages: Set[str] = set()
        
        # Set data directory relative to project root
        self.data_dir = project_root / "data" / "bioconductor_collection"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Official Bioconductor URLs - more reliable approach
        self.base_url = "https://bioconductor.org"
        self.packages_file_url = "https://bioconductor.org/packages/release/bioc/src/contrib/PACKAGES"
        self.package_base_url = "https://bioconductor.org/packages/release/bioc/html"
        
        # Session for HTTP requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Category mapping for better organization
        self.category_mapping = {
            'annotation': 'Annotation',
            'microarray': 'Microarray Analysis',
            'rnaseq': 'RNA-seq Analysis',
            'rna': 'RNA-seq Analysis',
            'sequencing': 'Sequencing Analysis',
            'seq': 'Sequencing Analysis',
            'genomics': 'Genomics',
            'proteomics': 'Proteomics',
            'metabolomics': 'Metabolomics',
            'statistics': 'Statistical Analysis',
            'stat': 'Statistical Analysis',
            'visualization': 'Visualization',
            'plot': 'Visualization',
            'vis': 'Visualization',
            'workflow': 'Workflow',
            'infrastructure': 'Infrastructure',
            'classification': 'Classification',
            'clustering': 'Clustering',
            'preprocess': 'Data Preprocessing',
            'quality': 'Quality Control',
            'qc': 'Quality Control',
            'alignment': 'Sequence Alignment',
            'align': 'Sequence Alignment',
            'assembly': 'Genome Assembly',
            'variant': 'Variant Analysis',
            'pathway': 'Pathway Analysis',
            'network': 'Network Analysis',
            'single': 'Single Cell Analysis',
            'cell': 'Cell Biology',
            'immuno': 'Immunology',
            'cancer': 'Cancer Research',
            'epigenomics': 'Epigenomics',
            'epigenetic': 'Epigenomics',
            'transcriptomics': 'Transcriptomics',
            'gene': 'Gene Expression',
            'expression': 'Gene Expression'
        }
    
    def _categorize_package(self, package_name: str, description: str = "") -> str:
        """Categorize a package based on its name and description."""
        name_lower = package_name.lower()
        desc_lower = description.lower()
        
        # Check for specific patterns in name and description
        for keyword, category in self.category_mapping.items():
            if keyword in name_lower or keyword in desc_lower:
                return category
        
        # Default category
        return 'General Bioinformatics'
    
    def _clean_description(self, description: str) -> str:
        """Clean and format the description text."""
        if not description:
            return "Bioconductor package for bioinformatics analysis"
        
        # Remove extra whitespace and normalize
        description = ' '.join(description.split())
        
        # Remove HTML tags if any
        description = re.sub(r'<[^>]+>', '', description)
        
        # Remove common prefixes
        description = re.sub(r'^(This package provides?|This package is|The package)', '', description, flags=re.IGNORECASE)
        
        # Limit length
        if len(description) > 800:
            description = description[:800] + "..."
        
        return description.strip()
    
    def _extract_features_from_description(self, description: str, package_name: str) -> List[str]:
        """Extract key features from the description."""
        features = []
        
        # Common bioinformatics features based on description patterns
        feature_patterns = [
            r'provides?\s+([^.]+)',
            r'implements?\s+([^.]+)', 
            r'supports?\s+([^.]+)',
            r'includes?\s+([^.]+)',
            r'enables?\s+([^.]+)',
            r'performs?\s+([^.]+)',
            r'for\s+([^.]+analysis)',
            r'to\s+(analyze|process|identify|detect|compare|visualize)\s+([^.]+)'
        ]
        
        for pattern in feature_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    feature = ' '.join(match).strip()
                else:
                    feature = match.strip()
                
                if len(feature) > 5 and len(feature) < 80:
                    features.append(feature)
                    if len(features) >= 5:
                        break
            if len(features) >= 5:
                break
        
        # If no features found, create generic ones based on package name
        if not features:
            name_lower = package_name.lower()
            if 'seq' in name_lower:
                features = ["sequence analysis", "bioinformatics processing", "data analysis"]
            elif 'stat' in name_lower:
                features = ["statistical analysis", "data modeling", "hypothesis testing"]
            elif 'plot' in name_lower or 'vis' in name_lower:
                features = ["data visualization", "plotting", "graphical analysis"]
            else:
                features = ["bioinformatics analysis", "data processing", "computational biology"]
        
        return features[:5]  # Limit to 5 features
    
    def _fetch_packages_list(self) -> List[str]:
        """
        Fetch the official list of package names from the PACKAGES file.
        This is much more reliable than parsing HTML.
        """
        try:
            logger.info("Fetching official Bioconductor PACKAGES file...")
            logger.info(f"URL: {self.packages_file_url}")
            
            response = self.session.get(self.packages_file_url, timeout=30)
            response.raise_for_status()
            
            packages_text = response.text
            package_names = []
            
            # Parse the DCF (Debian Control Format) file
            current_package = None
            for line in packages_text.split('\n'):
                line = line.strip()
                
                if line.startswith('Package:'):
                    # Extract package name
                    package_name = line.split(':', 1)[1].strip()
                    if package_name and package_name not in package_names:
                        package_names.append(package_name)
                        logger.debug(f"Found package: {package_name}")
            
            logger.info(f"Successfully extracted {len(package_names)} package names from PACKAGES file")
            
            # Log first few packages for verification
            if package_names:
                logger.info(f"First 10 packages: {package_names[:10]}")
            
            return package_names
            
        except Exception as e:
            logger.error(f"Error fetching PACKAGES file: {e}")
            traceback.print_exc()
            return []
    
    def _fetch_page_content(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a web page."""
        try:
            logger.debug(f"Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            return soup
            
        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return None
    
    def _extract_package_info(self, soup: BeautifulSoup, package_name: str) -> Dict[str, str]:
        """
        Extract package information from the package page.
        FIXED: Now correctly extracts description between "Bioconductor version" and "Author" sections.
        """
        info = {
            'description': '',
            'version': '',
            'author': '',
            'maintainer': ''
        }
        
        try:
            # Get all text content for parsing
            page_text = soup.get_text()
            
            # Try to find the main content area
            main_content = soup.find('div', {'class': ['content', 'main-content', 'package-content']})
            if not main_content:
                main_content = soup.find('body')
            
            if main_content:
                content_text = main_content.get_text()
            else:
                content_text = page_text
            
            # FIXED: Extract description between "Bioconductor version" and "Author"
            description_patterns = [
                # Pattern 1: Text between "Bioconductor version" and "Author"
                r'Bioconductor version[^\n]*\n+(.*?)\n+Author',
                # Pattern 2: Text between "Release" and "Author" 
                r'Release[^\n]*\n+(.*?)\n+Author',
                # Pattern 3: Text between version info and "Author"
                r'version[^\n]*\n+(.*?)\n+Author',
                # Pattern 4: Text between "Bioconductor version" and any metadata field
                r'Bioconductor version[^\n]*\n+(.*?)\n+(?:Author|Maintainer|License|Version)',
                # Pattern 5: Look for substantial paragraphs before author section
                r'\n\s*([A-Z][^.]{30,}[.!?])\s*\n+.*?Author',
            ]
            
            description_found = False
            for pattern in description_patterns:
                match = re.search(pattern, content_text, re.IGNORECASE | re.DOTALL)
                if match:
                    desc = match.group(1).strip()
                    
                    # Clean up the description
                    desc = re.sub(r'\s+', ' ', desc)  # Normalize whitespace
                    desc = re.sub(r'\n+', ' ', desc)  # Replace newlines with spaces
                    
                    # Remove common unwanted patterns
                    desc = re.sub(r'^\s*' + re.escape(package_name) + r'\s*', '', desc, flags=re.IGNORECASE)
                    desc = re.sub(r'This is the released version.*?devel version.*?\.', '', desc, flags=re.IGNORECASE)
                    desc = re.sub(r'Package:\s*' + re.escape(package_name), '', desc, flags=re.IGNORECASE)
                    
                    # Only use substantial descriptions
                    if len(desc.strip()) > 20 and not desc.strip().lower().startswith(('author', 'maintainer', 'license')):
                        info['description'] = desc.strip()
                        logger.debug(f"Found description for {package_name}: {desc.strip()[:80]}...")
                        description_found = True
                        break
            
            # If no description found with the above patterns, try alternative approaches
            if not description_found:
                # Try to find description in HTML elements more specifically
                # Look for paragraphs that contain substantial content
                paragraphs = soup.find_all('p')
                for p in paragraphs:
                    p_text = p.get_text().strip()
                    # Clean and check if this looks like a package description
                    p_text_clean = re.sub(r'\s+', ' ', p_text)
                    
                    # Skip if it's too short or contains metadata keywords
                    if (len(p_text_clean) > 30 and 
                        not any(keyword in p_text_clean.lower() for keyword in 
                            ['author:', 'maintainer:', 'license:', 'version:', 'depends:', 'imports:']) and
                        not p_text_clean.lower().startswith(('this is the released version', 'package:', 'author', 'maintainer'))):
                        
                        info['description'] = p_text_clean
                        logger.debug(f"Found description in paragraph for {package_name}: {p_text_clean[:80]}...")
                        description_found = True
                        break
            
            # Extract Bioconductor version
            version_patterns = [
                r'Bioconductor version[:\s]*Release\s*\(([0-9\.]+)\)',
                r'Release\s*\(([0-9\.]+)\)',
                r'Version[:\s]*([0-9\.]+)',
                r'Bioconductor\s*([0-9\.]+)',
                r'release\s*([0-9\.]+)'
            ]
            
            for pattern in version_patterns:
                match = re.search(pattern, content_text, re.IGNORECASE)
                if match:
                    info['version'] = match.group(1)
                    logger.debug(f"Found version: {info['version']}")
                    break
            
            # Extract Author
            author_patterns = [
                r'Author[:\s]*([^\n\r]+)',
                r'Authors?[:\s]*([^\n\r]+)',
                r'Package author[:\s]*([^\n\r]+)'
            ]
            
            for pattern in author_patterns:
                match = re.search(pattern, content_text, re.IGNORECASE)
                if match:
                    author = match.group(1).strip()
                    # Clean up author field (remove emails, extra spaces)
                    author = re.sub(r'<[^>]+>', '', author)  # Remove emails
                    author = re.sub(r'\[[^\]]+\]', '', author)  # Remove role indicators
                    author = re.sub(r'\s+', ' ', author)     # Normalize spaces
                    if len(author) > 3 and len(author) < 200:
                        info['author'] = author
                        logger.debug(f"Found author: {author}")
                        break
            
            # Extract Maintainer
            maintainer_patterns = [
                r'Maintainer[:\s]*([^\n\r]+)',
                r'Package maintainer[:\s]*([^\n\r]+)'
            ]
            
            for pattern in maintainer_patterns:
                match = re.search(pattern, content_text, re.IGNORECASE)
                if match:
                    maintainer = match.group(1).strip()
                    # Clean up maintainer field
                    maintainer = re.sub(r'<[^>]+>', '', maintainer)  # Remove emails
                    maintainer = re.sub(r'\s+', ' ', maintainer)     # Normalize spaces
                    if len(maintainer) > 3 and len(maintainer) < 200:
                        info['maintainer'] = maintainer
                        logger.debug(f"Found maintainer: {maintainer}")
                        break
            
            # Clean and validate extracted information
            info['description'] = self._clean_description(info['description'])
            
            # Set defaults if not found
            if not info['version']:
                info['version'] = '3.21'  # Default Bioconductor version
            if not info['description']:
                info['description'] = f'Bioconductor package {package_name} for bioinformatics analysis'
                
        except Exception as e:
            logger.warning(f"Error extracting info for {package_name}: {e}")
            # Set defaults
            info['version'] = '3.21'
            info['description'] = f'Bioconductor package {package_name} for bioinformatics analysis'
        
        return info
    
    def _create_package_tool(self, package_name: str, package_info: Dict[str, str]) -> BioconductorTool:
        """Create a BioconductorTool object for a package."""
        description = package_info.get('description', f'Bioconductor package {package_name}')
        category = self._categorize_package(package_name, description)
        features = self._extract_features_from_description(description, package_name)
        
        package_url = f"{self.package_base_url}/{package_name}.html"
        installation_cmd = f'BiocManager::install("{package_name}")'
        
        return BioconductorTool(
            name=package_name,
            category=category,
            description=description,
            features=features,
            documentation=package_url,
            version=package_info.get('version', '3.21'),
            author=package_info.get('author'),
            maintainer=package_info.get('maintainer'),
            installation_guide=installation_cmd
        )
    
    async def discover_all_bioconductor_packages(self) -> List[BioconductorTool]:
        """
        Discover all Bioconductor packages using the fixed approach:
        1. Use the official PACKAGES file to get all package names
        2. For each package, visit its individual page  
        3. Extract version, description, author, maintainer as requested
        """
        logger.info("Starting FIXED Bioconductor package discovery...")
        
        try:
            # Step 1: Get package names from official PACKAGES file (much more reliable)
            logger.info("Step 1: Fetching package names from official PACKAGES file...")
            package_names = self._fetch_packages_list()
            
            if not package_names:
                logger.error("No package names found from PACKAGES file!")
                return []
            
            logger.info(f"✅ Found {len(package_names)} official Bioconductor packages")
            
            # Step 2-4: For each package, visit its page and extract info
            successful_extractions = 0
            failed_extractions = 0
            batch_size = 25  # Reasonable batch size
            
            # Limit to first 100 packages for testing (remove this for full collection)
            # package_names = package_names[:100]  # Uncomment for testing
            
            for i in range(0, len(package_names), batch_size):
                batch = package_names[i:i + batch_size]
                batch_num = i//batch_size + 1
                total_batches = (len(package_names) + batch_size - 1)//batch_size
                
                logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} packages)")
                
                for package_name in batch:
                    if package_name in self.processed_packages:
                        continue
                    
                    try:
                        logger.debug(f"Processing package: {package_name}")
                        
                        # Construct package URL (following user's exact specification)
                        package_url = f"{self.package_base_url}/{package_name}.html"
                        
                        # Fetch package page
                        package_soup = self._fetch_page_content(package_url)
                        
                        if package_soup:
                            # Extract info (version, description, author, maintainer)
                            package_info = self._extract_package_info(package_soup, package_name)
                            
                            # Create tool object
                            tool = self._create_package_tool(package_name, package_info)
                            
                            self.collected_tools.append(tool)
                            self.processed_packages.add(package_name)
                            successful_extractions += 1
                            
                            logger.debug(f"✅ Successfully processed {package_name}")
                        else:
                            failed_extractions += 1
                            logger.warning(f"❌ Failed to fetch page for {package_name}")
                        
                        # Small delay to be respectful (0.1 seconds per request)
                        await asyncio.sleep(0.1)
                        
                    except Exception as e:
                        failed_extractions += 1
                        logger.error(f"Error processing {package_name}: {e}")
                        continue
                
                # Longer delay between batches
                if i + batch_size < len(package_names):
                    logger.info(f"Completed batch {batch_num}. Waiting 2 seconds before next batch...")
                    await asyncio.sleep(2)
            
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
        authors = {}
        
        for tool in tools:
            # Count by category
            category = tool.get('category', 'Unknown')
            categories[category] = categories.get(category, 0) + 1
            
            # Count by author (first author)
            author = tool.get('author', '')
            if author:
                first_author = author.split(',')[0].split('[')[0].strip()
                if first_author and len(first_author) > 2:
                    authors[first_author] = authors.get(first_author, 0) + 1
        
        report = {
            "collection_summary": {
                "total_tools": len(tools),
                "bioconductor_version": tools[0].get('version', '3.21') if tools else 'Unknown',
                "collection_timestamp": time.time(),
                "source": "Bioconductor Official PACKAGES File + Individual Pages",
                "method": "FIXED: Official PACKAGES file → Individual package pages",
                "improvements": [
                    "✅ Uses official Bioconductor PACKAGES file for reliable package discovery",
                    "✅ Avoids parsing complex HTML tables",
                    "✅ Follows user's exact URL pattern for package pages",
                    "✅ Extracts author and maintainer information as requested",
                    "✅ Handles 2000+ packages efficiently with rate limiting"
                ]
            },
            "categories": categories,
            "top_categories": sorted(categories.items(), key=lambda x: x[1], reverse=True)[:15],
            "top_authors": sorted(authors.items(), key=lambda x: x[1], reverse=True)[:20],
            "extraction_method": "Fixed Official PACKAGES Approach",
            "base_url": self.base_url
        }
        
        # Save report
        report_file = self.data_dir / "bioconductor_collection_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Collection report saved to: {report_file}")
        
        # Print summary
        logger.info("FIXED Bioconductor Collection Summary:")
        logger.info(f"  Total packages: {report['collection_summary']['total_tools']}")
        logger.info(f"  Categories: {len(categories)}")
        logger.info(f"  Method: {report['extraction_method']}")
        
        logger.info("\nTop Categories:")
        for category, count in report["top_categories"]:
            percentage = (count / len(tools)) * 100
            logger.info(f"  {category:30} {count:4d} packages ({percentage:5.1f}%)")
        
        if report["top_authors"]:
            logger.info("\nTop Authors:")
            for author, count in report["top_authors"][:10]:
                logger.info(f"  {author:30} {count:3d} packages")
    
    async def collect_and_save(self) -> List[Dict]:
        """Main method to collect all Bioconductor packages and save them."""
        start_time = time.time()
        
        logger.info("Starting FIXED Bioconductor package collection...")
        
        # Discover all packages
        tools = await self.discover_all_bioconductor_packages()
        
        if not tools:
            logger.error("No Bioconductor packages discovered!")
            return []
        
        # Convert to dictionary format
        tools_dict = [tool.to_dict() for tool in tools]
        
        # Save collected data
        output_file = self.data_dir / "complete_bioconductor_tools.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(tools_dict, f, indent=2, ensure_ascii=False)
        
        collection_time = time.time() - start_time
        
        # Generate report
        self._generate_collection_report(tools_dict)
        
        logger.info(f"Collection completed in {collection_time:.1f} seconds")
        logger.info(f"Data saved to: {output_file}")
        logger.info(f"Packages per second: {len(tools_dict) / collection_time:.1f}")
        
        return tools_dict


async def standalone_collection():
    """Standalone function to run collection from scripts folder."""
    print("🔧 FIXED Bioconductor Package Collection")
    print("=" * 60)
    print("🛠️  Using the OFFICIAL Bioconductor PACKAGES file approach")
    print("✅ This method is much more reliable than parsing HTML tables")
    print()
    print("Steps:")
    print("1. 📥 Fetch official PACKAGES file from Bioconductor")
    print("2. 📋 Extract all package names (accurate and complete)")
    print("3. 🌐 Visit each package page following your URL pattern")
    print("4. 📊 Extract: version, description, author, maintainer")
    print("5. 💾 Process all ~2341 packages with rate limiting")
    print()
    
    # Check internet connectivity
    try:
        test_response = requests.get("https://bioconductor.org", timeout=10)
        print(f"✅ Internet connectivity verified (Status: {test_response.status_code})")
    except Exception as e:
        print(f"❌ Internet connectivity issue: {e}")
        print("Please check your internet connection and try again.")
        return False
    
    # Run collection
    collector = FixedBioconductorCollector()
    print("🔍 Starting FIXED comprehensive Bioconductor package collection...")
    print("⏱️  Expected time: 8-15 minutes with respectful rate limiting")
    
    start_time = time.time()
    tools = await collector.collect_and_save()
    total_time = time.time() - start_time
    
    if tools:
        print(f"\n🎉 FIXED collection completed successfully!")
        print(f"📊 Collected {len(tools)} Bioconductor packages")
        print(f"⏱️  Total time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
        print(f"🚀 Performance: {len(tools) / total_time:.1f} packages/second")
        print(f"💾 Data saved to: {collector.data_dir}")
        
        # Show sample packages
        print(f"\n📦 Sample Packages:")
        for tool in tools[:5]:
            print(f"   • {tool['name']}: {tool['description'][:60]}...")
            if tool.get('author'):
                print(f"     Author: {tool['author'][:50]}...")
            if tool.get('maintainer'):
                print(f"     Maintainer: {tool['maintainer'][:50]}...")
        
        # Show top categories
        categories = {}
        for tool in tools:
            cat = tool.get('category', 'Unknown')
            categories[cat] = categories.get(cat, 0) + 1
        
        print(f"\n🏷️  Top Categories:")
        top_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
        for cat, count in top_cats:
            print(f"   {cat}: {count} packages")
        
        print(f"\n✨ FIXED Method Advantages:")
        print("   ✅ Uses official Bioconductor PACKAGES file (not HTML parsing)")
        print("   ✅ Gets accurate package names (not navigation menu items)")
        print("   ✅ Follows your exact URL pattern for package pages")
        print("   ✅ Extracts author and maintainer as requested")
        print("   ✅ Handles 2000+ packages efficiently")
        print("   ✅ Much more reliable than previous HTML table parsing")
        
        return True
    else:
        print("❌ Collection failed!")
        return False


if __name__ == "__main__":
    """Run as standalone script from scripts folder."""
    print("🔧 Running FIXED Bioconductor Package Collector")
    success = asyncio.run(standalone_collection())
    
    if success:
        print("\n✅ FIXED Bioconductor collection completed! Files saved to data/bioconductor_collection/")
        print("🔗 Ready to integrate with ChromaDB")
        print("🎯 Uses reliable PACKAGES file approach instead of HTML parsing")
        print("📋 Next: Use this data with your load_bioconductor_tools.py script!")
    else:
        print("\n❌ Collection failed. Check error messages above.")
        sys.exit(1)