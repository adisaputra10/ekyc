# revision_2026 — Reproducible Ablation & Evaluation Pipeline

Kode di folder ini adalah pipeline eksperimen lengkap untuk paper **"eKYC Halal SME Compliance"** (revisi 2026). Mulai dari pembuatan dataset sintetis, ablasi multi-tier, evaluasi statistik, simulasi blockchain, hingga pembaruan manuskrip secara otomatis.

---

## Struktur Folder

```
revision_2026/
├── dataset_builder.py       # Buat dataset sintetis (gambar + ground truth)
├── ablation_runner.py       # Jalankan eksperimen ablasi T0–T3
├── retry_failed.py          # Ulangi kombinasi model/tier yang gagal
├── metrics.py               # CER, WER, Entity F1, Accuracy
├── models.py                # Wrapper Tesseract & OpenRouter mLLM
├── retrieval.py             # BM25 + dense kNN + RRF (Elasticsearch)
├── statistics_analysis.py   # Uji statistik & buat ablation_table.md
├── blockchain_sim.py        # Simulasi PoA consortium (credential reuse)
├── align_manuscript.py      # Sinkronkan tabel manuskrip v8 → v11
├── drop_t2_split_ci.py      # Hapus kolom T2, pisah Mean/CI → v12
├── update_docx.py           # Update tabel manuskrip final → _revised.docx
├── _build_v14.py            # Build manuskrip final v14 (4 tier)
├── _inspect_summary.py      # Cetak ringkasan summary.json ke terminal
├── dataset/
│   ├── ground_truth.json    # Ground truth tergenerate
│   └── images/              # Gambar dokumen sintetis
└── results/
    ├── raw_predictions.jsonl
    ├── per_doc_metrics.csv
    ├── summary.json
    ├── statistics.json
    ├── ablation_table.md
    └── blockchain.json
```

---

## Prasyarat

### Python & Virtual Environment

```powershell
cd d:\repo\ekyc\revision_2026
python -m venv venv
.\venv\Scripts\activate
pip install -r ..\ekyc\requirements.txt
# Atau minimal:
pip install openai python-dotenv elasticsearch rank-bm25 numpy scipy pillow pytesseract python-docx matplotlib
```

### Tesseract OCR (Windows)

Unduh dari https://github.com/UB-Mannheim/tesseract/wiki dan install ke:
`C:\Program Files\Tesseract-OCR\tesseract.exe`

### Elasticsearch 8.x

```powershell
# Jalankan via Docker (rekomendasi)
docker run -d --name es8 -p 9200:9200 -e "discovery.type=single-node" `
  -e "xpack.security.enabled=false" docker.elastic.co/elasticsearch/elasticsearch:8.13.0
```

### API Key

Buat file `.env` di root (`d:\repo\ekyc\.env`):

```env
key_open_ai=sk-or-...   # OpenRouter API key
```

---

## Alur Eksperimen (Urutan Eksekusi)

```
[1] dataset_builder.py
        ↓
[2] ablation_runner.py       ← eksperimen utama (T0–T3)
        ↓
[3] retry_failed.py          ← (opsional) ulangi yang gagal
        ↓
[4] statistics_analysis.py   ← hitung statistik & buat tabel
        ↓
[5] blockchain_sim.py        ← simulasi blockchain
        ↓
[6] align_manuscript.py      → v11_aligned.docx
        ↓
[7] drop_t2_split_ci.py      → v12_no_t2.docx
        ↓
[8] update_docx.py           → manuscript_revised.docx
        ↓
[9] _build_v14.py            → manuscript_v14_4tiers.docx  (final)
```

---

## Skenario 1 — Bangun Dataset Sintetis

```powershell
d:\repo\ekyc\revision_2026\venv\Scripts\python.exe `
    d:\repo\ekyc\revision_2026\dataset_builder.py
```

Menghasilkan gambar raster dokumen Indonesia sintetis (NIB, SIUP, NPWP, HALAL) beserta `dataset/ground_truth.json`. Tiga varian per dokumen: `clean`, `noisy`, `skewed`.

