#!/usr/bin/env python3
"""
Validate CensusFlow synthetic dataset v2.

Checks:
- every index row has a text packet and document bundle
- every bundle has gold extraction
- evidence quotes are exact substrings of the referenced source document
- mismatch evidence quotes are exact substrings when quote_verified is true
"""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

def main():
    index_path = ROOT / "data/referrals/referral_index_v2.csv"
    rows = list(csv.DictReader(index_path.open(encoding="utf-8")))
    assert rows, "referral_index_v2.csv is empty"

    gold = {item["referral_id"]: item for item in read_jsonl(ROOT / "data/labels/gold_extractions.jsonl")}
    evidence = {item["referral_id"]: item for item in read_jsonl(ROOT / "data/labels/evidence_labels.jsonl")}
    mismatches = {item["referral_id"]: item for item in read_jsonl(ROOT / "data/labels/mismatch_labels.jsonl")}

    errors = []

    for row in rows:
        rid = row["referral_id"]
        text_path = ROOT / f"data/referrals/text_packets/{rid}.txt"
        bundle_path = ROOT / f"data/referrals/document_bundles/{rid}.json"

        if not text_path.exists():
            errors.append(f"{rid}: missing text packet")
            continue
        if not bundle_path.exists():
            errors.append(f"{rid}: missing document bundle")
            continue

        if rid not in gold:
            errors.append(f"{rid}: missing gold extraction")
        if rid not in evidence:
            errors.append(f"{rid}: missing evidence labels")
        if rid not in mismatches:
            errors.append(f"{rid}: missing mismatch labels")

        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
        docs = {doc["source_doc_id"]: doc for doc in bundle["source_documents"]}

        if rid in evidence:
            for field in evidence[rid]["field_evidence"]:
                for ev in field.get("evidence", []):
                    if not ev.get("quote_verified"):
                        errors.append(f"{rid}: unverified evidence quote for field {field['field']}")
                        continue
                    doc = docs.get(ev["source_doc_id"])
                    if not doc:
                        errors.append(f"{rid}: evidence references missing doc {ev['source_doc_id']}")
                        continue
                    quote = ev["quote"]
                    start = ev["char_start"]
                    end = ev["char_end"]
                    if doc["text"][start:end] != quote:
                        errors.append(f"{rid}: evidence offset mismatch for {field['field']}")

        if rid in mismatches:
            for mismatch in mismatches[rid]["mismatches"]:
                for ev in mismatch.get("evidence", []):
                    if not ev or not ev.get("quote_verified"):
                        continue
                    doc = docs.get(ev["source_doc_id"])
                    if not doc:
                        errors.append(f"{rid}: mismatch evidence references missing doc {ev['source_doc_id']}")
                        continue
                    quote = ev["quote"]
                    start = ev["char_start"]
                    end = ev["char_end"]
                    if doc["text"][start:end] != quote:
                        errors.append(f"{rid}: mismatch evidence offset mismatch for {mismatch['mismatch_type']}")

    if errors:
        print("VALIDATION FAILED")
        for err in errors:
            print("-", err)
        raise SystemExit(1)

    print(f"VALIDATION PASSED: {len(rows)} referrals checked.")

if __name__ == "__main__":
    main()
