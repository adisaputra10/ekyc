"""Model wrappers for the eKYC ablation study.

Two backends are supported:
  - TesseractOCR : local rule-based baseline (tier T0)
  - OpenRouterMLLM : multimodal LLM via OpenRouter (tiers T1-T4)

All wrappers expose `predict(image_path, retrieval_context, schema_hint)`
and return a dict with `text` (raw extraction) and `fields` (entity dict).
"""
from __future__ import annotations
import base64
import json
import os
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Optional

from PIL import Image
import pytesseract

# Make sure tesseract.exe is locatable (Windows default install path)
_TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
]
for p in _TESSERACT_PATHS:
    if os.path.exists(p):
        pytesseract.pytesseract.tesseract_cmd = p
        break


SCHEMA_BY_TYPE: Dict[str, List[str]] = {
    "NIB": ["company_name", "nib_number", "npwp", "issue_date", "kbli_code",
            "address", "issuing_authority", "business_status", "applicable_regulation"],
    "SIUP": ["company_name", "siup_number", "npwp", "issue_date", "address",
             "trade_category", "issuing_authority", "business_status", "applicable_regulation"],
    "NPWP": ["company_name", "npwp", "issue_date", "address", "tax_office",
             "issuing_authority", "business_status", "applicable_regulation"],
    "HALAL": ["company_name", "halal_cert_number", "issue_date", "expiry_date",
              "product_category", "issuing_authority", "business_status", "applicable_regulation"],
}

ID_LABEL_TO_KEY = {
    "nomor": "nib_number",  # fallback heuristic; refined below
    "nama perusahaan": "company_name",
    "nama pelaku usaha": "company_name",
    "nama": "company_name",
    "npwp": "npwp",
    "tanggal terbit": "issue_date",
    "tanggal terdaftar": "issue_date",
    "kode kbli": "kbli_code",
    "alamat": "address",
    "status": "business_status",
    "kpp": "tax_office",
    "kategori usaha": "trade_category",
    "kategori produk": "product_category",
    "nomor sertifikat": "halal_cert_number",
    "berlaku sampai": "expiry_date",
}


def _heuristic_fields_from_text(text: str, doc_type: str) -> Dict[str, str]:
    """Rule-based extraction used by Tesseract baseline.

    Mirrors what a typical regex/template OCR pipeline would do.
    """
    fields: Dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if ":" not in line:
            continue
        label, value = line.split(":", 1)
        label = label.strip().lower()
        value = value.strip()
        for lab, key in ID_LABEL_TO_KEY.items():
            if lab in label:
                # disambiguate "Nomor" for different doc types
                if lab == "nomor":
                    if doc_type == "NIB":
                        fields["nib_number"] = value
                    elif doc_type == "SIUP":
                        fields["siup_number"] = value
                    else:
                        fields["halal_cert_number"] = value
                else:
                    fields[key] = value
                break
    # NPWP regex backup
    if "npwp" not in fields:
        m = re.search(r"\d{2}\.\d{3}\.\d{3}\.\d-\d{3}\.\d{3}", text)
        if m:
            fields["npwp"] = m.group(0)
    # issuing authority heuristic
    if doc_type == "NIB" and "OSS" in text and "issuing_authority" not in fields:
        fields["issuing_authority"] = "Lembaga OSS Republik Indonesia"
    if doc_type == "SIUP" and "Dinas" in text and "issuing_authority" not in fields:
        fields["issuing_authority"] = "Dinas Penanaman Modal dan PTSP"
    if doc_type == "NPWP" and "Jenderal Pajak" in text and "issuing_authority" not in fields:
        fields["issuing_authority"] = "Direktorat Jenderal Pajak"
    if doc_type == "HALAL" and "BPJPH" in text and "issuing_authority" not in fields:
        fields["issuing_authority"] = "BPJPH Kementerian Agama"
    return fields


@dataclass
class TesseractOCR:
    name: str = "Tesseract"

    def predict(self, image_path: str, doc_type: str,
                retrieval_context: Optional[List[Dict[str, Any]]] = None,
                schema_hint: Optional[List[str]] = None) -> Dict[str, Any]:
        t0 = time.perf_counter()
        img = Image.open(image_path)
        # Standard preprocessing pipeline cited in OCR literature
        # (grayscale + adaptive threshold via PIL point op).
        gray = img.convert("L")
        bw = gray.point(lambda x: 0 if x < 160 else 255, mode="L")
        try:
            text = pytesseract.image_to_string(bw, lang="ind+eng")
        except pytesseract.TesseractError:
            text = pytesseract.image_to_string(bw)
        fields = _heuristic_fields_from_text(text, doc_type)
        t1 = time.perf_counter()
        return {"text": text, "fields": fields, "latency_s": t1 - t0, "model": self.name}


