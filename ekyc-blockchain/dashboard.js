// Dashboard Management for eKYC Blockchain Verification
class eKYCDashboard {
    constructor() {
        this.blockchain = new BlockchainUtils();
        this.verifications = [];
        this.filteredVerifications = [];
        this.currentPage = 1;
        this.itemsPerPage = 10;
        this.searchTerm = '';
        this.statusFilter = '';
        this.dateFilter = '';
        
        this.initializeDashboard();
    }

    async initializeDashboard() {
        this.bindEvents();
        this.showLoading('Loading blockchain data...');
        
        try {
            await this.loadBlockchainData();
            await this.loadVerificationData();
            this.updateStats();
            this.renderTable();
            this.updatePagination();
        } catch (error) {
            console.error('Dashboard initialization error:', error);
            this.showError('Failed to load dashboard data');
        } finally {
            this.hideLoading();
        }
    }

    bindEvents() {
        // Header actions
        document.getElementById('new-verification').addEventListener('click', () => {
            window.location.href = 'index.html';
        });
        
        document.getElementById('refresh-data').addEventListener('click', () => {
            this.refreshData();
        });
        
        document.getElementById('export-data').addEventListener('click', () => {
            this.exportData();
        });

        // Search and filters
        document.getElementById('search-input').addEventListener('input', (e) => {
            this.searchTerm = e.target.value;
            this.applyFilters();
        });
        
        document.getElementById('search-btn').addEventListener('click', () => {
            this.applyFilters();
        });

        document.getElementById('status-filter').addEventListener('change', (e) => {
            this.statusFilter = e.target.value;
            this.applyFilters();
        });

        document.getElementById('date-filter').addEventListener('change', (e) => {
            this.dateFilter = e.target.value;
            this.applyFilters();
        });

        document.getElementById('clear-filters').addEventListener('click', () => {
            this.clearFilters();
        });

        // Table actions
        document.getElementById('select-all').addEventListener('change', (e) => {
            this.selectAllRows(e.target.checked);
        });

        document.getElementById('per-page').addEventListener('change', (e) => {
            this.itemsPerPage = parseInt(e.target.value);
            this.currentPage = 1;
            this.renderTable();
            this.updatePagination();
        });

        // Pagination
        document.getElementById('prev-page').addEventListener('click', () => {
            if (this.currentPage > 1) {
                this.currentPage--;
                this.renderTable();
                this.updatePagination();
            }
        });

        document.getElementById('next-page').addEventListener('click', () => {
            const totalPages = Math.ceil(this.filteredVerifications.length / this.itemsPerPage);
            if (this.currentPage < totalPages) {
                this.currentPage++;
                this.renderTable();
                this.updatePagination();
            }
        });

        // Modal events
        document.getElementById('close-detail-modal').addEventListener('click', () => {
            this.closeModal();
        });

        document.getElementById('download-certificate-modal').addEventListener('click', () => {
            this.downloadCertificateFromModal();
        });

        document.getElementById('verify-on-blockchain').addEventListener('click', () => {
            this.verifyOnBlockchain();
        });

        // Empty state action
        document.getElementById('create-first-verification').addEventListener('click', () => {
            window.location.href = 'index.html';
        });
    }

    async loadBlockchainData() {
        // Simulate connecting to blockchain
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // In real implementation, this would connect to actual blockchain
        this.blockchain.isConnected = true;
        this.blockchain.accounts = [this.blockchain.generateAddress()];
    }

    async loadVerificationData() {
        // Load demo data and any existing verifications
        this.verifications = [
            ...demoData.sampleVerifications,
            ...this.generateAdditionalDemoData()
        ];
        
        // Add user names and additional data
        this.verifications = this.verifications.map((verification, index) => ({
            ...verification,
            userName: this.generateRandomName(),
            email: `user${verification.tokenId}@example.com`,
            phone: `+6281234567${(index + 10).toString().padStart(2, '0')}`,
            documentTypes: ['National ID', 'Proof of Address'],
            biometricVerified: true,
            verificationScore: Math.floor(Math.random() * 10) + 90
        }));
        
        this.filteredVerifications = [...this.verifications];
    }

