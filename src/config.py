from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

REFERRAL_PACKET_DIR = DATA_DIR / "referrals" / "text_packets"
REFERRAL_INDEX_PATH = DATA_DIR / "referrals" / "referral_index.csv"
EXTRACTION_OUTPUT_PATH = PROJECT_ROOT / "outputs" / "extracted_referrals.jsonl"
