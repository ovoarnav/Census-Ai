from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow running as a script from repo root
if str(Path(__file__).resolve().parents[2]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from typing import Dict, Iterable, List

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


def _safe_equal(a: object, b: object) -> bool:
    return str(a).strip().lower() == str(b).strip().lower()


def _iter_field_pairs(gold: dict, pred: dict, excluded: Iterable[str]) -> Iterable[tuple[str, object, object]]:
    excluded_set = set(excluded)
    for field, gold_value in gold.items():
        if field in excluded_set:
            continue
        if field not in pred:
            continue
        yield field, gold_value, pred[field]


def evaluate_extractions() -> Dict[str, float]:
    gold_path = _resolve_label_path("gold_extractions.jsonl")
    if gold_path is None:
        print("Friendly exit: gold_extractions.jsonl not found. Copy labels into data/labels or censusflow_synthetic_data_v2/data/labels.")
        return {}

    gold_rows = _read_jsonl(gold_path)
    if not gold_rows:
        print("Friendly exit: gold_extractions.jsonl is empty.")
        return {}

    total_fields = 0
    exact_match_count = 0
    null_match_total = 0
    null_match_count = 0
    rows_skipped = 0

    has_gold_pred = any(
        isinstance(row.get("gold"), dict) and isinstance(row.get("pred"), dict)
        for row in gold_rows
    )
    has_flat_pred = any(isinstance(row.get("prediction"), dict) for row in gold_rows)
    if has_gold_pred:
        schema_mode = "gold+pred"
    elif has_flat_pred:
        schema_mode = "row+prediction"
    else:
        schema_mode = "unknown"

    print(f"Detected input schema mode: {schema_mode}")

    for row in gold_rows:
        gold = row.get("gold", row)
        pred = row.get("pred", row.get("prediction", {}))

        if not isinstance(gold, dict) or not isinstance(pred, dict):
            rows_skipped += 1
            continue

        for _, gold_value, pred_value in _iter_field_pairs(gold, pred, excluded=["referral_id", "evidence_spans"]):
            total_fields += 1
            if _safe_equal(gold_value, pred_value):
                exact_match_count += 1

            gold_is_null = gold_value in (None, "", [], {})
            pred_is_null = pred_value in (None, "", [], {})
            if gold_is_null:
                null_match_total += 1
                if pred_is_null:
                    null_match_count += 1

    evidence_path = _resolve_label_path("evidence_labels.jsonl")
    evidence_verification_rate = 0.0
    if evidence_path is not None:
        evidence_rows = _read_jsonl(evidence_path)
        if evidence_rows:
            verified = sum(1 for r in evidence_rows if r.get("quote_verified") is True)
            evidence_verification_rate = verified / len(evidence_rows)

    metrics = {
        "field_exact_match_rate": (exact_match_count / total_fields) if total_fields else 0.0,
        "field_missing_null_accuracy": (null_match_count / null_match_total) if null_match_total else 0.0,
        "evidence_quote_verification_rate": evidence_verification_rate,
    }

    print("Extraction evaluation metrics")
    print(f"- rows skipped due to schema mismatch: {rows_skipped}")
    print(f"- field_exact_match_rate: {metrics['field_exact_match_rate']:.3f}")
    print(f"- field_missing_null_accuracy: {metrics['field_missing_null_accuracy']:.3f}")
    print(f"- evidence_quote_verification_rate: {metrics['evidence_quote_verification_rate']:.3f}")

    return metrics


if __name__ == "__main__":
    evaluate_extractions()
