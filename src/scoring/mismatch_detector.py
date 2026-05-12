from __future__ import annotations

from typing import Dict, List, Optional

from src.config import REQUIRE_VERIFIED_QUOTES
from src.extraction.schema import ReferralExtract
from src.ingestion.models import EvidenceSpan, MismatchFinding


def contains(text: str | None, *keywords: str) -> bool:
    if not text:
        return False
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def _get_evidence(referral: ReferralExtract, field_name: str) -> Optional[EvidenceSpan]:
    return referral.get_best_evidence(field_name)


def _make_finding(
    mismatch_type: str,
    severity: str,
    field: str,
    message: str,
    why_it_matters: str,
    recommended_action: str,
    referral: ReferralExtract,
    facility_rule_triggered: Optional[str] = None,
) -> MismatchFinding:
    return MismatchFinding(
        mismatch_type=mismatch_type,
        severity=severity,  # type: ignore[arg-type]
        field=field,
        message=message,
        why_it_matters=why_it_matters,
        recommended_action=recommended_action,
        facility_rule_triggered=facility_rule_triggered,
        evidence=_get_evidence(referral, field),
    )


def detect_mismatches(referral: ReferralExtract, facility: dict, payer_rules: Dict[str, dict]) -> List[MismatchFinding]:
    findings: List[MismatchFinding] = []

    caps = facility.get("clinical_capabilities", {})
    accepted_payers = facility.get("accepted_payers", {})
    beds = facility.get("available_beds_today", {})
    admission_hours = facility.get("admission_hours", {})
    constraints = facility.get("operational_constraints", {})

    payer = referral.payer or ""
    auth = (referral.authorization_status or "").lower().strip()

    if payer and accepted_payers.get(payer) is False:
        findings.append(_make_finding(
            "payer_not_accepted", "critical", "payer",
            f"Payer '{payer}' is not accepted by this facility.",
            "The referral cannot be admitted under an unsupported payer arrangement.",
            "Confirm payer alternatives or redirect to an in-network/in-policy facility.",
            referral, "accepted_payers"
        ))

    payer_rule = payer_rules.get(payer, {})
    if payer_rule.get("prior_auth_required") and auth in {"", "missing", "pending", "unknown", "none"}:
        findings.append(_make_finding(
            "prior_auth_missing", "high", "authorization_status",
            "Prior authorization appears required but is missing or not approved.",
            "Admission may be delayed or denied without required authorization.",
            "Request/expedite prior authorization and obtain approval confirmation.",
            referral, "prior_auth_required"
        ))

    skilled_or_ltc_beds = beds.get("skilled_rehab", 0) + beds.get("long_term_care", 0)
    if skilled_or_ltc_beds <= 0:
        findings.append(_make_finding(
            "no_bed_capacity", "critical", "available_beds_today",
            "No skilled rehab or long-term care bed appears available.",
            "Lack of bed capacity blocks immediate placement.",
            "Place on waitlist or route to alternate facility with capacity.",
            referral, "available_beds_today"
        ))

    memory_text = " ".join([referral.cognitive_status or "", referral.behavioral_safety_concerns or ""])
    if contains(memory_text, "wandering", "exit-seeking", "secured memory", "memory-care") and not caps.get("memory_care_locked_unit", False):
        findings.append(_make_finding("memory_care_gap", "high", "cognitive_status",
            "Locked memory-care support appears needed but not available.",
            "Unmet memory-care needs can create safety risks and failed placements.",
            "Escalate to memory-care-capable facility or confirm alternate safety plan.",
            referral, "memory_care_locked_unit"))

    equipment_text = " ".join([referral.mobility_transfer_status or "", referral.durable_medical_equipment_needs or ""])
    if contains(equipment_text, "bariatric") and not caps.get("bariatric_bed_available", False):
        findings.append(_make_finding("bariatric_equipment_gap", "high", "durable_medical_equipment_needs",
            "Bariatric equipment appears required but is not available.",
            "Insufficient equipment can make care unsafe or infeasible.",
            "Confirm bariatric equipment availability or transfer to equipped site.",
            referral, "bariatric_bed_available"))

    airway_text = " ".join([referral.primary_diagnosis or "", referral.oxygen_respiratory_needs or "", referral.durable_medical_equipment_needs or ""])
    if contains(airway_text, "ventilator", "vent ") and not caps.get("ventilator", False):
        findings.append(_make_finding("ventilator_gap", "critical", "oxygen_respiratory_needs",
            "Ventilator support appears needed but facility does not provide it.",
            "Ventilator capability mismatch can make admission unsafe.",
            "Escalate for alternate placement with ventilator support.",
            referral, "ventilator"))

    if contains(airway_text, "tracheostomy", "trach") and not caps.get("tracheostomy_complex", False):
        findings.append(_make_finding("tracheostomy_gap", "high", "primary_diagnosis",
            "Complex tracheostomy care appears needed but not supported.",
            "Trach care mismatch may exceed available clinical capability.",
            "Confirm care complexity and route to trach-capable setting.",
            referral, "tracheostomy_complex"))

    if contains(referral.dialysis_need, "dialysis", "hemodialysis") and not caps.get("dialysis_on_site", False) and not caps.get("dialysis_transport_coordination", False):
        findings.append(_make_finding("dialysis_transport_coordination", "medium", "dialysis_need",
            "Dialysis is needed and transport coordination support appears unavailable.",
            "Missed dialysis logistics can disrupt continuity of care.",
            "Verify transport plan or refer to facility with dialysis coordination.",
            referral, "dialysis_transport_coordination"))

    if contains(referral.infection_isolation_status, "contact", "isolation") and beds.get("isolation_private", 0) <= 0:
        findings.append(_make_finding("isolation_private_room_gap", "high", "infection_isolation_status",
            "Isolation/private room need appears to conflict with bed availability.",
            "Isolation mismatch introduces infection-control and compliance risk.",
            "Confirm isolation requirements and secure an appropriate room.",
            referral, "isolation_private"))

    if admission_hours.get("after_hours_admissions_supported") is False and constraints.get("current_admissions_today", 0) >= constraints.get("max_new_admissions_per_day", 3):
        findings.append(_make_finding("after_hours_admission_risk", "medium", "received_at",
            "After-hours admission risk due to capacity/time-window constraints.",
            "Delayed handoff can create operational and safety issues.",
            "Coordinate next available admission window and confirm staffing.",
            referral, "after_hours_admissions_supported"))

    meds = (referral.current_medications_or_mar or "").lower()
    if not meds or "not included" in meds or "referenced but" in meds:
        findings.append(_make_finding("missing_mar", "high", "current_medications_or_mar",
            "Current MAR/medication list appears missing.",
            "Medication reconciliation is safety-critical at admission.",
            "Request latest MAR before acceptance decision.",
            referral))

    allergies = (referral.allergies or "").lower()
    if not allergies or "not listed" in allergies:
        findings.append(_make_finding("missing_allergies", "high", "allergies",
            "Allergy information appears missing or unclear.",
            "Unknown allergy status creates avoidable medication and dietary risk.",
            "Obtain and verify allergy profile before admission.",
            referral))

    packet_missing = " ".join(referral.missing_or_unclear_items).lower()
    diagnosis = (referral.primary_diagnosis or "").lower()
    if ("stroke" in diagnosis or "dysphagia" in diagnosis) and ("swallow" in packet_missing or "diet" in packet_missing):
        findings.append(_make_finding("missing_swallow_diet_orders", "high", "missing_or_unclear_items",
            "Swallow/diet orders appear missing for stroke/dysphagia context.",
            "Missing diet texture or swallow precautions can cause aspiration risk.",
            "Request explicit SLP/swallow and diet orders.",
            referral))

    if contains(referral.infection_isolation_status, "none", "no isolation") and packet_missing.find("isolation") >= 0:
        findings.append(_make_finding("conflicting_isolation_status", "medium", "infection_isolation_status",
            "Isolation status appears internally conflicting across referral content.",
            "Conflicting infection-control details can lead to unsafe bed placement.",
            "Resolve isolation discrepancy with source before admitting.",
            referral))

    if contains(referral.behavioral_safety_concerns, "none", "no concerns") and contains(memory_text, "aggressive", "unsafe", "exit-seeking"):
        findings.append(_make_finding("conflicting_behavioral_status", "medium", "behavioral_safety_concerns",
            "Behavioral/safety status appears conflicting across fields.",
            "Conflicting behavioral details can hide staffing or supervision risks.",
            "Clarify behavioral baseline and supervision requirements.",
            referral))

    important_fields = [
        "payer", "authorization_status", "current_medications_or_mar", "allergies",
        "infection_isolation_status", "cognitive_status", "oxygen_respiratory_needs",
    ]
    weak_fields = [f for f in important_fields if not referral.has_verified_evidence(f)]
    if weak_fields:
        severity = "medium"
        if REQUIRE_VERIFIED_QUOTES and any(field in {"payer", "authorization_status", "current_medications_or_mar", "allergies"} for field in weak_fields):
            severity = "high"

        findings.append(_make_finding("weak_or_missing_evidence", severity, "evidence_spans",
            f"Verified evidence is missing for key fields: {', '.join(weak_fields)}.",
            "Weak evidence traceability lowers confidence in admissions safety review.",
            "Request source documentation or verify quotes before final decision.",
            referral))

    return findings
