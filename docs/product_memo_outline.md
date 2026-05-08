# Product Memo Outline

## 1. Executive Summary

Build an AI-assisted referral capture platform for American Data's ECS customer base. The product helps small and mid-sized SNF/AL operators review referrals faster, identify facility fit, reduce missed admissions, and improve census.

## 2. Problem

Referral intake is fragmented, time-sensitive, and operationally messy. Facilities must evaluate clinical fit, payer fit, bed availability, equipment needs, missing information, and safety risks quickly. Slow or incomplete responses can lose beds.

## 3. Product

CensusFlow AI ingests referral packets, extracts structured information, checks missing information, compares referrals against facility-specific capabilities, generates fit recommendations, and drafts human-reviewed responses.

## 4. MVP

The MVP uses synthetic data, deterministic extraction, facility rules, payer rules, fit scoring, a referral dashboard, and ROI sensitivity modeling.

## 5. Differentiation

The wedge is not a generic AI summarizer. The wedge is an ECS-adjacent referral command center for small independent operators: lightweight, explainable, facility-specific, and revenue-focused.

## 6. Risk Controls

- Synthetic data for demo
- Human-in-the-loop decisions
- No autonomous admission decisioning
- Evidence snippets
- Rules-based scoring
- Future secure deployment controls

## 7. Deployment Path

Standalone synthetic MVP → local open-source model extraction → secure document ingestion → ECS integration → audit logs and role-based workflow → referral analytics and source optimization.
