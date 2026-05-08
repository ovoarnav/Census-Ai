import json
from typing import Any, Dict


def extract_first_json_object(text: str) -> Dict[str, Any]:
    """
    Extract the first JSON object from a model response.

    Small local models sometimes emit text before/after JSON.
    This tries to recover the first complete JSON object.
    """
    text = text.strip()

    if not text:
        raise ValueError("Model output is empty.")

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object start found in model output.")

    depth = 0
    in_string = False
    escape = False

    for i in range(start, len(text)):
        char = text[i]

        if escape:
            escape = False
            continue

        if char == "\\":
            escape = True
            continue

        if char == '"':
            in_string = not in_string
            continue

        if in_string:
            continue

        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                candidate = text[start:i + 1]
                parsed = json.loads(candidate)
                if not isinstance(parsed, dict):
                    raise ValueError("Extracted JSON is not an object.")
                return parsed

    raise ValueError("Could not find a complete JSON object in model output.")