import re
from typing import Optional, Dict, List

from src.extraction.schema import ReferralExtract


FIELD_PATTERNS = {
    "referral_id": r"Referral ID:\s*(.*)",
    "source": r"Source:\s*(.*)",
    "channel": r"Channel:\s*(.*)",
    "received_at": r"Received:\s*(.*)",
    "target_facility_id": r"Target Facility:\s*(.*)",
    "patient_initials": r"Patient Initials:\s*(.*)",
    "age": r"Age:\s*(.*)",
    "payer": r"Payer:\s*(.*)",
    "authorization_status": r"Authorization Status:\s*(.*)",
    "primary_diagnosis": r"Primary Diagnosis / Reason for Referral:\s*(.*)",
    "current_course_of_illness": r"Hospital Course:\s*(.*)",
    "current_medications_or_mar": r"Current Medications / MAR Summary:\s*(.*)",
    "allergies": r"Allergies:\s*(.*)",
    "mobility_transfer_status": r"Mobility / Transfer Status:\s*(.*)",
    "therapy_need": r"Therapy Need:\s*(.*)",
    "wound_skin_needs": r"Wound / Skin Needs:\s*(.*)",
    "oxygen_respiratory_needs": r"Oxygen / Respiratory Needs:\s*(.*)",
    "dialysis_need": r"Dialysis Need:\s*(.*)",
    "cognitive_status": r"Cognitive Status:\s*(.*)",
    "behavioral_safety_concerns": r"Behavioral / Safety Concerns:\s*(.*)",
    "infection_isolation_status": r"Infection / Isolation Status:\s*(.*)",
    "advance_directive_code_status": r"Advance Directive / Code Status:\s*(.*)",
    "durable_medical_equipment_needs": r"Durable Medical Equipment Needs:\s*(.*)",
}


IMPORTANT_EVIDENCE_FIELDS = [
    "primary_diagnosis",
    "payer",
    "authorization_status",
    "mobility_transfer_status",
    "therapy_need",
    "wound_skin_needs",
    "oxygen_respiratory_needs",
    "dialysis_need",
    "cognitive_status",
    "behavioral_safety_concerns",
    "infection_isolation_status",
    "durable_medical_equipment_needs",
]


def _find_field(pattern: str, text: str) -> Optional[str]:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return None

    value = match.group(1).strip()
    return value if value else None


def _parse_age(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    match = re.search(r"\d+", str(value))
    if not match:
        return None
    return int(match.group(0))


def _extract_missing_items(text: str) -> List[str]:
    marker = "KNOWN MISSING OR UNCLEAR ITEMS"
    if marker not in text:
        return []

    section = text.split(marker, 1)[1]
    section = section.split("DEMO NOTE", 1)[0]

    items = []
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("- "):
            continue

        item = line[2:].strip()
        if item and "None documented" not in item:
            items.append(item)

    return items


def _build_evidence(data: Dict[str, object]) -> Dict[str, str]:
    evidence = {}

    for field in IMPORTANT_EVIDENCE_FIELDS:
        value = data.get(field)
        if isinstance(value, str) and value.strip():
            evidence[field] = value.strip()[:300]

    return evidence


def extract_referral(text: str) -> ReferralExtract:
    extracted: Dict[str, object] = {}

    for field, pattern in FIELD_PATTERNS.items():
        extracted[field] = _find_field(pattern, text)

    extracted["age"] = _parse_age(extracted.get("age"))
    extracted["missing_or_unclear_items"] = _extract_missing_items(text)
    extracted["evidence"] = _build_evidence(extracted)

    if not extracted.get("referral_id"):
        raise ValueError("Could not extract referral_id from packet.")

    return ReferralExtract(**extracted)


def extract_many(packet_texts: Dict[str, str]) -> List[ReferralExtract]:
    results = []
    for referral_id, text in packet_texts.items():
        result = extract_referral(text)
        if result.referral_id != referral_id:
            raise ValueError(
                f"Referral ID mismatch: expected {referral_id}, got {result.referral_id}"
            )
        results.append(result)
    return results
