import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
V2_DATASET_ROOT = PROJECT_ROOT / "sythentic_censusdata"

if (V2_DATASET_ROOT / "data").exists():
    DATA_DIR = V2_DATASET_ROOT / "data"
else:
    DATA_DIR = PROJECT_ROOT / "data"

REFERRAL_PACKET_DIR = DATA_DIR / "referrals" / "text_packets"

if (DATA_DIR / "referrals" / "referral_index_v2.csv").exists():
    REFERRAL_INDEX_PATH = DATA_DIR / "referrals" / "referral_index_v2.csv"
else:
    REFERRAL_INDEX_PATH = DATA_DIR / "referrals" / "referral_index.csv"

EXTRACTION_OUTPUT_PATH = PROJECT_ROOT / "outputs" / "extracted_referrals.jsonl"


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


USE_DOCUMENT_BUNDLES = _env_bool("USE_DOCUMENT_BUNDLES", True)
EXTRACTION_MODE = os.environ.get("EXTRACTION_MODE", "deterministic")
REQUIRE_VERIFIED_QUOTES = _env_bool("REQUIRE_VERIFIED_QUOTES", False)