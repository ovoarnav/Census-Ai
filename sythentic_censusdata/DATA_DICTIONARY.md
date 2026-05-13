# Data Dictionary

## ReferralExtract-compatible fields

- `referral_id`: Synthetic referral identifier.
- `source`: Hospital, case management team, family inquiry, or referral source.
- `channel`: Intake channel such as referral portal, fax, email, phone transcript, OCR screenshot, or handwritten note.
- `received_at`: Intake timestamp.
- `target_facility_id`: Facility being evaluated.
- `patient_initials`: Synthetic initials only.
- `age`: Synthetic age.
- `payer`: Medicare Part A, Medicare Advantage, Medicaid, Commercial, Private Pay, Out of Network Managed Medicaid, or VA Community Care.
- `authorization_status`: approved, pending, missing, or not_required.
- `primary_diagnosis`: Main referral reason.
- `current_course_of_illness`: Summary of hospital course.
- `current_medications_or_mar`: Medication/MAR summary or missing-MAR cue.
- `allergies`: Allergy status.
- `mobility_transfer_status`: Functional mobility and transfer support level.
- `therapy_need`: PT/OT/ST need or absence.
- `wound_skin_needs`: Wound, dressing, wound VAC, skin, or no wound status.
- `oxygen_respiratory_needs`: Oxygen, CPAP/BiPAP, trach, ventilator, or room air.
- `dialysis_need`: Dialysis status and transport/chair-time details.
- `cognitive_status`: Cognition, aphasia, dementia, delirium, or orientation.
- `behavioral_safety_concerns`: Wandering, aggression, refusal, elopement risk, or no concerns.
- `infection_isolation_status`: Isolation status, contradiction, or no isolation.
- `advance_directive_code_status`: Full code or DNR.
- `durable_medical_equipment_needs`: Walker, wheelchair, bariatric bed, mechanical lift, oxygen, CPAP, trach supplies, etc.
- `missing_or_unclear_items`: Known gaps requiring follow-up.

## Label files

### `gold_extractions.jsonl`

One JSON object per referral with the gold structured extraction.

### `evidence_labels.jsonl`

One JSON object per referral. Each important field includes exact source evidence:
- `source_doc_id`
- `document_type`
- `quote`
- `char_start`
- `char_end`
- `quote_verified`

### `mismatch_labels.jsonl`

One JSON object per referral. Each mismatch includes:
- `mismatch_type`
- `severity`
- `reason`
- `evidence`
- `recommended_action`

## Important mismatch types

- `payer_not_accepted`
- `authorization_missing`
- `mar_missing`
- `memory_care_gap`
- `behavioral_high_acuity`
- `dialysis_transport_coordination`
- `wound_orders_missing`
- `iv_antibiotics_nurse_review`
- `tracheostomy_gap`
- `ventilator_gap`
- `bariatric_equipment_gap`
- `contradiction_isolation`
- `contradiction_behavioral_status`
- `diet_swallow_orders_missing`
- `qualifying_stay_unclear`
- `after_hours_admission_not_supported`
- `not_snf_level_of_care`
- `assisted_living_level_mismatch`
