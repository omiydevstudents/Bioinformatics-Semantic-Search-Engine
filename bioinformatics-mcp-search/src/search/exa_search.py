from typing import List, Dict, Optional
import os
from exa_py import Exa
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class SearchResult(BaseModel):
    """Model for search results."""
    title: str
    url: str
    text: str
    score: float
    metadata: Optional[Dict] = None

class ExaSearchClient:
    """Client for EXA search integration."""
    
    def __init__(self):
        api_key = os.getenv("EXA_API_KEY")
        if not api_key:
            raise ValueError("EXA_API_KEY environment variable is not set")
        self.client = Exa(api_key=api_key)

    async def search_tools(self, query: str, num_results: int = 5) -> List[SearchResult]:
        """Search for bioinformatics tools using EXA."""
        try:
            # Add bioinformatics context to the query
            enhanced_query = f"bioinformatics tools for {query}"
            
            response = self.client.search(
                query=enhanced_query,
                num_results=num_results,
                include_domains=["github.com", "bioconductor.org", "biopython.org"],
                use_autoprompt=True
            )

            results = []
            for result in response.results:
                search_result = SearchResult(
                    title=result.title,
                    url=result.url,
                    text=result.text,
                    score=result.score,
                    metadata=result.metadata
                )
                results.append(search_result)

            return results
        except Exception as e:
            print(f"Error in EXA search: {str(e)}")
            return []

    async def get_tool_details(self, url: str) -> Optional[Dict]:
        """Get detailed information about a specific tool."""
        try:
            response = self.client.get_contents([url])
            if response and response.contents:
                return response.contents[0]
            return None
        except Exception as e:
            print(f"Error getting tool details: {str(e)}")
            return None 