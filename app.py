from typing import Any, Dict, List, Tuple, cast
import pandas as pd
import streamlit as st

from src.analytics.metrics import build_evaluation_table, source_performance, summarize_dashboard
from src.analytics.roi import estimate_monthly_revenue_lift, format_currency
from src.extraction.deterministic_extractor import extract_referral
from pydantic import ValidationError

from src.extraction.schema import ReferralExtract
from src.ingestion.config_loader import load_facility_profile, load_payer_rules
from src.ingestion.document_loader import list_referral_ids, load_referral_packet
from src.scoring.fit_engine import evaluate_referral
from src.workflow.response_draft import generate_response_draft
from src.extraction.extractor_router import extract_referral_by_mode

EvaluationBundle = Dict[str, Any]


STATUS_LABELS = {
    "accept_ready": "Accept-ready",
    "likely_accept_needs_info": "Likely accept — needs info",
    "clinical_review": "Clinical review",
    "decline_recommended": "Decline recommended",
}


def status_label(status: str) -> str:
    return STATUS_LABELS.get(status, status)


@st.cache_data
def load_all_evaluations() -> Tuple[List[EvaluationBundle], List[Dict[str, str]]]:
    facility = load_facility_profile()
    payer_rules = load_payer_rules()

    results: List[EvaluationBundle] = []
    skipped_referrals: List[Dict[str, str]] = []

    for referral_id in list_referral_ids():
        try:
            raw_packet = load_referral_packet(referral_id)
            referral = extract_referral(raw_packet)
            evaluation = evaluate_referral(referral, facility, payer_rules)
        except (FileNotFoundError, ValidationError, ValueError, KeyError) as exc:
            skipped_referrals.append({
                "referral_id": referral_id,
                "error": str(exc).splitlines()[0][:180],
            })
            continue

        results.append({
            "referral": referral,
            "evaluation": evaluation,
            "raw_packet": raw_packet,
        })

    return results, skipped_referrals


def find_bundle(evaluations: List[EvaluationBundle], referral_id: str) -> EvaluationBundle:
    for bundle in evaluations:
        referral = bundle["referral"]
        if referral.referral_id == referral_id:
            return bundle

    raise ValueError(f"Referral not found: {referral_id}")


def render_score_table(evaluation: Dict[str, Any]) -> None:
    scores = evaluation["scores"]
    score_rows = [
        {"Category": "Clinical fit", "Score": scores["clinical_fit"]},
        {"Category": "Operational fit", "Score": scores["operational_fit"]},
        {"Category": "Financial fit", "Score": scores["financial_fit"]},
        {"Category": "Completeness", "Score": scores["completeness"]},
        {"Category": "Urgency", "Score": scores["urgency"]},
    ]
    st.dataframe(pd.DataFrame(score_rows), use_container_width=True, hide_index=True)


def render_missing_info(evaluation: Dict[str, Any]) -> None:
    missing_info = evaluation["missing_info"]

    if not missing_info:
        st.success("No major missing information detected.")
        return

    for item in missing_info:
        severity = str(item["severity"]).upper()
        question = str(item["question"])
        reason = str(item["reason"])
        st.warning(f"**{severity}** — {question}\n\n{reason}")


def render_hard_constraints(evaluation: Dict[str, Any]) -> None:
    hard_constraints = evaluation["hard_constraints"]

    if not hard_constraints:
        st.success("No hard facility constraints triggered.")
        return

    for item in hard_constraints:
        st.error(f"**{item['type']}** — {item['message']}")