**Catatan penting:** Field `applicable_regulation` **sengaja tidak dicetak** pada gambar. Nilai yang benar hanya bisa diperoleh dari knowledge base RAG, menjadikannya pembeda ablasi utama.

---

## Skenario 2 — Ablasi Multi-Tier (T0–T3)

```powershell
d:\repo\ekyc\revision_2026\venv\Scripts\python.exe `
    d:\repo\ekyc\revision_2026\ablation_runner.py `
    *>&1 | Tee-Object -FilePath d:\repo\ekyc\revision_2026\results\run_log.txt
```

### Definisi Tier

| Tier | Deskripsi |
|---|---|
| **T0** | Tesseract OCR baseline — rule-based, tanpa model bahasa |
| **T1** | mLLM-OCR without retrieval — zero-shot tanpa schema hint |
| **T2** | mLLM-OCR + RAG — Hybrid RAG (BM25 + dense kNN via RRF) |
| **T3** | T2 + MLOps — regulatory adaptation layer aktif di runtime |

> **RAG** = BM25 (lexical) + dense kNN (embedding berbasis hashing deterministik) difusi via **Reciprocal Rank Fusion (RRF)**.  
> **MLOps** = filter `select_active_version` memilih entri regulasi terbaru per jenis dokumen tanpa retraining model.

> **Catatan implementasi:** Di dalam kode, T2 dan T3 (paper) dieksekusi sebagai tier internal `T4` dan `T5` — karena kode juga memiliki tier antara (T2 = schema-only, T3 = dense-RAG saja) yang tidak ditampilkan di paper.

### Model yang Diuji

| Nama Model (Paper) | Provider |
|--------------------|----------|
| Qwen VL Plus | Alibaba via OpenRouter |
| GPT-4o | OpenAI via OpenRouter |
| GPT-5.2 | OpenAI via OpenRouter |
| Claude Sonnet 4 | Anthropic via OpenRouter |
| GPT-5.2 Pro | OpenAI via OpenRouter |
| Claude Sonnet 4.5 | Anthropic via OpenRouter |

### Output

| File | Isi |
|------|-----|
| `results/raw_predictions.jsonl` | Setiap prediksi per (model, tier, dokumen) |
| `results/per_doc_metrics.csv` | Metrik per baris: CER, WER, Precision, Recall, F1, Layout, Accuracy |
| `results/summary.json` | Rata-rata + 95% bootstrap CI per (model, tier) |

### Argumen Opsional (via kode)

Edit fungsi `main()` di `ablation_runner.py`:

```python
# Batasi dataset (debug cepat):
main(per_type_limit=5)

# Filter model tertentu:
main(models_filter=["GPT-4o", "Qwen VL Plus"])

# Jalankan semua tier default (T0, T1, T4, T5 internal = Paper T0–T3)
main()
```

---

## Skenario 3 — Retry Kombinasi yang Gagal

Jika ada model/tier yang gagal (quota, timeout, dll.):

```powershell
d:\repo\ekyc\revision_2026\venv\Scripts\python.exe `
    d:\repo\ekyc\revision_2026\retry_failed.py `
    *>&1 | Tee-Object -FilePath d:\repo\ekyc\revision_2026\results\retry.log
```

Edit bagian `RETRY` di `retry_failed.py` untuk menentukan kombinasi mana yang diulang:

```python
# T4 (internal) = T2 paper (+RAG)
# T5 (internal) = T3 paper (+MLOps)
RETRY = {
    "GPT-5.2 Pro":      ["T5"],               # T3 (+MLOps)
    "Claude Sonnet 4.5": ["T1", "T4", "T5"],  # T1, T2, T3
}
```

Script ini:
1. Menjalankan hanya kombinasi yang gagal
2. Menggabungkan hasil baru dengan `raw_predictions.jsonl` lama
3. Rebuild `per_doc_metrics.csv` dan `summary.json`
4. Otomatis menjalankan `statistics_analysis.py` dan `update_docx.py`

---

