# Bioinformatics Semantic Search Engine

A powerful semantic search engine specifically designed for bioinformatics tools, leveraging advanced language models and vector databases to provide intelligent tool discovery and recommendation.

## Features

- **Semantic Search**: Find bioinformatics tools using natural language queries
- **Tool Discovery**: Discover tools by category, functionality, or similarity
- **Comprehensive Data**: Integrated data from multiple bioinformatics repositories
- **Intelligent Ranking**: Results ranked by relevance and similarity
- **Biomedical-Specific**: Optimized for bioinformatics terminology and concepts
- **Workflow Management**: Execute and manage bioinformatics workflows using Smithery
- **Advanced Integration**: Seamless integration with MCP, EXA Search, and Smithery platforms

## Architecture

The project is structured into several key components:

### 1. Data Ingestion (`src/data/ingestion.py`)
- Scrapes and processes bioinformatics repositories
- Supports Biopython and Bioconductor
- Extracts tool information, documentation, and features
- Stores processed data in JSON format

### 2. Semantic Search Store (`src/db/chroma_store.py`)
- Uses ChromaDB for vector storage
- Implements biomedical-specific embeddings
- Provides semantic search functionality
- Supports category-based and similarity-based search

### 3. MCP Integration (`src/mcp/mcp_client.py`)
- Connects to multiple MCP servers
- Queries bioinformatics tool metadata
- Enhances search results with up-to-date information
- Supports workflow execution

### 4. Smithery Integration (`src/smithery/smithery_client.py`)
- Interacts with the Smithery platform
- Executes bioinformatics workflows
- Manages workflow templates
- Enhances tool discovery with workflow context

### 5. Tool Discovery Agent (`src/agents/tool_discovery_agent.py`)
- Uses LangChain for intelligent workflow management
- Integrates multiple search sources (MCP, EXA, ChromaDB, Smithery)
- Provides natural language query processing
- Generates comprehensive tool recommendations

### 6. Initialization Script (`src/scripts/initialize_store.py`)
- Sets up the semantic search store
- Ingests repository data
- Populates the vector database
- Tests search functionality

## Setup

1. **Clone the repository**:
```bash
git clone https://github.com/yourusername/bioinformatics-mcp-search.git
cd bioinformatics-mcp-search
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Initialize the search store**:
```bash
python src/scripts/initialize_store.py
```

## Usage

### Basic Search

```python
from src.db.chroma_store import SemanticSearchStore

# Initialize store
store = SemanticSearchStore()

# Search for tools
results = await store.semantic_search("sequence alignment")

# Search by category
rna_tools = await store.search_by_category("rna", "differential expression")

# Find similar tools
similar = await store.get_similar_tools("BLAST")
```

### Advanced Search with Workflows

```python
from src.agents.tool_discovery_agent import ToolDiscoveryAgent

# Initialize agent
agent = ToolDiscoveryAgent()

# Discover tools with workflow execution
result = await agent.discover_tools("I need to analyze RNA-seq data for differential expression")
print(result["response"])
```

### Search Results

Search results include:
- Tool name and description
- Category and functionality
- Source repository
- Relevance score
- Similar tools
- Workflow recommendations (when applicable)

## Configuration

The following environment variables can be configured in `.env`:

- `CHROMA_DB_DIR`: Directory for ChromaDB storage
- `EMBEDDING_MODEL`: Model for generating embeddings
- `REPOSITORY_DATA_DIR`: Directory for storing repository data
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `SMITHERY_API_KEY`: API key for Smithery platform
- `SMITHERY_API_URL`: Base URL for Smithery API
- `BIO_MCP_URL`: URL for bioinformatics MCP server
- `PUBMED_MCP_URL`: URL for PubMed MCP server
- `BIO_CONTEXT_URL`: URL for BioContext MCP server

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Biopython and Bioconductor communities for their comprehensive tool repositories
- ChromaDB for vector storage capabilities
- Google Gemini for advanced language model capabilities
- Smithery platform for workflow management
- LangChain for intelligent agent capabilities 