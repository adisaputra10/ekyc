"""
Synthetic Halal SME compliance document dataset builder.

Generates rasterized images simulating Indonesian compliance documents
with deterministic ground truth (entity values & full text). Used for
reproducible ablation experiments without exposing real PII.

Document types generated:
  - NIB (Nomor Induk Berusaha)
  - SIUP (Surat Izin Usaha Perdagangan)
  - NPWP (Tax registration)
  - HALAL (Halal certification)

Variants per document:
  - clean      : crisp render
  - noisy      : gaussian noise + slight blur
  - skewed     : 3-7 degree rotation + noise
"""
from __future__ import annotations
import json
import os
import random
import string
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np


RNG = random.Random(42)
np.random.seed(42)

# Regulatory strings — INTENTIONALLY NOT PRINTED ON THE DOCUMENT IMAGE.
# Their correct value must be retrieved from the regulatory KB; without
# RAG (and especially without the MLOps-applied v2 KB), the model has no
# way to recover them. This is the ablation differentiator.
REGULATION_V2 = {
    "NIB":   "OSS-RBA Reg. 12/2024 Art. 4",
    "SIUP":  "Permendag 25/2024 Art. 9",
    "NPWP":  "PER-12/PJ/2024 Art. 3",
    "HALAL": "BPJPH Reg. 14/2025 Art. 7(2)(b)",
}
REGULATION_V1 = {
    "NIB":   "OSS-RBA Reg. 5/2021",
    "SIUP":  "Permendag 36/2007",
    "NPWP":  "PER-04/PJ/2020",
    "HALAL": "MUI Reg. 9/2020",
}

OUT_DIR = Path(__file__).parent / "dataset"
IMG_DIR = OUT_DIR / "images"
GT_PATH = OUT_DIR / "ground_truth.json"
IMG_DIR.mkdir(parents=True, exist_ok=True)