## Skenario 4 — Analisis Statistik & Tabel Ablasi

```powershell
d:\repo\ekyc\revision_2026\venv\Scripts\python.exe `
    d:\repo\ekyc\revision_2026\statistics_analysis.py
```

Membaca `per_doc_metrics.csv` dan menghitung:

- **Paired t-test**: Tesseract (T0) vs setiap (model, tier full RAG)
- **Wilcoxon signed-rank**: uji non-parametrik yang sama
- **Cohen's d**: effect size
- **Tier-vs-tier**: T1→T2→T3 (Δaccuracy per komponen yang ditambahkan: +RAG, +MLOps)

Output:
- `results/statistics.json` — semua nilai uji statistik
- `results/ablation_table.md` — tabel Markdown siap masuk manuskrip

---

## Skenario 5 — Simulasi Blockchain

```powershell
d:\repo\ekyc\revision_2026\venv\Scripts\python.exe `
    d:\repo\ekyc\revision_2026\blockchain_sim.py
```

Mensimulasikan konsorsium **PoA (Proof of Authority)** in-memory (tanpa jaringan Geth/Besu nyata):

- N authority nodes menandatangani blok secara round-robin
- Setiap blok butuh >50% tanda tangan untuk finalisasi
- **Credential reuse**: hash lookup + konfirmasi 2-fase consensus
- Mengukur latency wall-clock untuk verifikasi awal vs reuse

Output: `results/blockchain.json`

---

## Skenario 6 — Sinkronisasi Manuskrip (v8 → v11)

```powershell
d:\repo\ekyc\revision_2026\venv\Scripts\python.exe `
    d:\repo\ekyc\revision_2026\align_manuscript.py
```

Membutuhkan file: `manuscript_ekyc_halal_sme_v8_final.docx` di root repo.

Memperbarui Tabel III–VII dan Gambar 3–5 di manuskrip dengan data pengukuran aktual dari `summary.json`. Output: `manuscript_ekyc_halal_sme_v11_aligned.docx`.

---

## Skenario 7 — Hapus Kolom T2, Pisah Mean/CI (v11 → v12)

```powershell
d:\repo\ekyc\revision_2026\venv\Scripts\python.exe `
    d:\repo\ekyc\revision_2026\drop_t2_split_ci.py
```

Membutuhkan: `manuscript_ekyc_halal_sme_v11_aligned.docx`

Menghapus kolom T2 (+schema) dari tabel ablasi dan memisahkan setiap sel menjadi kolom **Mean** dan **95% CI** terpisah. Output: `manuscript_ekyc_halal_sme_v12_no_t2.docx`.

---

## Skenario 8 — Update Manuskrip Final (→ _revised.docx)

```powershell
d:\repo\ekyc\revision_2026\venv\Scripts\python.exe `
    d:\repo\ekyc\revision_2026\update_docx.py
```

Membutuhkan: `manuscript_ekyc_halal_sme (1).docx` di root repo.

Mengganti konten numerik Tabel IV–VIII dengan hasil pengukuran terbaru dan menyisipkan sub-bagian "Ablation Study" ke dalam bagian RESULTS. Output: `manuscript_ekyc_halal_sme_revised.docx`.

---

## Skenario 9 — Build Manuskrip Final v14 (4 Tier)

```powershell
d:\repo\ekyc\revision_2026\venv\Scripts\python.exe `
    d:\repo\ekyc\revision_2026\_build_v14.py
```

Build final dengan **4 tier** sesuai penamaan paper:

| Tier | Deskripsi |
|---|---|
| T0 — Tesseract OCR baseline | Rule-based OCR, tanpa model bahasa |
| T1 — mLLM-OCR without retrieval | mLLM zero-shot |
| T2 — mLLM-OCR + RAG | Hybrid RAG (BM25 + dense kNN, RRF) |
| T3 — mLLM-OCR + RAG + MLOps | T2 + regulatory adaptation layer |

Output: `manuscript_ekyc_halal_sme_v14_4tiers.docx`

---

