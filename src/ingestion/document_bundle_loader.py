from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List

from src.config import DATA_DIR, PROJECT_ROOT, REFERRAL_PACKET_DIR
from src.ingestion.models import ReferralDocumentBundle, SourceDocument


V2_DATASET_ROOT = PROJECT_ROOT / "censusflow_synthetic_data_v2"


def _bundle_directories() -> List[Path]:
    return [
        DATA_DIR / "referrals" / "document_bundles",
        V2_DATASET_ROOT / "data" / "referrals" / "document_bundles",
    ]


def _text_packet_directories() -> List[Path]:
    return [
        REFERRAL_PACKET_DIR,
        V2_DATASET_ROOT / "data" / "referrals" / "text_packets",
    ]


def _iter_referral_ids_from_paths(paths: Iterable[Path], suffix: str) -> List[str]:
    referral_ids = set()
    for base in paths:
        if not base.exists():
            continue
        for path in base.glob(f"REF-*{suffix}"):
            referral_ids.add(path.stem)
    return sorted(referral_ids)


def list_available_referral_ids() -> List[str]:
    bundle_dirs = _bundle_directories()
    if any(path.exists() for path in bundle_dirs):
        bundle_ids = _iter_referral_ids_from_paths(bundle_dirs, ".json")
        if bundle_ids:
            return bundle_ids

    return _iter_referral_ids_from_paths(_text_packet_directories(), ".txt")


def _find_existing_path(candidates: Iterable[Path]) -> Path | None:
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _load_json_bundle(path: Path) -> ReferralDocumentBundle:
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    return ReferralDocumentBundle.model_validate(payload)


def _wrap_text_packet(path: Path, referral_id: str) -> ReferralDocumentBundle:
    text = path.read_text(encoding="utf-8")
    synthetic_doc = SourceDocument(
        source_doc_id=f"{referral_id}-txt-1",
        document_type="text_packet",
        source_name=path.name,
        text=text,
    )
    return ReferralDocumentBundle(
        referral_id=referral_id,
        source_documents=[synthetic_doc],
        metadata={"legacy_text_packet": True},
    )


def load_referral_document_bundle(referral_id: str) -> ReferralDocumentBundle:
    json_path = _find_existing_path(
        [base / f"{referral_id}.json" for base in _bundle_directories()]
    )
    if json_path is not None:
        return _load_json_bundle(json_path)

    txt_path = _find_existing_path(
        [base / f"{referral_id}.txt" for base in _text_packet_directories()]
    )
    if txt_path is not None:
        return _wrap_text_packet(txt_path, referral_id)

    searched_paths = [
        *[base / f"{referral_id}.json" for base in _bundle_directories()],
        *[base / f"{referral_id}.txt" for base in _text_packet_directories()],
    ]
    raise FileNotFoundError(
        "Referral not found in bundle or text packet paths: "
        + ", ".join(str(path) for path in searched_paths)
    )
