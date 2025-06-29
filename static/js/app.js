/**
 * Bioinformatics Tool Discovery Web App
 * Interactive JavaScript for the search interface with Self-RAG enhancements
 */

class BioinformaticsSearchApp {
    constructor() {
        this.searchForm = document.getElementById('searchForm');
        this.searchInput = document.getElementById('searchInput');
        this.searchButton = document.getElementById('searchButton');
        this.loadingContainer = document.getElementById('loadingContainer');
        this.resultsContainer = document.getElementById('resultsContainer');
        this.suggestionChips = document.getElementById('suggestionChips');
        
        this.isSearching = false;
        this.currentQuery = '';
        
        this.initializeEventListeners();
        this.loadSuggestions();
    }
    
    initializeEventListeners() {
        // Search form submission
        this.searchForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.performSearch();
        });
        
        // Search input events
        this.searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !this.isSearching) {
                this.performSearch();
            }
        });
        
        // Search button click
        this.searchButton.addEventListener('click', (e) => {
            e.preventDefault();
            this.performSearch();
        });
        
        // Input focus for better UX
        this.searchInput.addEventListener('focus', () => {
            this.searchInput.parentElement.classList.add('focused');
        });
        
        this.searchInput.addEventListener('blur', () => {
            this.searchInput.parentElement.classList.remove('focused');
        });
    }
    
    async loadSuggestions() {
        try {
            const response = await fetch('/api/suggestions');
            const data = await response.json();
            
            if (data.suggestions) {
                this.renderSuggestions(data.suggestions);
            }
        } catch (error) {
            console.error('Failed to load suggestions:', error);
        }
    }
    
    renderSuggestions(suggestions) {
        this.suggestionChips.innerHTML = '';
        
        suggestions.forEach(suggestion => {
            const chip = document.createElement('div');
            chip.className = 'suggestion-chip';
            chip.textContent = suggestion;
            chip.addEventListener('click', () => {
                this.searchInput.value = suggestion;
                this.performSearch();
            });
            this.suggestionChips.appendChild(chip);
        });
    }
    
    async performSearch() {
        const query = this.searchInput.value.trim();
        
        if (!query) {
            this.showError('Please enter a search query');
            return;
        }
        
        if (this.isSearching) {
            return;
        }
        
        this.currentQuery = query;
        this.isSearching = true;
        this.showLoading();
        this.hideResults();
        
        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    max_results: 10
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.renderResults(data);
            } else {
                this.showError(data.error || 'Search failed');
            }
            
        } catch (error) {
            console.error('Search error:', error);
            this.showError('Failed to perform search. Please try again.');
        } finally {
            this.isSearching = false;
            this.hideLoading();
        }
    }
    
    showLoading() {
        this.loadingContainer.style.display = 'block';
        this.searchButton.disabled = true;
        this.searchButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    }
    
    hideLoading() {
        this.loadingContainer.style.display = 'none';
        this.searchButton.disabled = false;
        this.searchButton.innerHTML = '<i class="fas fa-arrow-right"></i>';
    }
    
    showError(message) {
        this.hideLoading();
        this.hideResults();
        
        const errorHtml = `
            <div class="response-section">
                <div class="response-header">
                    <div class="response-icon">
                        <i class="fas fa-exclamation-triangle"></i>
                    </div>
                    <h3>Search Error</h3>
                </div>
                <div class="response-text">
                    ${message}
                </div>
            </div>
        `;
        
        this.resultsContainer.innerHTML = errorHtml;
        this.resultsContainer.style.display = 'block';
    }
    
    hideResults() {
        this.resultsContainer.style.display = 'none';
    }
    
    renderResults(data) {
        const resultsHtml = this.generateResultsHTML(data);
        this.resultsContainer.innerHTML = resultsHtml;
        this.resultsContainer.style.display = 'block';
        
        // Scroll to results
        this.resultsContainer.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start' 
        });
    }
    
    generateResultsHTML(data) {
        const { query, response, analysis, tools, sources, total_results, search_time, enhanced_with_gemini, quality_metrics } = data;
        
        let html = `
            <div class="response-section">
                <div class="response-header">
                    <div class="response-icon">
                        <i class="fas fa-search"></i>
                    </div>
                    <div>
                        <h3>Search Results</h3>
                        <p style="color: var(--text-secondary); font-size: var(--font-size-sm); margin-top: 4px;">
                            Found ${total_results} results in ${search_time.toFixed(2)}s
                            ${enhanced_with_gemini ? '• Enhanced with AI' : ''}
                            ${quality_metrics ? '• Self-RAG Quality Control' : ''}
                        </p>
                    </div>
                </div>
                <div class="response-text">
                    ${response}
                </div>
                ${analysis ? `<div class="analysis-text">${analysis}</div>` : ''}
            </div>
        `;
        
        // Tools section
        if (tools && tools.length > 0) {
            html += `
                <div class="tools-section">
                    <div class="tools-header">
                        <h3 class="tools-title">Recommended Tools</h3>
                        <span class="tools-count">${tools.length} tools</span>
                    </div>
                    <div class="tools-grid">
                        ${tools.map(tool => this.generateToolCardHTML(tool)).join('')}
                    </div>
                </div>
            `;
        }
        
        // Sources section
        if (sources && sources.length > 0) {
            html += `
                <div class="sources-section">
                    <h3 class="sources-title">Sources</h3>
                    <div class="sources-list">
                        ${sources.map(source => this.generateSourceHTML(source)).join('')}
                    </div>
                </div>
            `;
        }
        
        return html;
    }
    
    generateToolCardHTML(tool) {
        const { name, category, description, source, relevance_score, type, url, quality_grade, quality_reasoning } = tool;
        
        const scorePercentage = Math.round(relevance_score * 100);
        const scoreColor = relevance_score > 0.8 ? 'var(--success-green)' : 
                          relevance_score > 0.6 ? 'var(--warning-orange)' : 'var(--text-secondary)';
        
        const typeIcon = this.getTypeIcon(type);
        const sourceIcon = this.getSourceIcon(source);
        
        // Quality grade indicator
        let qualityIndicator = '';
        if (quality_grade && quality_grade !== 'unknown') {
            const qualityColor = quality_grade === 'yes' ? 'var(--success-green)' : 
                               quality_grade === 'no' ? 'var(--error-red)' : 'var(--text-secondary)';
            const qualityIcon = quality_grade === 'yes' ? 'fas fa-check-circle' : 
                              quality_grade === 'no' ? 'fas fa-times-circle' : 'fas fa-question-circle';
            
            qualityIndicator = `
                <div class="tool-quality" style="margin-top: var(--spacing-sm);">
                    <i class="${qualityIcon}" style="color: ${qualityColor}; font-size: var(--font-size-sm);"></i>
                    <span style="font-size: var(--font-size-xs); color: var(--text-secondary); margin-left: var(--spacing-xs);">
                        Quality: ${quality_grade === 'yes' ? 'Verified' : quality_grade === 'no' ? 'Low Relevance' : quality_grade}
                    </span>
                </div>
            `;
        }
        
        return `
            <div class="tool-card" ${url ? `onclick="window.open('${url}', '_blank')"` : ''}>
                <div class="tool-header">
                    <h4 class="tool-name">${this.escapeHtml(name)}</h4>
                    <span class="tool-score" style="background: ${scoreColor}">
                        ${scorePercentage}%
                    </span>
                </div>
                <div class="tool-category">
                    <i class="${typeIcon}"></i> ${this.escapeHtml(category)}
                </div>
                <p class="tool-description">${this.escapeHtml(description)}</p>
                <div class="tool-source">
                    <i class="${sourceIcon}"></i>
                    ${this.escapeHtml(source)}
                </div>
                ${qualityIndicator}
            </div>
        `;
    }
    
    generateSourceHTML(source) {
        const { name, description, type } = source;
        const icon = this.getSourceIcon(name);
        
        return `
            <div class="source-item">
                <i class="${icon}"></i>
                <div>
                    <strong>${this.escapeHtml(name)}</strong>
                    <div style="font-size: var(--font-size-xs); color: var(--text-secondary);">
                        ${this.escapeHtml(description)}
                    </div>
                </div>
            </div>
        `;
    }
    
    getTypeIcon(type) {
        const icons = {
            'local_tool': 'fas fa-database',
            'web_tool': 'fas fa-globe',
            'scientific_paper': 'fas fa-file-alt',
            'default': 'fas fa-tools'
        };
        return icons[type] || icons.default;
    }
    
    getSourceIcon(source) {
        const sourceLower = source.toLowerCase();
        
        if (sourceLower.includes('chromadb') || sourceLower.includes('local')) {
            return 'fas fa-database';
        } else if (sourceLower.includes('web') || sourceLower.includes('search')) {
            return 'fas fa-search';
        } else if (sourceLower.includes('pubmed') || sourceLower.includes('literature')) {
            return 'fas fa-book';
        } else if (sourceLower.includes('biopython')) {
            return 'fab fa-python';
        } else if (sourceLower.includes('bioconductor')) {
            return 'fas fa-r-project';
        } else {
            return 'fas fa-info-circle';
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new BioinformaticsSearchApp();
});

// Add some utility functions for better UX
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + K to focus search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        document.getElementById('searchInput').focus();
    }
});

// Add smooth scrolling for better UX
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
}); 