import pytest

from src.extraction.bundle_extractor import FIELD_PATTERNS, extract_referral_from_bundle
from src.extraction.extractor_router import extract_referral_from_bundle_by_mode
from src.ingestion.models import ReferralDocumentBundle, SourceDocument


def _bundle():
    return ReferralDocumentBundle(
        referral_id="REF-700",
        source="Hospital A",
        channel="fax",
        source_documents=[
            SourceDocument(
                source_doc_id="doc-1",
                document_type="fax",
                text=(
                    "Referral ID: REF-700\n"
                    "Patient Initials: J.D.\n"
                    "Payer: Medicare Advantage\n"
                    "Authorization Status: Pending\n"
                    "Primary Diagnosis: CHF exacerbation\n"
                    "Allergies: NKDA\n"
                ),
            )
        ],
    )


def test_heuristic_bundle_extracts_fields_and_evidence():
    extracted = extract_referral_from_bundle(_bundle(), mode="heuristic_bundle")

    assert extracted.referral_id == "REF-700"
    assert extracted.payer == "Medicare Advantage"
    assert extracted.authorization_status == "Pending"
    assert extracted.primary_diagnosis == "CHF exacerbation"
    assert extracted.source_document_ids == ["doc-1"]
    payer_span = extracted.get_best_evidence("payer")
    assert payer_span is not None
    assert payer_span.quote_verified is False


def test_deterministic_text_packet_mode_still_runs_on_bundle():
    extracted = extract_referral_from_bundle(_bundle(), mode="deterministic_text_packet")
    assert extracted.referral_id == "REF-700"


def test_llm_placeholder_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        extract_referral_from_bundle(_bundle(), mode="llm_placeholder")


def test_router_supports_bundle_mode_and_verifies_evidence():
    extracted = extract_referral_from_bundle_by_mode(_bundle(), mode="heuristic_bundle")
    assert extracted.referral_id == "REF-700"
    payer_span = extracted.get_best_evidence("payer")
    assert payer_span is not None
    assert payer_span.quote_verified is True


def test_field_patterns_are_compiled_regexes():
    assert FIELD_PATTERNS
    for pattern in FIELD_PATTERNS.values():
        assert hasattr(pattern, "search")


def test_primary_diagnosis_alternate_label_still_extracts_value_and_evidence():
    bundle = ReferralDocumentBundle(
        referral_id="REF-701",
        source="Hospital A",
        channel="fax",
        source_documents=[
            SourceDocument(
                source_doc_id="doc-2",
                document_type="fax",
                text=(
                    "Primary Diagnosis / Reason for Referral: COPD exacerbation\n"
                ),
            )
        ],
    )

    extracted = extract_referral_from_bundle(bundle, mode="heuristic_bundle")

    assert extracted.primary_diagnosis == "COPD exacerbation"
    span = extracted.get_best_evidence("primary_diagnosis")
    assert span is not None
    assert span.quote == "COPD exacerbation"
