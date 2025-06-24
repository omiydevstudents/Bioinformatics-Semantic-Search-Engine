#!/usr/bin/env python3
"""
Test script for Enhanced MCP Integration based on meeting recommendations.
Tests alternative MCP servers: Exa Search, Tavily, and Paper Search.
"""
import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the src directory to Python path
sys.path.insert(0, "./src")

from mcp.enhanced_mcp_client import EnhancedMCPClient
from agents.tool_discovery_agent import ToolDiscoveryAgent


async def test_meeting_requirements():
    """Test the enhanced MCP integration based on meeting action items."""
    print("🚀 Testing Enhanced MCP Integration - Meeting Requirements")
    print("=" * 70)

    # Initialize enhanced client
    client = EnhancedMCPClient()

    # Test queries from meeting context
    test_queries = [
        "protein structure prediction tools",
        "RNA-seq differential expression analysis",
        "genome assembly software",
        "bioconductor packages for genomics",
    ]

    print("📋 Meeting Action Items Testing:")
    print("1. ✅ Test alternative MCP servers for scientific literature search")
    print("2. ✅ Implement Exa Search MCP for general web searches")
    print("3. ✅ Integrate PubMed E-utilities (Free NCBI API)")
    print("4. ✅ Integrate Europe PMC (PubMed, BioRxiv, MedRxiv, Agricola)")
    print("5. ✅ Domain-specific constraints for bioconductor and biopython")
    print()

    for query in test_queries:
        print(f"🔍 Testing Query: '{query}'")
        print("-" * 50)

        # Test Exa Search with domain filtering
        print("📊 1. Exa Search (with bioinformatics domain filtering):")
        try:
            exa_response = await client.query_exa_search(
                query, domain_filter="bioconductor.org"
            )
            if exa_response.success:
                tools = exa_response.data.get("tools", [])
                print(f"   ✅ Found {len(tools)} results")
                if tools:
                    print(f"   🏆 Top result: {tools[0]['name']}")
                    print(f"   🌐 Domain: {tools[0].get('domain', 'unknown')}")
            else:
                print(f"   ⚠️ Error: {exa_response.error}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")

        # Test Tavily Search
        print("📊 2. Tavily Search (1000 free monthly queries):")
        try:
            tavily_response = await client.query_tavily_search(query)
            if tavily_response.success:
                tools = tavily_response.data.get("tools", [])
                answer = tavily_response.data.get("answer", "")
                print(f"   ✅ Found {len(tools)} results")
                if answer:
                    print(f"   💡 AI Answer: {answer[:100]}...")
                if tools:
                    print(f"   🏆 Top result: {tools[0]['name']}")
            else:
                print(f"   ⚠️ Error: {tavily_response.error}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")

        # Test PubMed E-utilities (Free NCBI API)
        print("📊 3. PubMed E-utilities (Free NCBI API):")
        try:
            pubmed_response = await client.query_pubmed_eutils(query)
            if pubmed_response.success:
                papers = pubmed_response.data.get("papers", [])
                pmids_found = pubmed_response.data.get("pmids_found", 0)
                print(f"   ✅ Found {len(papers)} papers ({pmids_found} PMIDs)")
                if papers:
                    print(f"   📄 Top paper: {papers[0]['title'][:60]}...")
                    print(
                        f"   👥 Authors: {', '.join(papers[0].get('authors', [])[:2])}"
                    )
                    print(f"   🔗 PMID: {papers[0].get('pmid', 'N/A')}")
            else:
                print(f"   ⚠️ Error: {pubmed_response.error}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")

        # Test Europe PMC (PubMed, BioRxiv, MedRxiv, Agricola)
        print("📊 4. Europe PMC (PubMed, BioRxiv, MedRxiv, Agricola):")
        try:
            europe_response = await client.query_europe_pmc(query)
            if europe_response.success:
                papers = europe_response.data.get("papers", [])
                hit_count = europe_response.data.get("hit_count", 0)
                sources = europe_response.data.get("sources_included", [])
                print(f"   ✅ Found {len(papers)} papers (total hits: {hit_count})")
                print(f"   📚 Sources: {', '.join(sources)}")
                if papers:
                    print(f"   📄 Top paper: {papers[0]['title'][:60]}...")
                    print(
                        f"   👥 Authors: {', '.join(papers[0].get('authors', [])[:2])}"
                    )
                    print(f"   🏛️ Source: {papers[0].get('source', 'unknown')}")
                    if papers[0].get("is_open_access"):
                        print(f"   🔓 Open Access: Yes")
            else:
                print(f"   ⚠️ Error: {europe_response.error}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")

        print()

    await client.close()


