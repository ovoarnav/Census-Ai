from typing import Literal

from src.extraction.deterministic_extractor import (
    extract_referral as extract_referral_deterministic,
)
from src.extraction.hf_extractor import extract_referral_with_hf
from src.extraction.schema import ReferralExtract


ExtractionMode = Literal["deterministic", "hf_with_fallback"]


def extract_referral_by_mode(
    referral_text: str,
    mode: ExtractionMode = "deterministic",
) -> ReferralExtract:
    """
    Choose extraction mode.

    deterministic:
        Fast, reliable baseline for synthetic packets.

    hf_with_fallback:
        Try local Hugging Face extraction. If model loading, generation,
        JSON parsing, or schema validation fails, fall back to deterministic.
    """
    if mode == "deterministic":
        return extract_referral_deterministic(referral_text)

    if mode == "hf_with_fallback":
        try:
            return extract_referral_with_hf(referral_text)
        except Exception:
            return extract_referral_deterministic(referral_text)

    raise ValueError(f"Unknown extraction mode: {mode}")