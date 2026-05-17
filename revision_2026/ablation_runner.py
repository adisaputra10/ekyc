"""Ablation runner for the eKYC revision experiment.

Tiers evaluated:
  T0 - Tesseract baseline (no semantic reasoning)
  T1 - mLLM-OCR zero-shot (no schema hint, no retrieval)
  T2 - mLLM-OCR + schema-guided prompting (no retrieval)
  T3 - T2 + Dense kNN RAG
  T4 - T2 + Hybrid (BM25 + Dense, RRF) RAG
  T5 - T4 + MLOps regulatory adaptation (versioned KB applied at runtime)

Outputs:
  results/raw_predictions.jsonl   (every (model, tier, doc) prediction)
  results/per_doc_metrics.csv     (one row per prediction with metrics)
  results/summary.json            (means + bootstrap CIs per (model, tier))

Run with:
  python -m revision_2026.ablation_runner
"""
from __future__ import annotations
import argparse
import csv
import json
import os
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Any, List

import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from dotenv import load_dotenv
from metrics import evaluate, composite_accuracy
from models import (TesseractOCR, OpenRouterMLLM, MLLM_REGISTRY, SCHEMA_BY_TYPE,
                    build_mllm_clients)
from retrieval import (KnowledgeBase, index_kb, retrieve, select_active_version,
                       _es_client)


load_dotenv(HERE.parent / ".env")
API_KEY = os.getenv("key_open_ai")

DATASET_PATH = HERE / "dataset" / "ground_truth.json"
RESULTS_DIR = HERE / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
RAW_PATH = RESULTS_DIR / "raw_predictions.jsonl"
METRICS_PATH = RESULTS_DIR / "per_doc_metrics.csv"
SUMMARY_PATH = RESULTS_DIR / "summary.json"

TIERS = ["T0", "T1", "T2", "T3", "T4", "T5"]
TIER_DESCRIPTION = {
    "T0": "Tesseract baseline",
    "T1": "mLLM-OCR (zero-shot, no schema, no RAG)",
    "T2": "mLLM-OCR + schema-guided prompt",
    "T3": "mLLM-OCR + schema + Dense RAG",
    "T4": "mLLM-OCR + schema + Hybrid RAG (BM25+Dense)",
    "T5": "mLLM-OCR + schema + Hybrid RAG + MLOps regulatory update",
}


def _doc_query(rec: Dict[str, Any]) -> str:
    return f"{rec['doc_type']} document " + " ".join(SCHEMA_BY_TYPE.get(rec['doc_type'], []))


def _run_tier(tier: str, mllm: OpenRouterMLLM, rec: Dict[str, Any],
              es, kb_default: KnowledgeBase,
              kb_updated: KnowledgeBase) -> Dict[str, Any]:
    image_path = str(HERE / rec["image_path"])
    doc_type = rec["doc_type"]
    schema = SCHEMA_BY_TYPE.get(doc_type)
    ctx: List[Dict[str, Any]] = []
    if tier == "T1":
        # zero-shot: no schema, no retrieval
        return mllm.predict(image_path, doc_type, retrieval_context=None,
                            schema_hint=None)
    if tier == "T2":
        return mllm.predict(image_path, doc_type, retrieval_context=None,
                            schema_hint=schema)
    if tier == "T3":
        # ensure baseline KB indexed
        ctx = retrieve(es, _doc_query(rec), mode="dense", k=3)
        return mllm.predict(image_path, doc_type, retrieval_context=ctx,
                            schema_hint=schema)
    if tier == "T4":
        ctx = retrieve(es, _doc_query(rec), mode="hybrid", k=3)
        return mllm.predict(image_path, doc_type, retrieval_context=ctx,
                            schema_hint=schema)
    if tier == "T5":
        # active-version filter over hybrid retrieval
        ctx = retrieve(es, _doc_query(rec), mode="hybrid", k=4)
        ctx = select_active_version(ctx)
        return mllm.predict(image_path, doc_type, retrieval_context=ctx,
                            schema_hint=schema)
    raise ValueError(f"Unknown tier: {tier}")


def _bootstrap_ci(values: List[float], n_boot: int = 2000, alpha: float = 0.05
                  ) -> Dict[str, float]:
    if not values:
        return {"mean": 0.0, "ci_low": 0.0, "ci_high": 0.0}
    arr = np.asarray(values, dtype=np.float64)
    rng = np.random.default_rng(123)
    means = []
    for _ in range(n_boot):
        sample = rng.choice(arr, size=len(arr), replace=True)
        means.append(sample.mean())
    low = float(np.quantile(means, alpha / 2))
    high = float(np.quantile(means, 1 - alpha / 2))
    return {"mean": float(arr.mean()), "ci_low": low, "ci_high": high}


