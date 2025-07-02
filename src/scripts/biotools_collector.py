#!/usr/bin/env python3
"""
Bio.tools Collector - Fixed Version
Collects all bioinformatics tools from bio.tools API.
Excludes Biopython and Bioconductor tools as requested.
Follows the same pattern as existing collectors.

Author: Based on existing collector patterns
"""

import json
import time
import requests
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Set, Optional, Any
from dataclasses import dataclass, asdict
import sys
import re
import traceback

# Setup project paths
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class BioToolsTool:
    """Data structure for a bio.tools entry."""
    name: str
    description: str
    category: str
    documentation: str
    programming_language: str
    license: str = "Unknown"
    version: str = "Latest"
    source: str = "bio.tools"
    features: List[str] = None
    
    # Additional bio.tools specific fields
    biotoolsID: str = ""
    homepage: str = ""
    topics: List[str] = None
    operations: List[str] = None
    tool_types: List[str] = None
    maturity: str = ""
    publications: List[Dict] = None
    
    def __post_init__(self):
        if self.features is None:
            self.features = []
        if self.topics is None:
            self.topics = []
        if self.operations is None:
            self.operations = []
        if self.tool_types is None:
            self.tool_types = []
        if self.publications is None:
            self.publications = []
    
    def to_dict(self) -> Dict:
        """Convert to dictionary format."""
        return asdict(self)


