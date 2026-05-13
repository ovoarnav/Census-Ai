#!/usr/bin/env python3
import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    rows = list(csv.DictReader((ROOT / "data/referrals/referral_index_v2.csv").open(encoding="utf-8")))
    print(f"Referrals: {len(rows)}")
    print("Statuses:")
    for k, v in Counter(row["expected_status"] for row in rows).items():
        print(f"  {k}: {v}")
    print("Facilities:")
    for k, v in Counter(row["target_facility_id"] for row in rows).items():
        print(f"  {k}: {v}")
    print("Top mismatch types:")
    c = Counter()
    for row in rows:
        for m in row["mismatch_types"].split("|"):
            if m:
                c[m] += 1
    for k, v in c.most_common(15):
        print(f"  {k}: {v}")

if __name__ == "__main__":
    main()
