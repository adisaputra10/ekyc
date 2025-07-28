# eKYC Smart Contract API Documentation

## Overview
Smart Contract untuk sistem verifikasi identitas (eKYC) yang menyimpan hash verifikasi dan menerbitkan token sebagai bukti verifikasi yang valid.

## Contract Methods

### 1. deploy(ownerAddress)
Mengdeploy smart contract baru.

**Parameters:**
- `ownerAddress` (string): Alamat wallet yang akan menjadi owner contract

**Returns:**
```javascript
{
  success: true,
  contractAddress: "0x...",
  transactionHash: "0x...",
  blockNumber: 1234567
}
```

**Example:**
```javascript
const contract = new eKYCSmartContract();
const result = await contract.deploy("0x742d35Cc6435C9dBE2b8d935A4BF2b7b2C1F3a5D");
```

### 2. mintVerificationToken(userAddress, verificationData)
Menerbitkan token verifikasi untuk user yang telah terverifikasi.

**Parameters:**
- `userAddress` (string): Alamat wallet user
- `verificationData` (object): Data verifikasi yang akan di-hash

**Verification Data Structure:**
```javascript
{
  fullName: "John Doe",
  nationalId: "1234567890123456",
  dateOfBirth: "1990-05-15",
  email: "john@example.com",
  phone: "+62812345678",
  address: "Jl. Sudirman No. 123",
  documentHashes: {
    idCard: "0x...",
    addressProof: "0x..."
  },
  biometricHash: "0x...",
  timestamp: "2024-01-15T10:30:00Z"
}
```

**Returns:**
```javascript
{
  success: true,
  tokenId: 1,
  transactionHash: "0x...",
  verification: {
    tokenId: 1,
    userAddress: "0x...",
    verificationHash: "0x...",
    timestamp: "2024-01-15T10:30:00Z",
    status: "verified",
    blockNumber: 1234567,
    transactionHash: "0x..."
  }
}
```

### 3. verifyToken(tokenId)
Memverifikasi validitas token berdasarkan token ID.

**Parameters:**
- `tokenId` (number): ID token yang akan diverifikasi

**Returns:**
```javascript
{
  success: true,
  verification: {
    tokenId: 1,
    userAddress: "0x...",
    verificationHash: "0x...",
    timestamp: "2024-01-15T10:30:00Z",
    status: "verified",
    blockNumber: 1234567,
    transactionHash: "0x..."
  }
}
```

### 4. getVerificationsByAddress(userAddress)
Mendapatkan semua verifikasi untuk alamat tertentu.

**Parameters:**
- `userAddress` (string): Alamat wallet user

**Returns:**
```javascript
[
  {
    tokenId: 1,
    userAddress: "0x...",
    verificationHash: "0x...",
    timestamp: "2024-01-15T10:30:00Z",
    status: "verified",
    blockNumber: 1234567,
    transactionHash: "0x..."
  }
]
```

### 5. isUserVerified(userAddress)
Mengecek apakah user sudah terverifikasi.

**Parameters:**
- `userAddress` (string): Alamat wallet user

**Returns:**
- `boolean`: true jika user sudah terverifikasi

### 6. getContractInfo()
Mendapatkan informasi contract.

**Returns:**
```javascript
{
  address: "0x...",
  owner: "0x...",
  totalVerifications: 150,
  totalTokens: 150
}
```

## Blockchain Utils API

### 1. connectWallet()
Mengkoneksikan aplikasi dengan wallet (MetaMask simulation).

**Returns:**
```javascript
{
  success: true,
  accounts: ["0x..."],
  chainId: 1337,
  network: "Local Development Network"
}
```

### 2. deployContract()
Deploy smart contract menggunakan connected wallet.

**Returns:**
```javascript
{
  success: true,
  contractAddress: "0x...",
  transactionHash: "0x...",
  blockNumber: 1234567
}
```

### 3. prepareVerificationData(formData, files, biometricData)
Mempersiapkan data verifikasi dengan melakukan hashing.

