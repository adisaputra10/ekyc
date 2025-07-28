// Main application logic for eKYC Blockchain Verification
class eKYCApplication {
    constructor() {
        this.currentStep = 1;
        this.maxSteps = 4;
        this.formData = {};
        this.uploadedFiles = {};
        this.biometricData = null;
        this.blockchain = new BlockchainUtils();
        this.verificationToken = null;
        
        this.initializeApp();
    }

    initializeApp() {
        this.bindEvents();
        this.initializeCamera();
        this.initializeFileUploads();
        this.updateStepProgress();
    }

    bindEvents() {
        // Step navigation
        document.querySelectorAll('.next-step').forEach(btn => {
            btn.addEventListener('click', () => this.nextStep());
        });

        document.querySelectorAll('.prev-step').forEach(btn => {
            btn.addEventListener('click', () => this.previousStep());
        });

        // Form validation
        document.getElementById('personal-info-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.validatePersonalInfo();
        });

        // Blockchain actions
        document.getElementById('connect-wallet').addEventListener('click', () => this.connectWallet());
        document.getElementById('deploy-contract').addEventListener('click', () => this.deployContract());
        document.getElementById('mint-token').addEventListener('click', () => this.mintVerificationToken());
        document.getElementById('download-certificate').addEventListener('click', () => this.downloadCertificate());
        document.getElementById('complete-verification').addEventListener('click', () => this.completeVerification());

