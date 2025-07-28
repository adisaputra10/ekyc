# eKYC Blockchain Verification System

Sistem verifikasi identitas (eKYC) berbasis blockchain yang menggunakan smart contract untuk menyimpan dan memverifikasi data identitas pengguna secara terdesentralisasi.

## 🌟 Fitur Utama

- **4-Step Verification Process**: Proses verifikasi bertahap yang mudah diikuti
- **Document Upload**: Upload KTP dan bukti alamat dengan preview
- **Biometric Verification**: Capture foto wajah untuk verifikasi biometrik
- **Blockchain Integration**: Smart contract untuk menyimpan hash verifikasi
- **Token-based Verification**: NFT token sebagai bukti verifikasi yang valid
- **Certificate Generation**: Download sertifikat verifikasi dalam format JSON
- **Dashboard Management**: Dashboard untuk melihat dan mengelola semua verifikasi
- **Search & Filter**: Pencarian dan filter verifikasi berdasarkan berbagai kriteria
- **Export Functionality**: Export data verifikasi untuk backup atau analisis

## 🏗️ Struktur Proyek

```
ekyc-blockchain/
├── index.html              # Main HTML interface
├── dashboard.html          # Dashboard untuk management verifikasi
├── styles.css              # Styling dan responsive design
├── dashboard.css           # Styling khusus untuk dashboard
├── app.js                  # Main application logic
├── dashboard.js            # Dashboard management logic
├── blockchain-utils.js     # Blockchain utilities dan Web3 integration
├── smart-contract.js       # Smart contract simulation
├── demo-data.js           # Demo data untuk testing
└── README.md              # Dokumentasi ini
```

## 🚀 Cara Menggunakan

### 1. Setup
- Clone atau download repository ini
- Buka `index.html` di browser modern (Chrome, Firefox, Safari)
- Pastikan browser mendukung WebRTC untuk fitur kamera

### 2. Proses Verifikasi

#### Halaman Utama (index.html)
#### Step 1: Personal Information
- Isi data pribadi lengkap (nama, tanggal lahir, NIK, dll)
- Semua field bertanda * wajib diisi

#### Step 2: Document Upload
- Upload foto KTP yang jelas
- Upload bukti alamat (tagihan listrik/bank statement)
- Drag & drop atau click untuk browse file
- Format yang didukung: JPG, PNG, PDF (max 5MB)

#### Step 3: Biometric Verification
- Klik "Start Camera" untuk mengaktifkan kamera
- Posisikan wajah dalam frame yang tersedia
- Klik "Capture Photo" untuk mengambil foto
- Foto akan diproses untuk ekstraksi biometrik

#### Step 4: Blockchain Verification
- Klik "Connect Wallet" untuk simulasi koneksi MetaMask
- Klik "Deploy Smart Contract" untuk deploy contract
- Klik "Mint Verification Token" untuk membuat token verifikasi
- Download sertifikat verifikasi

#### Dashboard (dashboard.html)
- **Overview Statistics**: Lihat statistik total verifikasi, token, dan tingkat keberhasilan
- **Verification Records**: Tabel lengkap semua verifikasi yang tersimpan di blockchain
- **Search & Filter**: Cari berdasarkan nama, token ID, atau alamat wallet
- **Detail View**: Lihat detail lengkap setiap verifikasi
- **Certificate Download**: Download ulang sertifikat verifikasi
- **Blockchain Verification**: Verifikasi ulang token di blockchain
- **Export Data**: Export semua data verifikasi untuk backup

## 🔧 Teknologi yang Digunakan

### Frontend
- **HTML5**: Struktur aplikasi dan form handling
- **CSS3**: Styling dengan Grid, Flexbox, dan Animations
- **JavaScript ES6+**: Logic aplikasi dan DOM manipulation
- **WebRTC API**: Untuk akses kamera dan capture foto
- **FileReader API**: Untuk preview dan processing file upload

### Blockchain Simulation
- **Web3.js**: Library untuk interaksi blockchain (included via CDN)
- **Smart Contract Simulation**: Mock implementation untuk testing
- **Cryptographic Hashing**: Simulasi hashing untuk data security
- **Token Standard**: ERC-721 style NFT untuk verification tokens

## 📋 Proses Verifikasi Detail

### 1. Data Collection
- Personal information validation
- Document integrity checking
- Biometric data extraction

### 2. Hash Generation
- SHA-256 hash untuk uploaded documents
- Biometric feature extraction dan hashing
- Verification data packaging

### 3. Blockchain Storage
- Smart contract deployment
- Verification hash storage on-chain
- NFT token minting dengan metadata

### 4. Certificate Generation
- Tamper-proof verification certificate
- Blockchain transaction reference
- Downloadable proof of verification

## 🔒 Security Features

### Data Protection
- **Hash-only Storage**: Hanya hash yang disimpan di blockchain, bukan data asli
- **Client-side Processing**: Data sensitif diproses di browser, tidak dikirim ke server
- **Immutable Records**: Blockchain memastikan data tidak dapat diubah

### Privacy Considerations
- **Minimal Data Exposure**: Hanya hash verification yang public
- **Local Storage**: File upload dan biometric data hanya tersimpan lokal
- **Decentralized Verification**: Tidak ada central authority yang menyimpan data

## 🌐 Browser Compatibility

- ✅ Chrome 80+
- ✅ Firefox 75+
- ✅ Safari 13+
- ✅ Edge 80+

### Required Permissions
- Camera access untuk biometric verification
- File system access untuk document upload

## 🛠️ Development Setup

Untuk development dan testing:

```bash
# Serve files dengan HTTP server
python -m http.server 8000
# atau
npx serve .
# atau menggunakan Live Server extension di VS Code
```

## 📦 Production Deployment

### Web Server
Upload semua file ke web server yang mendukung HTTPS (required untuk camera access)

### IPFS Deployment
```bash
# Upload ke IPFS untuk decentralized hosting
ipfs add -r ekyc-blockchain/
```

### Blockchain Integration
Untuk production dengan blockchain real:
1. Ganti simulasi dengan Web3 provider actual
2. Deploy smart contract ke testnet/mainnet
3. Update contract address di konfigurasi
4. Implement proper wallet connection (MetaMask, WalletConnect)

## 🔮 Future Enhancements

- [ ] Integration dengan blockchain testnet (Polygon, BSC)
- [ ] Support untuk multiple wallet providers
- [ ] Advanced biometric algorithms (liveness detection)
- [ ] Mobile app dengan React Native
- [ ] IPFS storage untuk document backup
- [ ] Multi-signature verification untuk enterprise
- [ ] Integration dengan government ID databases
- [ ] OAuth integration untuk social verification

## 📄 License

MIT License - bebas digunakan untuk personal dan komersial.

## 🤝 Contributing

Kontribusi sangat diterima! Silakan:
1. Fork repository
2. Create feature branch
3. Submit pull request

## 📧 Support

Untuk pertanyaan dan support, silakan buat issue di repository ini.

---

**⚠️ Disclaimer**: Ini adalah implementasi mockup untuk demonstrasi. Untuk production, implementasikan security measures yang proper dan gunakan blockchain network yang actual.
