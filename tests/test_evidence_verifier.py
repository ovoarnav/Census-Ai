from src.evidence.verifier import (
    repair_span_offsets_if_possible,
    verify_evidence_span,
    verify_quote_in_document,
    verify_referral_evidence,
)
from src.extraction.schema import ReferralExtract
from src.ingestion.models import EvidenceSpan, ReferralDocumentBundle, SourceDocument


def test_verify_quote_in_document_exact_match():
    assert verify_quote_in_document("Medicare A", "Payer is Medicare A.") is True


def test_repair_span_offsets_if_possible_when_quote_exists_elsewhere():
    doc = SourceDocument(source_doc_id="doc-1", text="abc Medicare A xyz")
    span = EvidenceSpan(
        field_name="payer",
        source_doc_id="doc-1",
        quote="Medicare A",
        char_start=0,
        char_end=3,
        quote_verified=False,
    )

    repaired = repair_span_offsets_if_possible(span, {"doc-1": doc})
    assert repaired.char_start == 4
    assert repaired.char_end == 14


def test_verify_evidence_span_quote_not_found_marks_unverified():
    doc = SourceDocument(source_doc_id="doc-1", text="No payer listed")
    span = EvidenceSpan(field_name="payer", source_doc_id="doc-1", quote="Medicare A")

    checked = verify_evidence_span(span, {"doc-1": doc})
    assert checked.quote_verified is False


def test_verify_evidence_span_missing_source_doc_id_marks_unverified():
    span = EvidenceSpan(field_name="payer", source_doc_id=None, quote="Medicare A")
    checked = verify_evidence_span(span, {})
    assert checked.quote_verified is False


def test_verify_referral_evidence_verifies_and_repairs():
    extract = ReferralExtract(
        referral_id="REF-101",
        evidence_spans={
            "payer": [
                EvidenceSpan(
                    field_name="payer",
                    source_doc_id="doc-1",
                    quote="Medicare A",
                    char_start=0,
                    char_end=2,
                )
            ]
        },
    )
    bundle = ReferralDocumentBundle(
        referral_id="REF-101",
        source_documents=[SourceDocument(source_doc_id="doc-1", text="Payer: Medicare A")],
    )

    verified = verify_referral_evidence(extract, bundle)
    best = verified.get_best_evidence("payer")
    assert best is not None
    assert best.quote_verified is True
    assert best.char_start == 7
    assert best.char_end == 17


def test_verify_referral_evidence_in_place_true_mutates_original():
    extract = ReferralExtract(
        referral_id="REF-101",
        evidence_spans={
            "payer": [
                EvidenceSpan(
                    field_name="payer",
                    source_doc_id="doc-1",
                    quote="Medicare A",
                    char_start=0,
                    char_end=2,
                )
            ]
        },
    )
    bundle = ReferralDocumentBundle(
        referral_id="REF-101",
        source_documents=[SourceDocument(source_doc_id="doc-1", text="Payer: Medicare A")],
    )

    verified = verify_referral_evidence(extract, bundle, in_place=True)

    assert verified is extract
    assert extract.evidence_spans["payer"][0].char_start == 7
    assert extract.evidence_spans["payer"][0].char_end == 17
    assert extract.evidence_spans["payer"][0].quote_verified is True


def test_verify_referral_evidence_in_place_false_returns_copy():
    extract = ReferralExtract(
        referral_id="REF-101",
        evidence_spans={
            "payer": [
                EvidenceSpan(
                    field_name="payer",
                    source_doc_id="doc-1",
                    quote="Medicare A",
                    char_start=0,
                    char_end=2,
                    quote_verified=False,
                )
            ]
        },
    )
    bundle = ReferralDocumentBundle(
        referral_id="REF-101",
        source_documents=[SourceDocument(source_doc_id="doc-1", text="Payer: Medicare A")],
    )

    verified = verify_referral_evidence(extract, bundle, in_place=False)

    assert verified is not extract
    assert verified.evidence_spans["payer"][0] is not extract.evidence_spans["payer"][0]
    assert extract.evidence_spans["payer"][0].char_start == 0
    assert extract.evidence_spans["payer"][0].char_end == 2
    assert extract.evidence_spans["payer"][0].quote_verified is False
    assert verified.evidence_spans["payer"][0].char_start == 7
    assert verified.evidence_spans["payer"][0].char_end == 17
    assert verified.evidence_spans["payer"][0].quote_verified is True
