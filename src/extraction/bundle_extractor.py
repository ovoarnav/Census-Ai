from __future__ import annotations

import re
from typing import Literal, Pattern

from src.extraction.deterministic_extractor import extract_referral as extract_deterministic
from src.extraction.schema import ReferralExtract
from src.ingestion.models import EvidenceSpan, ReferralDocumentBundle, SourceDocument

BundleExtractionMode = Literal[
    "deterministic_text_packet",
    "heuristic_bundle",
    "llm_placeholder",
]


FIELD_PATTERNS: dict[str, Pattern[str]] = {
    "patient_initials": re.compile(r"Patient Initials:\s*(.*)", re.IGNORECASE),
    "payer": re.compile(r"Payer:\s*(.*)", re.IGNORECASE),
    "authorization_status": re.compile(r"Authorization Status:\s*(.*)", re.IGNORECASE),
    "primary_diagnosis": re.compile(
        r"Primary Diagnosis(?: / Reason for Referral)?:\s*(.*)", re.IGNORECASE
    ),
    "current_medications_or_mar": re.compile(
        r"(?:Current Medications / MAR Summary|MAR):\s*(.*)", re.IGNORECASE
    ),
    "allergies": re.compile(r"Allergies:\s*(.*)", re.IGNORECASE),
    "mobility_transfer_status": re.compile(r"Mobility / Transfer Status:\s*(.*)", re.IGNORECASE),
    "therapy_need": re.compile(r"Therapy Need:\s*(.*)", re.IGNORECASE),
    "oxygen_respiratory_needs": re.compile(r"Oxygen / Respiratory Needs:\s*(.*)", re.IGNORECASE),
    "dialysis_need": re.compile(r"Dialysis Need:\s*(.*)", re.IGNORECASE),
    "cognitive_status": re.compile(r"Cognitive Status:\s*(.*)", re.IGNORECASE),
    "behavioral_safety_concerns": re.compile(r"Behavioral / Safety Concerns:\s*(.*)", re.IGNORECASE),
    "infection_isolation_status": re.compile(r"Infection / Isolation Status:\s*(.*)", re.IGNORECASE),
    "durable_medical_equipment_needs": re.compile(
        r"Durable Medical Equipment Needs:\s*(.*)", re.IGNORECASE
    ),
}


def _normalized_bundle_text(bundle: ReferralDocumentBundle) -> str:
    parts = []
    for doc in bundle.source_documents:
        header = f"[DOC {doc.source_doc_id} | {doc.document_type or 'unknown'}]\n"
        parts.append(header + (doc.text or ""))
    return "\n\n".join(parts)


def _find_line_value(label_pattern: Pattern[str], text: str) -> str | None:
    match = label_pattern.search(text)
    if not match:
        return None
    value = match.group(1).strip()
    return value if value else None


def _extract_evidence_from_doc(
    field_name: str, pattern: Pattern[str], doc: SourceDocument
) -> EvidenceSpan | None:
    match = pattern.search(doc.text or "")
    if not match:
        return None
    quote = match.group(1).strip()
    if not quote:
        return None
    return EvidenceSpan(
        field_name=field_name,
        source_doc_id=doc.source_doc_id,
        quote=quote,
        char_start=match.start(1),
        char_end=match.end(1),
        quote_verified=False,
    )


def extract_referral_from_bundle(
    bundle: ReferralDocumentBundle,
    mode: BundleExtractionMode = "heuristic_bundle",
) -> ReferralExtract:
    if mode == "deterministic_text_packet":
        text = _normalized_bundle_text(bundle)
        extracted = extract_deterministic(text)
        extracted.source_document_ids = [doc.source_doc_id for doc in bundle.source_documents]
        return extracted

    if mode == "heuristic_bundle":
        all_text = _normalized_bundle_text(bundle)

        payload = {
            "referral_id": bundle.referral_id,
            "source": bundle.source,
            "channel": bundle.channel,
            "received_at": bundle.received_at,
            "target_facility_id": bundle.target_facility_id,
            "source_document_ids": [doc.source_doc_id for doc in bundle.source_documents],
        }

        evidence_spans: dict[str, list[EvidenceSpan]] = {}

        for field_name, pattern in FIELD_PATTERNS.items():
            value = _find_line_value(pattern, all_text)
            if value:
                payload[field_name] = value

            for doc in bundle.source_documents:
                span = _extract_evidence_from_doc(field_name, pattern, doc)
                if span:
                    evidence_spans.setdefault(field_name, []).append(span)

        extracted = ReferralExtract(**payload)
        extracted.evidence_spans = evidence_spans
        extracted.extraction_confidence = {
            field: 0.85 if spans else 0.0 for field, spans in evidence_spans.items()
        }
        extracted.evidence = {
            field: spans[0].quote for field, spans in evidence_spans.items() if spans
        }
        return extracted

    if mode == "llm_placeholder":
        raise NotImplementedError(
            "LLM extraction placeholder only. Interface reserved for a future API/local model integration. "
            "Expected inputs: normalized document bundle text + source document metadata. "
            "Expected outputs: ReferralExtract with grounded evidence spans."
        )

    raise ValueError(f"Unknown bundle extraction mode: {mode}")
