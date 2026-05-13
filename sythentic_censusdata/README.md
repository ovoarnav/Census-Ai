# CensusFlow Synthetic Referral Dataset v2

This dataset is synthetic and contains **no real patient data**. It is designed as a higher-quality backbone for the CensusFlow AI admissions/referral review MVP.

## What is included

- 36 synthetic referral cases
- 3 synthetic facility profiles with different constraints
- Backward-compatible `.txt` packets for the current Streamlit app
- Rich JSON document bundles for next-stage ingestion work
- Gold extraction labels
- Exact evidence labels with source document IDs and character offsets
- Mismatch labels focused on reasons a referral may fail or need escalation
- Payer rules and mismatch rule seeds
- Validation script

## Directory structure

```text
data/
  facilities/
    facility_profiles.json
  rules/
    payer_rules_v2.json
    mismatch_rules_seed.json
  referrals/
    referral_index_v2.csv
    text_packets/
    document_bundles/
  labels/
    gold_extractions.jsonl
    evidence_labels.jsonl
    mismatch_labels.jsonl
scripts/
  validate_dataset.py
  summarize_dataset.py
```

## Design philosophy

The dataset is built around the core product idea:

> Do not just recommend good-fit referrals. First search for reasons the referral may fail at the center.

That means the labels emphasize:
- hard facility constraints
- payer/auth blockers
- missing safety-critical information
- contradictions across documents
- low-confidence OCR/handwriting
- operational timing and capacity issues
- evidence-grounded rationale

## Backward compatibility

The files in `data/referrals/text_packets/` preserve the exact normalized field labels used by the current deterministic extractor. They also include raw source documents underneath so the same file can support both the current demo and a future LLM extraction pipeline.

## Recommended next architecture

Use `document_bundles/*.json` as the source of truth for the next ingestion layer:

```text
source_documents
  -> extraction with exact evidence
  -> schema validation
  -> contradiction detection
  -> mismatch detection
  -> deterministic scoring
  -> human-reviewed response draft
```

## Evidence policy

For the production-shaped version, UI quotes should only be shown if they are exact substrings from a source document. Paraphrased evidence should be treated as unverified and should not be displayed as a quote.

## Synthetic data warning

All names are initials only. All facilities, referral sources, and patient details are synthetic.