def render_mismatch_findings(evaluation: Dict[str, Any]) -> None:
    findings = evaluation.get("mismatch_findings", [])
    if not findings:
        st.success("No mismatch findings detected.")
        return

    for item in findings:
        severity = str(item.get("severity", "unknown")).upper()
        mismatch_type = str(item.get("mismatch_type", "unknown"))
        message = str(item.get("message", ""))
        why_it_matters = str(item.get("why_it_matters", ""))
        recommended_action = str(item.get("recommended_action", ""))
        evidence = item.get("evidence") or {}
        quote = evidence.get("quote") if isinstance(evidence, dict) else None
        quote_verified = evidence.get("quote_verified") if isinstance(evidence, dict) else None

        if severity in {"CRITICAL", "HIGH"}:
            st.error(f"**{severity}** — `{mismatch_type}`: {message}")
        elif severity == "MEDIUM":
            st.warning(f"**{severity}** — `{mismatch_type}`: {message}")
        else:
            st.info(f"**{severity}** — `{mismatch_type}`: {message}")

        st.write(f"**Why it matters:** {why_it_matters}")
        st.write(f"**Recommended action:** {recommended_action}")

        if quote:
            quote_label = "verified" if quote_verified else "unverified"
            st.caption(f"Evidence ({quote_label}): \"{quote}\"")


def render_evidence_grounding(referral: ReferralExtract) -> None:
    fields = [
        "payer",
        "authorization_status",
        "primary_diagnosis",
        "current_medications_or_mar",
        "allergies",
        "infection_isolation_status",
        "cognitive_status",
        "behavioral_safety_concerns",
        "oxygen_respiratory_needs",
        "dialysis_need",
    ]

    rows = []
    for field_name in fields:
        value = getattr(referral, field_name, None)
        best = referral.get_best_evidence(field_name)
        if best:
            rows.append({
                "field": field_name,
                "value": value,
                "source_doc_id": best.source_doc_id,
                "exact_quote": best.quote,
                "quote_verified": best.quote_verified,
                "confidence": referral.extraction_confidence.get(field_name),
                "evidence_status": "verified" if best.quote_verified else "unverified/low-confidence",
            })
        else:
            rows.append({
                "field": field_name,
                "value": value,
                "source_doc_id": None,
                "exact_quote": None,
                "quote_verified": False,
                "confidence": referral.extraction_confidence.get(field_name),
                "evidence_status": "missing evidence",
            })

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

def render_referral_summary(referral: ReferralExtract) -> None:
    summary_rows = [
        ("Referral ID", referral.referral_id),
        ("Source", referral.source),
        ("Channel", referral.channel),
        ("Patient", referral.patient_initials),
        ("Age", referral.age),
        ("Payer", referral.payer),
        ("Authorization", referral.authorization_status),
        ("Primary diagnosis", referral.primary_diagnosis),
        ("Hospital course", referral.current_course_of_illness),
        ("Medications/MAR", referral.current_medications_or_mar),
        ("Allergies", referral.allergies),
        ("Mobility/transfer", referral.mobility_transfer_status),
        ("Therapy need", referral.therapy_need),
        ("Wound/skin", referral.wound_skin_needs),
        ("Oxygen/respiratory", referral.oxygen_respiratory_needs),
        ("Dialysis", referral.dialysis_need),
        ("Cognitive status", referral.cognitive_status),
        ("Behavioral/safety", referral.behavioral_safety_concerns),
        ("Infection/isolation", referral.infection_isolation_status),
        ("Code status", referral.advance_directive_code_status),
        ("DME", referral.durable_medical_equipment_needs),
    ]

    df = pd.DataFrame(summary_rows, columns=["Field", "Value"])
    st.dataframe(df, use_container_width=True, hide_index=True)