        // Biometric controls
        document.getElementById('start-camera').addEventListener('click', () => this.startCamera());
        document.getElementById('capture-photo').addEventListener('click', () => this.capturePhoto());
        document.getElementById('retake-photo').addEventListener('click', () => this.retakePhoto());
    }

    initializeFileUploads() {
        this.setupFileUpload('id-card-upload', 'idCard', 'id-preview');
        this.setupFileUpload('address-proof-upload', 'addressProof', 'address-preview');
    }

    setupFileUpload(uploadAreaId, fileType, previewId) {
        const uploadArea = document.getElementById(uploadAreaId);
        const fileInput = uploadArea.querySelector('input[type="file"]');
        const previewArea = document.getElementById(previewId);
        const previewImg = previewArea.querySelector('img');
        const removeBtn = previewArea.querySelector('.remove-file');

        // Click to browse
        uploadArea.addEventListener('click', () => fileInput.click());

        // File selection
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                this.handleFileUpload(file, fileType, previewArea, previewImg);
            }
        });

        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const file = e.dataTransfer.files[0];
            if (file) {
                this.handleFileUpload(file, fileType, previewArea, previewImg);
            }
        });

        // Remove file
        removeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.removeFile(fileType, previewArea, fileInput);
        });
    }

    handleFileUpload(file, fileType, previewArea, previewImg) {
        // Validate file type
        const allowedTypes = ['image/jpeg', 'image/png', 'image/jpg'];
        if (fileType === 'addressProof') {
            allowedTypes.push('application/pdf');
        }

        if (!allowedTypes.includes(file.type)) {
            this.showMessage('Please upload a valid image or PDF file.', 'error');
            return;
        }

        // Validate file size (max 5MB)
        if (file.size > 5 * 1024 * 1024) {
            this.showMessage('File size should not exceed 5MB.', 'error');
            return;
        }

        // Store file
        this.uploadedFiles[fileType] = file;

        // Show preview
        if (file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = (e) => {
                previewImg.src = e.target.result;
                previewArea.style.display = 'block';
                previewArea.parentElement.querySelector('.upload-content').style.display = 'none';
            };
            reader.readAsDataURL(file);
        } else {
            // For PDF files, show a placeholder
            previewImg.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjE1MCIgdmlld0JveD0iMCAwIDIwMCAxNTAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iMTUwIiBmaWxsPSIjRjNGNEY2Ii8+Cjx0ZXh0IHg9IjEwMCIgeT0iNzUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNiIgZmlsbD0iIzY2NzNEMiIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9IjAuM2VtIj5QREYgRmlsZTwvdGV4dD4KPHN2Zz4K';
            previewArea.style.display = 'block';
            previewArea.parentElement.querySelector('.upload-content').style.display = 'none';
        }

        this.checkStepCompletion();
    }

    removeFile(fileType, previewArea, fileInput) {
        delete this.uploadedFiles[fileType];
        previewArea.style.display = 'none';
        previewArea.parentElement.querySelector('.upload-content').style.display = 'block';
        fileInput.value = '';
        this.checkStepCompletion();
    }

    async initializeCamera() {
        try {
            // Check if camera is available
            const devices = await navigator.mediaDevices.enumerateDevices();
            const hasCamera = devices.some(device => device.kind === 'videoinput');
            
            if (!hasCamera) {
                document.getElementById('biometric-status').innerHTML = 
                    '<p style="color: #ff4757;">No camera detected. Please connect a camera to proceed.</p>';
            }
        } catch (error) {
            console.log('Camera check failed:', error);
        }
    }

    async startCamera() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ 
                video: { 
                    width: 400, 
                    height: 300,
                    facingMode: 'user'
                } 
            });
            
            const video = document.getElementById('camera');
            video.srcObject = stream;
            
            document.getElementById('start-camera').style.display = 'none';
            document.getElementById('capture-photo').style.display = 'inline-block';
            
            document.getElementById('biometric-status').innerHTML = 
                '<p style="color: #28a745;">Camera started. Position your face within the frame and click capture.</p>';
                
        } catch (error) {
            console.error('Camera access failed:', error);
            document.getElementById('biometric-status').innerHTML = 
                '<p style="color: #ff4757;">Camera access denied. Please allow camera permissions and try again.</p>';
        }
    }

    capturePhoto() {
        const video = document.getElementById('camera');
        const canvas = document.getElementById('photo-canvas');
        const context = canvas.getContext('2d');
        
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        
        context.drawImage(video, 0, 0);
        
        // Get image data for biometric processing
        this.biometricData = context.getImageData(0, 0, canvas.width, canvas.height).data;
        
        // Show captured photo
        const capturedImg = document.getElementById('captured-img');
        capturedImg.src = canvas.toDataURL('image/jpeg');
        
        document.getElementById('captured-photo').style.display = 'block';
        document.querySelector('.camera-container').style.display = 'none';
        document.getElementById('capture-photo').style.display = 'none';
        
        // Stop camera stream
        const stream = video.srcObject;
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
        
        document.getElementById('biometric-status').innerHTML = 
            '<p style="color: #28a745;">Photo captured successfully! You can proceed to blockchain verification.</p>';
            
        document.getElementById('proceed-to-blockchain').disabled = false;
    }

    retakePhoto() {
        document.getElementById('captured-photo').style.display = 'none';
        document.querySelector('.camera-container').style.display = 'block';
        document.getElementById('start-camera').style.display = 'inline-block';
        document.getElementById('proceed-to-blockchain').disabled = true;
        this.biometricData = null;
        
        document.getElementById('biometric-status').innerHTML = 
            '<p>Please position your face within the frame and capture a clear photo</p>';
    }

    validatePersonalInfo() {
        const form = document.getElementById('personal-info-form');
        const formData = new FormData(form);
        
        // Basic validation
        const requiredFields = ['fullName', 'dateOfBirth', 'nationalId', 'address', 'phone', 'email'];
        const missingFields = requiredFields.filter(field => !formData.get(field));
        
        if (missingFields.length > 0) {
            this.showMessage('Please fill in all required fields.', 'error');
            return false;
        }
        
        // Store form data
        this.formData = Object.fromEntries(formData);
        return true;
    }

    nextStep() {
        if (this.currentStep === 1) {
            if (!this.validatePersonalInfo()) return;
        }
        
        if (this.currentStep === 2) {
            if (!this.uploadedFiles.idCard || !this.uploadedFiles.addressProof) {
                this.showMessage('Please upload all required documents.', 'error');
                return;
            }
        }
        
        if (this.currentStep === 3) {
            if (!this.biometricData) {
                this.showMessage('Please capture your photo for biometric verification.', 'error');
                return;
            }
        }
        
        if (this.currentStep < this.maxSteps) {
            this.currentStep++;
            this.updateStepDisplay();
            this.updateStepProgress();
        }
    }

    previousStep() {
        if (this.currentStep > 1) {
            this.currentStep--;
            this.updateStepDisplay();
            this.updateStepProgress();
        }
    }

    updateStepDisplay() {
        // Hide all steps
        document.querySelectorAll('.form-step').forEach(step => {
            step.classList.remove('active');
        });
        
        // Show current step
        document.getElementById(`step-${this.currentStep}`).classList.add('active');
    }

    updateStepProgress() {
        document.querySelectorAll('.step').forEach((step, index) => {
            const stepNumber = index + 1;
            
            if (stepNumber < this.currentStep) {
                step.classList.add('completed');
                step.classList.remove('active');
            } else if (stepNumber === this.currentStep) {
                step.classList.add('active');
                step.classList.remove('completed');
            } else {
                step.classList.remove('active', 'completed');
            }
        });
    }

    checkStepCompletion() {
        // Implementation for checking if current step is complete
        // This can be used to enable/disable next button
    }

    showMessage(message, type = 'info') {
        // Create a simple message display
        const messageDiv = document.createElement('div');
        messageDiv.className = `message message-${type}`;
        messageDiv.textContent = message;
        
        // Style the message
        messageDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 600;
            z-index: 10000;
            animation: slideIn 0.3s ease;
        `;
        
        if (type === 'error') {
            messageDiv.style.backgroundColor = '#ff4757';
        } else if (type === 'success') {
            messageDiv.style.backgroundColor = '#28a745';
        } else {
            messageDiv.style.backgroundColor = '#17a2b8';
        }
        
        document.body.appendChild(messageDiv);
        
        // Remove message after 3 seconds
        setTimeout(() => {
            messageDiv.remove();
        }, 3000);
    }

    showLoading(text = 'Processing...') {
        const overlay = document.getElementById('loading-overlay');
        const loadingText = document.getElementById('loading-text');
        loadingText.textContent = text;
        overlay.style.display = 'flex';
    }

    hideLoading() {
        document.getElementById('loading-overlay').style.display = 'none';
    }

    async connectWallet() {
        this.showLoading('Connecting to wallet...');
        
        try {
            const result = await this.blockchain.connectWallet();
            
            if (result.success) {
                document.getElementById('wallet-status').textContent = 'Connected';
                document.getElementById('network-status').textContent = result.network;
                document.getElementById('deploy-contract').disabled = false;
                
                this.showMessage('Wallet connected successfully!', 'success');
            } else {
                this.showMessage('Failed to connect wallet.', 'error');
            }
        } catch (error) {
            this.showMessage('Error connecting wallet: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async deployContract() {
        this.showLoading('Deploying smart contract...');
        
        try {
            const result = await this.blockchain.deployContract();
            
            if (result.success) {
                document.getElementById('contract-status').textContent = 'Deployed';
                document.getElementById('mint-token').disabled = false;
                
                this.showMessage('Smart contract deployed successfully!', 'success');
            } else {
                this.showMessage('Failed to deploy contract.', 'error');
            }
        } catch (error) {
            this.showMessage('Error deploying contract: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async mintVerificationToken() {
        this.showLoading('Preparing verification data and minting token...');
        
        try {
            // Prepare verification data
            const verificationData = await this.blockchain.prepareVerificationData(
                this.formData,
                this.uploadedFiles,
                this.biometricData
            );
            
            // Mint token
            const result = await this.blockchain.mintVerificationToken(verificationData);
            
            if (result.success) {
                this.verificationToken = result;
                
                // Show transaction details
                document.getElementById('transaction-details').style.display = 'block';
                document.getElementById('tx-hash').textContent = this.blockchain.formatTxHash(result.transactionHash);
                document.getElementById('token-id').textContent = result.tokenId;
                document.getElementById('final-status').textContent = 'Verified';
                
                // Show verification certificate
                setTimeout(() => {
                    this.showVerificationCertificate();
                }, 2000);
                
                this.showMessage('Verification token minted successfully!', 'success');
            } else {
                this.showMessage('Failed to mint verification token.', 'error');
            }
        } catch (error) {
            this.showMessage('Error minting token: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    showVerificationCertificate() {
        const certificate = document.getElementById('verification-certificate');
        const account = this.blockchain.getCurrentAccount();
        
        document.getElementById('cert-token-id').textContent = this.verificationToken.tokenId;
        document.getElementById('cert-address').textContent = this.blockchain.formatAddress(account);
        document.getElementById('cert-timestamp').textContent = new Date().toLocaleString();
        
        certificate.style.display = 'block';
        document.getElementById('complete-verification').style.display = 'inline-block';
    }

    downloadCertificate() {
        if (!this.verificationToken) {
            this.showMessage('No verification certificate available.', 'error');
            return;
        }
        
        const certificate = this.blockchain.generateCertificate(this.formData, this.verificationToken);
        this.blockchain.downloadCertificate(certificate);
        
        this.showMessage('Certificate downloaded successfully!', 'success');
    }

    completeVerification() {
        this.showMessage('eKYC verification completed successfully! Your identity is now verified on the blockchain.', 'success');
        
        // Optionally redirect or refresh
        setTimeout(() => {
            // window.location.reload();
            console.log('Verification complete!');
        }, 2000);
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new eKYCApplication();
});