    generateAdditionalDemoData() {
        const additionalData = [];
        const statuses = ['verified', 'pending', 'verified', 'verified', 'pending'];
        
        for (let i = 3; i <= 25; i++) {
            const date = new Date();
            date.setDate(date.getDate() - Math.floor(Math.random() * 30));
            
            additionalData.push({
                tokenId: i,
                userAddress: this.blockchain.generateAddress(),
                verificationHash: this.generateHash(),
                timestamp: date.toISOString(),
                status: statuses[Math.floor(Math.random() * statuses.length)],
                blockNumber: 1200000 + i * 100,
                transactionHash: this.generateHash()
            });
        }
        
        return additionalData;
    }

    generateRandomName() {
        const firstNames = ['John', 'Jane', 'Michael', 'Sarah', 'David', 'Lisa', 'Robert', 'Emily', 'James', 'Maria', 'William', 'Jessica', 'Richard', 'Ashley', 'Joseph', 'Amanda'];
        const lastNames = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas'];
        
        const firstName = firstNames[Math.floor(Math.random() * firstNames.length)];
        const lastName = lastNames[Math.floor(Math.random() * lastNames.length)];
        
        return `${firstName} ${lastName}`;
    }

    generateHash() {
        return '0x' + Array.from({length: 64}, () => Math.floor(Math.random() * 16).toString(16)).join('');
    }

    updateStats() {
        const totalUsers = this.verifications.length;
        const totalTokens = this.verifications.length;
        const totalTransactions = this.verifications.length;
        const verifiedCount = this.verifications.filter(v => v.status === 'verified').length;
        const successRate = totalUsers > 0 ? Math.round((verifiedCount / totalUsers) * 100) : 100;

        // Animate numbers
        this.animateNumber('total-users', totalUsers);
        this.animateNumber('total-tokens', totalTokens);
        this.animateNumber('total-transactions', totalTransactions);
        document.getElementById('success-rate').textContent = `${successRate}%`;
    }

    animateNumber(elementId, targetValue) {
        const element = document.getElementById(elementId);
        const startValue = parseInt(element.textContent) || 0;
        const duration = 1000; // 1 second
        const startTime = performance.now();

        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Easing function for smooth animation
            const easeOutCubic = 1 - Math.pow(1 - progress, 3);
            const currentValue = Math.round(startValue + (targetValue - startValue) * easeOutCubic);
            
            element.textContent = currentValue;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }

    applyFilters() {
        this.filteredVerifications = this.verifications.filter(verification => {
            // Search filter
            const searchMatch = this.searchTerm === '' || 
                verification.userName.toLowerCase().includes(this.searchTerm.toLowerCase()) ||
                verification.tokenId.toString().includes(this.searchTerm) ||
                verification.userAddress.toLowerCase().includes(this.searchTerm.toLowerCase());

            // Status filter
            const statusMatch = this.statusFilter === '' || verification.status === this.statusFilter;

            // Date filter
            let dateMatch = true;
            if (this.dateFilter !== '') {
                const verificationDate = new Date(verification.timestamp);
                const now = new Date();
                
                switch (this.dateFilter) {
                    case 'today':
                        dateMatch = verificationDate.toDateString() === now.toDateString();
                        break;
                    case 'week': {
                        const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                        dateMatch = verificationDate >= weekAgo;
                        break;
                    }
                    case 'month': {
                        const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
                        dateMatch = verificationDate >= monthAgo;
                        break;
                    }
                }
            }

            return searchMatch && statusMatch && dateMatch;
        });

        this.currentPage = 1;
        this.renderTable();
        this.updatePagination();
    }