class BioToolsCollector:
    """Collector for bio.tools registry."""
    
    def __init__(self):
        self.collected_tools: List[BioToolsTool] = []
        self.processed_ids: Set[str] = set()
        
        # Set data directory to match existing pattern
        self.data_dir = project_root / "data" / "biotools_collection"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # API configuration
        self.api_base = "https://bio.tools/api/tool/"
        self.base_url = "https://bio.tools/"
        
        # Session for HTTP requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BioToolsCollector/1.0 (Python; bioinformatics tool aggregator)',
            'Accept': 'application/json'
        })
        
        # Statistics
        self.stats = {
            'total_tools': 0,
            'excluded_biopython': 0,
            'excluded_bioconductor': 0,
            'api_errors': 0,
            'pages_fetched': 0
        }
        
        # Category mapping for consistency with other collectors
        self.category_mapping = {
            'Genomics': 'Genomics',
            'Transcriptomics': 'RNA-seq Analysis',
            'Proteomics': 'Proteomics',
            'Metabolomics': 'Metabolomics',
            'Systems biology': 'Systems Biology',
            'Sequence analysis': 'Sequence Analysis',
            'Structure analysis': 'Protein Structure',
            'Phylogenetics': 'Phylogenetics',
            'Metagenomics': 'Metagenomics',
            'Epigenomics': 'Epigenomics',
            'Data visualisation': 'Visualization',
            'Statistics and probability': 'Statistical Analysis',
            'Machine learning': 'Machine Learning',
            'Bioinformatics': 'General Bioinformatics'
        }
    
    def _should_exclude_tool(self, tool_data: Dict) -> bool:
        """Check if tool should be excluded (Biopython or Bioconductor)."""
        name = tool_data.get('name', '').lower()
        biotoolsID = tool_data.get('biotoolsID', '').lower()
        description = tool_data.get('description', '').lower()
        homepage = tool_data.get('homepage', '').lower()
        
        # Check for Biopython
        biopython_indicators = ['biopython', 'bio.', 'bio python']
        for indicator in biopython_indicators:
            if indicator in name or indicator in biotoolsID:
                self.stats['excluded_biopython'] += 1
                logger.debug(f"Excluding Biopython tool: {name}")
                return True
        
        # Check for Bioconductor
        bioconductor_indicators = ['bioconductor', 'bioc.', 'r package']
        if 'bioconductor.org' in homepage:
            self.stats['excluded_bioconductor'] += 1
            logger.debug(f"Excluding Bioconductor tool: {name}")
            return True
        
        for indicator in bioconductor_indicators:
            if indicator in name or indicator in biotoolsID:
                self.stats['excluded_bioconductor'] += 1
                logger.debug(f"Excluding Bioconductor tool: {name}")
                return True
        
        # Additional check: if it's primarily an R package
        languages = tool_data.get('language', [])
        if isinstance(languages, list) and len(languages) == 1 and 'R' in languages:
            # Check if it mentions Bioconductor in description
            if 'bioconductor' in description:
                self.stats['excluded_bioconductor'] += 1
                logger.debug(f"Excluding R/Bioconductor tool: {name}")
                return True
        
        return False
    
    def _categorize_tool(self, tool_data: Dict) -> str:
        """Categorize a tool based on its topics."""
        topics = tool_data.get('topic', [])
        
        if topics:
            # Use first topic's term
            first_topic = topics[0].get('term', '')
            
            # Map to our categories
            for key, value in self.category_mapping.items():
                if key.lower() in first_topic.lower():
                    return value
            
            # Default to first topic if no mapping
            return first_topic
        
        # Fallback categorization based on operations
        operations = []
        for function in tool_data.get('function', []):
            for op in function.get('operation', []):
                operations.append(op.get('term', ''))
        
        if operations:
            return operations[0]
        
        return 'General Bioinformatics'
    
    def _extract_features(self, tool_data: Dict) -> List[str]:
        """Extract features from tool data."""
        features = []
        
        # Add tool types as features
        for tool_type in tool_data.get('toolType', []):
            if tool_type:
                features.append(f"Type: {tool_type}")
        
        # Add operations as features
        for function in tool_data.get('function', []):
            for operation in function.get('operation', []):
                op_term = operation.get('term', '')
                if op_term:
                    features.append(f"Operation: {op_term}")
        
        # Add maturity as feature
        maturity = tool_data.get('maturity')
        if maturity:
            features.append(f"Maturity: {maturity}")
        
        return features[:10]  # Limit to 10 features
    
    def _create_tool_from_api_data(self, tool_data: Dict) -> Optional[BioToolsTool]:
        """Create a BioToolsTool object from API data."""
        try:
            # Skip if should be excluded
            if self._should_exclude_tool(tool_data):
                return None
            
            # Extract basic info
            name = tool_data.get('name', '')
            biotoolsID = tool_data.get('biotoolsID', '')
            
            if not name:
                return None
            
            # Extract description
            description = tool_data.get('description', 'No description available')
            
            # Extract documentation URL
            documentation = self.base_url + biotoolsID
            docs = tool_data.get('documentation', [])
            if docs and isinstance(docs, list) and docs[0].get('url'):
                documentation = docs[0]['url']
            
            # Extract programming languages
            languages = tool_data.get('language', [])
            if isinstance(languages, list) and languages:
                programming_language = ', '.join(languages)
            else:
                programming_language = 'Not specified'
            
            # Extract homepage
            homepage = tool_data.get('homepage', documentation)
            
            # Extract topics
            topics = []
            for topic in tool_data.get('topic', []):
                term = topic.get('term', '')
                if term:
                    topics.append(term)
            
            # Extract operations
            operations = []
            for function in tool_data.get('function', []):
                for operation in function.get('operation', []):
                    term = operation.get('term', '')
                    if term:
                        operations.append(term)
            
            # Extract tool types
            tool_types = tool_data.get('toolType', [])
            
            # Extract publications
            publications = []
            for pub in tool_data.get('publication', []):
                pub_info = {}
                if pub.get('doi'):
                    pub_info['doi'] = pub['doi']
                if pub.get('pmid'):
                    pub_info['pmid'] = pub['pmid']
                if pub_info:
                    publications.append(pub_info)
            
            # Create tool object
            tool = BioToolsTool(
                name=name,
                description=description,
                category=self._categorize_tool(tool_data),
                documentation=documentation,
                programming_language=programming_language,
                license=tool_data.get('license', 'Unknown'),
                version=', '.join(tool_data.get('version', ['Latest'])) if tool_data.get('version') else 'Latest',
                features=self._extract_features(tool_data),
                biotoolsID=biotoolsID,
                homepage=homepage,
                topics=topics,
                operations=operations,
                tool_types=tool_types,
                maturity=tool_data.get('maturity', ''),
                publications=publications
            )
            
            return tool
            
        except Exception as e:
            logger.error(f"Error creating tool from data: {e}")
            return None
    
    async def fetch_page(self, page: int) -> Optional[Dict[str, Any]]:
        """Fetch a single page of results from the API."""
        url = f"{self.api_base}?page={page}&format=json"
        
        for attempt in range(3):  # 3 retries
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                logger.warning(f"Error fetching page {page} (attempt {attempt + 1}/3): {e}")
                if attempt < 2:
                    await asyncio.sleep(5)  # Wait before retry
                else:
                    self.stats['api_errors'] += 1
                    return None
    
    async def discover_all_biotools(self) -> List[BioToolsTool]:
        """Discover all tools from bio.tools API."""
        logger.info("Starting bio.tools API discovery...")
        page = 1
        
        while True:
            logger.info(f"Fetching page {page}...")
            data = await self.fetch_page(page)
            
            if not data:
                logger.warning(f"No data received for page {page}, stopping")
                break
            
            # Extract tools from response
            tools_list = data.get('list', [])
            if not tools_list:
                logger.info("No more tools found, finished fetching")
                break
            
            # Process each tool
            for tool_data in tools_list:
                try:
                    tool = self._create_tool_from_api_data(tool_data)
                    if tool:
                        self.collected_tools.append(tool)
                        self.processed_ids.add(tool.biotoolsID)
                        self.stats['total_tools'] += 1
                except Exception as e:
                    logger.error(f"Error processing tool: {e}")
                    continue
            
            self.stats['pages_fetched'] = page
            
            # Log progress
            logger.info(f"Page {page}: {len(tools_list)} tools, "
                       f"Total collected: {len(self.collected_tools)}, "
                       f"Excluded: Biopython={self.stats['excluded_biopython']}, "
                       f"Bioconductor={self.stats['excluded_bioconductor']}")
            
            # Check for next page
            next_url = data.get('next')
            if not next_url:
                logger.info("No next page URL, finished fetching")
                break
            
            page += 1
            
            # Polite delay
            await asyncio.sleep(1.0)
            
            # Save intermediate results every 50 pages
            if page % 50 == 0:
                self._save_intermediate_results()
        
        logger.info(f"Discovery completed. Total tools collected: {len(self.collected_tools)}")
        return self.collected_tools
    
    def _save_intermediate_results(self):
        """Save intermediate results to avoid data loss."""
        temp_file = self.data_dir / f"biotools_temp_{int(time.time())}.json"
        tools_dict = [tool.to_dict() for tool in self.collected_tools]
        
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(tools_dict, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved intermediate results to {temp_file}")
    
    def _generate_collection_report(self, tools: List[Dict]):
        """Generate comprehensive collection report."""
        categories = {}
        languages = {}
        tool_types = {}
        topics_count = {}
        
        for tool in tools:
            # Count by category
            category = tool.get('category', 'Unknown')
            categories[category] = categories.get(category, 0) + 1
            
            # Count by language
            lang = tool.get('programming_language', 'Not specified')
            for l in lang.split(', '):
                if l:
                    languages[l] = languages.get(l, 0) + 1
            
            # Count by tool type
            for tt in tool.get('tool_types', []):
                if tt:
                    tool_types[tt] = tool_types.get(tt, 0) + 1
            
            # Count topics
            for topic in tool.get('topics', []):
                if topic:
                    topics_count[topic] = topics_count.get(topic, 0) + 1
        
        report = {
            "collection_summary": {
                "total_tools": len(tools),
                "excluded_biopython": self.stats['excluded_biopython'],
                "excluded_bioconductor": self.stats['excluded_bioconductor'],
                "api_errors": self.stats['api_errors'],
                "pages_fetched": self.stats['pages_fetched'],
                "collection_timestamp": time.time(),
                "source": "bio.tools API",
                "api_base_url": self.api_base
            },
            "categories": categories,
            "top_categories": sorted(categories.items(), key=lambda x: x[1], reverse=True)[:20],
            "languages": languages,
            "top_languages": sorted(languages.items(), key=lambda x: x[1], reverse=True)[:15],
            "tool_types": tool_types,
            "top_topics": sorted(topics_count.items(), key=lambda x: x[1], reverse=True)[:20]
        }
        
        # Save report
        report_file = self.data_dir / "biotools_collection_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Collection report saved to: {report_file}")
        
        # Print summary
        logger.info("Bio.tools Collection Summary:")
        logger.info(f"  Total tools collected: {len(tools)}")
        logger.info(f"  Excluded Biopython tools: {self.stats['excluded_biopython']}")
        logger.info(f"  Excluded Bioconductor tools: {self.stats['excluded_bioconductor']}")
        logger.info(f"  Categories: {len(categories)}")
        logger.info(f"  Programming languages: {len(languages)}")
        
        logger.info("\nTop Categories:")
        for category, count in report["top_categories"][:10]:
            percentage = (count / len(tools)) * 100
            logger.info(f"  {category:30} {count:4d} tools ({percentage:5.1f}%)")
        
        logger.info("\nTop Programming Languages:")
        for lang, count in report["top_languages"][:10]:
            percentage = (count / len(tools)) * 100
            logger.info(f"  {lang:20} {count:4d} tools ({percentage:5.1f}%)")
    
    async def collect_and_save(self) -> List[Dict]:
        """Main method to collect all bio.tools and save them."""
        start_time = time.time()
        
        logger.info("Starting bio.tools collection (excluding Biopython and Bioconductor)...")
        
        # Discover all tools
        tools = await self.discover_all_biotools()
        
        if not tools:
            logger.error("No tools discovered!")
            return []
        
        # Convert to dictionary format
        tools_dict = [tool.to_dict() for tool in tools]
        
        # Save collected data in chunks of 2500 tools per file
        chunk_size = 2500
        num_chunks = (len(tools_dict) + chunk_size - 1) // chunk_size  # Ceiling division
        
        logger.info(f"Saving {len(tools_dict)} tools in {num_chunks} files ({chunk_size} tools per file)...")
        
        for i in range(num_chunks):
            start_idx = i * chunk_size
            end_idx = min((i + 1) * chunk_size, len(tools_dict))
            chunk = tools_dict[start_idx:end_idx]
            
            output_file = self.data_dir / f"complete_biotools_tools_{i + 1}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(chunk, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved file {i + 1}/{num_chunks}: {output_file.name} ({len(chunk)} tools)")
        
        collection_time = time.time() - start_time
        
        # Clean up temp files
        for temp_file in self.data_dir.glob("biotools_temp_*.json"):
            temp_file.unlink()
        
        # Generate report
        self._generate_collection_report(tools_dict)
        
        logger.info(f"Collection completed in {collection_time:.1f} seconds")
        logger.info(f"Data saved to: {self.data_dir} (in {num_chunks} files)")
        logger.info(f"Tools per second: {len(tools_dict) / collection_time:.1f}")
        
        return tools_dict


