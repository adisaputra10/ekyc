"""Retry only the failed model/tier combinations and merge with existing results.

GPT-5.2 Pro:    T2-T5 failed (T1 = 96.17% OK)
Claude Sonnet 4.5: T1-T5 all failed

Strategy:
 1. Run only the failed combos, write to a TEMP jsonl.
 2. Combine old raw_predictions.jsonl (drop the failed rows) + new rows.
 3. Rebuild per_doc_metrics.csv and summary.json from the combined set.
 4. Re-run statistics_analysis.py and update_docx.py automatically.

Usage:
  python revision_2026/retry_failed.py
"""
from __future__ import annotations
import csv
import json
import os
import statistics
import subprocess
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
from metrics import evaluate
from models import OpenRouterMLLM, MLLM_REGISTRY, SCHEMA_BY_TYPE, build_mllm_clients
from retrieval import (KnowledgeBase, index_kb, retrieve,
                       select_active_version, _es_client)

load_dotenv(HERE.parent / ".env")
API_KEY = os.getenv("key_open_ai")

DATASET_PATH = HERE / "dataset" / "ground_truth.json"
RESULTS_DIR = HERE / "results"
RAW_PATH = RESULTS_DIR / "raw_predictions.jsonl"
METRICS_PATH = RESULTS_DIR / "per_doc_metrics.csv"
SUMMARY_PATH = RESULTS_DIR / "summary.json"

# --- Which combos to retry --------------------------------------------------
RETRY = {
    "GPT-5.2 Pro": ["T5"],   # T1-T4 already good
    "Claude Sonnet 4.5": ["T1", "T2", "T3", "T4", "T5"],
}
# ----------------------------------------------------------------------------


def _doc_query(rec: Dict[str, Any]) -> str:
    return f"{rec['doc_type']} document " + " ".join(
        SCHEMA_BY_TYPE.get(rec["doc_type"], []))


def _run_tier(tier: str, mllm: OpenRouterMLLM, rec: Dict[str, Any],
              es, kb_default: KnowledgeBase,
              kb_updated: KnowledgeBase) -> Dict[str, Any]:
    image_path = str(HERE / rec["image_path"])
    doc_type = rec["doc_type"]
    schema = SCHEMA_BY_TYPE.get(doc_type)
    if tier == "T1":
        return mllm.predict(image_path, doc_type, retrieval_context=None,
                            schema_hint=None)
    if tier == "T2":
        return mllm.predict(image_path, doc_type, retrieval_context=None,
                            schema_hint=schema)
    if tier == "T3":
        ctx = retrieve(es, _doc_query(rec), mode="dense", k=3)
        return mllm.predict(image_path, doc_type, retrieval_context=ctx,
                            schema_hint=schema)
    if tier == "T4":
        ctx = retrieve(es, _doc_query(rec), mode="hybrid", k=3)
        return mllm.predict(image_path, doc_type, retrieval_context=ctx,
                            schema_hint=schema)
    if tier == "T5":
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
    means = [rng.choice(arr, size=len(arr), replace=True).mean()
             for _ in range(n_boot)]
    return {"mean": float(arr.mean()),
            "ci_low": float(np.quantile(means, alpha / 2)),
            "ci_high": float(np.quantile(means, 1 - alpha / 2))}


def main() -> None:
    records = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    print(f"Dataset size: {len(records)} documents")

    kb_default = KnowledgeBase.default()
    kb_updated = kb_default.apply_regulatory_update()
    es = index_kb(kb_updated)
    print(f"Indexed {len(kb_updated.entries)} KB entries (with v2 update)")

    all_mllms = {m.paper_name: m for m in build_mllm_clients(API_KEY)}

    # --- Run only the failed combos -----------------------------------------
    new_rows: List[Dict[str, Any]] = []  # raw jsonl rows
    for model_name, tiers in RETRY.items():
        mllm = all_mllms[model_name]
        for tier in tiers:
            print(f"  Running {model_name} / {tier}...", flush=True)
            t_start = time.perf_counter()
            preds_by_doc: Dict[str, Dict[str, Any]] = {}
            with ThreadPoolExecutor(max_workers=4) as ex:
                futures = {ex.submit(_run_tier, tier, mllm, rec, es,
                                     kb_default, kb_updated): rec
                           for rec in records}
                for fut in as_completed(futures):
                    rec = futures[fut]
                    try:
                        pred = fut.result()
                    except Exception as exc:  # noqa: BLE001
                        pred = {"text": "", "fields": {}, "latency_s": 0.0,
                                "error": str(exc)}
                    preds_by_doc[rec["id"]] = pred
            elapsed = time.perf_counter() - t_start
            tier_evs = []
            for rec in records:
                pred = preds_by_doc[rec["id"]]
                ev = evaluate(pred, rec)
                row = {"tier": tier, "model": model_name, "doc_id": rec["id"],
                       "doc_type": rec["doc_type"], "variant": rec["variant"],
                       "pred": {k: pred.get(k)
                                for k in ("text", "fields", "latency_s", "error")},
                       "metrics": ev}
                new_rows.append(row)
                tier_evs.append(ev)
            acc = statistics.mean(e["accuracy"] for e in tier_evs)
            f1 = statistics.mean(e["f1"] for e in tier_evs)
            print(f"    -> acc={acc*100:.2f}% f1={f1*100:.2f}% "
                  f"({elapsed:.1f}s for {len(tier_evs)} docs)")

    # --- Merge with existing results ----------------------------------------
    print("\nMerging with existing results...")
    existing_rows: List[Dict[str, Any]] = []
    failed_keys = {(m, t) for m, tiers in RETRY.items() for t in tiers}
    with RAW_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if (r["model"], r["tier"]) in failed_keys:
                continue  # drop old failed rows
            existing_rows.append(r)

    combined = existing_rows + new_rows

    # Write merged raw JSONL
    with RAW_PATH.open("w", encoding="utf-8") as f:
        for r in combined:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Combined JSONL: {len(combined)} rows -> {RAW_PATH}")

    # Rebuild CSV and summary
    bucket: Dict[tuple, List[Dict[str, float]]] = {}
    csv_field_names = ["doc_id", "doc_type", "variant", "model", "tier",
                       "cer", "wer", "precision", "recall", "f1", "layout",
                       "accuracy", "latency_s"]
    with METRICS_PATH.open("w", encoding="utf-8", newline="") as csvf:
        writer = csv.DictWriter(csvf, fieldnames=csv_field_names)
        writer.writeheader()
        for r in combined:
            ev = r.get("metrics", {})
            # normalise: old rows have flat metrics, new rows have 'metrics' key
            writer.writerow({
                "doc_id": r.get("doc_id"),
                "doc_type": r.get("doc_type", ""),
                "variant": r.get("variant", ""),
                "model": r["model"],
                "tier": r["tier"],
                **{k: ev.get(k, 0.0) for k in
                   ("cer", "wer", "precision", "recall",
                    "f1", "layout", "accuracy", "latency_s")},
            })
            bucket.setdefault((r["model"], r["tier"]), []).append(ev)

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
    print(f"Saved summary -> {SUMMARY_PATH}")
    print(f"Saved CSV -> {METRICS_PATH}")

    # --- Re-run downstream analysis ----------------------------------------
    print("\nRunning statistics_analysis.py...")
    subprocess.run([sys.executable, str(HERE / "statistics_analysis.py")], check=True)
    print("Running update_docx.py...")
    subprocess.run([sys.executable, str(HERE / "update_docx.py")], check=True)
    print("\nAll done! Revised manuscript saved.")


if __name__ == "__main__":
    main()
