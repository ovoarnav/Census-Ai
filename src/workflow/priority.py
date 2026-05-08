from typing import Any, Dict


def get_next_best_action(evaluation: Dict[str, Any]) -> str:
    recommendation = evaluation["recommendation"]
    status = recommendation["status"]

    hard_constraints = evaluation.get("hard_constraints", [])
    missing_info = evaluation.get("missing_info", [])

    if status == "accept_ready":
        return "Respond now — strong fit"

    if status == "likely_accept_needs_info":
        high_missing = [
            item for item in missing_info
            if item.get("severity") == "high"
        ]
        if high_missing:
            return "Request high-priority missing info"
        return "Request clarification"

    if status == "clinical_review":
        return "Route to nurse / clinical reviewer"

    if status == "decline_recommended":
        if hard_constraints:
            return "Decline or escalate due to hard constraint"
        return "Decline or review manually"

    return "Review manually"


def get_priority_level(evaluation: Dict[str, Any]) -> str:
    status = evaluation["recommendation"]["status"]
    score = int(evaluation["overall_score"])
    hard_constraints = evaluation.get("hard_constraints", [])
    missing_info = evaluation.get("missing_info", [])

    high_missing_count = sum(
        1 for item in missing_info
        if item.get("severity") == "high"
    )

    if status == "accept_ready" and score >= 85:
        return "High"

    if status == "likely_accept_needs_info" and high_missing_count <= 2:
        return "High"

    if status == "clinical_review":
        return "Medium"

    if hard_constraints:
        return "Low"

    if score >= 75:
        return "Medium"

    return "Low"
