from __future__ import annotations


def contains(text: str | None, *keywords: str) -> bool:
    if not text:
        return False
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)
