from typing import Any, Dict, List

import pandas as pd

from src.workflow.priority import get_next_best_action, get_priority_level


def build_evaluation_table(evaluations: List[Dict[str, Any]]) -> pd.DataFrame:
    rows = []

    for item in evaluations:
        referral = item["referral"]
        evaluation = item["evaluation"]
        recommendation = evaluation["recommendation"]
        scores = evaluation["scores"]

        missing_info = evaluation.get("missing_info", [])
        hard_constraints = evaluation.get("hard_constraints", [])

        missing_high = sum(
            1 for missing in missing_info
            if missing.get("severity") == "high"
        )

        rows.append({
            "referral_id": referral.referral_id,
            "source": referral.source,
            "channel": referral.channel,
            "patient": referral.patient_initials,
            "age": referral.age,
            "payer": referral.payer,
            "diagnosis": referral.primary_diagnosis,
            "status": recommendation["status"],
            "recommendation": recommendation["label"],
            "next_best_action": get_next_best_action(evaluation),
            "priority": get_priority_level(evaluation),
            "overall_score": evaluation["overall_score"],
            "clinical_fit": scores["clinical_fit"],
            "operational_fit": scores["operational_fit"],
            "financial_fit": scores["financial_fit"],
            "completeness": scores["completeness"],
            "urgency": scores["urgency"],
            "missing_total": len(missing_info),
            "missing_high": missing_high,
            "hard_constraints": len(hard_constraints),
        })

    return pd.DataFrame(rows)


def summarize_dashboard(table: pd.DataFrame) -> Dict[str, Any]:
    if table.empty:
        return {
            "total_referrals": 0,
            "accept_ready": 0,
            "needs_info": 0,
            "clinical_review": 0,
            "decline_recommended": 0,
            "high_priority": 0,
            "average_score": 0,
        }

    return {
        "total_referrals": int(len(table)),
        "accept_ready": int((table["status"] == "accept_ready").sum()),
        "needs_info": int((table["status"] == "likely_accept_needs_info").sum()),
        "clinical_review": int((table["status"] == "clinical_review").sum()),
        "decline_recommended": int((table["status"] == "decline_recommended").sum()),
        "high_priority": int((table["priority"] == "High").sum()),
        "average_score": round(float(table["overall_score"].mean()), 1),
    }


def source_performance(table: pd.DataFrame) -> pd.DataFrame:
    if table.empty:
        return pd.DataFrame()

    grouped = table.groupby("source").agg(
        referrals=("referral_id", "count"),
        average_score=("overall_score", "mean"),
        high_priority=("priority", lambda values: int((values == "High").sum())),
        accept_ready=("status", lambda values: int((values == "accept_ready").sum())),
        needs_info=("status", lambda values: int((values == "likely_accept_needs_info").sum())),
        clinical_review=("status", lambda values: int((values == "clinical_review").sum())),
        decline_recommended=("status", lambda values: int((values == "decline_recommended").sum())),
    ).reset_index()

    grouped["average_score"] = grouped["average_score"].round(1)
    return grouped.sort_values(["high_priority", "referrals", "average_score"], ascending=[False, False, False])
