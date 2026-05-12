# CensusFlow AI MVP

CensusFlow AI is a **synthetic-data MVP** for AI-assisted referral capture and admissions review for skilled nursing facilities / assisted living operators.

> This repository is for workflow support and product prototyping only. It is **not** production clinical decision software and contains no real patient PHI.

---

## Current capabilities

- Legacy `.txt` referral packet ingestion.
- Bundle-aware ingestion (`document_bundles/*.json`) with fallback to legacy text packets.
- Structured extraction into `ReferralExtract`.
- Evidence grounding fields (`evidence_spans`, verification status, confidence).
- Missing-information detection.
- Hard-constraint checks and fit scoring.
- Mismatch-first admissions risk detection.
- Referral Review dashboard with mismatch + evidence sections.
- ROI and referral analytics views.

---

## Data modes

### 1) Original synthetic demo data (already in repo)
- `data/referrals/text_packets/*.txt`
- `data/facilities/*`
- `data/rules/*`

### 2) v2 bundle dataset (optional, copied in later)
Expected location:

- `censusflow_synthetic_data_v2/data/referrals/document_bundles/*.json`
- `censusflow_synthetic_data_v2/data/referrals/text_packets/*.txt`
- `censusflow_synthetic_data_v2/data/labels/*.jsonl`

The code is built to run with either dataset shape.

---

## Configuration flags

Set via environment variables (see `.env.example`):

- `USE_DOCUMENT_BUNDLES=true|false`
- `EXTRACTION_MODE=deterministic|heuristic_bundle|hf_with_fallback`
- `REQUIRE_VERIFIED_QUOTES=true|false`

Notes:
- Legacy flow remains available even when bundle mode is disabled.
- `hf_with_fallback` uses local HF extraction and falls back deterministically.

---

## Run the app

```bash
streamlit run app.py
```

If data files are missing, the app now shows friendly setup guidance instead of crashing.

---

## Run validation / evaluation scripts

Extraction metrics:

```bash
python src/evaluation/evaluate_extractions.py
```

Mismatch metrics:

```bash
python src/evaluation/evaluate_mismatches.py
```

If label files are not present yet, scripts print a friendly message and exit.

---

## Safety framing

- Synthetic data only.
- No external API calls are required for default flows.
- Outputs are intended for **human admissions review support**, not autonomous medical decisions.