async def standalone_collection():
    """Standalone function to run collection."""
    print("🧬 Bio.tools Registry Collection")
    print("=" * 60)
    print("Collecting tools from bio.tools API")
    print("Excluding Biopython and Bioconductor tools as requested")
    
    # Check internet connectivity
    try:
        test_response = requests.get("https://bio.tools", timeout=10)
        print(f"✅ Internet connectivity verified (Status: {test_response.status_code})")
    except Exception as e:
        print(f"❌ Internet connectivity issue: {e}")
        print("Please check your internet connection and try again.")
        return False
    
    # Run collection
    collector = BioToolsCollector()
    print("🔍 Starting bio.tools collection...")
    print("⏱️  This may take 30-60 minutes for 30,000+ tools...")
    
    start_time = time.time()
    tools = await collector.collect_and_save()
    total_time = time.time() - start_time
    
    if tools:
        print(f"\n🎉 Collection completed successfully!")
        print(f"📊 Collected {len(tools)} tools from bio.tools")
        print(f"⏱️  Total time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
        print(f"🚀 Performance: {len(tools) / total_time:.1f} tools/second")
        print(f"💾 Data saved to: {collector.data_dir}")
        
        # Show exclusion stats
        print(f"\n📊 Exclusion Statistics:")
        print(f"   Excluded Biopython tools: {collector.stats['excluded_biopython']}")
        print(f"   Excluded Bioconductor tools: {collector.stats['excluded_bioconductor']}")
        
        return True
    else:
        print("❌ Collection failed!")
        return False


if __name__ == "__main__":
    """Run as standalone script."""
    print("🔧 Running Bio.tools Collector")
    success = asyncio.run(standalone_collection())
    
    if success:
        print("\n✅ Bio.tools collection completed! Files saved to data/biotools_collection/")
    else:
        print("\n❌ Collection failed. Check error messages above.")
        sys.exit(1)