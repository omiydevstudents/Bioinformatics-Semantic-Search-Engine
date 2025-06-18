from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
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
        
        # Initialize ChromaDB client
        self.client = chromadb.Client(Settings(
            persist_directory=str(self.persist_dir),
            anonymized_telemetry=False
        ))
        
        # Initialize embeddings with biomedical model
        self.embeddings = HuggingFaceEmbeddings(
            model_name="microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext",
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
        
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name="bioinformatics_tools",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Initialize LangChain vector store
        self.vector_store = Chroma(
            client=self.client,
            collection_name="bioinformatics_tools",
            embedding_function=self.embeddings
        )

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
            for tool in tools:
                # Prepare tool document
                tool_text = self._prepare_tool_document(tool)
                
                # Split text into chunks
                chunks = self.text_splitter.split_text(tool_text)
                
                # Add to ChromaDB
                self.collection.add(
                    documents=chunks,
                    metadatas=[{
                        "name": tool['name'],
                        "category": tool['category'],
                        "source": tool.get('source', 'unknown')
                    } for _ in chunks],
                    ids=[f"{tool['name']}_{i}" for i in range(len(chunks))]
                )
            
            return True
        except Exception as e:
            print(f"Error adding tools: {str(e)}")
            return False

    async def semantic_search(self, query: str, n_results: int = 5) -> List[Dict]:
        """Perform semantic search for bioinformatics tools."""
        try:
            # Search using LangChain's similarity search
            results = self.vector_store.similarity_search_with_score(
                query,
                k=n_results
            )
            
            # Process results
            tools = []
            for doc, score in results:
                tool_data = {
                    "name": doc.metadata.get("name", "Unknown"),
                    "category": doc.metadata.get("category", "Unknown"),
                    "content": doc.page_content,
                    "relevance_score": float(score),
                    "source": doc.metadata.get("source", "unknown")
                }
                tools.append(tool_data)
            
            return tools
        except Exception as e:
            print(f"Error in semantic search: {str(e)}")
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
            # Search using LangChain's similarity search with filter
            results = self.vector_store.similarity_search_with_score(
                query,
                k=n_results,
                filter={"category": category}
            )
            
            # Process results
            tools = []
            for doc, score in results:
                tool_data = {
                    "name": doc.metadata.get("name", "Unknown"),
                    "category": doc.metadata.get("category", "Unknown"),
                    "content": doc.page_content,
                    "relevance_score": float(score),
                    "source": doc.metadata.get("source", "unknown")
                }
                tools.append(tool_data)
            
            return tools
        except Exception as e:
            print(f"Error in category search: {str(e)}")
            return []

    async def get_similar_tools(self, tool_name: str, n_results: int = 5) -> List[Dict]:
        """Find tools similar to a given tool."""
        try:
            # Get the tool's content
            tool = await self.get_tool_by_name(tool_name)
            if not tool:
                return []
            
            # Search for similar tools
            results = self.vector_store.similarity_search_with_score(
                tool["content"],
                k=n_results,
                filter={"name": {"$ne": tool_name}}  # Exclude the original tool
            )
            
            # Process results
            tools = []
            for doc, score in results:
                tool_data = {
                    "name": doc.metadata.get("name", "Unknown"),
                    "category": doc.metadata.get("category", "Unknown"),
                    "content": doc.page_content,
                    "similarity_score": float(score),
                    "source": doc.metadata.get("source", "unknown")
                }
                tools.append(tool_data)
            
            return tools
        except Exception as e:
            print(f"Error finding similar tools: {str(e)}")
            return [] 