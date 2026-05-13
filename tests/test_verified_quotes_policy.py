from src.extraction.schema import ReferralExtract
from src.scoring import fit_engine, mismatch_detector
from typing import Any, cast

def _facility_fixture():
    return {
        "available_beds_today": {"skilled_rehab": 2, "long_term_care": 1, "isolation_private": 1},
        "accepted_payers": {"Medicare A": True},
        "clinical_capabilities": {
            "memory_care_locked_unit": True,
            "bariatric_bed_available": True,
            "ventilator": True,
            "tracheostomy_complex": True,
            "dialysis_on_site": True,
            "dialysis_transport_coordination": True,
            "oxygen_support": True,
            "wound_care": True,
            "iv_antibiotics": True,
            "two_person_assist_supported": True,
            "total_mechanical_lift_supported": True,
        },
        "admission_hours": {"after_hours_admissions_supported": True},
        "operational_constraints": {"current_admissions_today": 0, "max_new_admissions_per_day": 3},
    }


def _referral_fixture():
    return ReferralExtract(
        referral_id="REF-VQ-1",
        payer="Medicare A",
        authorization_status="approved",
        primary_diagnosis="General debility",
        current_medications_or_mar="Acetaminophen 650mg q6h PRN",
        allergies="NKDA",
        mobility_transfer_status="one-person assist",
        infection_isolation_status="none",
        oxygen_respiratory_needs="room air",
        cognitive_status="alert and oriented",
        behavioral_safety_concerns="none",
        channel="portal",
    )


def test_weak_evidence_severity_escalates_when_verified_quotes_required(monkeypatch):
    referral = _referral_fixture()

    monkeypatch.setattr(mismatch_detector, "REQUIRE_VERIFIED_QUOTES", False)
    findings_relaxed = mismatch_detector.detect_mismatches(referral, _facility_fixture(), {"Medicare A": {"prior_auth_required": True}})
    weak_relaxed = next(f for f in findings_relaxed if f.mismatch_type == "weak_or_missing_evidence")
    assert weak_relaxed.severity == "medium"

    monkeypatch.setattr(mismatch_detector, "REQUIRE_VERIFIED_QUOTES", True)
    findings_strict = mismatch_detector.detect_mismatches(referral, _facility_fixture(), {"Medicare A": {"prior_auth_required": True}})
    weak_strict = next(f for f in findings_strict if f.mismatch_type == "weak_or_missing_evidence")
    assert weak_strict.severity == "high"


def test_accept_ready_blocked_when_verified_quotes_required(monkeypatch):
    referral = _referral_fixture()

    monkeypatch.setattr(mismatch_detector, "REQUIRE_VERIFIED_QUOTES", False)
    monkeypatch.setattr(fit_engine, "REQUIRE_VERIFIED_QUOTES", False)

    relaxed_eval = fit_engine.evaluate_referral(
        referral,
        _facility_fixture(),
        {"Medicare A": {"prior_auth_required": True}},
    )

    relaxed_recommendation = cast(dict[str, Any], relaxed_eval["recommendation"])
    assert relaxed_recommendation["status"] == "accept_ready"

    monkeypatch.setattr(mismatch_detector, "REQUIRE_VERIFIED_QUOTES", True)
    monkeypatch.setattr(fit_engine, "REQUIRE_VERIFIED_QUOTES", True)

    strict_eval = fit_engine.evaluate_referral(
        referral,
        _facility_fixture(),
        {"Medicare A": {"prior_auth_required": True}},
    )

    strict_recommendation = cast(dict[str, Any], strict_eval["recommendation"])
    assert strict_recommendation["status"] != "accept_ready"

    reasons = cast(list[str], strict_recommendation["reasons"])

    assert any(
        reason == "Verified quote evidence is required for critical fields before acceptance."
        for reason in reasons
    )