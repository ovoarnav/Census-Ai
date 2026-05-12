from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

# Allow running as a script from repo root
if str(Path(__file__).resolve().parents[2]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from typing import Dict, List, Tuple

from src.config import DATA_DIR, PROJECT_ROOT

V2_LABELS_DIR = PROJECT_ROOT / "censusflow_synthetic_data_v2" / "data" / "labels"


def _candidate_label_paths(filename: str) -> List[Path]:
    return [
        DATA_DIR / "labels" / filename,
        V2_LABELS_DIR / filename,
    ]


def _resolve_label_path(filename: str) -> Path | None:
    for path in _candidate_label_paths(filename):
        if path.exists():
            return path
    return None


def _read_jsonl(path: Path) -> List[dict]:
    rows: List[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _precision_recall_f1(tp: int, fp: int, fn: int) -> Tuple[float, float, float]:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return precision, recall, f1


def evaluate_mismatches() -> Dict[str, dict]:
    mismatch_path = _resolve_label_path("mismatch_labels.jsonl")
    if mismatch_path is None:
        print("Friendly exit: mismatch_labels.jsonl not found. Copy labels into data/labels or censusflow_synthetic_data_v2/data/labels.")
        return {}

    rows = _read_jsonl(mismatch_path)
    if not rows:
        print("Friendly exit: mismatch_labels.jsonl is empty.")
        return {}

    per_type = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})

    high_severity_expected = 0
    high_severity_detected = 0
    rows_skipped = 0

    has_expected_predicted = any(
        isinstance(row.get("expected_mismatches"), list)
        and isinstance(row.get("predicted_mismatches"), list)
        for row in rows
    )
    has_gold_pred = any(
        isinstance(row.get("gold"), list) and isinstance(row.get("pred"), list)
        for row in rows
    )
    if has_expected_predicted:
        schema_mode = "expected_mismatches+predicted_mismatches"
    elif has_gold_pred:
        schema_mode = "gold+pred"
    else:
        schema_mode = "unknown"

    print(f"Detected input schema mode: {schema_mode}")

    for row in rows:
        expected = row.get("expected_mismatches", row.get("gold"))
        predicted = row.get("predicted_mismatches", row.get("pred"))

        if not isinstance(expected, list) or not isinstance(predicted, list):
            rows_skipped += 1
            continue

        if not all(isinstance(e, dict) for e in expected) or not all(
            isinstance(p, dict) for p in predicted
        ):
            rows_skipped += 1
            continue

        exp_types = {e.get("mismatch_type") for e in expected if e.get("mismatch_type")}
        pred_types = {p.get("mismatch_type") for p in predicted if p.get("mismatch_type")}

        for t in exp_types & pred_types:
            per_type[t]["tp"] += 1
        for t in pred_types - exp_types:
            per_type[t]["fp"] += 1
        for t in exp_types - pred_types:
            per_type[t]["fn"] += 1

        for e in expected:
            if e.get("severity") in {"high", "critical"}:
                high_severity_expected += 1
                if e.get("mismatch_type") in pred_types:
                    high_severity_detected += 1

    metrics_by_type = {}
    for mismatch_type, counts in sorted(per_type.items()):
        p, r, f1 = _precision_recall_f1(counts["tp"], counts["fp"], counts["fn"])
        metrics_by_type[mismatch_type] = {
            **counts,
            "precision": p,
            "recall": r,
            "f1": f1,
        }

    high_severity_recall = (
        high_severity_detected / high_severity_expected if high_severity_expected else 0.0
    )

    print("Mismatch evaluation metrics")
    print(f"- rows skipped due to schema mismatch: {rows_skipped}")
    for mismatch_type, m in metrics_by_type.items():
        print(
            f"- {mismatch_type}: precision={m['precision']:.3f}, recall={m['recall']:.3f}, f1={m['f1']:.3f}"
        )
    print(f"- high_severity_mismatch_recall: {high_severity_recall:.3f}")

    return {
        "by_mismatch_type": metrics_by_type,
        "high_severity_mismatch_recall": high_severity_recall,
    }


if __name__ == "__main__":
    evaluate_mismatches()
