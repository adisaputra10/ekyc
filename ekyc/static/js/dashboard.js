class EKYCDashboard {
    constructor() {
        this.stats = {
            totalDocs: 0,
            verifiedDocs: 0,
            avgTime: 0,
            avgConfidence: 0
        };
        this.history = [];
        this.currentFile = null;
        
        this.initEventListeners();
        this.loadStats();
        this.loadHistory();
    }
    
    initEventListeners() {
        // Upload functionality
        const uploadZone = document.getElementById('uploadZone');
        const fileInput = document.getElementById('fileInput');
        
        uploadZone.addEventListener('click', () => fileInput.click());
        uploadZone.addEventListener('dragover', this.handleDragOver.bind(this));
        uploadZone.addEventListener('dragleave', this.handleDragLeave.bind(this));
        uploadZone.addEventListener('drop', this.handleDrop.bind(this));
        fileInput.addEventListener('change', this.handleFileSelect.bind(this));
        
        // Chat functionality
        document.getElementById('sendChatBtn').addEventListener('click', this.sendChatMessage.bind(this));
        document.getElementById('chatInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendChatMessage();
        });
        
        // Chat examples
        document.querySelectorAll('.chat-example').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const question = e.target.closest('.chat-example').dataset.question;
                document.getElementById('chatInput').value = question;
                this.sendChatMessage();
            });
        });
        
        // Knowledge base
        document.getElementById('addKnowledgeForm').addEventListener('submit', this.addKnowledge.bind(this));
        document.getElementById('searchKnowledgeBtn').addEventListener('click', this.searchKnowledge.bind(this));
        document.getElementById('searchKnowledge').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.searchKnowledge();
        });
        
        // Refresh buttons
        document.getElementById('refreshHistoryBtn').addEventListener('click', this.loadHistory.bind(this));
    }
    
    // Drag and Drop handlers
    handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        document.getElementById('uploadZone').classList.add('dragover');
    }
    
    handleDragLeave(e) {
        e.preventDefault();
        e.stopPropagation();
        document.getElementById('uploadZone').classList.remove('dragover');
    }
    
    handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        document.getElementById('uploadZone').classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.handleFile(files[0]);
        }
    }
    
    handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) {
            this.handleFile(file);
        }
    }
    
    async handleFile(file) {
        // Validate file
        if (!this.validateFile(file)) return;
        
        this.currentFile = file;
        this.showProgress();
        
        try {
            // Upload file
            const uploadResult = await this.uploadFile(file);
            this.updateProgress(30, 'File uploaded, processing...');
            
            // Analyze document
            const analysisResult = await this.analyzeDocument(uploadResult.filename);
            this.updateProgress(80, 'Analysis complete, generating results...');
            
            // Show results
            await this.delay(500); // Small delay for UX
            this.updateProgress(100, 'Complete!');
            
            setTimeout(() => {
                this.hideProgress();
                this.showResults(analysisResult);
                this.updateStats();
                this.addToHistory(file.name, analysisResult);
            }, 1000);
            
        } catch (error) {
            console.error('Error processing file:', error);
            this.hideProgress();
            this.showAlert('Error: ' + error.message, 'danger');
        }
    }
    
    validateFile(file) {
        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf'];
        const maxSize = 10 * 1024 * 1024; // 10MB
        
        if (!allowedTypes.includes(file.type)) {
            this.showAlert('Format file tidak didukung. Gunakan JPG, PNG, atau PDF.', 'danger');
            return false;
        }
        
        if (file.size > maxSize) {
            this.showAlert('File terlalu besar. Maksimal 10MB.', 'danger');
            return false;
        }
        
        return true;
    }
    
    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/api/upload-document/', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Upload failed');
        }
        
        return await response.json();
    }
    
    async analyzeDocument(filename) {
        const response = await fetch(`/api/analyze-document/${filename}`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error('Analysis failed');
        }
        
        return await response.json();
    }
    
    showProgress() {
        document.querySelector('.progress-container').style.display = 'block';
        document.getElementById('resultCard').style.display = 'none';
    }
    
    updateProgress(percent, text) {
        document.getElementById('progressBar').style.width = `${percent}%`;
        document.getElementById('progressText').textContent = `${percent}%`;
        
        if (text) {
            document.querySelector('.progress-container span').textContent = text;
        }
    }
    
    hideProgress() {
        document.querySelector('.progress-container').style.display = 'none';
        document.getElementById('progressBar').style.width = '0%';
    }
    
    showResults(result) {
        const resultCard = document.getElementById('resultCard');
        const statusBadge = document.getElementById('statusBadge');
        const confidenceBar = document.getElementById('confidenceBar');
        const confidenceText = document.getElementById('confidenceText');
        const processingTime = document.getElementById('processingTime');
        const verificationStatus = document.getElementById('verificationStatus');
        const extractedData = document.getElementById('extractedData');
        const extractedFields = document.getElementById('extractedFields');
        const documentPreview = document.getElementById('documentPreview');
        
        // Set status badge
        const confidence = result.confidence_score || 0;
        let statusClass = 'bg-success';
        let statusText = 'Verified';
        
        if (confidence < 0.5) {
            statusClass = 'bg-danger';
            statusText = 'Rejected';
        } else if (confidence < 0.8) {
            statusClass = 'bg-warning';
            statusText = 'Review Required';
        }
        
        statusBadge.className = `badge ${statusClass}`;
        statusBadge.textContent = statusText;
        
        // Set confidence
        const confidencePercent = Math.round(confidence * 100);
        confidenceBar.style.width = `${confidencePercent}%`;
        confidenceText.textContent = `${confidencePercent}%`;
        
        // Set other info
        processingTime.textContent = `${result.processing_time || 0} detik`;
        verificationStatus.textContent = result.verification_status || 'Unknown';
        
        // Show extracted data
        if (result.extracted_fields && Object.keys(result.extracted_fields).length > 0) {
            extractedFields.innerHTML = this.formatExtractedFields(result.extracted_fields);
            extractedData.style.display = 'block';
        }
        
        // Show document preview
        if (this.currentFile) {
            const reader = new FileReader();
            reader.onload = (e) => {
                documentPreview.src = e.target.result;
                documentPreview.style.display = 'block';
            };
            reader.readAsDataURL(this.currentFile);
        }
        
        resultCard.style.display = 'block';
        this.showAlert('Dokumen berhasil dianalisis!', 'success');
    }
    
    formatExtractedFields(fields) {
        let html = '<div class="row">';
        
        Object.entries(fields).forEach(([key, value]) => {
            html += `
                <div class="col-md-6 mb-2">
                    <strong>${this.formatFieldName(key)}:</strong><br>
                    <span class="text-muted">${value || '-'}</span>
                </div>
            `;
        });
        
        html += '</div>';
        return html;
    }
    
    formatFieldName(key) {
        const fieldNames = {
            'nik': 'NIK',
            'nama': 'Nama Lengkap',
            'tempat_lahir': 'Tempat Lahir',
            'tanggal_lahir': 'Tanggal Lahir',
            'jenis_kelamin': 'Jenis Kelamin',
            'alamat': 'Alamat',
            'rt_rw': 'RT/RW',
            'kelurahan': 'Kelurahan/Desa',
            'kecamatan': 'Kecamatan',
            'kabupaten': 'Kabupaten/Kota',
            'provinsi': 'Provinsi',
            'agama': 'Agama',
            'status_perkawinan': 'Status Perkawinan',
            'pekerjaan': 'Pekerjaan',
            'kewarganegaraan': 'Kewarganegaraan',
            'berlaku_hingga': 'Berlaku Hingga'
        };
        
        return fieldNames[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
    
    // Chat functionality
    async sendChatMessage() {
        const input = document.getElementById('chatInput');
        const message = input.value.trim();
        
        if (!message) return;
        
        // Add user message
        this.addChatMessage(message, 'user');
        input.value = '';
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            const response = await fetch('/api/rag/query/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query: message })
            });
            
            if (!response.ok) {
                throw new Error('Chat request failed');
            }
            
            const result = await response.json();
            
            setTimeout(() => {
                this.hideTypingIndicator();
                this.addChatMessage(result.answer || 'Maaf, saya tidak dapat memberikan jawaban untuk pertanyaan tersebut.', 'bot');
            }, 1000); // Simulate thinking time
            
        } catch (error) {
            console.error('Chat error:', error);
            this.hideTypingIndicator();
            this.addChatMessage('Maaf, terjadi kesalahan. Silakan coba lagi.', 'bot');
        }
    }
    
    addChatMessage(message, type) {
        const chatContainer = document.getElementById('chatContainer');
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${type}-message`;
        
        const sender = type === 'user' ? 'Anda' : 'AI Assistant';
        messageDiv.innerHTML = `<strong>${sender}:</strong><br>${message}`;
        
        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    showTypingIndicator() {
        document.getElementById('typingIndicator').style.display = 'block';
        document.getElementById('chatContainer').scrollTop = document.getElementById('chatContainer').scrollHeight;
    }
    
    hideTypingIndicator() {
        document.getElementById('typingIndicator').style.display = 'none';
    }
    
    // Knowledge base functionality
    async addKnowledge(e) {
        e.preventDefault();
        
        const title = document.getElementById('knowledgeTitle').value;
        const category = document.getElementById('knowledgeCategory').value;
        const tags = document.getElementById('knowledgeTags').value.split(',').map(t => t.trim()).filter(t => t);
        const content = document.getElementById('knowledgeContent').value;
        
        try {
            const response = await fetch('/api/knowledge/add/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    title,
                    category,
                    tags,
                    content
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to add knowledge');
            }
            
            const result = await response.json();
            this.showAlert('Knowledge berhasil ditambahkan!', 'success');
            
            // Reset form
            document.getElementById('addKnowledgeForm').reset();
            
        } catch (error) {
            console.error('Knowledge add error:', error);
            this.showAlert('Gagal menambahkan knowledge: ' + error.message, 'danger');
        }
    }
    
    async searchKnowledge() {
        const query = document.getElementById('searchKnowledge').value.trim();
        const resultsContainer = document.getElementById('knowledgeSearchResults');
        
        if (!query) {
            resultsContainer.innerHTML = `
                <div class="text-center text-muted">
                    <i class="fas fa-search fa-2x mb-2"></i><br>
                    Masukkan kata kunci untuk mencari
                </div>
            `;
            return;
        }
        
        try {
            const response = await fetch('/api/knowledge/search/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query })
            });
            
            if (!response.ok) {
                throw new Error('Search failed');
            }
            
            const results = await response.json();
            this.displayKnowledgeResults(results.results || []);
            
        } catch (error) {
            console.error('Knowledge search error:', error);
            resultsContainer.innerHTML = `
                <div class="alert alert-danger">
                    Error: ${error.message}
                </div>
            `;
        }
    }
    
    displayKnowledgeResults(results) {
        const container = document.getElementById('knowledgeSearchResults');
        
        if (results.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted">
                    <i class="fas fa-search fa-2x mb-2"></i><br>
                    Tidak ada hasil ditemukan
                </div>
            `;
            return;
        }
        
        let html = '';
        results.forEach(result => {
            html += `
                <div class="card mb-2">
                    <div class="card-body p-3">
                        <h6 class="card-title mb-1">${result.title || 'Unknown'}</h6>
                        <p class="card-text small text-muted mb-1">
                            ${(result.content || '').substring(0, 100)}...
                        </p>
                        <span class="badge bg-secondary">${result.category || 'general'}</span>
                        <span class="small text-muted ms-2">Score: ${Math.round((result.score || 0) * 100)}%</span>
                    </div>
                </div>
            `;
        });
        
        container.innerHTML = html;
    }
    
    // Stats and history
    updateStats() {
        this.stats.totalDocs++;
        this.stats.avgTime = ((this.stats.avgTime * (this.stats.totalDocs - 1)) + 2) / this.stats.totalDocs;
        this.stats.avgConfidence = ((this.stats.avgConfidence * (this.stats.totalDocs - 1)) + 85) / this.stats.totalDocs;
        
        document.getElementById('totalDocs').textContent = this.stats.totalDocs;
        document.getElementById('avgTime').textContent = `${Math.round(this.stats.avgTime)}s`;
        document.getElementById('avgConfidence').textContent = `${Math.round(this.stats.avgConfidence)}%`;
    }
    
    addToHistory(filename, result) {
        const historyItem = {
            timestamp: new Date(),
            filename,
            documentType: result.document_type || 'Unknown',
            status: result.verification_status || 'Unknown',
            confidence: Math.round((result.confidence_score || 0) * 100)
        };
        
        this.history.unshift(historyItem);
        this.updateHistoryTable();
    }
    
    updateHistoryTable() {
        const tbody = document.getElementById('historyTableBody');
        
        if (this.history.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center text-muted">
                        <i class="fas fa-inbox fa-2x mb-2"></i><br>
                        Belum ada riwayat pemrosesan
                    </td>
                </tr>
            `;
            return;
        }
        
        let html = '';
        this.history.slice(0, 10).forEach(item => {
            const statusClass = item.confidence > 80 ? 'success' : item.confidence > 50 ? 'warning' : 'danger';
            html += `
                <tr>
                    <td>${item.timestamp.toLocaleString('id-ID')}</td>
                    <td>${item.filename}</td>
                    <td>${item.documentType}</td>
                    <td><span class="badge bg-${statusClass}">${item.status}</span></td>
                    <td>${item.confidence}%</td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary">
                            <i class="fas fa-eye"></i>
                        </button>
                    </td>
                </tr>
            `;
        });
        
        tbody.innerHTML = html;
    }
    
    async loadStats() {
        // Load stats from server or localStorage
        const savedStats = localStorage.getItem('ekyc_stats');
        if (savedStats) {
            this.stats = JSON.parse(savedStats);
            this.updateStatsDisplay();
        }
    }
    
    async loadHistory() {
        // Load history from server or localStorage
        const savedHistory = localStorage.getItem('ekyc_history');
        if (savedHistory) {
            this.history = JSON.parse(savedHistory).map(item => ({
                ...item,
                timestamp: new Date(item.timestamp)
            }));
            this.updateHistoryTable();
        }
    }
    
    updateStatsDisplay() {
        document.getElementById('totalDocs').textContent = this.stats.totalDocs;
        document.getElementById('verifiedDocs').textContent = this.stats.verifiedDocs;
        document.getElementById('avgTime').textContent = `${Math.round(this.stats.avgTime)}s`;
        document.getElementById('avgConfidence').textContent = `${Math.round(this.stats.avgConfidence)}%`;
    }
    
    // Utility functions
    showAlert(message, type = 'success') {
        const alert = document.getElementById('floatingAlert');
        const alertMessage = document.getElementById('alertMessage');
        
        alert.className = `alert alert-${type} alert-dismissible alert-floating`;
        alertMessage.textContent = message;
        alert.style.display = 'block';
        
        setTimeout(() => {
            alert.style.display = 'none';
        }, 5000);
    }
    
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.ekycDashboard = new EKYCDashboard();
});

// Save stats and history before page unload
window.addEventListener('beforeunload', () => {
    if (window.ekycDashboard) {
        localStorage.setItem('ekyc_stats', JSON.stringify(window.ekycDashboard.stats));
        localStorage.setItem('ekyc_history', JSON.stringify(window.ekycDashboard.history));
    }
});