    clearFilters() {
        document.getElementById('search-input').value = '';
        document.getElementById('status-filter').value = '';
        document.getElementById('date-filter').value = '';
        
        this.searchTerm = '';
        this.statusFilter = '';
        this.dateFilter = '';
        
        this.filteredVerifications = [...this.verifications];
        this.currentPage = 1;
        this.renderTable();
        this.updatePagination();
    }

    renderTable() {
        const tbody = document.getElementById('verification-tbody');
        const emptyState = document.getElementById('empty-state');
        const recordsSection = document.querySelector('.records-section');

        if (this.filteredVerifications.length === 0) {
            recordsSection.style.display = 'none';
            emptyState.style.display = 'block';
            return;
        }

        recordsSection.style.display = 'block';
        emptyState.style.display = 'none';

        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = startIndex + this.itemsPerPage;
        const pageData = this.filteredVerifications.slice(startIndex, endIndex);

        tbody.innerHTML = pageData.map(verification => this.createTableRow(verification)).join('');

        // Bind row events
        this.bindTableRowEvents();
    }

    createTableRow(verification) {
        const statusClass = `status-${verification.status}`;
        const formattedDate = new Date(verification.timestamp).toLocaleDateString();
        const shortAddress = this.formatAddress(verification.userAddress);
        const shortTxHash = this.formatTxHash(verification.transactionHash);

        return `
            <tr data-token-id="${verification.tokenId}">
                <td><input type="checkbox" class="row-checkbox"></td>
                <td><strong>#${verification.tokenId}</strong></td>
                <td>${verification.userName}</td>
                <td>
                    <span class="address-display" title="${verification.userAddress}" onclick="this.copyToClipboard('${verification.userAddress}')">
                        ${shortAddress}
                    </span>
                </td>
                <td><span class="status-badge ${statusClass}">${verification.status}</span></td>
                <td>${formattedDate}</td>
                <td>
                    <span class="address-display" title="${verification.transactionHash}" onclick="this.copyToClipboard('${verification.transactionHash}')">
                        ${shortTxHash}
                    </span>
                </td>
                <td>
                    <div class="action-buttons">
                        <button class="action-btn view" onclick="dashboard.viewDetails(${verification.tokenId})">View</button>
                        <button class="action-btn download" onclick="dashboard.downloadCertificate(${verification.tokenId})">Download</button>
                        <button class="action-btn verify" onclick="dashboard.verifyToken(${verification.tokenId})">Verify</button>
                    </div>
                </td>
            </tr>
        `;
    }

    bindTableRowEvents() {
        // Add click handlers for address copying
        document.querySelectorAll('.address-display').forEach(element => {
            element.addEventListener('click', (e) => {
                const address = e.target.getAttribute('title');
                this.copyToClipboard(address);
            });
        });
    }

