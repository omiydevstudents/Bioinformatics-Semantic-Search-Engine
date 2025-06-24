"""
Enhanced MCP Client with alternative MCP servers based on meeting recommendations.
Implements Exa Search, Tavily, and Paper Search MCPs for comprehensive tool discovery.
"""

from typing import Dict, List, Optional, Any
import httpx
from pydantic import BaseModel
import os
import json
import asyncio
from dotenv import load_dotenv
from .mcp_client import MCPClient, MCPResponse

load_dotenv()


class EnhancedMCPClient(MCPClient):
    """Enhanced MCP client with alternative community-supported MCP servers."""

    def __init__(self):
        super().__init__()
        # Additional MCP server URLs from meeting recommendations
        self.exa_search_url = os.getenv(
            "EXA_SEARCH_MCP_URL", "https://api.exa.ai/search"
        )
        self.tavily_search_url = os.getenv(
            "TAVILY_MCP_URL", "https://api.tavily.com/search"
        )

        # Scientific literature APIs (replacing non-working Paper Search MCP)
        self.pubmed_eutils_base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.europe_pmc_base = "https://www.ebi.ac.uk/europepmc/webservices/rest"

        # API keys for alternative services
        self.exa_api_key = os.getenv("EXA_API_KEY")
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        # Note: PubMed E-utilities and Europe PMC are free and don't require API keys

    async def query_exa_search(
        self, query: str, domain_filter: str = None, num_results: int = 10
    ) -> MCPResponse:
        """
        Query Exa Search MCP for bioinformatics-focused web searches.

        Args:
            query: Search query
            domain_filter: Optional domain filter (e.g., "bioconductor.org", "biopython.org")
            num_results: Number of results to return
        """
        if not self.exa_api_key:
            return MCPResponse(
                success=False, data={}, error="EXA_API_KEY not configured"
            )

        try:
            # Enhance query with bioinformatics context
            enhanced_query = self._enhance_bio_query(query)

            payload = {
                "query": enhanced_query,
                "num_results": num_results,
                "include_domains": (
                    [domain_filter]
                    if domain_filter
                    else [
                        "bioconductor.org",
                        "biopython.org",
                        "bioinformatics.org",
                        "ncbi.nlm.nih.gov",
                        "github.com",
                    ]
                ),
                "use_autoprompt": True,
                "type": "neural",
            }

            headers = {
                "Authorization": f"Bearer {self.exa_api_key}",
                "Content-Type": "application/json",
            }

            response = await self.client.post(
                self.exa_search_url, json=payload, headers=headers
            )
            response.raise_for_status()

            # Parse Exa response
            exa_data = response.json()

            # Transform to our standard format
            tools = []
            for result in exa_data.get("results", []):
                tools.append(
                    {
                        "name": result.get("title", "Unknown Tool"),
                        "description": result.get("text", ""),
                        "url": result.get("url", ""),
                        "score": result.get("score", 0),
                        "source": "exa_search",
                        "domain": self._extract_domain(result.get("url", "")),
                    }
                )

            return MCPResponse(
                success=True,
                data={
                    "tools": tools,
                    "query": query,
                    "enhanced_query": enhanced_query,
                    "total_results": len(tools),
                    "source": "exa_search",
                    "domain_filter": domain_filter,
                },
            )

        except Exception as e:
            return MCPResponse(
                success=False, data={}, error=f"Exa Search error: {str(e)}"
            )

    async def query_tavily_search(
        self, query: str, search_depth: str = "basic"
    ) -> MCPResponse:
        """
        Query Tavily MCP for comprehensive web search (1000 free monthly queries).

        Args:
            query: Search query
            search_depth: "basic" or "advanced"
        """
        if not self.tavily_api_key:
            return MCPResponse(
                success=False, data={}, error="TAVILY_API_KEY not configured"
            )

        try:
            # Enhance query for bioinformatics context
            enhanced_query = f"{query} bioinformatics tools software"

            payload = {
                "query": enhanced_query,
                "search_depth": search_depth,
                "include_answer": True,
                "include_images": False,
                "include_raw_content": False,
                "max_results": 10,
                "include_domains": [
                    "github.com",
                    "bioconductor.org",
                    "biopython.org",
                    "bioinformatics.org",
                    "ncbi.nlm.nih.gov",
                    "pubmed.ncbi.nlm.nih.gov",
                ],
            }

            headers = {
                "Authorization": f"Bearer {self.tavily_api_key}",
                "Content-Type": "application/json",
            }

            response = await self.client.post(
                self.tavily_search_url, json=payload, headers=headers
            )
            response.raise_for_status()

            # Parse Tavily response
            tavily_data = response.json()

            # Transform to our standard format
            tools = []
            for result in tavily_data.get("results", []):
                tools.append(
                    {
                        "name": result.get("title", "Unknown Tool"),
                        "description": result.get("content", ""),
                        "url": result.get("url", ""),
                        "score": result.get("score", 0),
                        "source": "tavily_search",
                        "published_date": result.get("published_date", ""),
                    }
                )

            return MCPResponse(
                success=True,
                data={
                    "tools": tools,
                    "query": query,
                    "enhanced_query": enhanced_query,
                    "answer": tavily_data.get("answer", ""),
                    "total_results": len(tools),
                    "source": "tavily_search",
                    "search_depth": search_depth,
                },
            )

        except Exception as e:
            return MCPResponse(
                success=False, data={}, error=f"Tavily Search error: {str(e)}"
            )

    async def query_pubmed_eutils(
        self, query: str, max_results: int = 20
    ) -> MCPResponse:
        """
        Query PubMed E-utilities (NCBI API) for biomedical literature search.
        Free API with rate limiting (3 requests/second recommended).

        Args:
            query: Search query
            max_results: Maximum number of results (default 20)
        """
        try:
            # Enhance query for biomedical literature
            enhanced_query = self._enhance_scientific_query(query)

            # Add rate limiting delay (NCBI recommends max 3 requests/second)
            await asyncio.sleep(0.34)  # ~3 requests per second

            # Step 1: Search for PMIDs using esearch
            search_params = {
                "db": "pubmed",
                "term": enhanced_query,
                "retmax": max_results,
                "retmode": "json",
                "sort": "relevance",
                "field": "title/abstract",
                "tool": "bioinformatics_search_engine",  # Identify our tool
                "email": "research@example.com",  # Required for good citizenship
            }

            search_url = f"{self.pubmed_eutils_base}/esearch.fcgi"
            search_response = await self.client.get(search_url, params=search_params)
            search_response.raise_for_status()

            search_data = search_response.json()
            pmids = search_data.get("esearchresult", {}).get("idlist", [])

            if not pmids:
                return MCPResponse(
                    success=True,
                    data={
                        "papers": [],
                        "query": query,
                        "enhanced_query": enhanced_query,
                        "total_results": 0,
                        "source": "pubmed_eutils",
                    },
                )

            # Add another rate limiting delay before second request
            await asyncio.sleep(0.34)

            # Step 2: Fetch detailed information using esummary
            summary_params = {
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "json",
                "tool": "bioinformatics_search_engine",
                "email": "research@example.com",
            }

            summary_url = f"{self.pubmed_eutils_base}/esummary.fcgi"
            summary_response = await self.client.get(summary_url, params=summary_params)
            summary_response.raise_for_status()

            summary_data = summary_response.json()

            # Transform to our standard format
            papers = []
            for pmid in pmids:
                if pmid in summary_data.get("result", {}):
                    paper_info = summary_data["result"][pmid]

                    # Extract authors
                    authors = []
                    for author in paper_info.get("authors", []):
                        authors.append(author.get("name", ""))

                    papers.append(
                        {
                            "title": paper_info.get("title", "Unknown Title"),
                            "abstract": paper_info.get("abstract", ""),
                            "authors": authors,
                            "pmid": pmid,
                            "doi": paper_info.get("elocationid", "").replace(
                                "doi: ", ""
                            ),
                            "journal": paper_info.get("fulljournalname", ""),
                            "published_date": paper_info.get("pubdate", ""),
                            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                            "source": "pubmed",
                            "relevance_score": 1.0
                            - (len(papers) * 0.05),  # Decreasing relevance
                        }
                    )

            return MCPResponse(
                success=True,
                data={
                    "papers": papers,
                    "query": query,
                    "enhanced_query": enhanced_query,
                    "total_results": len(papers),
                    "pmids_found": len(pmids),
                    "source": "pubmed_eutils",
                },
            )

        except Exception as e:
            return MCPResponse(
                success=False, data={}, error=f"PubMed E-utilities error: {str(e)}"
            )

    async def query_europe_pmc(self, query: str, max_results: int = 20) -> MCPResponse:
        """
        Query Europe PMC API for life sciences literature search.
        Supports PubMed, BioRxiv, MedRxiv, and Agricola.
        Free API with unlimited academic usage.

        Args:
            query: Search query
            max_results: Maximum number of results (default 20)
        """
        try:
            # Start with simple query (enhanced queries cause issues with Europe PMC)
            search_query = query

            # Europe PMC search parameters - simplified based on debug results
            search_params = {
                "query": search_query,
                "pageSize": min(max_results, 25),  # Europe PMC max is 25
                "format": "json",
                "resultType": "core",  # Get more detailed results
            }

            search_url = f"{self.europe_pmc_base}/search"
            response = await self.client.get(search_url, params=search_params)
            response.raise_for_status()

            data = response.json()
            results_list = data.get("resultList", {}).get("result", [])

            # Transform to our standard format
            papers = []
            for result in results_list:
                # Extract authors
                authors = []
                author_list = result.get("authorList", {}).get("author", [])
                for author in author_list:
                    full_name = f"{author.get('firstName', '')} {author.get('lastName', '')}".strip()
                    if full_name:
                        authors.append(full_name)

                # Determine source
                source = result.get("source", "unknown").lower()
                if "pubmed" in source:
                    source = "pubmed"
                elif "biorxiv" in source:
                    source = "biorxiv"
                elif "medrxiv" in source:
                    source = "medrxiv"
                elif "agricola" in source:
                    source = "agricola"

                # Build URL
                pmid = result.get("pmid")
                doi = result.get("doi")
                url = ""
                if pmid:
                    url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                elif doi:
                    url = f"https://doi.org/{doi}"
                elif result.get("fullTextUrlList"):
                    urls = result["fullTextUrlList"].get("fullTextUrl", [])
                    if urls:
                        url = urls[0].get("url", "")

                papers.append(
                    {
                        "title": result.get("title", "Unknown Title"),
                        "abstract": result.get("abstractText", ""),
                        "authors": authors,
                        "pmid": pmid,
                        "doi": doi,
                        "journal": result.get("journalInfo", {})
                        .get("journal", {})
                        .get("title", ""),
                        "published_date": result.get("firstPublicationDate", ""),
                        "url": url,
                        "source": source,
                        "citation_count": result.get("citedByCount", 0),
                        "relevance_score": 1.0
                        - (len(papers) * 0.03),  # Decreasing relevance
                        "is_open_access": result.get("isOpenAccess", "N") == "Y",
                    }
                )

            return MCPResponse(
                success=True,
                data={
                    "papers": papers,
                    "query": query,
                    "search_query": search_query,
                    "total_results": len(papers),
                    "hit_count": data.get("hitCount", 0),
                    "sources_included": ["PubMed", "BioRxiv", "MedRxiv", "Agricola"],
                    "source": "europe_pmc",
                },
            )

        except Exception as e:
            return MCPResponse(
                success=False, data={}, error=f"Europe PMC error: {str(e)}"
            )

    async def query_all_sources(self, query: str) -> Dict[str, MCPResponse]:
        """
        Query all available MCP sources concurrently for comprehensive results.

        Args:
            query: Search query

        Returns:
            Dictionary with responses from all sources
        """
        # Create tasks for all MCP sources
        tasks = {
            "bio_mcp": self.query_bio_mcp(query),
            "pubmed_mcp": self.query_pubmed_mcp(query),
            "bio_context": self.query_bio_context(query),
            "exa_search": self.query_exa_search(query),
            "tavily_search": self.query_tavily_search(query),
            "pubmed_eutils": self.query_pubmed_eutils(query),
            "europe_pmc": self.query_europe_pmc(query),
        }

        # Execute all queries concurrently
        results = {}
        for source, task in tasks.items():
            try:
                results[source] = await task
            except Exception as e:
                results[source] = MCPResponse(
                    success=False, data={}, error=f"Error querying {source}: {str(e)}"
                )

        return results

    def _enhance_bio_query(self, query: str) -> str:
        """Enhance query with bioinformatics context for better web search results."""
        bio_terms = [
            "bioinformatics",
            "computational biology",
            "genomics",
            "proteomics",
        ]

        # Add bioinformatics context if not already present
        query_lower = query.lower()
        if not any(term in query_lower for term in bio_terms):
            return f"{query} bioinformatics computational biology tools"
        return query

    def _enhance_scientific_query(self, query: str) -> str:
        """Enhance query for scientific literature search."""
        scientific_terms = ["algorithm", "method", "analysis", "software", "tool"]

        query_lower = query.lower()
        if not any(term in query_lower for term in scientific_terms):
            return f"{query} computational methods algorithms"
        return query

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse

            return urlparse(url).netloc
        except:
            return "unknown"


