from src.extraction.schema import ReferralExtract


def _format_questions(missing_info: list[dict]) -> str:
    if not missing_info:
        return ""
    return "\n".join(
        f"{i}. {item['question']}"
        for i, item in enumerate(missing_info, start=1)
    )


def generate_response_draft(referral: ReferralExtract, evaluation: dict) -> str:
    source = referral.source or "Referral Team"
    patient = referral.patient_initials or "the referred resident"
    status = evaluation["recommendation"]["status"]

    if status == "accept_ready":
        return f'''Hi {source},

Thank you for sending the referral for {patient}.

Based on our initial review, this resident appears to be a strong fit for our facility. We have capacity to proceed with admissions review and can support the documented care needs.

Please confirm the preferred transfer time and send final discharge paperwork when available.

Best,
Admissions Team'''

    if status == "likely_accept_needs_info":
        questions = _format_questions(evaluation["missing_info"])
        return f'''Hi {source},

Thank you for sending the referral for {patient}.

Based on our initial review, this resident may be a fit for our facility pending a few clarifications.

Could you please confirm:
{questions}

Once received, our admissions team can complete review and respond quickly.

Best,
Admissions Team'''

    if status == "clinical_review":
        questions = _format_questions(evaluation["missing_info"])
        follow_up = f"\n\nHelpful follow-up items:\n{questions}" if questions else ""
        return f'''Hi {source},

Thank you for sending the referral for {patient}.

This referral requires clinical review because some care needs may require additional nursing or operational confirmation.{follow_up}

We will review internally and follow up as soon as possible.

Best,
Admissions Team'''

    constraints = evaluation.get("hard_constraints", [])
    reasons = "\n".join(f"- {item['message']}" for item in constraints)
    if not reasons:
        reasons = "- Facility fit issue identified."

    return f'''Hi {source},

Thank you for sending the referral for {patient}.

Based on the information currently available, this resident does not appear to be an appropriate fit for our facility at this time.

Reason(s):
{reasons}

If circumstances change or additional information becomes available, please feel free to resend for review.

Best,
Admissions Team'''
