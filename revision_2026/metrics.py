"""Metrics for the eKYC ablation study.

Implements:
  - CER / WER : character / word error rate vs ground truth text
  - Entity Precision / Recall / F1 : on the structured fields
  - Layout score : line-level structural preservation (longest common
    subsequence of non-empty lines, normalised)
  - Accuracy score : composite weighted score used in the paper

All metrics return values in [0, 1]; the paper reports percentages.
"""
from __future__ import annotations
import re
from difflib import SequenceMatcher
from typing import Dict, Any, List, Tuple


_WS = re.compile(r"\s+")


def _norm(s: str) -> str:
    return _WS.sub(" ", s).strip().lower()


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if len(a) < len(b):
        a, b = b, a
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            curr[j] = min(curr[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost)
        prev = curr
    return prev[-1]


def char_error_rate(pred: str, ref: str) -> float:
    ref_n = _norm(ref)
    pred_n = _norm(pred)
    if not ref_n:
        return 0.0
    return min(1.0, _levenshtein(pred_n, ref_n) / len(ref_n))


def word_error_rate(pred: str, ref: str) -> float:
    ref_w = _norm(ref).split()
    pred_w = _norm(pred).split()
    if not ref_w:
        return 0.0
    # token-level edit distance
    n, m = len(ref_w), len(pred_w)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if ref_w[i - 1] == pred_w[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)
    return min(1.0, dp[n][m] / n)


def _value_match(pred: str, gt: str) -> bool:
    if pred is None or gt is None:
        return False
    return _norm(str(pred)) == _norm(str(gt))


def entity_prf(pred_fields: Dict[str, Any], gt_fields: Dict[str, Any]
               ) -> Tuple[float, float, float]:
    """Compute precision, recall, F1 over ground-truth field set."""
    expected = set(gt_fields.keys())
    correct = 0
    pred_count = 0
    for k, v in (pred_fields or {}).items():
        if v in (None, ""):
            continue
        pred_count += 1
        if k in gt_fields and _value_match(v, gt_fields[k]):
            correct += 1
    precision = correct / pred_count if pred_count else 0.0
    recall = correct / len(expected) if expected else 0.0
    f1 = (2 * precision * recall / (precision + recall)
          if (precision + recall) else 0.0)
    return precision, recall, f1


def layout_score(pred_text: str, ref_text: str) -> float:
    """Longest-common-subsequence based line preservation score in [0,1]."""
    ref_lines = [ln.strip() for ln in ref_text.splitlines() if ln.strip()]
    pred_lines = [ln.strip() for ln in pred_text.splitlines() if ln.strip()]
    if not ref_lines:
        return 0.0
    # match lines whose similarity > 0.6 in order
    matcher = SequenceMatcher(
        a=[_norm(x) for x in ref_lines],
        b=[_norm(x) for x in pred_lines],
        autojunk=False,
    )
    lcs = sum(block.size for block in matcher.get_matching_blocks())
    return min(1.0, lcs / len(ref_lines))


def composite_accuracy(cer: float, f1: float, layout: float) -> float:
    """Weighted accuracy composite used in the paper's main result table.

    Weights: 0.4 character-level (1-CER), 0.4 entity F1, 0.2 layout.
    """
    return 0.4 * (1 - cer) + 0.4 * f1 + 0.2 * layout


def evaluate(pred: Dict[str, Any], gt: Dict[str, Any]) -> Dict[str, float]:
    pred_text = pred.get("text", "") or ""
    pred_fields = pred.get("fields", {}) or {}
    gt_text = gt.get("ground_truth_text", "")
    gt_fields = gt.get("ground_truth_fields", {})
    cer = char_error_rate(pred_text, gt_text)
    wer = word_error_rate(pred_text, gt_text)
    p, r, f1 = entity_prf(pred_fields, gt_fields)
    layout = layout_score(pred_text, gt_text)
    acc = composite_accuracy(cer, f1, layout)
    return {
        "cer": cer, "wer": wer,
        "precision": p, "recall": r, "f1": f1,
        "layout": layout, "accuracy": acc,
        "latency_s": float(pred.get("latency_s", 0.0)),
    }