def _font(size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            return ImageFont.truetype(c, size)
    return ImageFont.load_default()


def _random_company() -> str:
    bases = ["Berkah", "Halal", "Sentosa", "Mandiri", "Sejahtera", "Amanah", "Cahaya", "Bintang", "Mulia", "Insan"]
    suffix = ["Pangan", "Makmur", "Niaga", "Boga", "Sukses", "Utama", "Jaya", "Abadi", "Selaras"]
    return f"PT {RNG.choice(bases)} {RNG.choice(suffix)}"


def _random_address() -> str:
    streets = ["Jl. Diponegoro", "Jl. Sudirman", "Jl. Gajah Mada", "Jl. Veteran", "Jl. Ahmad Yani", "Jl. Pemuda"]
    cities = ["Surabaya", "Jakarta Selatan", "Bandung", "Yogyakarta", "Semarang", "Malang"]
    return f"{RNG.choice(streets)} No. {RNG.randint(1, 250)}, {RNG.choice(cities)}"


def _rand_digits(n: int) -> str:
    return "".join(RNG.choice(string.digits) for _ in range(n))


def _random_date_2025_plus() -> str:
    """All issue dates fall after the v2 regulations take effect."""
    return f"{RNG.randint(1,28):02d}/{RNG.randint(1,12):02d}/{RNG.randint(2025,2026)}"


def _make_nib() -> Dict[str, Any]:
    company = _random_company()
    nib_num = _rand_digits(13)
    npwp = f"{_rand_digits(2)}.{_rand_digits(3)}.{_rand_digits(3)}.{_rand_digits(1)}-{_rand_digits(3)}.{_rand_digits(3)}"
    issue = _random_date_2025_plus()
    kbli = _rand_digits(5)
    address = _random_address()
    return {
        "doc_type": "NIB",
        "fields": {
            "company_name": company,
            "nib_number": nib_num,
            "npwp": npwp,
            "issue_date": issue,
            "kbli_code": kbli,
            "address": address,
            "issuing_authority": "Lembaga OSS Republik Indonesia",
            "business_status": "Aktif",
            # NOT printed on the document; must come from the KB
            "applicable_regulation": REGULATION_V2["NIB"],
        },
        "text": (
            f"REPUBLIK INDONESIA\n"
            f"NOMOR INDUK BERUSAHA (NIB)\n"
            f"Nomor: {nib_num}\n"
            f"Nama Perusahaan: {company}\n"
            f"NPWP: {npwp}\n"
            f"Tanggal Terbit: {issue}\n"
            f"Kode KBLI: {kbli}\n"
            f"Alamat: {address}\n"
            f"Status: Aktif\n"
            f"Diterbitkan oleh Lembaga OSS Republik Indonesia"
        ),
    }


def _make_siup() -> Dict[str, Any]:
    company = _random_company()
    siup_num = f"503/{_rand_digits(4)}/SIUP-K/{RNG.randint(2025,2026)}"
    npwp = f"{_rand_digits(2)}.{_rand_digits(3)}.{_rand_digits(3)}.{_rand_digits(1)}-{_rand_digits(3)}.{_rand_digits(3)}"
    issue = _random_date_2025_plus()
    address = _random_address()
    return {
        "doc_type": "SIUP",
        "fields": {
            "company_name": company,
            "siup_number": siup_num,
            "npwp": npwp,
            "issue_date": issue,
            "address": address,
            "trade_category": "Perdagangan Besar Bahan Makanan Halal",
            "issuing_authority": "Dinas Penanaman Modal dan PTSP",
            "business_status": "Aktif",
            "applicable_regulation": REGULATION_V2["SIUP"],
        },
        "text": (
            f"SURAT IZIN USAHA PERDAGANGAN (SIUP)\n"
            f"Nomor: {siup_num}\n"
            f"Nama Perusahaan: {company}\n"
            f"NPWP: {npwp}\n"
            f"Tanggal Terbit: {issue}\n"
            f"Alamat: {address}\n"
            f"Kategori Usaha: Perdagangan Besar Bahan Makanan Halal\n"
            f"Status: Aktif\n"
            f"Dikeluarkan oleh Dinas Penanaman Modal dan PTSP"
        ),
    }


def _make_npwp() -> Dict[str, Any]:
    company = _random_company()
    npwp = f"{_rand_digits(2)}.{_rand_digits(3)}.{_rand_digits(3)}.{_rand_digits(1)}-{_rand_digits(3)}.{_rand_digits(3)}"
    issue = _random_date_2025_plus()
    address = _random_address()
    return {
        "doc_type": "NPWP",
        "fields": {
            "company_name": company,
            "npwp": npwp,
            "issue_date": issue,
            "address": address,
            "tax_office": f"KPP Pratama {address.split(', ')[-1]}",
            "issuing_authority": "Direktorat Jenderal Pajak",
            "business_status": "Aktif",
            "applicable_regulation": REGULATION_V2["NPWP"],
        },
        "text": (
            f"KEMENTERIAN KEUANGAN REPUBLIK INDONESIA\n"
            f"DIREKTORAT JENDERAL PAJAK\n"
            f"NPWP: {npwp}\n"
            f"Nama: {company}\n"
            f"Alamat: {address}\n"
            f"Tanggal Terdaftar: {issue}\n"
            f"KPP: KPP Pratama {address.split(', ')[-1]}\n"
            f"Status: Aktif"
        ),
    }


def _make_halal() -> Dict[str, Any]:
    company = _random_company()
    cert_num = f"ID00{_rand_digits(8)}{RNG.randint(2025,2026)}"
    issue = _random_date_2025_plus()
    expiry_year = int(issue.split("/")[-1]) + 4
    expiry = f"{RNG.randint(1,28):02d}/{RNG.randint(1,12):02d}/{expiry_year}"
    return {
        "doc_type": "HALAL",
        "fields": {
            "company_name": company,
            "halal_cert_number": cert_num,
            "issue_date": issue,
            "expiry_date": expiry,
            "product_category": "Produk Olahan Makanan",
            "issuing_authority": "BPJPH Kementerian Agama",
            "business_status": "Berlaku",
            "applicable_regulation": REGULATION_V2["HALAL"],
        },
        "text": (
            f"BADAN PENYELENGGARA JAMINAN PRODUK HALAL\n"
            f"SERTIFIKAT HALAL\n"
            f"Nomor Sertifikat: {cert_num}\n"
            f"Nama Pelaku Usaha: {company}\n"
            f"Kategori Produk: Produk Olahan Makanan\n"
            f"Tanggal Terbit: {issue}\n"
            f"Berlaku Sampai: {expiry}\n"
            f"Status: Berlaku\n"
            f"Dikeluarkan oleh BPJPH Kementerian Agama Republik Indonesia"
        ),
    }


GENERATORS = {"NIB": _make_nib, "SIUP": _make_siup, "NPWP": _make_npwp, "HALAL": _make_halal}


def _render_text_to_image(text: str, variant: str) -> Image.Image:
    W, H = 1100, 1400
    img = Image.new("RGB", (W, H), color=(252, 252, 248))
    draw = ImageDraw.Draw(img)
    title_font = _font(34)
    body_font = _font(24)
    lines = text.split("\n")
    y = 80
    for i, ln in enumerate(lines):
        font = title_font if i < 2 else body_font
        draw.text((80, y), ln, fill=(15, 15, 30), font=font)
        y += (44 if font is title_font else 38)
    # add a fake border / seal
    draw.rectangle([(40, 40), (W - 40, H - 40)], outline=(50, 50, 80), width=3)
    draw.ellipse([(W - 220, H - 220), (W - 60, H - 60)], outline=(120, 50, 50), width=3)
    draw.text((W - 200, H - 150), "RESMI", fill=(120, 50, 50), font=_font(28))

    if variant == "clean":
        return img
    if variant == "noisy":
        arr = np.array(img).astype(np.int16)
        noise = np.random.normal(0, 28, arr.shape).astype(np.int16)
        arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
        img = Image.fromarray(arr)
        img = img.filter(ImageFilter.GaussianBlur(radius=1.0))
        small = img.resize((W // 2, H // 2), Image.BILINEAR)
        img = small.resize((W, H), Image.BILINEAR)
        return img
    if variant == "skewed":
        arr = np.array(img).astype(np.int16)
        noise = np.random.normal(0, 22, arr.shape).astype(np.int16)
        arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
        img = Image.fromarray(arr)
        img = img.filter(ImageFilter.GaussianBlur(radius=0.8))
        angle = RNG.uniform(6, 10) * (1 if RNG.random() < 0.5 else -1)
        img = img.rotate(angle, fillcolor=(252, 252, 248), expand=False)
        occ = ImageDraw.Draw(img)
        x0 = RNG.randint(60, W - 260)
        y0 = RNG.randint(220, H - 260)
        occ.rectangle([(x0, y0), (x0 + 200, y0 + 28)],
                      fill=(220, 220, 215))
        return img
    return img


# Lines whose presence on the rendered image is removed for a given variant
# (simulates redaction / occlusion / stamp overlap). The corresponding ground
# truth fields remain authoritative, so only retrieval-augmented tiers can
# recover them — these schema-default fields are exactly the kind a regulatory
# KB stores authoritatively.
REDACTED_PREFIXES_BY_VARIANT = {
    "clean": (),
    "noisy": ("Status:", "Diterbitkan oleh", "Dikeluarkan oleh",
              "DIREKTORAT JENDERAL PAJAK"),
    "skewed": ("Status:",),
}


def _redact_lines(text: str, variant: str) -> str:
    prefixes = REDACTED_PREFIXES_BY_VARIANT.get(variant, ())
    if not prefixes:
        return text
    kept: List[str] = []
    for ln in text.split("\n"):
        if any(ln.lstrip().startswith(p) for p in prefixes):
            continue
        kept.append(ln)
    return "\n".join(kept)


def build_dataset(per_type: int = 6, variants: List[str] = None) -> List[Dict[str, Any]]:
    if variants is None:
        variants = ["clean", "noisy", "skewed"]
    records: List[Dict[str, Any]] = []
    idx = 0
    for doc_type, gen in GENERATORS.items():
        for k in range(per_type):
            sample = gen()
            variant = variants[k % len(variants)]
            rendered_text = _redact_lines(sample["text"], variant)
            img = _render_text_to_image(rendered_text, variant)
            file_name = f"{doc_type}_{idx:03d}_{variant}.png"
            file_path = IMG_DIR / file_name
            img.save(file_path, format="PNG")
            rec = {
                "id": f"doc_{idx:03d}",
                "doc_type": doc_type,
                "variant": variant,
                "image_path": str(file_path.relative_to(OUT_DIR.parent)).replace("\\", "/"),
                "ground_truth_text": sample["text"],
                "ground_truth_fields": sample["fields"],
            }
            records.append(rec)
            idx += 1
    with open(GT_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    return records


if __name__ == "__main__":
    recs = build_dataset(per_type=6)
    by_type: Dict[str, int] = {}
    by_variant: Dict[str, int] = {}
    for r in recs:
        by_type[r["doc_type"]] = by_type.get(r["doc_type"], 0) + 1
        by_variant[r["variant"]] = by_variant.get(r["variant"], 0) + 1
    print(f"Generated {len(recs)} documents")
    print(f"By type: {by_type}")
    print(f"By variant: {by_variant}")
    print(f"Ground truth saved to: {GT_PATH}")
