import json
from pathlib import Path
from typing import Any

from src.config import DATA_DIR


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing config file: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}, got {type(data).__name__}")

    return data


def load_facility_profile() -> dict[str, Any]:
    """
    Supports old MVP:
      data/facilities/facility_profile_green_valley_snf.json

    Supports v2 dataset:
      data/facilities/facility_profiles.json
    """
    old_path = DATA_DIR / "facilities" / "facility_profile_green_valley_snf.json"
    new_path = DATA_DIR / "facilities" / "facility_profiles.json"

    if old_path.exists():
        return load_json(old_path)

    if new_path.exists():
        profiles_data = load_json(new_path)

        # Case 1: {"facilities": [...]}
        facilities = profiles_data.get("facilities")
        if isinstance(facilities, list):
            for profile in facilities:
                if isinstance(profile, dict) and profile.get("facility_id") == "GV-SNF-001":
                    return profile
            if facilities and isinstance(facilities[0], dict):
                return facilities[0]

        # Case 2: {"GV-SNF-001": {...}}
        profile = profiles_data.get("GV-SNF-001")
        if isinstance(profile, dict):
            return profile

        # Case 3: already a single facility profile
        if profiles_data.get("facility_id"):
            return profiles_data

        raise ValueError(f"Could not parse facility profile file: {new_path}")

    raise FileNotFoundError(
        "Missing facility config. Checked:\n"
        f"- {old_path}\n"
        f"- {new_path}"
    )


def load_payer_rules() -> dict[str, Any]:
    """
    Supports old MVP:
      data/rules/payer_rules.json

    Supports v2 dataset:
      data/rules/payer_rules_v2.json
    """
    old_path = DATA_DIR / "rules" / "payer_rules.json"
    new_path = DATA_DIR / "rules" / "payer_rules_v2.json"

    if old_path.exists():
        return load_json(old_path)

    if new_path.exists():
        return load_json(new_path)

    raise FileNotFoundError(
        "Missing payer rules. Checked:\n"
        f"- {old_path}\n"
        f"- {new_path}"
    )


def load_capability_rules() -> dict[str, Any]:
    old_path = DATA_DIR / "rules" / "capability_rules.json"
    if old_path.exists():
        return load_json(old_path)

    return {}


def load_missing_info_policy() -> dict[str, Any]:
    old_path = DATA_DIR / "rules" / "missing_info_policy.json"
    if old_path.exists():
        return load_json(old_path)

    return {}