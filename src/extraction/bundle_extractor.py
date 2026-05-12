from __future__ import annotations

import re
from typing import Literal

from src.extraction.deterministic_extractor import extract_referral as extract_deterministic
from src.extraction.schema import ReferralExtract
from src.ingestion.models import EvidenceSpan, ReferralDocumentBundle, SourceDocument

BundleExtractionMode = Literal[
    "deterministic_text_packet",
    "heuristic_bundle",
    "llm_placeholder",
]


def _normalized_bundle_text(bundle: ReferralDocumentBundle) -> str:
    parts = []
    for doc in bundle.source_documents:
        header = f"[DOC {doc.source_doc_id} | {doc.document_type or 'unknown'}]\n"
        parts.append(header + (doc.text or ""))
    return "\n\n".join(parts)


def _find_line_value(label_regex: str, text: str) -> str | None:
    match = re.search(label_regex, text, flags=re.IGNORECASE)
    if not match:
        return None
    value = match.group(1).strip()
    return value if value else None


def _extract_evidence_from_doc(field_name: str, pattern: str, doc: SourceDocument) -> EvidenceSpan | None:
    match = re.search(pattern, doc.text or "", flags=re.IGNORECASE)
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

        field_patterns = {
            "patient_initials": r"Patient Initials:\s*(.*)",
            "payer": r"Payer:\s*(.*)",
            "authorization_status": r"Authorization Status:\s*(.*)",
            "primary_diagnosis": r"Primary Diagnosis(?: / Reason for Referral)?:\s*(.*)",
            "current_medications_or_mar": r"(?:Current Medications / MAR Summary|MAR):\s*(.*)",
            "allergies": r"Allergies:\s*(.*)",
            "mobility_transfer_status": r"Mobility / Transfer Status:\s*(.*)",
            "therapy_need": r"Therapy Need:\s*(.*)",
            "oxygen_respiratory_needs": r"Oxygen / Respiratory Needs:\s*(.*)",
            "dialysis_need": r"Dialysis Need:\s*(.*)",
            "cognitive_status": r"Cognitive Status:\s*(.*)",
            "behavioral_safety_concerns": r"Behavioral / Safety Concerns:\s*(.*)",
            "infection_isolation_status": r"Infection / Isolation Status:\s*(.*)",
            "durable_medical_equipment_needs": r"Durable Medical Equipment Needs:\s*(.*)",
        }

        evidence_spans: dict[str, list[EvidenceSpan]] = {}

        for field_name, pattern in field_patterns.items():
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
