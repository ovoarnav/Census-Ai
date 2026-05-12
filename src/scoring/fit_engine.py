from typing import Dict, List

from src.extraction.schema import ReferralExtract
from src.workflow.missing_info import check_missing_information
from src.scoring.mismatch_detector import detect_mismatches
from src.scoring.text_utils import contains


def check_hard_constraints(referral: ReferralExtract, facility: dict) -> List[Dict[str, str]]:
    caps = facility.get("clinical_capabilities", {})
    accepted_payers = facility.get("accepted_payers", {})
    beds = facility.get("available_beds_today", {})
    constraints = []

    def add(kind: str, message: str):
        constraints.append({
            "type": kind,
            "severity": "high",
            "message": message,
        })

    payer = referral.payer or ""
    if payer and accepted_payers.get(payer) is False:
        add("payer_not_accepted", f"Payer '{payer}' is not accepted by this facility.")

    skilled_or_ltc_beds = beds.get("skilled_rehab", 0) + beds.get("long_term_care", 0)
    if skilled_or_ltc_beds <= 0:
        add("no_bed_capacity", "No skilled rehab or long-term care beds are available today.")

    airway_text = " ".join([
        referral.primary_diagnosis or "",
        referral.oxygen_respiratory_needs or "",
        referral.durable_medical_equipment_needs or "",
    ])

    if contains(airway_text, "ventilator", "vent "):
        if not caps.get("ventilator", False):
            add("ventilator_gap", "Ventilator support appears required, but facility does not support ventilators.")

    if contains(airway_text, "tracheostomy", "trach"):
        if not caps.get("tracheostomy_complex", False):
            add("tracheostomy_gap", "Complex tracheostomy care appears required, but facility does not support it.")

    equipment_text = " ".join([
        referral.mobility_transfer_status or "",
        referral.durable_medical_equipment_needs or "",
    ])

    if contains(equipment_text, "bariatric"):
        if not caps.get("bariatric_bed_available", False):
            add("bariatric_equipment_gap", "Bariatric bed/equipment appears required, but facility has none available.")

    memory_text = " ".join([
        referral.cognitive_status or "",
        referral.behavioral_safety_concerns or "",
    ])

    if contains(memory_text, "wandering", "exit-seeking", "secured memory", "memory-care"):
        if not caps.get("memory_care_locked_unit", False):
            add("memory_care_gap", "Secured memory-care capability appears required, but facility lacks a locked memory-care unit.")

    return constraints


def score_clinical_fit(referral: ReferralExtract, facility: dict) -> int:
    caps = facility.get("clinical_capabilities", {})
    score = 90

    if contains(referral.wound_skin_needs, "wound vac"):
        score -= 0 if caps.get("wound_vac", False) else 35
    elif contains(referral.wound_skin_needs, "wound", "dressing", "pressure injury"):
        score -= 0 if caps.get("wound_care", False) else 25

    if contains(referral.current_medications_or_mar, "iv ", " iv", "cefazolin", "vancomycin"):
        score -= 0 if caps.get("iv_antibiotics", False) else 30

    if contains(referral.oxygen_respiratory_needs, "oxygen", "nasal cannula", "cpap", "bipap"):
        score -= 0 if caps.get("oxygen_support", False) else 25

    if contains(referral.dialysis_need, "dialysis", "hemodialysis"):
        if not caps.get("dialysis_on_site", False):
            score -= 25

    if contains(referral.behavioral_safety_concerns, "wandering", "exit-seeking", "aggressive", "unsafe"):
        score -= 30

    if contains(referral.cognitive_status, "severe", "secured", "memory-care"):
        score -= 20

    if contains(referral.primary_diagnosis, "tracheostomy") and not caps.get("tracheostomy_complex", False):
        score -= 40

    return max(0, min(100, score))


def score_operational_fit(referral: ReferralExtract, facility: dict) -> int:
    caps = facility.get("clinical_capabilities", {})
    beds = facility.get("available_beds_today", {})
    constraints = facility.get("operational_constraints", {})
    score = 85

    if contains(referral.therapy_need, "pt", "ot", "rehab"):
        if beds.get("skilled_rehab", 0) <= 0:
            score -= 30

    if contains(referral.mobility_transfer_status, "two-person"):
        if not caps.get("two_person_assist_supported", False):
            score -= 30

    if contains(referral.mobility_transfer_status, "mechanical lift"):
        if not caps.get("total_mechanical_lift_supported", False):
            score -= 30

    if contains(referral.infection_isolation_status, "contact", "isolation"):
        if beds.get("isolation_private", 0) <= 0:
            score -= 25

    if contains(referral.durable_medical_equipment_needs, "bariatric"):
        if not caps.get("bariatric_bed_available", False):
            score -= 35

    current = constraints.get("current_admissions_today", 0)
    max_today = constraints.get("max_new_admissions_per_day", 3)
    if current >= max_today:
        score -= 20

    return max(0, min(100, score))


