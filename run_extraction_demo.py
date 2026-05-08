import json

from src.config import EXTRACTION_OUTPUT_PATH
from src.ingestion.document_loader import list_referral_ids, load_referral_packet
from src.extraction.deterministic_extractor import extract_referral


def main() -> None:
    referral_ids = list_referral_ids()

    if not referral_ids:
        raise RuntimeError("No referral packets found.")

    EXTRACTION_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    extracted = []
    with open(EXTRACTION_OUTPUT_PATH, "w", encoding="utf-8") as f:
        for referral_id in referral_ids:
            text = load_referral_packet(referral_id)
            record = extract_referral(text)
            extracted.append(record)
            f.write(json.dumps(record.model_dump(), ensure_ascii=False) + "\n")

    print(f"Extracted {len(extracted)} referral packets.")
    print(f"Wrote output to: {EXTRACTION_OUTPUT_PATH}")
    print()
    print("Sample extracted records:")
    for record in extracted[:3]:
        print("-", record.short_summary())


if __name__ == "__main__":
    main()
