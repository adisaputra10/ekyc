// Blockchain utilities for eKYC application
class BlockchainUtils {
    constructor() {
        this.web3 = null;
        this.accounts = [];
        this.chainId = null;
        this.contract = new window.eKYCSmartContract();
        this.isConnected = false;
    }

    // Simulate wallet connection (MetaMask)
    async connectWallet() {
        return new Promise((resolve, reject) => {
            // Simulate MetaMask connection delay
            setTimeout(() => {
                try {
                    // Simulate successful connection
                    this.accounts = [this.generateAddress()];
                    this.chainId = 1337; // Local development network
                    this.isConnected = true;
                    
                    resolve({
                        success: true,
                        accounts: this.accounts,
                        chainId: this.chainId,
                        network: this.getNetworkName(this.chainId)
                    });
                } catch (error) {
                    reject({
                        success: false,
                        error: error.message
                    });
                }
            }, 1500);
        });
    }

    // Generate mock wallet address
    generateAddress() {
        return '0x' + Array.from({length: 40}, () => Math.floor(Math.random() * 16).toString(16)).join('');
    }

    // Get network name by chain ID
    getNetworkName(chainId) {
        const networks = {
            1: 'Ethereum Mainnet',
            3: 'Ropsten Test Network',
            4: 'Rinkeby Test Network',
            5: 'Goerli Test Network',
            42: 'Kovan Test Network',
            1337: 'Local Development Network',
            31337: 'Hardhat Network'
        };
        return networks[chainId] || 'Unknown Network';
    }

    // Deploy the smart contract
    async deployContract() {
        if (!this.isConnected) {
            throw new Error('Wallet not connected');
        }

        const result = await this.contract.deploy(this.accounts[0]);
        return result;
    }

    // Create hash for uploaded files (simulation)
    async hashFile(file) {
        return new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = function(e) {
                // Simple hash simulation
                const arrayBuffer = e.target.result;
                const bytes = new Uint8Array(arrayBuffer);
                let hash = 0;
                
                for (let i = 0; i < Math.min(bytes.length, 10000); i++) { // Limit for performance
                    hash = ((hash << 5) - hash + bytes[i]) & 0xffffffff;
                }
                
                const hashHex = '0x' + Math.abs(hash).toString(16).padStart(64, '0');
                resolve(hashHex);
            };
            reader.readAsArrayBuffer(file);
        });
    }

    // Create hash for biometric data
    hashBiometricData(imageData) {
        // Simulate biometric hashing
        let hash = 0;
        for (let i = 0; i < imageData.length; i += 100) { // Sample data for performance
            hash = ((hash << 5) - hash + imageData[i]) & 0xffffffff;
        }
        return '0x' + Math.abs(hash).toString(16).padStart(64, '0');
    }

    // Prepare verification data for blockchain
    async prepareVerificationData(formData, files, biometricData) {
        const documentHashes = {};
        
        // Hash uploaded documents
        if (files.idCard) {
            documentHashes.idCard = await this.hashFile(files.idCard);
        }
        if (files.addressProof) {
            documentHashes.addressProof = await this.hashFile(files.addressProof);
        }

        // Hash biometric data
        const biometricHash = biometricData ? this.hashBiometricData(biometricData) : null;

        return {
            fullName: formData.fullName,
            nationalId: formData.nationalId,
            dateOfBirth: formData.dateOfBirth,
            email: formData.email,
            phone: formData.phone,
            address: formData.address,
            documentHashes,
            biometricHash,
            timestamp: new Date().toISOString()
        };
    }

    // Mint verification token
    async mintVerificationToken(verificationData) {
        if (!this.isConnected) {
            throw new Error('Wallet not connected');
        }

        const result = await this.contract.mintVerificationToken(this.accounts[0], verificationData);
        return result;
    }

    // Verify an existing token
    async verifyToken(tokenId) {
        const result = await this.contract.verifyToken(tokenId);
        return result;
    }

    // Get user's verification status
    isUserVerified() {
        if (!this.isConnected) return false;
        return this.contract.isUserVerified(this.accounts[0]);
    }

    // Get contract information
    getContractInfo() {
        return this.contract.getContractInfo();
    }

    // Format address for display
    formatAddress(address) {
        if (!address) return '';
        return `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;
    }

    // Format transaction hash for display
    formatTxHash(hash) {
        if (!hash) return '';
        return `${hash.substring(0, 10)}...${hash.substring(hash.length - 8)}`;
    }

    // Get current account
    getCurrentAccount() {
        return this.accounts.length > 0 ? this.accounts[0] : null;
    }

    // Get wallet connection status
    getConnectionStatus() {
        return {
            isConnected: this.isConnected,
            account: this.getCurrentAccount(),
            network: this.chainId ? this.getNetworkName(this.chainId) : null,
            contractAddress: this.contract.contractAddress
        };
    }

    // Simulate gas estimation
    estimateGas(operation) {
        const gasEstimates = {
            deploy: Math.floor(Math.random() * 1000000) + 2000000,
            mint: Math.floor(Math.random() * 500000) + 100000,
            verify: Math.floor(Math.random() * 100000) + 50000
        };
        return gasEstimates[operation] || 100000;
    }

    // Simulate gas price
    getGasPrice() {
        // Return gas price in Gwei
        return Math.floor(Math.random() * 50) + 10;
    }

    // Calculate transaction cost
    calculateTransactionCost(operation) {
        const gasLimit = this.estimateGas(operation);
        const gasPrice = this.getGasPrice();
        const costInGwei = gasLimit * gasPrice;
        const costInEth = costInGwei / 1e9;
        
        return {
            gasLimit,
            gasPrice,
            costInGwei,
            costInEth: costInEth.toFixed(6)
        };
    }

    // Generate verification certificate
    generateCertificate(verificationData, tokenData) {
        const certificate = {
            title: 'eKYC Blockchain Verification Certificate',
            tokenId: tokenData.tokenId,
            userAddress: this.getCurrentAccount(),
            userName: verificationData.fullName,
            verificationHash: tokenData.verification.verificationHash,
            transactionHash: tokenData.transactionHash,
            blockNumber: tokenData.verification.blockNumber,
            timestamp: tokenData.verification.timestamp,
            contractAddress: this.contract.contractAddress,
            issuedBy: 'eKYC Blockchain System',
            status: 'VERIFIED'
        };

        return certificate;
    }

    // Download certificate as JSON
    downloadCertificate(certificate) {
        const dataStr = JSON.stringify(certificate, null, 2);
        const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
        
        const exportFileDefaultName = `ekyc-certificate-${certificate.tokenId}.json`;
        
        const linkElement = document.createElement('a');
        linkElement.setAttribute('href', dataUri);
        linkElement.setAttribute('download', exportFileDefaultName);
        linkElement.click();
    }
}

// Export for use in other scripts
if (typeof window !== 'undefined') {
    window.BlockchainUtils = BlockchainUtils;
} else if (typeof module !== 'undefined') {
    module.exports = BlockchainUtils;
}
