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
    """ChromaDB-based semantic search store for bioinformatics tools."""
    
    def __init__(self, persist_dir: str = "data/chroma"):
        # Create persist directory
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize embeddings with biomedical model FIRST
        self.embeddings = HuggingFaceEmbeddings(
            model_name="NeuML/pubmedbert-base-embeddings",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Initialize text splitter for document chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
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
        """Prepare a tool document for embedding."""
        return f"""
        Tool Name: {tool_data['name']}
        Category: {tool_data['category']}
        Description: {tool_data['description']}
        Features: {', '.join(tool_data['features'])}
        Documentation: {tool_data['documentation']}
        """

    async def add_tools(self, tools: List[Dict]) -> bool:
        """Add multiple tools to the semantic search store."""
        try:
            # Prepare all documents for LangChain
            texts = []
            metadatas = []
            
            for tool in tools:
                # Prepare tool document
                tool_text = self._prepare_tool_document(tool)
                
                # Split text into chunks
                chunks = self.text_splitter.split_text(tool_text)
                
                # Add chunks to the batch
                for chunk in chunks:
                    texts.append(chunk)
                    metadatas.append({
                        "name": tool['name'],
                        "category": tool['category'],
                        "source": tool.get('source', 'unknown')
                    })
            
            # Use LangChain's add_texts method (handles embeddings automatically)
            self.vector_store.add_texts(
                texts=texts,
                metadatas=metadatas
            )
            
            return True
        except Exception as e:
            print(f"Error adding tools: {str(e)}")
            return False

    async def semantic_search(self, query: str, n_results: int = 5) -> List[Dict]:
        """Perform semantic search for bioinformatics tools."""
        try:
            # Try LangChain first for compatibility
            results = self.vector_store.similarity_search_with_score(
                query,
                k=n_results
            )
            
            # Process LangChain results
            tools = []
            for doc, score in results:
                tool_data = {
                    "name": doc.metadata.get("name", "Unknown"),
                    "category": doc.metadata.get("category", "Unknown"),
                    "content": doc.page_content,
                    "relevance_score": float(1.0 - score),  # Convert distance to similarity
                    "source": doc.metadata.get("source", "unknown")
                }
                tools.append(tool_data)
            
            return tools
            
        except Exception as e:
            print(f"LangChain search failed: {str(e)}, falling back to native ChromaDB...")
            # Fallback to native ChromaDB if LangChain fails
            return await self._native_search_fallback(query, n_results)

    async def _native_search_fallback(self, query: str, n_results: int = 5) -> List[Dict]:
        """Fallback to native ChromaDB search if LangChain fails."""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # Process results
            tools = []
            for i in range(len(results['documents'][0])):
                tool_data = {
                    "name": results['metadatas'][0][i].get("name", "Unknown"),
                    "category": results['metadatas'][0][i].get("category", "Unknown"), 
                    "content": results['documents'][0][i],
                    "relevance_score": 1.0 - results['distances'][0][i],  # Convert distance to similarity
                    "source": results['metadatas'][0][i].get("source", "unknown")
                }
                tools.append(tool_data)
            
            return tools
        except Exception as e:
            print(f"Error in fallback search: {str(e)}")
            return []
        
    async def get_tool_by_name(self, name: str) -> Optional[Dict]:
        """Retrieve a specific tool by name."""
        try:
            results = self.collection.get(
                where={"name": name}
            )
            
            if not results['documents']:
                return None
            
            # Combine chunks into a single document
            tool_data = {
                "name": name,
                "content": " ".join(results['documents']),
                "metadata": results['metadatas'][0] if results['metadatas'] else {}
            }
            
            return tool_data
        except Exception as e:
            print(f"Error retrieving tool: {str(e)}")
            return None

    async def search_by_category(self, category: str, query: str, n_results: int = 5) -> List[Dict]:
        """Search for tools within a specific category."""
        try:
            # Try LangChain first for compatibility
            results = self.vector_store.similarity_search_with_score(
                query,
                k=n_results,
                filter={"category": category}
            )
            
            # Process LangChain results
            tools = []
            for doc, score in results:
                tool_data = {
                    "name": doc.metadata.get("name", "Unknown"),
                    "category": doc.metadata.get("category", "Unknown"),
                    "content": doc.page_content,
                    "relevance_score": float(1.0 - score),
                    "source": doc.metadata.get("source", "unknown")
                }
                tools.append(tool_data)
            
            return tools
            
        except Exception as e:
            print(f"LangChain category search failed: {str(e)}, falling back to native ChromaDB...")
            # Fallback to native ChromaDB
            return await self._native_category_search_fallback(category, query, n_results)

    async def _native_category_search_fallback(self, category: str, query: str, n_results: int = 5) -> List[Dict]:
        """Fallback to native ChromaDB category search."""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where={"category": category}
            )
            
            # Process results
            tools = []
            for i in range(len(results['documents'][0])):
                tool_data = {
                    "name": results['metadatas'][0][i].get("name", "Unknown"),
                    "category": results['metadatas'][0][i].get("category", "Unknown"),
                    "content": results['documents'][0][i],
                    "relevance_score": 1.0 - results['distances'][0][i],
                    "source": results['metadatas'][0][i].get("source", "unknown")
                }
                tools.append(tool_data)
            
            return tools
        except Exception as e:
            print(f"Error in category search fallback: {str(e)}")
            return []
        
    async def get_similar_tools(self, tool_name: str, n_results: int = 5) -> List[Dict]:
        """Find tools similar to a given tool."""
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
            
            # Process results and filter out the original tool
            tools = []
            for doc, score in results:
                if doc.metadata.get("name", "Unknown") != tool_name:  # Exclude original tool
                    tool_data = {
                        "name": doc.metadata.get("name", "Unknown"),
                        "category": doc.metadata.get("category", "Unknown"),
                        "content": doc.page_content,
                        "similarity_score": float(1.0 - score),  # Convert distance to similarity
                        "source": doc.metadata.get("source", "unknown")
                    }
                    tools.append(tool_data)
                    
                    if len(tools) >= n_results:  # Stop when we have enough results
                        break
            
            return tools
        except Exception as e:
            print(f"Error finding similar tools: {str(e)}")
            return []