def _encode_image(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def _extract_json(content: str) -> Dict[str, Any]:
    # strip fenced code blocks first
    cleaned = re.sub(r"^```(?:json)?", "", content.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"```$", "", cleaned.strip())
    m = JSON_RE.search(cleaned)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except Exception:
        return {}


@dataclass
class OpenRouterMLLM:
    model_id: str
    paper_name: str
    api_key: str
    base_url: str = "https://openrouter.ai/api/v1"
    timeout: int = 120

    def predict(self, image_path: str, doc_type: str,
                retrieval_context: Optional[List[Dict[str, Any]]] = None,
                schema_hint: Optional[List[str]] = None) -> Dict[str, Any]:
        import openai
        client = openai.OpenAI(base_url=self.base_url, api_key=self.api_key,
                               timeout=self.timeout)
        image_b64 = _encode_image(image_path)
        schema = schema_hint or SCHEMA_BY_TYPE.get(doc_type, [])
        ctx_block = ""
        if retrieval_context:
            ctx_lines = [f"- [{c.get('doc_type')} {c.get('version')}] {c.get('text')}"
                         for c in retrieval_context]
            ctx_block = ("\nRegulatory knowledge context (apply when relevant):\n"
                         + "\n".join(ctx_lines))
        sys_prompt = (
            "You are a compliance document extraction engine for Indonesian Halal SME eKYC. "
            "Read the image and return STRICTLY a single JSON object with two keys: "
            '"text" (full transcribed plain text) and "fields" (object with the requested keys). '
            "Do not include explanations."
        )
        user_prompt = (
            f"Document type: {doc_type}\n"
            f"Required fields: {', '.join(schema)}\n"
            f"{ctx_block}\n"
            "Return JSON only."
        )
        t0 = time.perf_counter()
        try:
            resp = client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {"type": "image_url",
                             "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
                        ],
                    },
                ],
                max_tokens=1500,
                temperature=0,
            )
            content = resp.choices[0].message.content or ""
        except Exception as exc:  # noqa: BLE001
            t1 = time.perf_counter()
            return {"text": "", "fields": {}, "latency_s": t1 - t0,
                    "model": self.paper_name, "error": str(exc)}
        t1 = time.perf_counter()
        parsed = _extract_json(content)
        text = parsed.get("text", "") if isinstance(parsed, dict) else ""
        fields_raw = parsed.get("fields", {}) if isinstance(parsed, dict) else {}
        if not isinstance(fields_raw, dict):
            fields_raw = {}
        # normalise keys (lowercase snake_case-ish)
        fields = {k: str(v) for k, v in fields_raw.items()}
        return {"text": text or content, "fields": fields,
                "latency_s": t1 - t0, "model": self.paper_name,
                "raw": content}


MLLM_REGISTRY: List[Dict[str, str]] = [
    {"paper_name": "Qwen VL Plus", "model_id": "qwen/qwen2.5-vl-72b-instruct"},
    {"paper_name": "GPT-4o", "model_id": "openai/gpt-4o-2024-11-20"},
    {"paper_name": "GPT-5.2", "model_id": "openai/gpt-5.2"},
    {"paper_name": "Claude Sonnet 4", "model_id": "anthropic/claude-sonnet-4"},
    {"paper_name": "GPT-5.2 Pro", "model_id": "openai/gpt-5.2-pro"},
    {"paper_name": "Claude Sonnet 4.5", "model_id": "anthropic/claude-sonnet-4.5"},
]


def build_mllm_clients(api_key: str) -> List[OpenRouterMLLM]:
    return [OpenRouterMLLM(model_id=m["model_id"], paper_name=m["paper_name"],
                           api_key=api_key) for m in MLLM_REGISTRY]


if __name__ == "__main__":
    ds = Path(__file__).parent / "dataset" / "ground_truth.json"
    records = json.loads(ds.read_text(encoding="utf-8"))
    rec = records[0]
    img = Path(__file__).parent / Path(rec["image_path"])
    res = TesseractOCR().predict(str(img), rec["doc_type"])
    print(json.dumps({"text_len": len(res["text"]),
                      "fields": res["fields"],
                      "latency_s": round(res["latency_s"], 3)}, indent=2,
                     ensure_ascii=False))
