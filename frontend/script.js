let isProcessing = false;

// Load system status on page load
document.addEventListener('DOMContentLoaded', () => {
    loadStatus();
    setupUploadForm();
});

async function loadStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        const indexStatus = document.getElementById('indexStatus');
        const chunksCount = document.getElementById('chunksCount');
        
        if (data.index_loaded) {
            indexStatus.textContent = 'Loaded';
            indexStatus.className = 'badge';
            indexStatus.style.background = 'var(--success)';
        } else {
            indexStatus.textContent = 'Not Loaded';
            indexStatus.className = 'badge';
            indexStatus.style.background = 'var(--error)';
        }
        
        chunksCount.textContent = data.chunks_count;
        document.getElementById('modelName').textContent = data.models.llm;
    } catch (error) {
        console.error('Error loading status:', error);
    }
}

async function askQuestion() {
    if (isProcessing) return;
    
    const questionInput = document.getElementById('questionInput');
    const question = questionInput.value.trim();
    
    if (!question) {
        addMessage('Please enter a question!', 'error');
        return;
    }
    
    // Clear input
    questionInput.value = '';
    
    // Add user message to chat
    addMessage(question, 'user');
    
    // Show loading indicator
    isProcessing = true;
    const loadingMsg = addMessage('Thinking...', 'assistant', true);
    
    try {
        const response = await fetch('/api/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: question })
        });
        
        const data = await response.json();
        
        // Remove loading message
        if (loadingMsg) loadingMsg.remove();
        
        if (data.error) {
            addMessage(`Error: ${data.error}`, 'assistant');
        } else {
            addAssistantMessage(data);
        }
    } catch (error) {
        if (loadingMsg) loadingMsg.remove();
        addMessage(`Network error: ${error.message}`, 'assistant');
    } finally {
        isProcessing = false;
    }
}

function addMessage(text, type, isLoading = false) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    if (isLoading) {
        contentDiv.innerHTML = '<div class="loading"></div>';
    } else if (type === 'user') {
        contentDiv.innerHTML = `<p>${escapeHtml(text)}</p>`;
    } else {
        contentDiv.innerHTML = `<p>${escapeHtml(text)}</p>`;
    }
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageDiv;
}

function addAssistantMessage(data) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant-message';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Format answer with markdown-like styling
    let answerHtml = `<p>${escapeHtml(data.answer).replace(/\n/g, '<br>')}</p>`;
    
    // Add references if available
    if (data.references && data.references.length > 0) {
        answerHtml += '<div class="references"><strong>📚 Relevant Course Sections:</strong>';
        
        data.references.forEach(ref => {
            answerHtml += `
                <div class="reference-item">
                    <strong>Video ${ref.number}: ${ref.title}</strong><br>
                    ⏱️ Timestamp: ${ref.start} - ${ref.end}<br>
                    <span class="timestamp">${escapeHtml(ref.text)}</span>
                </div>
            `;
        });
        
        answerHtml += '</div>';
    }
    
    contentDiv.innerHTML = answerHtml;
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function setupUploadForm() {
    const form = document.getElementById('uploadForm');
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const videoNumber = document.getElementById('videoNumber').value;
        const videoTitle = document.getElementById('videoTitle').value;
        const videoFile = document.getElementById('videoFile').files[0];
        
        if (!videoFile) {
            alert('Please select a video file');
            return;
        }
        
        const formData = new FormData();
        formData.append('file', videoFile);
        formData.append('number', videoNumber);
        formData.append('title', videoTitle);
        
        const progressBar = document.getElementById('uploadProgress');
        progressBar.style.display = 'block';
        
        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                alert('Video processed successfully!');
                form.reset();
                loadStatus(); // Refresh status
                addMessage(`✅ New video added: "${videoTitle}" (Video ${videoNumber})`, 'assistant');
            } else {
                alert(`Error: ${data.error}`);
            }
        } catch (error) {
            alert(`Upload failed: ${error.message}`);
        } finally {
            progressBar.style.display = 'none';
        }
    });
}

function askQuickQuestion(question) {
    document.getElementById('questionInput').value = question;
    askQuestion();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Allow Enter key to submit (Shift+Enter for new line)
document.getElementById('questionInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        askQuestion();
    }
});