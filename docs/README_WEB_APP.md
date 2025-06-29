# Bioinformatics Tool Discovery Web Application

A beautiful, Perplexity-style web interface for discovering bioinformatics tools with AI-powered search and **Self-RAG quality control**. Built with Apple-inspired design principles and modern web technologies.

## 🌟 Features

- **Conversational Search Interface**: Natural language queries like "I need tools for RNA-seq analysis"
- **AI-Powered Results**: Enhanced with Google Gemini for intelligent analysis
- **Self-RAG Quality Control**: Automatic query refinement, tool grading, hallucination detection, and iterative improvement for the highest quality answers
- **Multi-Source Discovery**: Combines local ChromaDB, web search, and scientific literature
- **Apple-Inspired Design**: Clean, modern UI following Apple's Human Interface Guidelines
- **Real-Time Search**: Fast, responsive search with loading states
- **Source Attribution**: Clear indication of where results come from
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Create a `.env` file in the project root:

```env
# Required for AI enhancement
GOOGLE_API_KEY=your_google_api_key_here

# Optional: Custom port
PORT=8000
```

### 3. Run the Web Application

```bash
python main.py
```

### 4. Open Your Browser

Navigate to: http://localhost:8000

## 🎯 How to Use

### Basic Search

1. **Enter a natural query** in the search box:
   - "I need tools for DNA sequence alignment"
   - "Looking for RNA-seq analysis software"
   - "What tools can I use for variant calling?"

2. **Click the search button** or press Enter

3. **View results** with:
   - AI-generated analysis
   - Recommended tools with relevance scores and quality grades
   - Source attribution
   - Direct links to tools (when available)
   - **Self-RAG quality metrics and reasoning**

### Example Queries

Try these realistic bioinformatics queries:

#### Sequence Analysis
- "I need tools for DNA sequence alignment"
- "Looking for multiple sequence alignment software"
- "What tools can I use for sequence motif discovery?"

#### Genomics & NGS
- "I'm working on RNA-seq data and need analysis tools"
- "Looking for variant calling software for my NGS data"
- "What are the best tools for genome assembly?"

#### Protein Analysis
- "I need protein structure prediction tools"
- "What software can I use for protein-protein interactions?"
- "Looking for tools to identify protein domains"

#### Phylogenetics
- "I need to build phylogenetic trees from my sequence data"
- "Looking for molecular evolution analysis tools"

#### Data Analysis
- "I need to visualize my genomic data"
- "Looking for statistical analysis tools for my RNA-seq results"

## 🧠 Self-RAG Quality Control

This web app now uses a **Self-RAGAgent** for all queries, providing:

- **Automatic Query Refinement**: If the initial query is too broad or unclear, the agent will refine it for better results.
- **Tool Relevance Grading**: Each tool is graded for relevance to your query, with reasoning shown in the UI.
- **Hallucination Detection**: The agent checks if recommendations are grounded in real, factual sources.
- **Iterative Improvement**: The agent can run multiple rounds of search and refinement to maximize answer quality.
- **Quality Metrics**: See at-a-glance indicators for relevance, factual accuracy, and answer quality.

**How it works:**
- When you submit a query, the agent may refine it, grade the results, and iterate up to 3 times for the best answer.
- The UI displays quality grades (e.g., "Verified", "Low Relevance") and reasoning for each tool.
- The analysis section summarizes the quality assessment for the whole answer.

## 🏗️ Architecture

### Backend (FastAPI)
- **main.py**: Main application entry point, now using `SelfRAGAgent` for all queries
- **SelfRAGAgent**: Orchestrates search, quality control, and iterative improvement
- **SemanticSearchStore**: ChromaDB-based local tool database
- **EnhancedMCPClient**: External tool discovery via MCP

### Frontend (HTML/CSS/JavaScript)
- **templates/index.html**: Main web interface
- **static/css/style.css**: Apple-inspired design system
- **static/js/app.js**: Interactive functionality, now displays Self-RAG quality metrics

### Data Sources
1. **Local ChromaDB**: Biopython and Bioconductor tools
2. **Web Search**: EXA and Tavily search engines
3. **Scientific Literature**: PubMed and Europe PMC
4. **AI Enhancement**: Google Gemini for intelligent analysis

## 🎨 Design Features

### Apple-Inspired Design System
- **Typography**: SF Pro Display font family
- **Colors**: Apple's SF Design System color palette
- **Spacing**: Consistent spacing scale
- **Shadows**: Subtle depth with layered shadows
- **Animations**: Smooth, purposeful transitions

### User Experience
- **Loading States**: Clear feedback during search
- **Error Handling**: Graceful error messages
- **Responsive**: Works on all screen sizes
- **Accessibility**: Keyboard navigation and screen reader support
- **Performance**: Fast search with optimized queries
- **Self-RAG Quality Feedback**: See why each tool was recommended and how relevant it is

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Google Gemini API key for AI enhancement | Yes |
| `PORT` | Web server port (default: 8000) | No |

### Customization

#### Styling
Edit `static/css/style.css` to customize:
- Colors and themes
- Typography
- Spacing and layout
- Animations

#### Functionality
Edit `static/js/app.js` to customize:
- Search behavior
- Result formatting
- User interactions
- **Self-RAG quality display**

#### Backend
Edit `main.py` to customize:
- API endpoints
- Response formatting
- Search logic
- **Self-RAG agent behavior**

## 🧪 Testing

Run the test script to verify everything works:

```bash
python test_web_app.py
```

This will check:
- ✅ All required files exist
- ✅ Dependencies are properly installed
- ✅ Components can be imported
- ✅ Database connections work

## 📱 Mobile Support

The web application is fully responsive and works great on:
- **Desktop**: Full-featured experience
- **Tablet**: Optimized touch interface
- **Mobile**: Streamlined mobile experience

## 🔍 Search Capabilities

### Local Database (ChromaDB)
- **Biopython Tools**: 200+ tools and modules
- **Bioconductor Packages**: R-based bioinformatics tools
- **Semantic Search**: AI-powered relevance matching

### External Sources
- **Web Search**: Latest tools and resources
- **Scientific Literature**: Research papers and publications
- **Real-time Discovery**: Always up-to-date results

### AI Enhancement
- **Intelligent Analysis**: Context-aware recommendations
- **Query Understanding**: Natural language processing
- **Result Ranking**: Relevance-based sorting
- **Self-RAG Quality Control**: Automatic grading and iterative improvement

## 🚀 Performance

- **Fast Search**: Results in 1-3 seconds
- **Optimized Queries**: Efficient database queries
- **Caching**: Intelligent result caching
- **Async Processing**: Non-blocking search operations

## 🔒 Security

- **Input Validation**: Sanitized user inputs
- **Error Handling**: Secure error messages
- **CORS Support**: Configurable cross-origin requests
- **Environment Variables**: Secure configuration management

## 📈 Future Enhancements

- **User Accounts**: Save search history and favorites
- **Advanced Filters**: Filter by tool type, language, etc.
- **Export Results**: Download results as CSV/JSON
- **API Access**: RESTful API for programmatic access
- **Dark Mode**: Automatic dark/light theme switching
- **Offline Support**: PWA capabilities for offline use
- **Deeper Self-RAG Analytics**: More detailed quality reporting

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter any issues:

1. Check the test script: `python test_web_app.py`
2. Verify your environment variables
3. Check the console for error messages
4. Open an issue on GitHub

## 🎉 Success!

Your Bioinformatics Tool Discovery Web Application is now ready! Enjoy discovering the perfect tools for your research with this beautiful, AI-powered, and **Self-RAG quality-controlled** interface. 