def main(per_type_limit: int | None = None, models_filter: List[str] | None = None,
         tiers_filter: List[str] | None = None) -> None:
    records = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    if per_type_limit:
        by_type: Dict[str, List[Dict[str, Any]]] = {}
        for r in records:
            by_type.setdefault(r["doc_type"], []).append(r)
        records = []
        for k, lst in by_type.items():
            records.extend(lst[:per_type_limit])
    print(f"Dataset size: {len(records)} documents")

    # Knowledge base & ES
    kb_default = KnowledgeBase.default()
    kb_updated = kb_default.apply_regulatory_update()
    es = index_kb(kb_updated)  # index BOTH versions so MLOps tier sees v2
    print(f"Indexed {len(kb_updated.entries)} KB entries (with v2 update)")

    tesseract = TesseractOCR()
    mllms = build_mllm_clients(API_KEY)
    if models_filter:
        mllms = [m for m in mllms if m.paper_name in models_filter]
    tiers = tiers_filter or TIERS
    print(f"Models under test: {[m.paper_name for m in mllms]}")
    print(f"Tiers: {tiers}")

    raw_fh = RAW_PATH.open("w", encoding="utf-8")
    csv_fh = METRICS_PATH.open("w", encoding="utf-8", newline="")
    writer = csv.DictWriter(csv_fh, fieldnames=[
        "doc_id", "doc_type", "variant", "model", "tier",
        "cer", "wer", "precision", "recall", "f1", "layout", "accuracy", "latency_s"
    ])
    writer.writeheader()

    bucket: Dict[tuple, List[Dict[str, float]]] = {}

    # T0 = Tesseract over all documents
    if "T0" in tiers:
        for rec in records:
            pred = tesseract.predict(str(HERE / rec["image_path"]),
                                     rec["doc_type"])
            ev = evaluate(pred, rec)
            raw_fh.write(json.dumps({"tier": "T0", "model": "Tesseract",
                                     "doc_id": rec["id"], "pred": pred,
                                     "metrics": ev}, ensure_ascii=False) + "\n")
            writer.writerow({"doc_id": rec["id"], "doc_type": rec["doc_type"],
                              "variant": rec["variant"], "model": "Tesseract",
                              "tier": "T0", **ev})
            bucket.setdefault(("Tesseract", "T0"), []).append(ev)

    # T1..T5 over each mLLM (parallelize per-document within a tier)
    mllm_tiers = [t for t in tiers if t != "T0"]
    for mllm in mllms:
        for tier in mllm_tiers:
            print(f"  Running {mllm.paper_name} / {tier}...", flush=True)
            t_start = time.perf_counter()
            preds_by_doc: Dict[str, Dict[str, Any]] = {}
            with ThreadPoolExecutor(max_workers=4) as ex:
                futures = {ex.submit(_run_tier, tier, mllm, rec, es,
                                     kb_default, kb_updated): rec for rec in records}
                for fut in as_completed(futures):
                    rec = futures[fut]
                    try:
                        pred = fut.result()
                    except Exception as exc:  # noqa: BLE001
                        pred = {"text": "", "fields": {}, "latency_s": 0.0,
                                "model": mllm.paper_name, "error": str(exc)}
                    preds_by_doc[rec["id"]] = pred
            for rec in records:
                pred = preds_by_doc[rec["id"]]
                ev = evaluate(pred, rec)
                raw_fh.write(json.dumps({"tier": tier, "model": mllm.paper_name,
                                         "doc_id": rec["id"], "pred": {k: pred.get(k) for k in ("text","fields","latency_s","error")},
                                         "metrics": ev}, ensure_ascii=False) + "\n")
                writer.writerow({"doc_id": rec["id"], "doc_type": rec["doc_type"],
                                  "variant": rec["variant"], "model": mllm.paper_name,
                                  "tier": tier, **ev})
                bucket.setdefault((mllm.paper_name, tier), []).append(ev)
            elapsed = time.perf_counter() - t_start
            ev_list = bucket[(mllm.paper_name, tier)]
            acc = statistics.mean(e["accuracy"] for e in ev_list)
            f1 = statistics.mean(e["f1"] for e in ev_list)
            print(f"    -> acc={acc*100:.2f}% f1={f1*100:.2f}% "
                  f"({elapsed:.1f}s for {len(ev_list)} docs)")

    raw_fh.close()
    csv_fh.close()

    summary: Dict[str, Any] = {}
    for (model, tier), evs in bucket.items():
        summary.setdefault(model, {})[tier] = {
            "n": len(evs),
            "accuracy": _bootstrap_ci([e["accuracy"] for e in evs]),
            "cer": _bootstrap_ci([e["cer"] for e in evs]),
            "wer": _bootstrap_ci([e["wer"] for e in evs]),
            "precision": _bootstrap_ci([e["precision"] for e in evs]),
            "recall": _bootstrap_ci([e["recall"] for e in evs]),
            "f1": _bootstrap_ci([e["f1"] for e in evs]),
            "layout": _bootstrap_ci([e["layout"] for e in evs]),
            "latency_s": _bootstrap_ci([e["latency_s"] for e in evs]),
        }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nSaved raw -> {RAW_PATH}")
    print(f"Saved CSV -> {METRICS_PATH}")
    print(f"Saved summary -> {SUMMARY_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-type", type=int, default=None,
                        help="Limit docs per type (smoke test)")
    parser.add_argument("--models", nargs="*", default=None,
                        help="Subset of paper_name models to run")
    parser.add_argument("--tiers", nargs="*", default=None,
                        help="Subset of tiers to run")
    args = parser.parse_args()
    main(per_type_limit=args.per_type, models_filter=args.models,
         tiers_filter=args.tiers)
