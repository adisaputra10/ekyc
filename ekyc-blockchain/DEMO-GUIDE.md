# eKYC Blockchain Demo Guide

## 🚀 Panduan Demo Aplikasi eKYC Blockchain

### Langkah 1: Membuka Aplikasi

1. Pastikan server sudah berjalan di `http://localhost:8000`
2. Buka browser dan akses salah satu dari:
   - **Verifikasi eKYC**: `http://localhost:8000/index.html`
   - **Dashboard**: `http://localhost:8000/dashboard.html`

### Langkah 2: Demo Verifikasi eKYC Baru

#### A. Menggunakan Data Demo Otomatis
1. Di halaman `index.html`, klik tombol **"🎭 Fill Demo Data"** di pojok kiri atas
2. Form akan terisi otomatis dengan data contoh
3. Lanjutkan ke step berikutnya

#### B. Mengisi Manual
1. **Step 1 - Personal Information**:
   ```
   Full Name: John Doe
   Date of Birth: 1990-05-15
   National ID: 1234567890123456
   Address: Jl. Sudirman No. 123, Jakarta Pusat
   Phone: +62812345678
   Email: john.doe@example.com
   ```

2. **Step 2 - Document Upload**:
   - Upload gambar KTP (format: JPG, PNG)
   - Upload bukti alamat (format: JPG, PNG, PDF)
   - Gunakan drag & drop atau klik untuk browse

3. **Step 3 - Biometric Verification**:
   - Klik "Start Camera"
   - Izinkan akses kamera
   - Posisikan wajah dalam frame
   - Klik "Capture Photo"

4. **Step 4 - Blockchain Verification**:
   - Klik "Connect Wallet" → Simulasi koneksi MetaMask
   - Klik "Deploy Smart Contract" → Deploy contract ke blockchain
   - Klik "Mint Verification Token" → Buat token verifikasi
   - Download sertifikat setelah selesai

### Langkah 3: Menggunakan Dashboard

#### Akses Dashboard
- Dari halaman verifikasi: Klik "📊 Dashboard" di navigasi
- Langsung: Buka `http://localhost:8000/dashboard.html`

#### Fitur Dashboard yang Bisa Dicoba

1. **Statistics Overview**:
   - Lihat total users, tokens, transactions
   - Success rate verifikasi

2. **Search & Filter**:
   ```
   - Search: Coba ketik "John" atau token ID
   - Status Filter: Pilih "verified", "pending", atau "rejected"  
   - Date Filter: Pilih "Today", "This Week", atau "This Month"
   ```

3. **Table Actions**:
   - **View**: Klik untuk melihat detail verifikasi
   - **Download**: Download sertifikat dalam format JSON
   - **Verify**: Verifikasi ulang token di blockchain

4. **Bulk Operations**:
   - Centang beberapa record
   - Gunakan "Bulk Actions" untuk operasi massal

5. **Pagination**:
   - Ubah jumlah item per halaman (10, 25, 50)
   - Navigate menggunakan tombol Previous/Next
   - Klik nomor halaman langsung

6. **Export Data**:
   - Klik "📥 Export Data"
   - Download semua data dalam format JSON

### Langkah 4: Demo Scenario

#### Scenario 1: User Baru Melakukan Verifikasi
1. Mulai di `index.html`
2. Gunakan tombol "🎭 Fill Demo Data"
3. Upload dokumen sample
4. Capture foto (atau skip jika tidak ada camera)
5. Simulasi blockchain verification
6. Download certificate
7. Pindah ke dashboard untuk melihat record baru

#### Scenario 2: Administrator Mengelola Data
1. Buka dashboard langsung
2. Lihat overview statistics
3. Search user specific
4. View detail verification
5. Download certificate untuk user
6. Verify token di blockchain
7. Export data untuk backup

#### Scenario 3: Troubleshooting User
1. Dashboard → Search berdasarkan nama/email user
2. Klik "View" untuk detail lengkap
3. Check verification status dan score
4. Re-verify token jika diperlukan
5. Download ulang certificate

### Langkah 5: Testing Advanced Features

#### A. Console Commands
Buka Developer Tools → Console, jalankan:

```javascript
// Populate form dengan demo data
demoHelpers.populateForm();

// Lihat sample verification
demoHelpers.showSample();

// Generate random address
demoHelpers.generateAddress();

// Access blockchain utils
window.dashboard.blockchain.getContractInfo();
```

#### B. Simulating Different Scenarios

1. **Pending Verification**:
   - Edit demo data di `demo-data.js`
   - Ubah status menjadi "pending"

2. **Failed Verification**:
   - Simulasi error dengan disconnect wallet
   - Test error handling

3. **Multiple Users**:
   - Refresh dashboard beberapa kali
   - Lihat data bertambah dengan random users

### Langkah 6: Understanding the Code

#### Key Files to Explore:

1. **smart-contract.js**: 
   - Simulasi smart contract
   - Token minting logic
   - Verification storage

2. **blockchain-utils.js**:
   - Wallet connection simulation
   - Hash generation
   - Certificate creation

3. **dashboard.js**:
   - Data management
   - Search & filter logic
   - Table rendering

4. **demo-data.js**:
   - Sample data generation
   - Testing utilities

### Langkah 7: Production Considerations

#### Hal yang Perlu Diubah untuk Production:

1. **Real Blockchain Integration**:
   ```javascript
   // Ganti simulasi dengan Web3 provider actual
   const web3 = new Web3(window.ethereum);
   ```

2. **Actual Smart Contract**:
   - Deploy real contract ke testnet
   - Update contract address
   - Implement proper ABI

3. **Security Enhancements**:
   - HTTPS untuk camera access
   - Proper file validation
   - Rate limiting

4. **Backend Integration**:
   - API for data persistence
   - User authentication
   - Email notifications

### Tips Demo yang Efektif

1. **Persiapan**:
   - Pastikan camera tersedia untuk biometric demo
   - Siapkan sample images untuk upload
   - Test di different browsers

2. **Flow Presentation**:
   - Mulai dengan dashboard overview
   - Show complete verification flow
   - Demonstrate search & management features

3. **Highlight Features**:
   - Responsive design (test di mobile)
   - Real-time updates
   - Blockchain immutability concept
   - Privacy-preserving (hash-only storage)

### Troubleshooting Demo

#### Common Issues:

1. **Camera Access Denied**:
   - Refresh page dan allow permissions
   - Atau skip biometric step

2. **Page Not Loading**:
   - Check server masih running
   - Try different port: `python -m http.server 8080`

3. **Data Tidak Muncul**:
   - Clear browser cache
   - Check console for errors

4. **Responsive Issues**:
   - Test di Chrome DevTools mobile view
   - Try different screen sizes

---

**🎯 Demo Success Criteria:**
- ✅ User dapat complete full verification flow
- ✅ Dashboard menampilkan data dengan benar
- ✅ Search & filter berfungsi normal
- ✅ Certificate download berhasil
- ✅ Responsive design bekerja di mobile
- ✅ No console errors

**Happy Demo! 🚀**
