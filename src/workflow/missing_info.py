from typing import Dict, List

from src.extraction.schema import ReferralExtract


def _add_missing(items: list, field: str, severity: str, question: str, reason: str) -> None:
    items.append({
        "field": field,
        "severity": severity,
        "question": question,
        "reason": reason,
    })


def check_missing_information(referral: ReferralExtract, payer_rules: dict) -> List[Dict[str, str]]:
    missing = []

    if not referral.primary_diagnosis:
        _add_missing(
            missing,
            "primary_diagnosis",
            "high",
            "Can you confirm the primary diagnosis/reason for referral?",
            "Primary diagnosis is required to understand clinical fit."
        )

    meds = (referral.current_medications_or_mar or "").lower()
    if not meds or "not included" in meds or "referenced but" in meds:
        _add_missing(
            missing,
            "current_medication_list_or_mar",
            "high",
            "Can you send the latest MAR or current medication list?",
            "Medication information is safety-critical for admission review."
        )

    allergies = (referral.allergies or "").lower()
    if not allergies or "not listed" in allergies:
        _add_missing(
            missing,
            "allergies",
            "high",
            "Can you confirm medication and food allergies?",
            "Allergy status must be known before admission."
        )

    if not referral.mobility_transfer_status:
        _add_missing(
            missing,
            "mobility_transfer_status",
            "high",
            "Can you confirm mobility and transfer assistance level?",
            "Mobility determines staffing, therapy, and equipment needs."
        )

    if not referral.infection_isolation_status:
        _add_missing(
            missing,
            "infection_isolation_status",
            "high",
            "Can you confirm infection/isolation status?",
            "Isolation needs affect room placement and safety."
        )

    payer = referral.payer or ""
    auth = (referral.authorization_status or "").lower()
    payer_rule = payer_rules.get(payer, {})

    if payer_rule.get("prior_auth_required") and auth in {"", "missing", "pending", "unknown", "none"}:
        _add_missing(
            missing,
            "authorization_status_if_required",
            "high",
            "Can you confirm whether payer authorization has been approved?",
            "This payer usually requires authorization before admission."
        )

    wound = (referral.wound_skin_needs or "").lower()
    if ("wound" in wound or "dressing" in wound or "vac" in wound) and ("unclear" in wound or "frequency unclear" in wound):
        _add_missing(
            missing,
            "wound_care_orders",
            "medium",
            "Can you send clear wound care orders and dressing-change frequency?",
            "Wound orders are needed to confirm nursing fit."
        )

    diagnosis = (referral.primary_diagnosis or "").lower()
    packet_missing = " ".join(referral.missing_or_unclear_items).lower()
    if ("stroke" in diagnosis or "dysphagia" in diagnosis) and ("swallow" in packet_missing or "diet" in packet_missing):
        _add_missing(
            missing,
            "diet_swallowing_orders",
            "high",
            "Can you provide diet texture, liquid consistency, and swallowing precautions?",
            "Swallowing orders are safety-critical after stroke/dysphagia."
        )

    for item in referral.missing_or_unclear_items:
        normalized = item.lower()
        severity = "medium"
        if any(token in normalized for token in [
            "authorization", "mar", "medication", "allergies", "diet", "swallow"
        ]):
            severity = "high"

        _add_missing(
            missing,
            item,
            severity,
            f"Can you provide or confirm: {item}?",
            "This item was explicitly listed as missing or unclear in the referral packet."
        )

    seen = set()
    deduped = []
    for item in missing:
        key = item["field"].strip().lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    return deduped
