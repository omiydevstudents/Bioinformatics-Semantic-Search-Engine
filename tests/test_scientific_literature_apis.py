#!/usr/bin/env python3
"""
Test script for the new scientific literature APIs:
- PubMed E-utilities (NCBI API)
- Europe PMC API

These replace the non-working Paper Search MCP with reliable, free APIs.
"""
import asyncio
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the src directory to Python path
sys.path.insert(0, "./src")

from mcp.mcp_client import EnhancedMCPClient


async def test_pubmed_eutils():
    """Test PubMed E-utilities API."""
    print("🧪 Testing PubMed E-utilities (NCBI API)")
    print("=" * 50)

    client = EnhancedMCPClient()

    test_queries = [
        "protein structure prediction",
        "CRISPR gene editing",
        "RNA-seq analysis methods",
        "bioinformatics machine learning",
    ]

    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        try:
            response = await client.query_pubmed_eutils(query, max_results=5)

            if response.success:
                papers = response.data.get("papers", [])
                pmids_found = response.data.get("pmids_found", 0)

                print(
                    f"✅ Success: {len(papers)} papers retrieved ({pmids_found} PMIDs found)"
                )

                for i, paper in enumerate(papers[:3], 1):
                    print(f"   {i}. {paper['title'][:80]}...")
                    print(f"      Authors: {', '.join(paper.get('authors', [])[:3])}")
                    print(f"      Journal: {paper.get('journal', 'Unknown')}")
                    print(f"      PMID: {paper.get('pmid', 'N/A')}")
                    print(f"      URL: {paper.get('url', 'N/A')}")
                    print()
            else:
                print(f"❌ Error: {response.error}")

        except Exception as e:
            print(f"🚨 Exception: {e}")

    await client.close()


async def test_europe_pmc():
    """Test Europe PMC API."""
    print("\n🧪 Testing Europe PMC API")
    print("=" * 50)

    client = EnhancedMCPClient()

    test_queries = [
        "genomics GWAS analysis",
        "COVID-19 bioinformatics",
        "single cell RNA sequencing",
        "protein folding AlphaFold",
    ]

    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        try:
            response = await client.query_europe_pmc(query, max_results=5)

            if response.success:
                papers = response.data.get("papers", [])
                hit_count = response.data.get("hit_count", 0)
                sources = response.data.get("sources_included", [])

                print(
                    f"✅ Success: {len(papers)} papers retrieved (total hits: {hit_count})"
                )
                print(f"📚 Sources included: {', '.join(sources)}")

                # Count by source
                source_counts = {}
                open_access_count = 0

                for paper in papers:
                    source = paper.get("source", "unknown")
                    source_counts[source] = source_counts.get(source, 0) + 1
                    if paper.get("is_open_access"):
                        open_access_count += 1

                print(f"📊 Source breakdown: {source_counts}")
                print(f"🔓 Open access papers: {open_access_count}/{len(papers)}")

                for i, paper in enumerate(papers[:3], 1):
                    print(f"   {i}. {paper['title'][:80]}...")
                    print(f"      Authors: {', '.join(paper.get('authors', [])[:3])}")
                    print(f"      Source: {paper.get('source', 'unknown')}")
                    print(f"      Citations: {paper.get('citation_count', 0)}")
                    print(
                        f"      Open Access: {'Yes' if paper.get('is_open_access') else 'No'}"
                    )
                    if paper.get("doi"):
                        print(f"      DOI: {paper.get('doi')}")
                    print()
            else:
                print(f"❌ Error: {response.error}")

        except Exception as e:
            print(f"🚨 Exception: {e}")

    await client.close()


async def test_concurrent_literature_search():
    """Test concurrent search across both literature APIs."""
    print("\n🚀 Testing Concurrent Literature Search")
    print("=" * 50)

    client = EnhancedMCPClient()

    query = "bioinformatics deep learning protein prediction"
    print(f"🔍 Query: '{query}'")
    print("🔄 Searching PubMed E-utilities and Europe PMC concurrently...")

    try:
        # Run both searches concurrently
        pubmed_task = client.query_pubmed_eutils(query, max_results=10)
        europe_task = client.query_europe_pmc(query, max_results=10)

        pubmed_response, europe_response = await asyncio.gather(
            pubmed_task, europe_task, return_exceptions=True
        )

        print("\n📊 Results Summary:")
        print("-" * 30)

        total_papers = 0

        # PubMed results
        if isinstance(pubmed_response, Exception):
            print(f"❌ PubMed E-utilities: Exception - {pubmed_response}")
        elif pubmed_response.success:
            pubmed_papers = pubmed_response.data.get("papers", [])
            total_papers += len(pubmed_papers)
            print(f"✅ PubMed E-utilities: {len(pubmed_papers)} papers")
        else:
            print(f"⚠️ PubMed E-utilities: {pubmed_response.error}")

        # Europe PMC results
        if isinstance(europe_response, Exception):
            print(f"❌ Europe PMC: Exception - {europe_response}")
        elif europe_response.success:
            europe_papers = europe_response.data.get("papers", [])
            total_papers += len(europe_papers)
            hit_count = europe_response.data.get("hit_count", 0)
            print(
                f"✅ Europe PMC: {len(europe_papers)} papers (total hits: {hit_count})"
            )
        else:
            print(f"⚠️ Europe PMC: {europe_response.error}")

        print(f"\n🎯 Total papers retrieved: {total_papers}")

        # Show unique insights from each source
        if (
            not isinstance(pubmed_response, Exception)
            and pubmed_response.success
            and not isinstance(europe_response, Exception)
            and europe_response.success
        ):

            pubmed_papers = pubmed_response.data.get("papers", [])
            europe_papers = europe_response.data.get("papers", [])

            print(f"\n🔍 Comparison:")
            print(f"   PubMed focus: Biomedical literature with PMIDs")
            print(f"   Europe PMC focus: Broader life sciences including preprints")

            if pubmed_papers:
                print(f"   PubMed top result: {pubmed_papers[0]['title'][:60]}...")
            if europe_papers:
                print(f"   Europe PMC top result: {europe_papers[0]['title'][:60]}...")

    except Exception as e:
        print(f"🚨 Concurrent search failed: {e}")

    await client.close()


async def main():
    """Main test function."""
    print("🔬 Scientific Literature APIs Testing Suite")
    print("Testing PubMed E-utilities and Europe PMC APIs")
    print("=" * 70)

    try:
        # Test individual APIs
        await test_pubmed_eutils()
        await test_europe_pmc()

        # Test concurrent search
        await test_concurrent_literature_search()

        print("\n🎉 Scientific Literature APIs Testing Complete!")
        print("\n✅ Key Benefits:")
        print("   - PubMed E-utilities: Free, reliable, biomedical focus")
        print("   - Europe PMC: Free, broader coverage, includes preprints")
        print("   - Both APIs: No rate limits for reasonable usage")
        print("   - Combined coverage: PubMed + BioRxiv + MedRxiv + Agricola")

        print("\n🚀 Ready to replace non-working Paper Search MCP!")

    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
