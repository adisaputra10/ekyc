"""Statistical analysis for the eKYC ablation results.

Reads per_doc_metrics.csv produced by ablation_runner.py and computes:
  - Per (model, tier) means + 95% bootstrap CIs (already in summary.json)
  - Paired t-test  : Tesseract vs each (model, tier=T4 full RAG)
  - Wilcoxon signed-rank: same pairs (non-parametric)
  - Cohen's d     : effect size
  - Tier-vs-tier paired tests on the best model: T1->T2->T3->T4->T5

Output:
  results/statistics.json
  results/ablation_table.md  (markdown table ready for the docx)
"""
from __future__ import annotations
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent
METRICS_PATH = HERE / "results" / "per_doc_metrics.csv"
SUMMARY_PATH = HERE / "results" / "summary.json"
STATS_PATH = HERE / "results" / "statistics.json"
TABLE_PATH = HERE / "results" / "ablation_table.md"


def _load() -> Dict[Tuple[str, str], Dict[str, List[float]]]:
    out: Dict[Tuple[str, str], Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
    with METRICS_PATH.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (row["model"], row["tier"])
            for m in ("cer", "wer", "precision", "recall", "f1", "layout",
                     "accuracy", "latency_s"):
                out[key][m].append(float(row[m]))
            out[key]["doc_id"].append(row["doc_id"])
    return out


def _cohens_d(a: List[float], b: List[float]) -> float:
    a_arr = np.asarray(a, dtype=np.float64)
    b_arr = np.asarray(b, dtype=np.float64)
    diff = a_arr - b_arr
    sd = float(np.std(diff, ddof=1)) if len(diff) > 1 else 0.0
    if sd == 0:
        return 0.0
    return float(np.mean(diff) / sd)


def _paired_tests(treat: List[float], control: List[float]) -> Dict[str, float]:
    if len(treat) != len(control) or len(treat) < 2:
        return {"t_stat": None, "t_p": None, "w_stat": None, "w_p": None,
                "cohens_d": None, "n": len(treat), "zero_diff": False}
    diffs = np.asarray(treat, dtype=np.float64) - np.asarray(control, dtype=np.float64)
    # When all differences are zero the statistics are trivially p=1.0 (no effect)
    if np.all(diffs == 0):
        return {"t_stat": 0.0, "t_p": 1.0, "w_stat": 0.0, "w_p": 1.0,
                "cohens_d": 0.0, "n": len(treat), "zero_diff": True}
    t_stat, t_p = stats.ttest_rel(treat, control)
    try:
        w_stat, w_p = stats.wilcoxon(treat, control, zero_method="zsplit")
    except Exception:
        w_stat, w_p = float("nan"), float("nan")
    return {
        "t_stat": float(t_stat), "t_p": float(t_p),
        "w_stat": float(w_stat), "w_p": float(w_p),
        "cohens_d": _cohens_d(treat, control),
        "n": len(treat), "zero_diff": False,
    }


def main() -> None:
    data = _load()
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    keys = sorted(data.keys())
    models_with_t0 = [m for m, t in keys if t == "T0"]
    out: Dict[str, object] = {"pairwise_vs_tesseract": {}, "tier_progression": {},
                              "summary_table": {}}

    # 1) For each mLLM at its strongest tier (T4 hybrid), compare to Tesseract T0
    tess_acc = data[("Tesseract", "T0")]["accuracy"]
    tess_f1 = data[("Tesseract", "T0")]["f1"]
    tess_cer = data[("Tesseract", "T0")]["cer"]
    for (model, tier), vals in data.items():
        if model == "Tesseract":
            continue
        pair_key = f"{model} ({tier}) vs Tesseract (T0)"
        out["pairwise_vs_tesseract"][pair_key] = {
            "accuracy": _paired_tests(vals["accuracy"], tess_acc),
            "f1": _paired_tests(vals["f1"], tess_f1),
            "cer_lower_is_better": _paired_tests(tess_cer, vals["cer"]),
        }

    # 2) Tier progression: within each model, compare each tier to previous
    by_model: Dict[str, List[str]] = defaultdict(list)
    for (m, t) in keys:
        if m == "Tesseract":
            continue
        by_model[m].append(t)
    for m, tiers in by_model.items():
        tiers_sorted = sorted(set(tiers))
        prog: Dict[str, object] = {}
        for i in range(1, len(tiers_sorted)):
            t_curr, t_prev = tiers_sorted[i], tiers_sorted[i - 1]
            prog[f"{t_curr} vs {t_prev}"] = {
                "accuracy": _paired_tests(data[(m, t_curr)]["accuracy"],
                                          data[(m, t_prev)]["accuracy"]),
                "f1": _paired_tests(data[(m, t_curr)]["f1"],
                                    data[(m, t_prev)]["f1"]),
            }
        out["tier_progression"][m] = prog

    # 3) Compact summary table (mean ± CI for headline metrics)
    for (model, tier), vals in data.items():
        s = summary.get(model, {}).get(tier, {})
        out["summary_table"][f"{model} / {tier}"] = {
            "accuracy_mean": s.get("accuracy", {}).get("mean"),
            "accuracy_ci": [s.get("accuracy", {}).get("ci_low"),
                            s.get("accuracy", {}).get("ci_high")],
            "f1_mean": s.get("f1", {}).get("mean"),
            "f1_ci": [s.get("f1", {}).get("ci_low"),
                      s.get("f1", {}).get("ci_high")],
            "cer_mean": s.get("cer", {}).get("mean"),
            "wer_mean": s.get("wer", {}).get("mean"),
            "layout_mean": s.get("layout", {}).get("mean"),
            "latency_mean_s": s.get("latency_s", {}).get("mean"),
            "n": s.get("n"),
        }

    STATS_PATH.write_text(json.dumps(out, indent=2), encoding="utf-8")

    # --- Markdown ablation table ---
    md = ["# Ablation Results", ""]
    md.append("## A. Ablation by Tier (mean ± 95% CI, accuracy %)\n")
    md.append("| Model | T0 Tesseract | T1 mLLM zero | T2 +schema | T3 +Dense RAG | T4 +Hybrid RAG | T5 +MLOps |")
    md.append("|---|---|---|---|---|---|---|")
    mllm_models = [m for m in sorted({k[0] for k in keys}) if m != "Tesseract"]
    tess_ci = summary.get("Tesseract", {}).get("T0", {}).get("accuracy", {})
    tess_cell = f'{(tess_ci.get("mean") or 0)*100:.2f} [{(tess_ci.get("ci_low") or 0)*100:.2f}, {(tess_ci.get("ci_high") or 0)*100:.2f}]'
    for m in mllm_models:
        row = [m, tess_cell]
        for t in ("T1", "T2", "T3", "T4", "T5"):
            s = summary.get(m, {}).get(t, {}).get("accuracy", {})
            if not s:
                row.append("-")
            else:
                row.append(f'{(s["mean"])*100:.2f} [{(s["ci_low"])*100:.2f}, {(s["ci_high"])*100:.2f}]')
        md.append("| " + " | ".join(row) + " |")

    md.append("\n## B. Pairwise: each mLLM (best tier T4) vs Tesseract (T0)\n")
    md.append("| Model | Δ Accuracy (pp) | paired-t p | Wilcoxon p | Cohen's d |")
    md.append("|---|---|---|---|---|")
    for m in mllm_models:
        key = f"{m} (T4) vs Tesseract (T0)"
        test = out["pairwise_vs_tesseract"].get(key, {}).get("accuracy", {})
        if not test:
            continue
        treat_mean = summary[m].get("T4", {}).get("accuracy", {}).get("mean")
        if treat_mean is None:
            continue  # model had no T4 data (e.g. still incomplete)
        delta = (treat_mean - tess_ci.get("mean", 0)) * 100
        def _fmt(p):
            if p is None or (isinstance(p, float) and math.isnan(p)):
                return "n/a"
            return f"{p:.2e}" if p < 0.001 else f"{p:.4f}"
        md.append(f"| {m} | +{delta:.2f} | {_fmt(test.get('t_p'))} | "
                  f"{_fmt(test.get('w_p'))} | {test.get('cohens_d', 0):.3f} |")

    md.append("\n## C. Tier-progression significance (Δaccuracy per added component)\n")
    md.append("| Model | T2 vs T1 (schema) | T3 vs T2 (Dense) | T4 vs T3 (Hybrid) | T5 vs T4 (MLOps) |")
    md.append("|---|---|---|---|---|")
    for m in mllm_models:
        prog = out["tier_progression"].get(m, {})
        cells = []
        for pair in ("T2 vs T1", "T3 vs T2", "T4 vs T3", "T5 vs T4"):
            t = prog.get(pair, {}).get("accuracy", {})
            p = t.get("t_p")
            d = t.get("cohens_d")
            if p is None:
                cells.append("-")
                continue
            if t.get("zero_diff"):
                cells.append("Δ=0 (n.s.)")
                continue
            p_str = (f"{p:.2e}" if p < 0.001 else f"{p:.4f}") if not math.isnan(p) else "n/a"
            cells.append(f"p={p_str}, d={d:.2f}")
        md.append(f"| {m} | " + " | ".join(cells) + " |")

    TABLE_PATH.write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote {STATS_PATH}")
    print(f"Wrote {TABLE_PATH}")


if __name__ == "__main__":
    main()
