// Demo data for testing eKYC application
const demoData = {
    // Sample personal information
    personalInfo: {
        fullName: "John Doe",
        dateOfBirth: "1990-05-15",
        nationalId: "1234567890123456",
        address: "Jl. Sudirman No. 123, Jakarta Pusat, DKI Jakarta 10220",
        phone: "+62812345678",
        email: "john.doe@example.com"
    },

    // Sample verification results
    sampleVerifications: [
        {
            tokenId: 1,
            userAddress: "0x742d35Cc6435C9dBE2b8d935A4BF2b7b2C1F3a5D",
            verificationHash: "0x1a2b3c4d5e6f7890abcdef1234567890abcdef1234567890abcdef1234567890",
            timestamp: "2024-01-15T10:30:00Z",
            status: "verified",
            blockNumber: 1234567,
            transactionHash: "0x9876543210abcdef9876543210abcdef9876543210abcdef9876543210abcdef"
        },
        {
            tokenId: 2,
            userAddress: "0x8F4b2C1a9D3e5F7g8H9i0J1k2L3m4N5o6P7q8R9s",
            verificationHash: "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            timestamp: "2024-01-16T14:15:30Z",
            status: "verified",
            blockNumber: 1234890,
            transactionHash: "0xfedcba0987654321fedcba0987654321fedcba0987654321fedcba0987654321"
        }
    ],

    // Sample smart contract info
    contractInfo: {
        address: "0xA1B2C3D4E5F6789012345678901234567890ABCD",
        owner: "0x742d35Cc6435C9dBE2b8d935A4BF2b7b2C1F3a5D",
        totalVerifications: 150,
        totalTokens: 150,
        deploymentBlock: 1200000,
        deploymentTx: "0x1111222233334444555566667777888899990000aaaabbbbccccddddeeeeffff"
    },

    // Sample network information
    networkInfo: {
        chainId: 1337,
        networkName: "Local Development Network",
        blockNumber: 1234567,
        gasPrice: "20 Gwei",
        avgBlockTime: "2 seconds"
    },

    // Sample transaction costs
    transactionCosts: {
        deployContract: {
            gasLimit: 2500000,
            gasPrice: 20,
            costInEth: "0.050000"
        },
        mintToken: {
            gasLimit: 250000,
            gasPrice: 20,
            costInEth: "0.005000"
        },
        verifyToken: {
            gasLimit: 75000,
            gasPrice: 20,
            costInEth: "0.001500"
        }
    },

    // Sample verification certificate
    sampleCertificate: {
        title: "eKYC Blockchain Verification Certificate",
        tokenId: 1,
        userAddress: "0x742d35Cc6435C9dBE2b8d935A4BF2b7b2C1F3a5D",
        userName: "John Doe",
        verificationHash: "0x1a2b3c4d5e6f7890abcdef1234567890abcdef1234567890abcdef1234567890",
        transactionHash: "0x9876543210abcdef9876543210abcdef9876543210abcdef9876543210abcdef",
        blockNumber: 1234567,
        timestamp: "2024-01-15T10:30:00Z",
        contractAddress: "0xA1B2C3D4E5F6789012345678901234567890ABCD",
        issuedBy: "eKYC Blockchain System",
        status: "VERIFIED",
        metadata: {
            verificationLevel: "Full KYC",
            documentsVerified: ["National ID", "Proof of Address"],
            biometricVerified: true,
            verificationScore: 98.5
        }
    }
};

// Function to populate form with demo data
function populateDemoData() {
    const personalInfo = demoData.personalInfo;
    
    // Fill personal information form
    Object.keys(personalInfo).forEach(key => {
        const element = document.getElementById(key);
        if (element) {
            element.value = personalInfo[key];
        }
    });
    
    console.log('Demo data populated');
}

// Function to simulate successful verification
function simulateSuccessfulVerification() {
    const app = window.eKYCApp;
    if (app) {
        // Set demo form data
        app.formData = demoData.personalInfo;
        
        // Simulate files uploaded
        app.uploadedFiles = {
            idCard: new File(['demo'], 'demo-id.jpg', { type: 'image/jpeg' }),
            addressProof: new File(['demo'], 'demo-address.pdf', { type: 'application/pdf' })
        };
        
        // Simulate biometric data
        app.biometricData = new Uint8Array(100).fill(128);
        
        console.log('Simulated successful verification setup');
    }
}

// Function to show sample verification result
function showSampleVerification() {
    const sample = demoData.sampleVerifications[0];
    
    console.log('Sample Verification:', {
        'Token ID': sample.tokenId,
        'User Address': sample.userAddress,
        'Status': sample.status,
        'Block Number': sample.blockNumber,
        'Transaction Hash': sample.transactionHash,
        'Timestamp': new Date(sample.timestamp).toLocaleString()
    });
    
    return sample;
}

// Function to generate random demo wallet address
function generateDemoWalletAddress() {
    const chars = '0123456789abcdef';
    let address = '0x';
    for (let i = 0; i < 40; i++) {
        address += chars[Math.floor(Math.random() * chars.length)];
    }
    return address;
}

// Function to generate random transaction hash
function generateDemoTxHash() {
    const chars = '0123456789abcdef';
    let hash = '0x';
    for (let i = 0; i < 64; i++) {
        hash += chars[Math.floor(Math.random() * chars.length)];
    }
    return hash;
}

// Demo helper functions
const demoHelpers = {
    populateForm: populateDemoData,
    simulateVerification: simulateSuccessfulVerification,
    showSample: showSampleVerification,
    generateAddress: generateDemoWalletAddress,
    generateTxHash: generateDemoTxHash,
    
    // Quick access to demo data
    get personalInfo() { return demoData.personalInfo; },
    get verifications() { return demoData.sampleVerifications; },
    get contractInfo() { return demoData.contractInfo; },
    get certificate() { return demoData.sampleCertificate; }
};

// Make demo data available globally for testing
if (typeof window !== 'undefined') {
    window.demoData = demoData;
    window.demoHelpers = demoHelpers;
    
    // Add demo button to page when DOM is ready
    document.addEventListener('DOMContentLoaded', () => {
        // Create demo button
        const demoButton = document.createElement('button');
        demoButton.textContent = '🎭 Fill Demo Data';
        demoButton.style.cssText = `
            position: fixed;
            top: 20px;
            left: 20px;
            z-index: 1000;
            padding: 10px 15px;
            background: #ff6b35;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        `;
        demoButton.onclick = populateDemoData;
        
        document.body.appendChild(demoButton);
        
        console.log('Demo helpers loaded. Use demoHelpers in console for testing.');
        console.log('Available commands:');
        console.log('- demoHelpers.populateForm()');
        console.log('- demoHelpers.simulateVerification()');
        console.log('- demoHelpers.showSample()');
    });
}