**Parameters:**
- `formData` (object): Data form personal information
- `files` (object): Uploaded files (idCard, addressProof)
- `biometricData` (Uint8Array): Biometric image data

**Returns:**
```javascript
{
  fullName: "John Doe",
  nationalId: "1234567890123456",
  dateOfBirth: "1990-05-15",
  email: "john@example.com",
  phone: "+62812345678",
  address: "Jl. Sudirman No. 123",
  documentHashes: {
    idCard: "0x...",
    addressProof: "0x..."
  },
  biometricHash: "0x...",
  timestamp: "2024-01-15T10:30:00Z"
}
```

### 4. mintVerificationToken(verificationData)
Mint token verifikasi dengan data yang sudah dipersiapkan.

### 5. hashFile(file)
Membuat hash dari file yang diupload.

**Parameters:**
- `file` (File): File object dari input

**Returns:**
- `string`: Hash dalam format hex (0x...)

### 6. hashBiometricData(imageData)
Membuat hash dari data biometrik.

**Parameters:**
- `imageData` (Uint8Array): Image data dari canvas

**Returns:**
- `string`: Hash dalam format hex (0x...)

### 7. generateCertificate(verificationData, tokenData)
Membuat sertifikat verifikasi.

**Returns:**
```javascript
{
  title: "eKYC Blockchain Verification Certificate",
  tokenId: 1,
  userAddress: "0x...",
  userName: "John Doe",
  verificationHash: "0x...",
  transactionHash: "0x...",
  blockNumber: 1234567,
  timestamp: "2024-01-15T10:30:00Z",
  contractAddress: "0x...",
  issuedBy: "eKYC Blockchain System",
  status: "VERIFIED"
}
```

## Error Handling

Semua metode async menggunakan Promise dan dapat meng-throw error:

```javascript
try {
  const result = await blockchain.connectWallet();
  if (result.success) {
    // Handle success
  }
} catch (error) {
  console.error('Error:', error.message);
}
```

## Events dan Callbacks

### Application Events
- `wallet-connected`: Ketika wallet berhasil terkoneksi
- `contract-deployed`: Ketika smart contract berhasil dideploy
- `token-minted`: Ketika verification token berhasil dimint
- `verification-complete`: Ketika proses verifikasi selesai

### Usage Example
```javascript
// Initialize blockchain utils
const blockchain = new BlockchainUtils();

// Connect wallet
const walletResult = await blockchain.connectWallet();

// Deploy contract
const deployResult = await blockchain.deployContract();

// Prepare verification data
const verificationData = await blockchain.prepareVerificationData(
  formData, files, biometricData
);

// Mint verification token
const tokenResult = await blockchain.mintVerificationToken(verificationData);

// Generate certificate
const certificate = blockchain.generateCertificate(verificationData, tokenResult);
```

## Security Considerations

### Hash Functions
- File hashing menggunakan sampling untuk performa
- Biometric hashing menggunakan feature extraction sederhana
- Production harus menggunakan algoritma kriptografi yang proper

### Data Privacy
- Hanya hash yang disimpan di blockchain
- Data asli tidak pernah meninggalkan browser
- Verifikasi dapat dilakukan tanpa mengungkap data pribadi

### Smart Contract Security
- Owner-only functions untuk administrative tasks
- Input validation untuk semua parameters
- Reentrancy protection untuk critical operations

## Testing

### Demo Mode
Gunakan `demo-data.js` untuk testing:

```javascript
// Populate form dengan demo data
demoHelpers.populateForm();

// Simulate successful verification
demoHelpers.simulateVerification();

// Show sample verification result
demoHelpers.showSample();
```

### Unit Testing
```javascript
// Test contract deployment
const contract = new eKYCSmartContract();
const deployResult = await contract.deploy("0x123...");
assert(deployResult.success === true);

// Test token minting
const tokenResult = await contract.mintVerificationToken("0x456...", data);
assert(tokenResult.tokenId > 0);
```
