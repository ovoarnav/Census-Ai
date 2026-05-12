from src.extraction.schema import ReferralExtract, legacy_evidence_to_spans
from src.ingestion.models import EvidenceSpan


def test_legacy_evidence_to_spans_creates_unverified_spans():
    spans = legacy_evidence_to_spans({"payer": "Medicare A", "allergies": "NKDA"})

    assert "payer" in spans
    assert spans["payer"][0].quote == "Medicare A"
    assert spans["payer"][0].quote_verified is False


def test_get_best_evidence_prefers_verified_span():
    extract = ReferralExtract(
        referral_id="REF-1",
        evidence_spans={
            "payer": [
                EvidenceSpan(field_name="payer", quote="Medicare", quote_verified=False),
                EvidenceSpan(field_name="payer", quote="Medicare A", quote_verified=True),
            ]
        },
    )

    best = extract.get_best_evidence("payer")
    assert best is not None
    assert best.quote == "Medicare A"


def test_get_best_evidence_falls_back_to_legacy_map():
    extract = ReferralExtract(referral_id="REF-2", evidence={"payer": "Medicare A"})

    best = extract.get_best_evidence("payer")
    assert best is not None
    assert best.quote == "Medicare A"
    assert best.quote_verified is False


def test_fields_missing_verified_evidence_reports_unverified_fields():
    extract = ReferralExtract(
        referral_id="REF-3",
        evidence={"payer": "Medicare A"},
        evidence_spans={
            "authorization_status": [
                EvidenceSpan(
                    field_name="authorization_status",
                    quote="Pending",
                    quote_verified=True,
                )
            ]
        },
    )

    missing = extract.fields_missing_verified_evidence()
    assert "payer" in missing
    assert "authorization_status" not in missing
