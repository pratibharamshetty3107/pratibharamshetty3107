// TechTrapture Search Application with Discovery Engine API
document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    const searchButton = document.getElementById('searchButton');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const resultsContainer = document.getElementById('resultsContainer');
    const answerContent = document.getElementById('answerContent');
    const searchResultsList = document.getElementById('searchResultsList');

    // Perform search
    async function performSearch(query) {
        if (!query.trim()) {
            alert('Please enter a search query');
            return;
        }

        // Show loading, hide results
        loadingIndicator.style.display = 'flex';
        resultsContainer.style.display = 'none';

        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query: query })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            displayResults(data);

        } catch (error) {
            console.error('Search error:', error);
            answerContent.innerHTML = `
                <div class="error-message">
                    <p>❌ Error performing search: ${error.message}</p>
                    <p>Please make sure you're authenticated with gcloud.</p>
                </div>
            `;
            resultsContainer.style.display = 'block';
        } finally {
            loadingIndicator.style.display = 'none';
        }
    }

    // Display search results
    function displayResults(data) {
        // Display AI Answer
        if (data.answer && data.answer.answer) {
            const answer = data.answer.answer;
            let answerHtml = '';

            // Render Markdown Answer
            if (answer.answerText) {
                const rawHtml = marked.parse(answer.answerText);
                answerHtml = `
                    <div class="answer-text markdown-body">${rawHtml}</div>
                `;
            }

            // Add citations if available
            if (answer.citations && answer.citations.length > 0 && answer.references) {
                answerHtml += '<div class="citations"><h4>Sources:</h4><div class="citation-list">';

                // Create a map of unique sources used
                const uniqueSources = new Map();

                answer.citations.forEach(citation => {
                    if (citation.sources) {
                        citation.sources.forEach(source => {
                            const refId = source.referenceId;
                            // Check if we have this reference
                            if (answer.references[refId]) {
                                const ref = answer.references[refId];
                                const metadata = ref.chunkInfo?.documentMetadata;
                                if (metadata) {
                                    const key = metadata.uri || metadata.title;
                                    if (!uniqueSources.has(key)) {
                                        uniqueSources.set(key, {
                                            title: metadata.title || 'Untitled Document',
                                            uri: metadata.uri || '#',
                                            id: refId
                                        });
                                    }
                                }
                            }
                        });
                    }
                });

                // Render unique sources
                uniqueSources.forEach((source, key) => {
                    // Convert gs:// URI to https://storage.cloud.google.com/ URL
                    let displayLink = source.uri;
                    if (displayLink.startsWith('gs://')) {
                        // Remove 'gs://' and prepend storage browser URL
                        const path = displayLink.substring(5);
                        displayLink = `https://storage.cloud.google.com/${path}`;
                    }

                    answerHtml += `
                        <div class="citation-item">
                            <span class="citation-number">[${parseInt(source.id) + 1}]</span>
                            <a href="${displayLink}" target="_blank" class="citation-link" title="${source.uri}">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                                    <polyline points="14 2 14 8 20 8"></polyline>
                                </svg>
                                ${source.title}
                            </a>
                        </div>
                    `;
                });

                answerHtml += '</div></div>';
            }

            answerContent.innerHTML = answerHtml;
        } else {
            answerContent.innerHTML = '<p class="no-answer">No AI answer generated for this query.</p>';
        }

        // Show results container
        resultsContainer.style.display = 'block';

        // Scroll to results
        resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // Format answer text with line breaks
    function formatAnswerText(text) {
        return text.replace(/\n/g, '<br>');
    }

    // Search button click
    searchButton.addEventListener('click', () => {
        performSearch(searchInput.value);
    });

    // Enter key to search
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performSearch(searchInput.value);
        }
    });

    // Keyboard shortcut: Cmd+K or Ctrl+K to focus search
    document.addEventListener('keydown', (e) => {
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
            e.preventDefault();
            searchInput.focus();
        }

        if (e.key === 'Escape' && document.activeElement === searchInput) {
            searchInput.blur();
        }
    });

    // Parallax effect for background gradients
    let mouseX = 0;
    let mouseY = 0;
    let currentX = 0;
    let currentY = 0;

    document.addEventListener('mousemove', (e) => {
        mouseX = e.clientX / window.innerWidth - 0.5;
        mouseY = e.clientY / window.innerHeight - 0.5;
    });

    function animateGradients() {
        currentX += (mouseX - currentX) * 0.05;
        currentY += (mouseY - currentY) * 0.05;

        const gradients = document.querySelectorAll('.bg-gradient');
        gradients.forEach((gradient, index) => {
            const speed = (index + 1) * 20;
            gradient.style.transform = `translate(${currentX * speed}px, ${currentY * speed}px)`;
        });

        requestAnimationFrame(animateGradients);
    }

    animateGradients();

    console.log('TechTrapture Search App with Discovery Engine API initialized! 🚀');
});
