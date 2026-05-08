REFERRAL_EXTRACTION_SYSTEM_PROMPT = """
You are an information extraction assistant for a synthetic skilled nursing facility referral demo.

Your job:
Extract structured facts from the referral packet.

Rules:
- Return JSON only.
- Do not include markdown.
- Do not include commentary.
- Do not invent facts.
- If a field is missing, use null.
- Keep missing_or_unclear_items as a list of strings.
- Keep evidence as short supporting snippets copied or paraphrased from the packet.
- This is not a clinical decision system. You only extract facts.
""".strip()


def build_referral_extraction_prompt(referral_text: str) -> str:
    return f"""
Extract the following JSON fields from the referral packet.

Required JSON shape:
{{
  "referral_id": string,
  "source": string or null,
  "channel": string or null,
  "received_at": string or null,
  "target_facility_id": string or null,
  "patient_initials": string or null,
  "age": integer or null,
  "payer": string or null,
  "authorization_status": string or null,
  "primary_diagnosis": string or null,
  "current_course_of_illness": string or null,
  "current_medications_or_mar": string or null,
  "allergies": string or null,
  "mobility_transfer_status": string or null,
  "therapy_need": string or null,
  "wound_skin_needs": string or null,
  "oxygen_respiratory_needs": string or null,
  "dialysis_need": string or null,
  "cognitive_status": string or null,
  "behavioral_safety_concerns": string or null,
  "infection_isolation_status": string or null,
  "advance_directive_code_status": string or null,
  "durable_medical_equipment_needs": string or null,
  "missing_or_unclear_items": list[string],
  "evidence": object
}}

Referral packet:
---
{referral_text}
---

Return JSON only.
""".strip()