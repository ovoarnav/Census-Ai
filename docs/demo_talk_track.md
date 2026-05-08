# CensusFlow AI Demo Talk Track

## One-sentence pitch

CensusFlow AI helps small and mid-sized SNF and assisted living operators capture more admissions by turning messy referral packets into fast, explainable, human-reviewed admission workflow decisions.

## Demo story

1. Open the Referral Inbox.
2. Show that all referrals are prioritized by status, fit score, missing information, hard constraints, and next best action.
3. Open an accept-ready referral and show that the system identifies why it is a good fit.
4. Open a missing-info referral and show the exact questions the admissions team should ask.
5. Open a decline case and show hard facility constraints.
6. Show the response draft.
7. Show analytics and ROI sensitivity.
8. Explain that the MVP uses synthetic data and deterministic extraction, with the architecture designed for a local Hugging Face model later.

## Core product point

This is not an autonomous clinical decision-maker. It is a referral workflow command center that helps admissions teams move faster while keeping humans in control.

## Key technical point

The model/extraction layer should extract facts. The scoring/rules layer should remain deterministic, auditable, and facility-specific.
