from typing import List, Dict, Optional
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import os
from pathlib import Path
import json
from datetime import datetime
from biopython import Bio
from bioconductor import Bioconductor

class RepositoryIngestion:
    """Handles ingestion of bioinformatics repositories and tools."""
    
    def __init__(self, data_dir: str = "data/repositories"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize repositories to track
        self.repositories = {
            "biopython": {
                "url": "https://biopython.org/wiki/Documentation",
                "type": "python"
            },
            "bioconductor": {
                "url": "https://www.bioconductor.org/packages/release/",
                "type": "r"
            }
        }

    async def fetch_repository_data(self, repo_name: str) -> Dict:
        """Fetch data from a specific repository."""
        repo_info = self.repositories.get(repo_name)
        if not repo_info:
            raise ValueError(f"Unknown repository: {repo_name}")

        async with aiohttp.ClientSession() as session:
            async with session.get(repo_info["url"]) as response:
                if response.status == 200:
                    content = await response.text()
                    return {
                        "name": repo_name,
                        "content": content,
                        "type": repo_info["type"],
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    raise Exception(f"Failed to fetch {repo_name}: {response.status}")

    def process_biopython_docs(self, content: str) -> List[Dict]:
        """Process Biopython documentation."""
        soup = BeautifulSoup(content, 'html.parser')
        tools = []
        
        # Extract tool information from documentation
        for section in soup.find_all(['h1', 'h2', 'h3']):
            if section.find_next('p'):
                tool_info = {
                    "name": section.text.strip(),
                    "description": section.find_next('p').text.strip(),
                    "category": "biopython",
                    "features": [],
                    "documentation": section.find_next('p').text.strip()
                }
                
                # Extract features from code examples
                code_blocks = section.find_all_next('pre')
                for block in code_blocks[:3]:  # Limit to first 3 examples
                    if block.text.strip():
                        tool_info["features"].append(block.text.strip())
                
                tools.append(tool_info)
        
        return tools

    def process_bioconductor_packages(self, content: str) -> List[Dict]:
        """Process Bioconductor packages."""
        soup = BeautifulSoup(content, 'html.parser')
        tools = []
        
        # Extract package information
        for package in soup.find_all('div', class_='package'):
            if package.find('h3'):
                tool_info = {
                    "name": package.find('h3').text.strip(),
                    "description": package.find('p').text.strip() if package.find('p') else "",
                    "category": "bioconductor",
                    "features": [],
                    "documentation": package.find('div', class_='description').text.strip() if package.find('div', class_='description') else ""
                }
                
                # Extract features from package details
                features = package.find_all('li')
                for feature in features:
                    if feature.text.strip():
                        tool_info["features"].append(feature.text.strip())
                
                tools.append(tool_info)
        
        return tools

    async def ingest_repository(self, repo_name: str) -> List[Dict]:
        """Ingest data from a specific repository."""
        try:
            # Fetch repository data
            repo_data = await self.fetch_repository_data(repo_name)
            
            # Process based on repository type
            if repo_data["type"] == "python":
                tools = self.process_biopython_docs(repo_data["content"])
            elif repo_data["type"] == "r":
                tools = self.process_bioconductor_packages(repo_data["content"])
            else:
                raise ValueError(f"Unsupported repository type: {repo_data['type']}")
            
            # Save processed data
            output_file = self.data_dir / f"{repo_name}_tools.json"
            with open(output_file, 'w') as f:
                json.dump({
                    "repository": repo_name,
                    "timestamp": repo_data["timestamp"],
                    "tools": tools
                }, f, indent=2)
            
            return tools
        except Exception as e:
            print(f"Error ingesting {repo_name}: {str(e)}")
            return []

    async def ingest_all_repositories(self) -> Dict[str, List[Dict]]:
        """Ingest data from all tracked repositories."""
        results = {}
        for repo_name in self.repositories:
            tools = await self.ingest_repository(repo_name)
            results[repo_name] = tools
        return results

    def get_ingested_tools(self) -> List[Dict]:
        """Retrieve all ingested tools."""
        all_tools = []
        for file in self.data_dir.glob("*_tools.json"):
            with open(file, 'r') as f:
                data = json.load(f)
                all_tools.extend(data["tools"])
        return all_tools 