def score_financial_fit(referral: ReferralExtract, facility: dict, payer_rules: dict) -> int:
    payer = referral.payer or ""
    auth = (referral.authorization_status or "").lower()

    if facility.get("accepted_payers", {}).get(payer) is False:
        return 20

    rule = payer_rules.get(payer, {})
    if not rule:
        return 55

    if rule.get("prior_auth_required"):
        if auth == "approved":
            return rule.get("demo_financial_score_if_complete", 80)
        if auth in {"missing", "pending", "unknown", "", "none"}:
            return rule.get("demo_financial_score_if_auth_missing", 50)

    return rule.get("demo_financial_score_if_complete", 70)


def score_completeness(missing_info: List[dict]) -> int:
    score = 100
    for item in missing_info:
        severity = item.get("severity")
        if severity == "high":
            score -= 20
        elif severity == "medium":
            score -= 10
        else:
            score -= 5
    return max(0, min(100, score))


def score_urgency(referral: ReferralExtract) -> int:
    channel = (referral.channel or "").lower()
    source = (referral.source or "").lower()

    if "portal" in channel:
        return 85
    if "phone" in channel:
        return 80
    if "fax" in channel:
        return 70
    if "ortho" in source:
        return 90
    return 75


def calculate_overall_score(scores: Dict[str, int]) -> int:
    return round(
        0.35 * scores["clinical_fit"]
        + 0.25 * scores["operational_fit"]
        + 0.20 * scores["financial_fit"]
        + 0.10 * scores["completeness"]
        + 0.10 * scores["urgency"]
    )


def generate_recommendation(
    overall_score: int,
    hard_constraints: List[dict],
    missing_info: List[dict],
    scores: Dict[str, int],
) -> Dict[str, object]:
    high_missing = [item for item in missing_info if item.get("severity") == "high"]

    if hard_constraints:
        status = "decline_recommended"
        label = "Decline recommended / escalation required"
    elif overall_score >= 85 and not high_missing:
        status = "accept_ready"
        label = "Accept-ready"
    elif overall_score >= 70:
        status = "likely_accept_needs_info"
        label = "Likely accept — needs information"
    elif overall_score >= 50:
        status = "clinical_review"
        label = "Clinical review required"
    else:
        status = "decline_recommended"
        label = "Decline recommended / escalation required"

    reasons = []

    if hard_constraints:
        reasons.extend([constraint["message"] for constraint in hard_constraints])

    if high_missing:
        reasons.append("High-severity missing information must be resolved before final admission decision.")

    if scores["clinical_fit"] >= 80:
        reasons.append("Clinical needs appear mostly within facility capabilities.")
    elif scores["clinical_fit"] < 60:
        reasons.append("Clinical fit is weak or requires escalation.")

    if scores["operational_fit"] >= 80:
        reasons.append("Operational capacity appears workable.")
    elif scores["operational_fit"] < 65:
        reasons.append("Operational capacity, equipment, staffing, or room constraints may block admission.")

    if scores["financial_fit"] < 60:
        reasons.append("Financial/payer fit is weak or authorization is missing.")

    if not reasons:
        reasons.append("Referral requires additional review based on score thresholds.")

    return {
        "status": status,
        "label": label,
        "overall_score": overall_score,
        "reasons": reasons,
    }


def evaluate_referral(referral: ReferralExtract, facility: dict, payer_rules: dict) -> Dict[str, object]:
    missing_info = check_missing_information(referral, payer_rules)
    hard_constraints = check_hard_constraints(referral, facility)
    mismatch_findings = detect_mismatches(referral, facility, payer_rules)

    scores = {
        "clinical_fit": score_clinical_fit(referral, facility),
        "operational_fit": score_operational_fit(referral, facility),
        "financial_fit": score_financial_fit(referral, facility, payer_rules),
        "completeness": score_completeness(missing_info),
        "urgency": score_urgency(referral),
    }

    overall_score = calculate_overall_score(scores)
    recommendation = generate_recommendation(overall_score, hard_constraints, missing_info, scores)

    return {
        "referral_id": referral.referral_id,
        "scores": scores,
        "overall_score": overall_score,
        "hard_constraints": hard_constraints,
        "mismatch_findings": [finding.model_dump() for finding in mismatch_findings],
        "missing_info": missing_info,
        "recommendation": recommendation,
    }
