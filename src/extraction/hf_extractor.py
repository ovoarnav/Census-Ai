import os
import importlib
from functools import lru_cache
from typing import Any, Dict

from src.extraction.json_utils import extract_first_json_object
from src.extraction.prompts import (
    REFERRAL_EXTRACTION_SYSTEM_PROMPT,
    build_referral_extraction_prompt,
)
from src.extraction.schema import ReferralExtract


DEFAULT_MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"


@lru_cache(maxsize=1)
def _load_model_and_tokenizer(model_id: str = DEFAULT_MODEL_ID) -> tuple[Any, Any]:
    """
    Lazy-load the local Hugging Face model.

    Chromebook note:
    This uses a small 0.5B model and CPU by default.
    First run may be slow because the model has to download and initialize.
    """
    try:
        torch = importlib.import_module("torch")
        transformers = importlib.import_module("transformers")
    except ImportError as exc:
        raise RuntimeError(
            "Hugging Face extraction requires transformers and torch. "
            "Install with: pip install transformers torch"
        ) from exc

    auto_tokenizer: Any = getattr(transformers, "AutoTokenizer")
    auto_model_for_causal_lm: Any = getattr(transformers, "AutoModelForCausalLM")

    tokenizer: Any = auto_tokenizer.from_pretrained(
        model_id,
        trust_remote_code=True,
    )

    model: Any = auto_model_for_causal_lm.from_pretrained(
        model_id,
        torch_dtype=torch.float32,
        trust_remote_code=True,
    )

    model.eval()

    return tokenizer, model


def _build_chat_prompt(tokenizer: Any, referral_text: str) -> str:
    user_prompt = build_referral_extraction_prompt(referral_text)

    messages = [
        {"role": "system", "content": REFERRAL_EXTRACTION_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    if hasattr(tokenizer, "apply_chat_template"):
        return tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

    return (
        f"System:\n{REFERRAL_EXTRACTION_SYSTEM_PROMPT}\n\n"
        f"User:\n{user_prompt}\n\n"
        f"Assistant:\n"
    )


def extract_referral_with_hf(
    referral_text: str,
    model_id: str | None = None,
    max_input_chars: int = 9000,
    max_new_tokens: int = 900,
) -> ReferralExtract:
    """
    Extract a ReferralExtract using a local Hugging Face model.

    Flow:
    model output -> JSON parse -> Pydantic validation.

    If this fails, caller should fall back to deterministic extraction.
    """
    selected_model_id = model_id or os.environ.get(
        "CENSUSFLOW_HF_MODEL",
        DEFAULT_MODEL_ID,
    )

    trimmed_text = referral_text[:max_input_chars]

    tokenizer, model = _load_model_and_tokenizer(selected_model_id)
    prompt = _build_chat_prompt(tokenizer, trimmed_text)

    inputs = tokenizer(prompt, return_tensors="pt")

    import torch

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )

    generated_ids = output_ids[0][inputs["input_ids"].shape[-1]:]
    raw_output = tokenizer.decode(generated_ids, skip_special_tokens=True)

    parsed: Dict[str, Any] = extract_first_json_object(raw_output)

    return ReferralExtract(**parsed)