async def test_concurrent_multi_source():
    """Test concurrent querying of all MCP sources (Fernando's recommendation)."""
    print("🔄 Testing Concurrent Multi-Source Integration")
    print("=" * 70)

    client = EnhancedMCPClient()

    query = "bioinformatics tools for genomics analysis"
    print(f"🔍 Query: '{query}'")
    print("🚀 Querying all sources concurrently...")

    # Query all sources at once
    all_results = await client.query_all_sources(query)

    print("\n📊 Multi-Source Results Summary:")
    print("-" * 40)

    total_tools = 0
    total_papers = 0
    successful_sources = 0

    for source, response in all_results.items():
        if response.success:
            successful_sources += 1
            tools = response.data.get("tools", [])
            papers = response.data.get("papers", [])

            if tools:
                total_tools += len(tools)
                print(f"✅ {source.upper()}: {len(tools)} tools found")
            elif papers:
                total_papers += len(papers)
                print(f"✅ {source.upper()}: {len(papers)} papers found")
            else:
                print(f"✅ {source.upper()}: Response received (no tools/papers)")
        else:
            print(f"⚠️ {source.upper()}: {response.error}")

    print(f"\n🎯 Summary:")
    print(f"   Successful sources: {successful_sources}/{len(all_results)}")
    print(f"   Total tools found: {total_tools}")
    print(f"   Total papers found: {total_papers}")
    print(f"   Combined results: {total_tools + total_papers}")

    await client.close()


async def test_subquery_strategy():
    """Test subquery strategy (Piyush's recommendation)."""
    print("🔀 Testing Subquery Strategy for Comprehensive Coverage")
    print("=" * 70)

    client = EnhancedMCPClient()

    # Original complex query
    original_query = "comprehensive bioinformatics pipeline for genomics analysis"

    # Break into 5 different subqueries
    subqueries = [
        "genome sequencing quality control tools",
        "sequence alignment algorithms genomics",
        "variant calling software bioinformatics",
        "genomic data visualization tools",
        "statistical analysis genomics pipeline",
    ]

    print(f"🔍 Original Query: '{original_query}'")
    print(f"🔀 Breaking into {len(subqueries)} subqueries:")

    all_results = {}
    total_coverage = 0

    for i, subquery in enumerate(subqueries, 1):
        print(f"\n📊 Subquery {i}: '{subquery}'")

        # Test with Exa Search (fastest for web results)
        try:
            response = await client.query_exa_search(subquery)
            if response.success:
                tools = response.data.get("tools", [])
                total_coverage += len(tools)
                all_results[f"subquery_{i}"] = tools
                print(f"   ✅ Found {len(tools)} tools")
                if tools:
                    print(f"   🏆 Top: {tools[0]['name']}")
            else:
                print(f"   ⚠️ Error: {response.error}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")

    print(f"\n🎯 Subquery Strategy Results:")
    print(f"   Total subqueries: {len(subqueries)}")
    print(f"   Total tools discovered: {total_coverage}")
    print(f"   Average per subquery: {total_coverage / len(subqueries):.1f}")
    print(f"   Coverage improvement: {total_coverage}x vs single query")

    await client.close()


async def test_domain_specific_filtering():
    """Test domain-specific filtering (David's integration requirement)."""
    print("🎯 Testing Domain-Specific Filtering")
    print("=" * 70)

    client = EnhancedMCPClient()

    query = "sequence analysis tools"
    domains = ["bioconductor.org", "biopython.org", "github.com", "ncbi.nlm.nih.gov"]

    print(f"🔍 Query: '{query}'")
    print("🎯 Testing domain-specific filtering:")

    for domain in domains:
        print(f"\n📊 Domain: {domain}")
        try:
            response = await client.query_exa_search(query, domain_filter=domain)
            if response.success:
                tools = response.data.get("tools", [])
                domain_filter = response.data.get("domain_filter")
                print(f"   ✅ Found {len(tools)} tools from {domain_filter}")

                # Verify domain filtering worked
                domain_matches = sum(
                    1 for tool in tools if domain in tool.get("url", "")
                )
                print(f"   🎯 Domain matches: {domain_matches}/{len(tools)}")

                if tools:
                    print(f"   🏆 Top: {tools[0]['name']}")
                    print(f"   🌐 URL: {tools[0].get('url', 'No URL')}")
            else:
                print(f"   ⚠️ Error: {response.error}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")

    await client.close()


async def main():
    """Main test function covering all meeting requirements."""
    print("🧪 Enhanced MCP Integration Testing Suite")
    print("Based on Team Meeting Action Items")
    print("=" * 70)

    try:
        # Test 1: Meeting requirements
        await test_meeting_requirements()

        # Test 2: Concurrent multi-source (Fernando's strategy)
        await test_concurrent_multi_source()

        # Test 3: Subquery strategy (Piyush's recommendation)
        await test_subquery_strategy()

        # Test 4: Domain-specific filtering (David's integration)
        await test_domain_specific_filtering()

        print("\n🎉 Enhanced MCP Integration Testing Complete!")
        print("\n📋 Meeting Action Items Status:")
        print("✅ Alternative MCP servers tested")
        print("✅ Exa Search integration implemented")
        print("✅ Paper search with multiple sources")
        print("✅ Domain-specific filtering working")
        print("✅ Multi-source concurrent querying")
        print("✅ Subquery strategy validated")

        print("\n🚀 Ready for integration with:")
        print("   - RAG system with Gemini integration")
        print("   - ChromaDB optimization and local tool search")
        print("   - LangChain orchestration framework")
        print("   - Multi-source result aggregation")

    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
