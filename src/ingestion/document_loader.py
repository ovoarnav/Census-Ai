from pathlib import Path
from typing import List
import csv

import pandas as pd

from src.config import REFERRAL_PACKET_DIR, REFERRAL_INDEX_PATH


def load_referral_packet(referral_id: str) -> str:
    path: Path = REFERRAL_PACKET_DIR / f"{referral_id}.txt"

    if not path.exists():
        raise FileNotFoundError(f"Referral packet not found: {path}")

    return path.read_text(encoding="utf-8")


def list_referral_ids() -> List[str]:
    return sorted(path.stem for path in REFERRAL_PACKET_DIR.glob("REF-*.txt"))


def load_referral_index() -> pd.DataFrame:
    if not REFERRAL_INDEX_PATH.exists():
        raise FileNotFoundError(f"Referral index not found: {REFERRAL_INDEX_PATH}")

    with open(REFERRAL_INDEX_PATH, mode="r", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))

    return pd.DataFrame(rows)