# Example usage and testing
async def test_enhanced_mcp_client():
    """Test the enhanced MCP client with alternative sources."""
    client = EnhancedMCPClient()

    test_query = "protein structure prediction tools"

    print(f"🔍 Testing Enhanced MCP Client with query: '{test_query}'")
    print("=" * 60)

    # Test individual sources
    sources_to_test = [
        ("Exa Search", client.query_exa_search),
        ("Tavily Search", client.query_tavily_search),
        ("PubMed E-utilities", client.query_pubmed_eutils),
        ("Europe PMC", client.query_europe_pmc),
    ]

    for source_name, query_func in sources_to_test:
        print(f"\n📊 Testing {source_name}...")
        try:
            response = await query_func(test_query)
            if response.success:
                tools_count = len(
                    response.data.get("tools", response.data.get("papers", []))
                )
                print(f"✅ {source_name}: {tools_count} results found")
            else:
                print(f"⚠️ {source_name}: {response.error}")
        except Exception as e:
            print(f"❌ {source_name}: Exception - {e}")

    # Test all sources concurrently
    print(f"\n🚀 Testing all sources concurrently...")
    all_results = await client.query_all_sources(test_query)

    total_tools = 0
    for source, response in all_results.items():
        if response.success:
            count = len(response.data.get("tools", response.data.get("papers", [])))
            total_tools += count
            print(f"✅ {source}: {count} results")
        else:
            print(f"⚠️ {source}: {response.error}")

    print(f"\n🎯 Total results from all sources: {total_tools}")

    await client.close()


if __name__ == "__main__":
    asyncio.run(test_enhanced_mcp_client())
