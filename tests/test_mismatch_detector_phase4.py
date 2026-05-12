from src.extraction.schema import ReferralExtract
from src.scoring.fit_engine import evaluate_referral
from src.scoring.mismatch_detector import detect_mismatches


def _facility_fixture():
    return {
        "available_beds_today": {"skilled_rehab": 0, "long_term_care": 0, "isolation_private": 0},
        "accepted_payers": {"Out of Network Managed Medicaid": False},
        "clinical_capabilities": {
            "memory_care_locked_unit": False,
            "bariatric_bed_available": False,
            "ventilator": False,
            "tracheostomy_complex": False,
            "dialysis_on_site": False,
            "dialysis_transport_coordination": False,
        },
        "admission_hours": {"after_hours_admissions_supported": False},
        "operational_constraints": {"current_admissions_today": 3, "max_new_admissions_per_day": 3},
    }


def _payer_rules_fixture():
    return {"Out of Network Managed Medicaid": {"prior_auth_required": True}}


def test_detect_mismatches_returns_structured_findings_for_core_risks():
    referral = ReferralExtract(
        referral_id="REF-500",
        payer="Out of Network Managed Medicaid",
        authorization_status="missing",
        cognitive_status="Exit-seeking behavior",
        durable_medical_equipment_needs="Bariatric bed needed",
        oxygen_respiratory_needs="Ventilator support",
        primary_diagnosis="Stroke with dysphagia and tracheostomy complication",
        dialysis_need="Hemodialysis three times weekly",
        infection_isolation_status="Contact isolation",
        current_medications_or_mar="Not included",
        allergies="Not listed",
        missing_or_unclear_items=["Swallow precautions/diet order missing"],
    )

    findings = detect_mismatches(referral, _facility_fixture(), _payer_rules_fixture())
    types = {f.mismatch_type for f in findings}

    assert "payer_not_accepted" in types
    assert "prior_auth_missing" in types
    assert "no_bed_capacity" in types
    assert "memory_care_gap" in types
    assert "bariatric_equipment_gap" in types
    assert "ventilator_gap" in types
    assert "tracheostomy_gap" in types
    assert "dialysis_transport_coordination" in types
    assert "isolation_private_room_gap" in types
    assert "after_hours_admission_risk" in types
    assert "missing_mar" in types
    assert "missing_allergies" in types
    assert "missing_swallow_diet_orders" in types
    assert "weak_or_missing_evidence" in types


def test_evaluate_referral_includes_mismatch_findings():
    referral = ReferralExtract(
        referral_id="REF-501",
        payer="Out of Network Managed Medicaid",
        authorization_status="missing",
        current_medications_or_mar="Not included",
        allergies="Not listed",
    )

    evaluation = evaluate_referral(referral, _facility_fixture(), _payer_rules_fixture())
    assert "mismatch_findings" in evaluation
    assert isinstance(evaluation["mismatch_findings"], list)
    assert any(f["mismatch_type"] == "payer_not_accepted" for f in evaluation["mismatch_findings"])


def test_detect_mismatches_regression_cached_text_triggers_core_gaps():
    referral = ReferralExtract(
        referral_id="REF-502",
        cognitive_status="Wandering and exit-seeking",
        mobility_transfer_status="Requires two-person transfer with bariatric support",
        durable_medical_equipment_needs="BARIATRIC bed and supplies",
        oxygen_respiratory_needs="Ventilator dependent",
        primary_diagnosis="Chronic respiratory failure with trach history",
    )

    findings = detect_mismatches(referral, _facility_fixture(), _payer_rules_fixture())
    types = {f.mismatch_type for f in findings}

    assert "memory_care_gap" in types
    assert "bariatric_equipment_gap" in types
    assert "ventilator_gap" in types
    assert "tracheostomy_gap" in types


def test_detect_mismatches_regression_conflicting_statuses_still_trigger():
    referral = ReferralExtract(
        referral_id="REF-503",
        behavioral_safety_concerns="No concerns",
        cognitive_status="Aggressive episodes and unsafe wandering",
        infection_isolation_status="No isolation",
        missing_or_unclear_items=["Isolation order unclear in packet"],
    )

    findings = detect_mismatches(referral, _facility_fixture(), _payer_rules_fixture())
    types = {f.mismatch_type for f in findings}

    assert "conflicting_behavioral_status" in types
    assert "conflicting_isolation_status" in types
