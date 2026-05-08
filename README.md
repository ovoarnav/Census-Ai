# CensusFlow AI MVP

CensusFlow AI is a synthetic-data MVP for an AI-assisted referral capture platform for skilled nursing facilities and assisted living operators.

The goal of the project is to demonstrate how an admissions team could use AI to review inbound referral packets faster, identify facility fit, flag missing information, detect hard constraints, draft responses, and analyze referral/ROI performance.

This is not production-ready healthcare software. It is a strong MVP designed to demonstrate the product workflow, architecture, and business case.

---

## What the Product Does

CensusFlow AI takes synthetic referral packets and turns them into an admissions workflow.

The workflow is:

```text
Referral packet
→ structured extraction
→ ReferralExtract schema validation
→ missing-information checker
→ facility and payer rules
→ hard constraint detection
→ weighted fit scoring
→ priority and next-best-action logic
→ editable response draft
→ referral analytics and ROI dashboard
