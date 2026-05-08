import json
from pathlib import Path

from src.config import DATA_DIR


FACILITY_PROFILE_PATH = DATA_DIR / "facilities" / "facility_profile_green_valley_snf.json"
PAYER_RULES_PATH = DATA_DIR / "rules" / "payer_rules.json"
CAPABILITY_RULES_PATH = DATA_DIR / "rules" / "capability_rules.json"
MISSING_INFO_POLICY_PATH = DATA_DIR / "rules" / "missing_info_policy.json"


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing config file: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_facility_profile() -> dict:
    return load_json(FACILITY_PROFILE_PATH)


def load_payer_rules() -> dict:
    return load_json(PAYER_RULES_PATH)


def load_capability_rules() -> dict:
    return load_json(CAPABILITY_RULES_PATH)


def load_missing_info_policy() -> dict:
    return load_json(MISSING_INFO_POLICY_PATH)
