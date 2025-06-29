import numpy as np
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
# Replace the old imports at the top of chroma_store.py
try:
    from langchain_chroma import Chroma
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    # Fallback to old versions
    from langchain_community.vectorstores import Chroma
    from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class SemanticSearchStore:
    """ChromaDB-based semantic search store for bioinformatics tools - SINGLE ENTRY PER TOOL."""
    
    def __init__(self, persist_dir: str = "data/chroma"):
        # Create persist directory
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize embeddings with biomedical model FIRST
        self.embeddings = HuggingFaceEmbeddings(
            model_name="FremyCompany/BioLORD-2023",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Keep text splitter for backward compatibility but won't use it for chunking
        # Some methods might still reference it, so we keep it initialized
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=100000,  # Very large size to prevent chunking
            chunk_overlap=0,    # No overlap needed
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Initialize LangChain vector store FIRST (this creates the ChromaDB client)
        self.vector_store = Chroma(
            collection_name="bioinformatics_tools_v2",
            embedding_function=self.embeddings,
            persist_directory=str(self.persist_dir)
        )
        
        # Get the ChromaDB client and collection from LangChain
        self.client = self.vector_store._client
        self.collection = self.vector_store._collection

    def _prepare_tool_document(self, tool_data: Dict) -> str:
        """Prepare a tool document for embedding - NO LENGTH LIMITS."""
        
        # Extract all available information with no truncation
        name = tool_data.get('name', 'Unknown Tool')
        category = tool_data.get('category', 'Unknown Category')
        description = tool_data.get('description', 'No description available')
        features = tool_data.get('features', [])
        documentation = tool_data.get('documentation', 'No documentation link')
        source = tool_data.get('source', 'Unknown Source')
        version = tool_data.get('version', 'Unknown Version')
        programming_language = tool_data.get('programming_language', 'Unknown Language')
        license_info = tool_data.get('license', 'Unknown License')
        full_name = tool_data.get('full_name', name)
        
        # Prepare features text - include ALL features, no limit
        if isinstance(features, list) and features:
            features_text = ', '.join(str(feature) for feature in features)
        else:
            features_text = 'No features listed'
        
        # Create comprehensive document with ALL information - NO TRUNCATION
        document = f"""Tool Name: {name}
Full Name: {full_name}
Source: {source}
Category: {category}
Programming Language: {programming_language}
Version: {version}
License: {license_info}

Description: {description}

Features: {features_text}

Documentation: {documentation}"""
        
        return document

    async def add_tools(self, tools: List[Dict]) -> bool:
        """Add multiple tools to the semantic search store - ONE ENTRY PER TOOL."""
        try:
            print(f"🔄 Processing {len(tools)} tools for ChromaDB (single entry per tool)")
            
            # Prepare all documents for LangChain - NO CHUNKING
            texts = []
            metadatas = []
            
            for tool in tools:
                # Prepare complete tool document with no length limits
                tool_text = self._prepare_tool_document(tool)
                
                # Add COMPLETE tool as single entry - NO SPLITTING
                texts.append(tool_text)
                
                # Enhanced metadata with all available fields
                metadata = {
                    "name": tool.get('name', 'Unknown'),
                    "category": tool.get('category', 'Unknown'),
                    "source": tool.get('source', 'unknown'),
                    "full_name": tool.get('full_name', tool.get('name', 'Unknown')),
                    "programming_language": tool.get('programming_language', 'Unknown'),
                    "version": tool.get('version', 'Unknown'),
                    "license": tool.get('license', 'Unknown'),
                    "tool_type": tool.get('tool_type', 'package')
                }
                metadatas.append(metadata)
            
            # Use LangChain's add_texts method (handles embeddings automatically)
            print(f"📝 Adding {len(texts)} complete tool documents to ChromaDB...")
            self.vector_store.add_texts(
                texts=texts,
                metadatas=metadatas
            )
            
            print(f"✅ Successfully added {len(tools)} tools as {len(texts)} single entries")
            print(f"🎯 Ratio: 1 tool = 1 database entry (no chunking applied)")
            
            return True
        except Exception as e:
            print(f"❌ Error adding tools: {str(e)}")
            return False

    async def semantic_search(self, query: str, n_results: int = 5) -> List[Dict]:
        """Perform semantic search for bioinformatics tools - ONE RESULT PER TOOL."""
        try:
            # Try LangChain first for compatibility
            results = self.vector_store.similarity_search_with_score(
                query,
                k=n_results
            )
            
            # Process LangChain results with FIXED scoring
            tools = []
            seen_tools = set()  # Ensure no duplicates (shouldn't happen with single entries)
            
            for doc, score in results:
                tool_name = doc.metadata.get("name", "Unknown")
                
                # Skip if we've already seen this tool (safety check)
                if tool_name in seen_tools:
                    print(f"⚠️ Warning: Duplicate tool '{tool_name}' found in results (shouldn't happen)")
                    continue
                seen_tools.add(tool_name)
                
                # FIX: Better distance to similarity conversion
                similarity_score = np.exp(-score * 0.5)
                
                # Ensure score is between 0 and 1
                similarity_score = max(0.0, min(1.0, similarity_score))
                
                tool_data = {
                    "name": tool_name,
                    "category": doc.metadata.get("category", "Unknown"),
                    "content": doc.page_content,
                    "relevance_score": float(similarity_score),  # Now always positive
                    "source": doc.metadata.get("source", "unknown"),
                    "full_name": doc.metadata.get("full_name", tool_name),
                    "programming_language": doc.metadata.get("programming_language", "Unknown"),
                    "version": doc.metadata.get("version", "Unknown"),
                    "license": doc.metadata.get("license", "Unknown"),
                    "tool_type": doc.metadata.get("tool_type", "package")
                }
                tools.append(tool_data)
            
            return tools
            
        except Exception as e:
            print(f"LangChain search failed: {str(e)}, falling back to native ChromaDB...")
            # Fallback to native ChromaDB if LangChain fails
            return await self._native_search_fallback(query, n_results)

    async def _native_search_fallback(self, query: str, n_results: int = 5) -> List[Dict]:
        """Fallback to native ChromaDB search with FIXED scoring - ONE RESULT PER TOOL."""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # Process results with FIXED scoring
            tools = []
            seen_tools = set()  # Ensure no duplicates
            
            for i in range(len(results['documents'][0])):
                tool_name = results['metadatas'][0][i].get("name", "Unknown")
                
                # Skip duplicates (safety check)
                if tool_name in seen_tools:
                    continue
                seen_tools.add(tool_name)
                
                distance = results['distances'][0][i]
                
                # FIX: Better distance to similarity conversion
                if distance <= 1.0:
                    similarity_score = 1.0 - distance
                else:
                    similarity_score = 1.0 / (1.0 + distance)
                
                # Ensure score is between 0 and 1
                similarity_score = max(0.0, min(1.0, similarity_score))
                
                tool_data = {
                    "name": tool_name,
                    "category": results['metadatas'][0][i].get("category", "Unknown"), 
                    "content": results['documents'][0][i],
                    "relevance_score": float(similarity_score),  # Now always positive
                    "source": results['metadatas'][0][i].get("source", "unknown"),
                    "full_name": results['metadatas'][0][i].get("full_name", tool_name),
                    "programming_language": results['metadatas'][0][i].get("programming_language", "Unknown"),
                    "version": results['metadatas'][0][i].get("version", "Unknown")
                }
                tools.append(tool_data)
            
            return tools
        except Exception as e:
            print(f"Error in fallback search: {str(e)}")
            return []
        
    async def get_tool_by_name(self, name: str) -> Optional[Dict]:
        """Retrieve a specific tool by name - SINGLE ENTRY EXPECTED."""
        try:
            results = self.collection.get(
                where={"name": name},
                limit=1  # Should only be one entry per tool now
            )
            
            if not results['documents']:
                return None
            
            # Should be exactly one document per tool
            tool_data = {
                "name": name,
                "content": results['documents'][0],  # Single document, no combining needed
                "metadata": results['metadatas'][0] if results['metadatas'] else {}
            }
            
            return tool_data
        except Exception as e:
            print(f"Error retrieving tool: {str(e)}")
            return None

    async def search_by_category(self, category: str, query: str, n_results: int = 5) -> List[Dict]:
        """Search for tools within a specific category - ONE RESULT PER TOOL."""
        try:
            # Try LangChain first for compatibility
            results = self.vector_store.similarity_search_with_score(
                query,
                k=n_results,
                filter={"category": category}
            )
            
            # Process LangChain results with FIXED scoring
            tools = []
            seen_tools = set()  # Ensure no duplicates
            
            for doc, score in results:
                tool_name = doc.metadata.get("name", "Unknown")
                
                # Skip duplicates
                if tool_name in seen_tools:
                    continue
                seen_tools.add(tool_name)
                
                # FIX: Better distance to similarity conversion
                similarity_score = np.exp(-score * 0.5)
                
                # Ensure score is between 0 and 1
                similarity_score = max(0.0, min(1.0, similarity_score))
                
                tool_data = {
                    "name": tool_name,
                    "category": doc.metadata.get("category", "Unknown"),
                    "content": doc.page_content,
                    "relevance_score": float(similarity_score),
                    "source": doc.metadata.get("source", "unknown"),
                    "full_name": doc.metadata.get("full_name", tool_name),
                    "programming_language": doc.metadata.get("programming_language", "Unknown")
                }
                tools.append(tool_data)
            
            return tools
            
        except Exception as e:
            print(f"LangChain category search failed: {str(e)}, falling back to native ChromaDB...")
            # Fallback to native ChromaDB
            return await self._native_category_search_fallback(category, query, n_results)

    async def _native_category_search_fallback(self, category: str, query: str, n_results: int = 5) -> List[Dict]:
        """Fallback to native ChromaDB category search with FIXED scoring - ONE RESULT PER TOOL."""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where={"category": category}
            )
            
            # Process results with FIXED scoring
            tools = []
            seen_tools = set()  # Ensure no duplicates
            
            for i in range(len(results['documents'][0])):
                tool_name = results['metadatas'][0][i].get("name", "Unknown")
                
                # Skip duplicates
                if tool_name in seen_tools:
                    continue
                seen_tools.add(tool_name)
                
                distance = results['distances'][0][i]
                
                # FIX: Better distance to similarity conversion
                if distance <= 1.0:
                    similarity_score = 1.0 - distance
                else:
                    similarity_score = 1.0 / (1.0 + distance)
                
                # Ensure score is between 0 and 1
                similarity_score = max(0.0, min(1.0, similarity_score))
                
                tool_data = {
                    "name": results['metadatas'][0][i].get("name", "Unknown"),
                    "category": results['metadatas'][0][i].get("category", "Unknown"),
                    "content": results['documents'][0][i],
                    "relevance_score": float(similarity_score),
                    "source": results['metadatas'][0][i].get("source", "unknown")
                }
                tools.append(tool_data)
            
            return tools
        except Exception as e:
            print(f"Error in category search fallback: {str(e)}")
            return []
        
    async def get_similar_tools(self, tool_name: str, n_results: int = 5) -> List[Dict]:
        """Find tools similar to a given tool - ONE RESULT PER SIMILAR TOOL."""
        try:
            # Get the tool's content
            tool = await self.get_tool_by_name(tool_name)
            if not tool:
                return []
            
            # Use LangChain for similarity search (this should work now)
            results = self.vector_store.similarity_search_with_score(
                tool["content"],
                k=n_results + 1  # Get extra results to filter out the original tool
            )
            
            # Process results and filter out the original tool with FIXED scoring
            tools = []
            seen_tools = set()
            
            for doc, score in results:
                found_tool_name = doc.metadata.get("name", "Unknown")
                
                # Skip the original tool and any duplicates
                if found_tool_name == tool_name or found_tool_name in seen_tools:
                    continue
                seen_tools.add(found_tool_name)
                
                # FIX: Better distance to similarity conversion
                similarity_score = np.exp(-score * 0.5)
                
                # Ensure score is between 0 and 1
                similarity_score = max(0.0, min(1.0, similarity_score))
                
                tool_data = {
                    "name": found_tool_name,
                    "category": doc.metadata.get("category", "Unknown"),
                    "content": doc.page_content,
                    "similarity_score": float(similarity_score),  # Now always positive
                    "source": doc.metadata.get("source", "unknown"),
                    "full_name": doc.metadata.get("full_name", found_tool_name)
                }
                tools.append(tool_data)
                
                if len(tools) >= n_results:  # Stop when we have enough results
                    break
            
            return tools
        except Exception as e:
            print(f"Error finding similar tools: {str(e)}")
            return []

    def get_database_stats(self) -> Dict:
        """Get database statistics - should show 1:1 tool to entry ratio."""
        try:
            total_count = self.collection.count()
            
            # Get sample to analyze sources and categories
            sample_size = min(100, total_count)
            sample = self.collection.get(limit=sample_size)
            
            sources = {}
            categories = {}
            programming_languages = {}
            
            if sample['metadatas']:
                for metadata in sample['metadatas']:
                    if metadata:
                        source = metadata.get('source', 'Unknown')
                        category = metadata.get('category', 'Unknown')
                        lang = metadata.get('programming_language', 'Unknown')
                        
                        sources[source] = sources.get(source, 0) + 1
                        categories[category] = categories.get(category, 0) + 1
                        programming_languages[lang] = programming_languages.get(lang, 0) + 1
            
            return {
                "total_entries": total_count,
                "sources": sources,
                "categories": categories,
                "programming_languages": programming_languages,
                "entries_per_tool": "1:1 (single entry per tool)",
                "chunking_disabled": True,
                "description_length_limit": None
            }
            
        except Exception as e:
            print(f"Error getting database stats: {str(e)}")
            return {"error": str(e)}