    formatAddress(address) {
        return `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;
    }

    formatTxHash(hash) {
        return `${hash.substring(0, 8)}...${hash.substring(hash.length - 6)}`;
    }

    updatePagination() {
        const totalItems = this.filteredVerifications.length;
        const totalPages = Math.ceil(totalItems / this.itemsPerPage);
        const startItem = (this.currentPage - 1) * this.itemsPerPage + 1;
        const endItem = Math.min(this.currentPage * this.itemsPerPage, totalItems);

        // Update info
        document.getElementById('showing-start').textContent = totalItems > 0 ? startItem : 0;
        document.getElementById('showing-end').textContent = endItem;
        document.getElementById('total-records').textContent = totalItems;

        // Update buttons
        document.getElementById('prev-page').disabled = this.currentPage <= 1;
        document.getElementById('next-page').disabled = this.currentPage >= totalPages;

        // Update page numbers
        this.renderPageNumbers(totalPages);
    }

    renderPageNumbers(totalPages) {
        const pageNumbersContainer = document.getElementById('page-numbers');
        const maxVisiblePages = 5;
        let startPage = Math.max(1, this.currentPage - Math.floor(maxVisiblePages / 2));
        let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

        if (endPage - startPage + 1 < maxVisiblePages) {
            startPage = Math.max(1, endPage - maxVisiblePages + 1);
        }

        let html = '';
        
        if (startPage > 1) {
            html += '<a href="#" class="page-number" data-page="1">1</a>';
            if (startPage > 2) {
                html += '<span class="page-ellipsis">...</span>';
            }
        }

        for (let i = startPage; i <= endPage; i++) {
            const activeClass = i === this.currentPage ? 'active' : '';
            html += `<a href="#" class="page-number ${activeClass}" data-page="${i}">${i}</a>`;
        }

        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                html += '<span class="page-ellipsis">...</span>';
            }
            html += `<a href="#" class="page-number" data-page="${totalPages}">${totalPages}</a>`;
        }

        pageNumbersContainer.innerHTML = html;

        // Bind page number events
        document.querySelectorAll('.page-number').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = parseInt(e.target.getAttribute('data-page'));
                this.currentPage = page;
                this.renderTable();
                this.updatePagination();
            });
        });
    }

    viewDetails(tokenId) {
        const verification = this.verifications.find(v => v.tokenId === tokenId);
        if (!verification) return;

        const modalBody = document.getElementById('detail-modal-body');
        modalBody.innerHTML = this.createDetailView(verification);
        
        document.getElementById('detail-modal').style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }

    createDetailView(verification) {
        return `
            <div class="detail-grid">
                <div class="detail-label">Token ID:</div>
                <div class="detail-value">#${verification.tokenId}</div>
                
                <div class="detail-label">User Name:</div>
                <div class="detail-value">${verification.userName}</div>
                
                <div class="detail-label">Email:</div>
                <div class="detail-value">${verification.email || 'N/A'}</div>
                
                <div class="detail-label">Phone:</div>
                <div class="detail-value">${verification.phone || 'N/A'}</div>
                
                <div class="detail-label">Wallet Address:</div>
                <div class="detail-value">${verification.userAddress}</div>
                
                <div class="detail-label">Status:</div>
                <div class="detail-value">
                    <span class="status-badge status-${verification.status}">${verification.status}</span>
                </div>
                
                <div class="detail-label">Verification Date:</div>
                <div class="detail-value">${new Date(verification.timestamp).toLocaleString()}</div>
                
                <div class="detail-label">Verification Score:</div>
                <div class="detail-value">${verification.verificationScore || 'N/A'}%</div>
            </div>
            
            <div class="detail-section">
                <h4>Blockchain Information</h4>
                <div class="detail-grid">
                    <div class="detail-label">Verification Hash:</div>
                    <div class="detail-value">${verification.verificationHash}</div>
                    
                    <div class="detail-label">Transaction Hash:</div>
                    <div class="detail-value">${verification.transactionHash}</div>
                    
                    <div class="detail-label">Block Number:</div>
                    <div class="detail-value">${verification.blockNumber}</div>
                </div>
            </div>
            
            <div class="detail-section">
                <h4>Verification Details</h4>
                <div class="detail-grid">
                    <div class="detail-label">Documents Verified:</div>
                    <div class="detail-value">${(verification.documentTypes || []).join(', ')}</div>
                    
                    <div class="detail-label">Biometric Verified:</div>
                    <div class="detail-value">${verification.biometricVerified ? 'Yes' : 'No'}</div>
                </div>
            </div>
        `;
    }

    closeModal() {
        document.getElementById('detail-modal').style.display = 'none';
        document.body.style.overflow = 'auto';
    }

    async downloadCertificate(tokenId) {
        const verification = this.verifications.find(v => v.tokenId === tokenId);
        if (!verification) return;

        this.showLoading('Generating certificate...');
        
        try {
            // Simulate certificate generation delay
            await new Promise(resolve => setTimeout(resolve, 1500));
            
            const certificate = {
                title: 'eKYC Blockchain Verification Certificate',
                tokenId: verification.tokenId,
                userAddress: verification.userAddress,
                userName: verification.userName,
                verificationHash: verification.verificationHash,
                transactionHash: verification.transactionHash,
                blockNumber: verification.blockNumber,
                timestamp: verification.timestamp,
                contractAddress: this.blockchain.contract.contractAddress,
                issuedBy: 'eKYC Blockchain System',
                status: verification.status.toUpperCase(),
                generatedAt: new Date().toISOString()
            };

            const dataStr = JSON.stringify(certificate, null, 2);
            const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
            
            const exportFileDefaultName = `ekyc-certificate-${tokenId}.json`;
            
            const linkElement = document.createElement('a');
            linkElement.setAttribute('href', dataUri);
            linkElement.setAttribute('download', exportFileDefaultName);
            linkElement.click();
            
            this.showMessage('Certificate downloaded successfully!', 'success');
        } catch (error) {
            this.showMessage('Error generating certificate: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async verifyToken(tokenId) {
        this.showLoading('Verifying token on blockchain...');
        
        try {
            // Simulate blockchain verification delay
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            const result = await this.blockchain.verifyToken(tokenId);
            
            if (result.success) {
                this.showMessage(`Token #${tokenId} verified successfully on blockchain!`, 'success');
            } else {
                this.showMessage(`Token #${tokenId} verification failed.`, 'error');
            }
        } catch (error) {
            this.showMessage('Error verifying token: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async refreshData() {
        this.showLoading('Refreshing data...');
        
        try {
            await this.loadVerificationData();
            this.updateStats();
            this.applyFilters();
            this.showMessage('Data refreshed successfully!', 'success');
        } catch (error) {
            this.showMessage('Error refreshing data: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    exportData() {
        const exportData = {
            exported_at: new Date().toISOString(),
            total_records: this.verifications.length,
            contract_address: this.blockchain.contract.contractAddress,
            verifications: this.verifications
        };

        const dataStr = JSON.stringify(exportData, null, 2);
        const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
        
        const exportFileDefaultName = `ekyc-verifications-${new Date().toISOString().split('T')[0]}.json`;
        
        const linkElement = document.createElement('a');
        linkElement.setAttribute('href', dataUri);
        linkElement.setAttribute('download', exportFileDefaultName);
        linkElement.click();
        
        this.showMessage('Data exported successfully!', 'success');
    }

    selectAllRows(checked) {
        document.querySelectorAll('.row-checkbox').forEach(checkbox => {
            checkbox.checked = checked;
        });
    }

    copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            this.showMessage('Copied to clipboard!', 'success');
        }).catch(err => {
            console.error('Copy failed:', err);
            this.showMessage('Failed to copy to clipboard', 'error');
        });
    }

    showLoading(text = 'Loading...') {
        const overlay = document.getElementById('loading-overlay');
        const loadingText = document.getElementById('loading-text');
        loadingText.textContent = text;
        overlay.style.display = 'flex';
    }

    hideLoading() {
        document.getElementById('loading-overlay').style.display = 'none';
    }

    showMessage(message, type = 'info') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message message-${type}`;
        messageDiv.textContent = message;
        
        messageDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 600;
            z-index: 10000;
            animation: slideInUp 0.3s ease;
        `;
        
        if (type === 'error') {
            messageDiv.style.backgroundColor = '#ff4757';
        } else if (type === 'success') {
            messageDiv.style.backgroundColor = '#28a745';
        } else {
            messageDiv.style.backgroundColor = '#17a2b8';
        }
        
        document.body.appendChild(messageDiv);
        
        setTimeout(() => {
            messageDiv.remove();
        }, 3000);
    }

    showError(message) {
        this.showMessage(message, 'error');
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new eKYCDashboard();
});

// Make dashboard available globally
if (typeof window !== 'undefined') {
    window.eKYCDashboard = eKYCDashboard;
}
