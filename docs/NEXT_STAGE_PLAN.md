# CensusFlow Next Stage Plan (Phase 0)

## Current architecture (as-is)

- **Streamlit app entrypoint:** `app.py`
  - Loads facility + payer config
  - Lists referral IDs from text packets
  - Loads packet text, extracts `ReferralExtract`, evaluates fit/constraints, and renders inbox/review/analytics/architecture tabs
- **Extraction schema:** `src/extraction/schema.py`
  - `ReferralExtract` contains core referral fields, `missing_or_unclear_items`, and legacy `evidence: Dict[str, str]`
- **Extraction paths:**
  - `src/extraction/deterministic_extractor.py` (regex extraction from clean synthetic packet text)
  - `src/extraction/extractor_router.py` and `src/extraction/hf_extractor.py` (optional local HF fallback path)
- **Ingestion:** `src/ingestion/document_loader.py`
  - Reads `.txt` packets from `data/referrals/text_packets`
  - Lists IDs via `REF-*.txt`
- **Scoring/evaluation:** `src/scoring/fit_engine.py`
  - Hard constraints + score components (clinical/operational/financial/completeness/urgency)
  - Final recommendation synthesis
- **Missing info workflow:** `src/workflow/missing_info.py`
  - High/medium missing info checks including MAR/allergies/auth/swallow-related checks
- **Data layout currently in use:**
  - `data/referrals/text_packets`
  - `data/facilities`
  - `data/rules`

## Proposed v2 architecture (incremental, backwards compatible)

1. **Add bundle-aware ingestion layer (new module, keep old loader intact)**
   - Introduce `src/ingestion/models.py` for shared structured objects:
     - `SourceDocument`, `ReferralDocumentBundle`, `EvidenceSpan`, `MismatchFinding`
   - Introduce `src/ingestion/document_bundle_loader.py`:
     - Prefer `document_bundles/*.json` when present
     - Fallback to wrapping legacy `.txt` packets as one-document bundles
2. **Extend extraction schema with grounded evidence fields**
   - Keep all existing `ReferralExtract` fields and current `evidence` map
   - Add optional exact evidence spans + confidence + conflict metadata + source doc IDs
3. **Add evidence verification utility**
   - Verify quote substring and offsets against source documents
   - Mark unverifiable quotes explicitly (`quote_verified=False`)
4. **Add mismatch detector layer before final recommendation messaging**
   - Return structured mismatch findings (severity, rationale, recommended action, evidence)
   - Preserve existing hard-constraint checks for compatibility
5. **Add bundle extraction path**
   - Support messy multi-document inputs without requiring external APIs

## Where document bundles plug in

- **Primary integration point:** new `src/ingestion/document_bundle_loader.py`
- **Near-term app compatibility:** keep `app.py` on `document_loader.py` during Phase 1; add optional bundle path behind a controlled switch later
- **Filesystem search order (planned):**
  1. `data/referrals/document_bundles`
  2. `censusflow_synthetic_data_v2/data/referrals/document_bundles`
  - If neither exists, fallback to `data/referrals/text_packets`

## Where evidence grounding plugs in

- **Schema:** extend `ReferralExtract` in `src/extraction/schema.py`
- **Extraction outputs:** deterministic/bundle extractors populate `evidence_spans` when possible
- **Verification:** new `src/evidence/verifier.py` checks quotes/offsets against `ReferralDocumentBundle.source_documents`
- **UI usage (later phase):** referral review page displays verified vs unverified evidence separately

## Where mismatch detection plugs in

- **Engine module:** new `src/scoring/mismatch_detector.py`
- **Call site:** `evaluate_referral(...)` in `src/scoring/fit_engine.py` adds `mismatch_findings` to returned evaluation dict
- **UI usage (later phase):** referral review tab adds an “Admissions Risk / Mismatch Review” section above score table

## Backwards compatibility plan for old text packet support

- Keep existing `src/ingestion/document_loader.py` and current app flow initially unchanged.
- New bundle loader will synthesize a one-document bundle from legacy `.txt` packets so downstream code can adopt bundle APIs safely.
- Preserve current deterministic extractor behavior and legacy `evidence` field while introducing richer evidence structures as optional additions.
- Preserve existing scoring, missing info checks, hard constraints, and response draft flow unless explicitly replaced in later phases.

## Phase sequencing summary

- **Completed now (Phase 0):** repo audit + planning doc only.
- **Next requested implementation phase:** **Phase 1** (bundle-aware ingestion with strict backwards compatibility and no app breakage).