## Skenario 10 — Inspeksi Cepat Hasil

```powershell
d:\repo\ekyc\revision_2026\venv\Scripts\python.exe `
    d:\repo\ekyc\revision_2026\_inspect_summary.py
```

Cetak ke terminal ringkasan metrik per model per tier (Accuracy, CER, WER, P, R, F1, Layout, Latency) dari `summary.json`.

---

## Metrik Evaluasi

| Metrik | Deskripsi |
|--------|-----------|
| **CER** | Character Error Rate — edit distance karakter vs ground truth |
| **WER** | Word Error Rate — edit distance token vs ground truth |
| **Precision** | Entity-level: field yang diprediksi benar / semua field diprediksi |
| **Recall** | Entity-level: field yang diprediksi benar / semua field ground truth |
| **F1** | Harmonic mean Precision & Recall |
| **Layout** | LCS baris non-kosong (normalized) — preservasi struktur dokumen |
| **Accuracy** | Skor komposit berbobot yang dipakai dalam paper |

Semua metrik bernilai `[0, 1]`; paper melaporkan dalam persentase `(× 100)`.

---

## Hasil Ringkas Ablasi

### A. Per Tier — Accuracy % / F1-Score %

| Model | T0 Tesseract (Acc/F1) | T1 mLLM-OCR (Acc/F1) | T2 +RAG (Acc/F1) | T3 +MLOps (Acc/F1) |
|---|---|---|---|---|
| Qwen VL Plus | 44.21 / 30.33 | 86.69 / 81.34 | 94.00 / 99.54 | 94.04 / 99.75 |
| GPT-4o | 44.21 / 30.33 | 83.26 / 72.80 | 93.99 / 99.48 | 94.02 / 99.48 |
| GPT-5.2 | 44.21 / 30.33 | 82.77 / 72.22 | 93.20 / 98.15 | 92.92 / 97.69 |
| Claude Sonnet 4 | 44.21 / 30.33 | 68.88 / 71.70 | 81.47 / 97.40 | 80.18 / 97.92 |
| GPT-5.2 Pro | 44.21 / 30.33 | 82.83 / 72.22 | 93.20 / 98.15 | 93.20 / 98.15 |
| Claude Sonnet 4.5 | 44.21 / 30.33 | 84.08 / 75.60 | 91.75 / 98.96 | 92.06 / 99.48 |

### B. Perbandingan T3 (+MLOps) vs T0 (Tesseract baseline)

| Model | Δ Accuracy | p-value | Cohen's d |
|-------|-----------|---------|-----------|
| Qwen VL Plus | +49.83 pp | < 0.001 | 1.498 |
| GPT-4o | +49.81 pp | < 0.001 | 1.513 |
| GPT-5.2 | +48.71 pp | < 0.001 | 1.486 |
| Claude Sonnet 4 | +35.97 pp | < 0.001 | 0.984 |
| GPT-5.2 Pro | +48.99 pp | < 0.001 | 1.479 |
| Claude Sonnet 4.5 | +47.85 pp | < 0.001 | 1.309 |

---

## Troubleshooting

**Elasticsearch tidak berjalan**  
```
ConnectionError: Failed to establish a new connection
```
Pastikan ES 8.x berjalan di `localhost:9200` (lihat perintah Docker di atas). Cek dengan: `Invoke-WebRequest http://localhost:9200`

**Tesseract tidak ditemukan**  
```
TesseractNotFoundError
```
Install Tesseract dan verifikasi path di `models.py` (`_TESSERACT_PATHS`).

**Error working directory saat jalankan dari luar folder**  
Selalu gunakan path absolut:
```powershell
d:\repo\ekyc\revision_2026\venv\Scripts\python.exe d:\repo\ekyc\revision_2026\ablation_runner.py
```
Jangan jalankan dari direktori lain karena beberapa script menggunakan `Path(__file__).resolve().parent`.

**Quota API habis / timeout**  
Gunakan `retry_failed.py` dengan mengisi dictionary `RETRY` sesuai kombinasi yang gagal.
