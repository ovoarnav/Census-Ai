from __future__ import annotations

from typing import Dict, List

from src.extraction.schema import ReferralExtract
from src.ingestion.models import EvidenceSpan, ReferralDocumentBundle, SourceDocument


def verify_quote_in_document(quote: str, document_text: str) -> bool:
    """Return True only when the quote exists exactly in document text."""
    if not quote:
        return False
    return quote in (document_text or "")


def repair_span_offsets_if_possible(
    span: EvidenceSpan,
    source_documents: Dict[str, SourceDocument],
) -> EvidenceSpan:
    """If quote exists but offsets are wrong/missing, repair char_start/char_end."""
    doc_id = span.source_doc_id
    if not doc_id or doc_id not in source_documents:
        return span

    doc_text = source_documents[doc_id].text or ""
    if not span.quote:
        return span

    if span.char_start is not None and span.char_end is not None:
        if 0 <= span.char_start < span.char_end <= len(doc_text):
            if doc_text[span.char_start : span.char_end] == span.quote:
                return span

    idx = doc_text.find(span.quote)
    if idx >= 0:
        span.char_start = idx
        span.char_end = idx + len(span.quote)

    return span


def verify_evidence_span(
    span: EvidenceSpan,
    source_documents: Dict[str, SourceDocument],
) -> EvidenceSpan:
    """Verify quote/source linkage and set quote_verified appropriately."""
    repaired = repair_span_offsets_if_possible(span, source_documents)

    doc_id = repaired.source_doc_id
    if not doc_id or doc_id not in source_documents:
        repaired.quote_verified = False
        return repaired

    doc_text = source_documents[doc_id].text or ""
    repaired.quote_verified = verify_quote_in_document(repaired.quote, doc_text)
    return repaired


def verify_referral_evidence(
    referral_extract: ReferralExtract,
    document_bundle: ReferralDocumentBundle,
) -> ReferralExtract:
    """Verify all evidence spans against source docs; never mark unverifiable quotes as verified."""
    source_docs = {d.source_doc_id: d for d in document_bundle.source_documents}

    if not referral_extract.evidence_spans and referral_extract.evidence:
        referral_extract.ensure_evidence_spans_from_legacy()

    verified_spans: Dict[str, List[EvidenceSpan]] = {}
    for field_name, spans in referral_extract.evidence_spans.items():
        verified_spans[field_name] = [verify_evidence_span(span, source_docs) for span in spans]

    referral_extract.evidence_spans = verified_spans

    if not referral_extract.source_document_ids:
        referral_extract.source_document_ids = [d.source_doc_id for d in document_bundle.source_documents]

    return referral_extract
