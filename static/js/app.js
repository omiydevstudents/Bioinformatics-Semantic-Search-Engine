/**
 * Bioinformatics Tool Discovery Web App
 * Interactive JavaScript for the search interface with Self-RAG enhancements
 */

// Immediate debugging - this should show up immediately when the file loads
console.log('🚀 Bioinformatics Search App JavaScript loaded!');
console.log('🔧 Testing if JavaScript is working...');

class BioinformaticsSearchApp {
    constructor() {
        console.log('🔧 Initializing BioinformaticsSearchApp...');
        this.searchForm = document.getElementById('searchForm');
        this.searchInput = document.getElementById('searchInput');
        this.searchButton = document.getElementById('searchButton');
        this.loadingContainer = document.getElementById('loadingContainer');
        this.resultsContainer = document.getElementById('resultsContainer');
        this.suggestionChips = document.getElementById('suggestionChips');
        
        console.log('🔧 Elements found:', {
            searchForm: !!this.searchForm,
            searchInput: !!this.searchInput,
            searchButton: !!this.searchButton,
            loadingContainer: !!this.loadingContainer,
            resultsContainer: !!this.resultsContainer,
            suggestionChips: !!this.suggestionChips
        });
        
        this.isSearching = false;
        this.currentQuery = '';
        
        this.initializeEventListeners();
        this.loadSuggestions();
        console.log('✅ BioinformaticsSearchApp initialized successfully!');
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
        const resultsLimit = parseInt(document.getElementById('resultsLimit').value) || 10;
        
        console.log('🔍 Starting search with query:', query);
        
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
            console.log('🔍 Sending request to /api/search');
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    max_results: resultsLimit
                })
            });
            
            console.log('🔍 Response received, status:', response.status);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('🔍 Data parsed successfully');
            
            if (data.success) {
                console.log('🔍 Rendering results...');
                this.renderResults(data);
            } else {
                this.showError(data.error || 'Search failed');
            }
            
        } catch (error) {
            console.error('❌ Search error:', error);
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
        console.log('🔍 Full response data:', data);
        console.log('🔍 Follow-up suggestions in renderResults:', data.follow_up_suggestions);
        
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
        const { query, response, analysis, tools, sources, total_results, search_time, enhanced_with_gemini, quality_metrics, follow_up_suggestions } = data;
        
        // Debug logging
        console.log('🔍 Follow-up suggestions received:', follow_up_suggestions);
        console.log('🔍 Follow-up suggestions type:', typeof follow_up_suggestions);
        console.log('🔍 Follow-up suggestions length:', follow_up_suggestions ? follow_up_suggestions.length : 'undefined');
        
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
                    ${this.formatResponseText(response)}
                </div>
            </div>
        `;
        
        // Add follow-up section if suggestions are available
        if (follow_up_suggestions && follow_up_suggestions.length > 0) {
            console.log('✅ Adding follow-up section with', follow_up_suggestions.length, 'suggestions');
            html += `
                <div class="response-section follow-up-section">
                    <div class="response-header">
                        <div class="response-icon">
                            <i class="fas fa-lightbulb"></i>
                        </div>
                        <h3>Need Better Results?</h3>
                    </div>
                    <div class="follow-up-content">
                        <p class="follow-up-intro">Try asking a follow-up question to get more specific results:</p>
                        
                        <div class="follow-up-suggestions">
                            ${follow_up_suggestions.map(suggestion => `
                                <div class="follow-up-suggestion" onclick="app.useFollowUpSuggestion('${this.escapeHtml(suggestion)}')">
                                    <i class="fas fa-arrow-right"></i>
                                    <span>${this.escapeHtml(suggestion)}</span>
                                </div>
                            `).join('')}
                        </div>
                        
                        <div class="follow-up-input-container">
                            <div class="follow-up-input-wrapper">
                                <i class="fas fa-comment"></i>
                                <input 
                                    type="text" 
                                    id="followUpInput" 
                                    class="follow-up-input" 
                                    placeholder="Or ask your own follow-up question..."
                                    autocomplete="off"
                                >
                                <button type="button" class="follow-up-button" id="followUpButton" onclick="app.performFollowUp()">
                                    <i class="fas fa-arrow-right"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } else {
            console.log('❌ No follow-up suggestions to display');
            // Add a test section to see if the CSS works
            html += `
                <div class="response-section follow-up-section">
                    <div class="response-header">
                        <div class="response-icon">
                            <i class="fas fa-lightbulb"></i>
                        </div>
                        <h3>Test Follow-up Section</h3>
                    </div>
                    <div class="follow-up-content">
                        <p class="follow-up-intro">This is a test section to verify the CSS is working:</p>
                        
                        <div class="follow-up-suggestions">
                            <div class="follow-up-suggestion">
                                <i class="fas fa-arrow-right"></i>
                                <span>Test suggestion 1 - This should be visible</span>
                            </div>
                            <div class="follow-up-suggestion">
                                <i class="fas fa-arrow-right"></i>
                                <span>Test suggestion 2 - If you see this, CSS is working</span>
                            </div>
                        </div>
                        
                        <div class="follow-up-input-container">
                            <div class="follow-up-input-wrapper">
                                <i class="fas fa-comment"></i>
                                <input 
                                    type="text" 
                                    id="followUpInput" 
                                    class="follow-up-input" 
                                    placeholder="Test input field..."
                                    autocomplete="off"
                                >
                                <button type="button" class="follow-up-button" id="followUpButton">
                                    <i class="fas fa-arrow-right"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        // Add analysis section
        if (analysis) {
            html += `
                <div class="response-section">
                    <div class="response-header">
                        <div class="response-icon">
                            <i class="fas fa-chart-line"></i>
                        </div>
                        <h3>Detailed Analysis</h3>
                    </div>
                    <div class="response-text">
                        ${this.formatAnalysisText(analysis)}
                    </div>
                </div>
            `;
        }
        
        // Tools section - organized by source type
        if (tools && tools.length > 0) {
            // Separate tools by type
            const localTools = tools.filter(tool => tool.type === 'local_tool');
            const webTools = tools.filter(tool => tool.type === 'web_tool');
            const scientificPapers = tools.filter(tool => tool.type === 'scientific_paper');
            
            html += `<div class="tools-section">`;
            
            // Local Database Tools
            if (localTools.length > 0) {
                html += `
                    <div class="tool-category-section">
                        <div class="tool-category-header">
                            <h3 class="tool-category-title">
                                <i class="fas fa-database"></i>
                                Tools from Database
                            </h3>
                            <span class="tool-category-count">${localTools.length} tools</span>
                        </div>
                        <div class="tools-grid">
                            ${localTools.map(tool => this.generateToolCardHTML(tool)).join('')}
                        </div>
                    </div>
                `;
            }
            
            // Web Tools
            if (webTools.length > 0) {
                html += `
                    <div class="tool-category-section">
                        <div class="tool-category-header">
                            <h3 class="tool-category-title">
                                <i class="fas fa-globe"></i>
                                Web Tools
                            </h3>
                            <span class="tool-category-count">${webTools.length} tools</span>
                        </div>
                        <div class="tools-grid">
                            ${webTools.map(tool => this.generateToolCardHTML(tool)).join('')}
                        </div>
                    </div>
                `;
            }
            
            // Scientific Papers
            if (scientificPapers.length > 0) {
                html += `
                    <div class="tool-category-section">
                        <div class="tool-category-header">
                            <h3 class="tool-category-title">
                                <i class="fas fa-file-alt"></i>
                                Scientific Literature
                            </h3>
                            <span class="tool-category-count">${scientificPapers.length} papers</span>
                        </div>
                        <div class="tools-grid">
                            ${scientificPapers.map(tool => this.generateToolCardHTML(tool)).join('')}
                        </div>
                    </div>
                `;
            }
            
            html += `</div>`;
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
    
    formatResponseText(text) {
        // Format the main response text with better structure
        if (!text) return '';
        
        // Convert markdown-style formatting to HTML
        let formatted = this.escapeHtml(text);
        
        // Convert **bold** to <strong>
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Convert *italic* to <em>
        formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        // Convert line breaks to paragraphs
        formatted = formatted.replace(/\n\n/g, '</p><p>');
        formatted = formatted.replace(/\n/g, '<br>');
        
        // Wrap in paragraph tags
        formatted = `<p>${formatted}</p>`;
        
        return formatted;
    }
    
    formatAnalysisText(text) {
        // Format the analysis text with better structure
        if (!text) return '';
        
        let formatted = this.escapeHtml(text);
        
        // Convert markdown headers to HTML headers
        formatted = formatted.replace(/^### (.*$)/gm, '<h3>$1</h3>');
        formatted = formatted.replace(/^## (.*$)/gm, '<h3>$1</h3>');
        formatted = formatted.replace(/^# (.*$)/gm, '<h2>$1</h2>');
        
        // Convert **bold** to <strong>
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Convert *italic* to <em>
        formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        // Handle specific enhanced agent response sections with better styling
        formatted = formatted.replace(/\*\*QUALITY ASSESSMENT:\*\*/g, '<h3 class="quality-section">Quality Assessment</h3>');
        formatted = formatted.replace(/\*\*TOP RECOMMENDATIONS.*?\*\*/g, '<h3 class="recommendations-section">Top Recommendations</h3>');
        formatted = formatted.replace(/\*\*DETAILED GAPS ANALYSIS:\*\*/g, '<h3 class="gaps-section">Detailed Gaps Analysis</h3>');
        formatted = formatted.replace(/\*\*ACTIONABLE RECOMMENDATIONS:\*\*/g, '<h3 class="actionable-section">Actionable Recommendations</h3>');
        formatted = formatted.replace(/\*\*OVERALL ASSESSMENT:\*\*/g, '<h3 class="overall-section">Overall Assessment</h3>');
        
        // Convert numbered lists with better formatting
        formatted = formatted.replace(/^(\d+\.\s+.*?)(?=\n\d+\.|$)/gms, '<li>$1</li>');
        
        // Convert bullet points
        formatted = formatted.replace(/^[\*\-•]\s+(.*$)/gm, '<li>$1</li>');
        
        // Wrap consecutive list items in <ul> or <ol> tags
        formatted = formatted.replace(/(<li>.*?<\/li>)(\s*<li>.*?<\/li>)*/gs, function(match) {
            // Check if it's a numbered list
            if (match.match(/^\d+\./)) {
                return `<ol>${match}</ol>`;
            } else {
                return `<ul>${match}</ul>`;
            }
        });
        
        // Convert line breaks to paragraphs
        formatted = formatted.replace(/\n\n/g, '</p><p>');
        formatted = formatted.replace(/\n/g, '<br>');
        
        // Wrap in paragraph tags
        formatted = `<p>${formatted}</p>`;
        
        return formatted;
    }
    
    useFollowUpSuggestion(suggestion) {
        const followUpInput = document.getElementById('followUpInput');
        if (followUpInput) {
            followUpInput.value = suggestion;
            this.performFollowUp();
        }
    }
    
    async performFollowUp() {
        const followUpInput = document.getElementById('followUpInput');
        const followUpButton = document.getElementById('followUpButton');
        
        if (!followUpInput) {
            console.error('Follow-up input not found');
            return;
        }
        
        const followUpQuestion = followUpInput.value.trim();
        const resultsLimit = parseInt(document.getElementById('resultsLimit').value) || 10;
        
        if (!followUpQuestion) {
            this.showError('Please enter a follow-up question');
            return;
        }
        
        if (this.isSearching) {
            return;
        }
        
        this.isSearching = true;
        this.showFollowUpLoading(followUpButton);
        
        try {
            const response = await fetch('/api/followup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    original_query: this.currentQuery,
                    follow_up_question: followUpQuestion,
                    max_results: resultsLimit
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.renderResults(data);
            } else {
                this.showError(data.error || 'Follow-up search failed');
            }
            
        } catch (error) {
            console.error('Follow-up search error:', error);
            this.showError('Failed to perform follow-up search. Please try again.');
        } finally {
            this.isSearching = false;
            this.hideFollowUpLoading(followUpButton);
        }
    }
    
    showFollowUpLoading(button) {
        if (button) {
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        }
    }
    
    hideFollowUpLoading(button) {
        if (button) {
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-arrow-right"></i>';
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
    console.log('📄 DOM loaded, creating app...');
    try {
        window.app = new BioinformaticsSearchApp();
        console.log('✅ App created and assigned to window.app');
    } catch (error) {
        console.error('❌ Error creating app:', error);
    }
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