def main() -> None:
    st.set_page_config(
        page_title="CensusFlow AI",
        page_icon="🏥",
        layout="wide",
    )

    st.title("CensusFlow AI")
    st.caption("Synthetic MVP — referral capture, fit scoring, admissions response support, and census-growth analytics")

    evaluations, skipped_referrals = load_all_evaluations()
    st.session_state["load_skipped_referrals"] = skipped_referrals
    if not evaluations:
        st.error("No referral data could be loaded. Confirm synthetic data files exist under data/referrals/text_packets.")
        st.info("You can also copy the optional v2 dataset into censusflow_synthetic_data_v2/ and rerun.")
        return

    table = build_evaluation_table(evaluations)
    summary = summarize_dashboard(table)

    with st.sidebar:
        st.header("Demo controls")
        status_options = ["All"] + list(STATUS_LABELS.values())
        selected_status_label = st.selectbox("Filter by status", status_options)

        priority_options = ["All", "High", "Medium", "Low"]
        selected_priority = st.selectbox("Filter by priority", priority_options)

        st.markdown("---")
        st.caption("This MVP uses synthetic data only.")

    filtered_table = table.copy()

    if selected_status_label != "All":
        reverse_status_map = {value: key for key, value in STATUS_LABELS.items()}
        filtered_table = filtered_table[
            filtered_table["status"] == reverse_status_map[selected_status_label]
        ]

    if selected_priority != "All":
        filtered_table = filtered_table[
            filtered_table["priority"] == selected_priority
        ]

    tabs = st.tabs([
        "Referral Inbox",
        "Referral Review",
        "Analytics + ROI",
        "Architecture",
    ])

    with tabs[0]:
        st.subheader("Referral Inbox")

        c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
        c1.metric("Total", summary["total_referrals"])
        c2.metric("High priority", summary["high_priority"])
        c3.metric("Accept-ready", summary["accept_ready"])
        c4.metric("Needs info", summary["needs_info"])
        c5.metric("Clinical review", summary["clinical_review"])
        c6.metric("Decline", summary["decline_recommended"])
        c7.metric("Avg score", summary["average_score"])

        display_table = filtered_table.copy()
        display_table["status"] = display_table["status"].map(status_label)
        display_table = display_table[
            [
                "priority",
                "referral_id",
                "source",
                "channel",
                "patient",
                "payer",
                "diagnosis",
                "status",
                "overall_score",
                "next_best_action",
                "missing_high",
                "hard_constraints",
            ]
        ]

        st.dataframe(display_table, use_container_width=True, hide_index=True)

    with tabs[1]:
        st.subheader("Referral Review")

        skipped_referrals = st.session_state.get("load_skipped_referrals", [])
        if skipped_referrals:
            st.warning(f"{len(skipped_referrals)} referrals skipped during load.")
            with st.expander("Show skipped referral details"):
                st.dataframe(pd.DataFrame(skipped_referrals), use_container_width=True, hide_index=True)

        if filtered_table.empty:
            st.info("No referrals match the current filters.")
        else:
            referral_ids = filtered_table["referral_id"].tolist()
            selected_referral_id = st.selectbox("Select referral", referral_ids)

            bundle = find_bundle(evaluations, selected_referral_id)
            referral = bundle["referral"]
            evaluation = bundle["evaluation"]
            raw_packet = bundle["raw_packet"]

            st.markdown("#### Optional local LLM extraction")

            use_hf_extractor = st.checkbox(
                "Run local Hugging Face extractor on this selected referral",
                value=False,
            )

            if use_hf_extractor:
                st.warning(
                    "This may be slow on Chromebook. If the local model fails, "
                    "the app falls back to deterministic extraction."
                )

                with st.spinner("Running local Hugging Face extraction..."):
                    referral = extract_referral_by_mode(
                        raw_packet,
                        mode="hf_with_fallback",
                    )

                    facility = load_facility_profile()
                    payer_rules = load_payer_rules()

                    evaluation = evaluate_referral(
                        referral,
                        facility,
                        payer_rules,
                    )

            row = table[table["referral_id"] == selected_referral_id].iloc[0]
            recommendation = cast(Dict[str, Any], evaluation["recommendation"])

            headline_cols = st.columns([1, 1, 1])
            headline_cols[0].metric("Priority", row["priority"])
            headline_cols[1].metric("Next action", row["next_best_action"])
            headline_cols[2].metric("Overall score", f"{evaluation['overall_score']}/100")

            top_left, top_right = st.columns([1.2, 0.8])

            with top_left:
                st.markdown("### AI Referral Summary")
                render_referral_summary(referral)

            with top_right:
                st.markdown("### Fit Recommendation")
                st.metric(recommendation["label"], f"{evaluation['overall_score']}/100")

                st.markdown("#### Admissions Risk / Mismatch Review")
                render_mismatch_findings(evaluation)

                st.markdown("#### Score Breakdown")
                render_score_table(evaluation)

                st.markdown("#### Recommendation Reasoning")
                for reason in recommendation["reasons"]:
                    st.write(f"- {reason}")

            st.markdown("---")

            left, right = st.columns(2)

            with left:
                st.markdown("### Missing / Unclear Information")
                render_missing_info(evaluation)

            with right:
                st.markdown("### Hard Constraints")
                render_hard_constraints(evaluation)

            st.markdown("---")

            evidence_col, response_col = st.columns([1, 1])

            with evidence_col:
                st.markdown("### Evidence Grounding")
                render_evidence_grounding(referral)

                with st.expander("Raw synthetic packet"):
                    st.text(raw_packet)

            with response_col:
                st.markdown("### Editable Response Draft")
                draft = generate_response_draft(referral, evaluation)
                st.text_area("Draft to referral source", value=draft, height=360)

    with tabs[2]:
        st.subheader("Pipeline Analytics + ROI")

        status_counts = table["status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        status_counts["Status"] = status_counts["Status"].map(status_label)

        st.markdown("### Status Counts")
        st.bar_chart(status_counts.set_index("Status"))

        st.markdown("### Referral Source Performance")
        source_df = source_performance(table)
        st.dataframe(source_df, use_container_width=True, hide_index=True)

        st.markdown("### Score Distribution")
        score_chart_df = table[["referral_id", "overall_score"]].set_index("referral_id")
        st.bar_chart(score_chart_df)

        st.markdown("---")
        st.markdown("### ROI Sensitivity Model")
        st.caption("Illustrative only — designed to show the business case structure, not validated customer economics.")

        r1, r2, r3 = st.columns(3)
        monthly_referral_volume = r1.number_input("Monthly referral volume", min_value=1, value=150, step=5)
        baseline_conversion_rate = r2.slider("Baseline conversion rate", min_value=0.0, max_value=1.0, value=0.32, step=0.01)
        improved_conversion_rate = r3.slider("Improved conversion rate", min_value=0.0, max_value=1.0, value=0.36, step=0.01)

        r4, r5 = st.columns(2)
        average_daily_revenue = r4.number_input("Average daily revenue per admission ($)", min_value=1, value=475, step=25)
        average_length_of_stay = r5.number_input("Average length of stay (days)", min_value=1, value=22, step=1)

        roi = estimate_monthly_revenue_lift(
            monthly_referral_volume=int(monthly_referral_volume),
            baseline_conversion_rate=float(baseline_conversion_rate),
            improved_conversion_rate=float(improved_conversion_rate),
            average_daily_revenue=float(average_daily_revenue),
            average_length_of_stay_days=float(average_length_of_stay),
        )

        roi_cols = st.columns(4)
        roi_cols[0].metric("Revenue / admission", format_currency(roi["revenue_per_admission"]))
        roi_cols[1].metric("Extra admits / month", roi["extra_admissions_per_month"])
        roi_cols[2].metric("Monthly lift", format_currency(roi["monthly_revenue_lift"]))
        roi_cols[3].metric("Annualized lift", format_currency(roi["annualized_revenue_lift"]))

        st.info(
            "Product framing: this is not just document summarization. "
            "It is a census-growth workflow: faster review, fewer missed referrals, "
            "better source visibility, clearer bottlenecks, and a measurable admissions/revenue case."
        )

    with tabs[3]:
        st.subheader("System Architecture")

        st.code(
            '''
Synthetic referral packet
    ↓
Deterministic extraction layer
    ↓
ReferralExtract schema
    ↓
Missing-info checker
    ↓
Facility capability + payer rules
    ↓
Hard constraints + weighted scoring
    ↓
Priority + next-best-action layer
    ↓
Recommendation + reasons
    ↓
Human-reviewed response draft
    ↓
Referral inbox + analytics + ROI dashboard
            '''.strip()
        )

        st.markdown("### Next upgrade")
        st.write(
            "Replace deterministic extraction with a local Hugging Face model extractor. "
            "The important design choice is that the model only extracts structured facts; "
            "the rules/scoring layer remains deterministic, explainable, and auditable."
        )

        st.markdown("### Demo safety posture")
        st.write(
            "This MVP uses synthetic data only. In production, the system would need secure ingestion, "
            "role-based access, audit logs, encryption, human review, and healthcare-compliant deployment controls."
        )


if __name__ == "__main__":
    main()
