from typing import Dict


def estimate_revenue_per_admission(
    average_daily_revenue: float,
    average_length_of_stay_days: float,
) -> float:
    return average_daily_revenue * average_length_of_stay_days


def estimate_extra_admissions(
    monthly_referral_volume: int,
    baseline_conversion_rate: float,
    improved_conversion_rate: float,
) -> float:
    conversion_lift = max(0.0, improved_conversion_rate - baseline_conversion_rate)
    return monthly_referral_volume * conversion_lift


def estimate_monthly_revenue_lift(
    monthly_referral_volume: int,
    baseline_conversion_rate: float,
    improved_conversion_rate: float,
    average_daily_revenue: float,
    average_length_of_stay_days: float,
) -> Dict[str, float]:
    revenue_per_admission = estimate_revenue_per_admission(
        average_daily_revenue=average_daily_revenue,
        average_length_of_stay_days=average_length_of_stay_days,
    )

    extra_admissions = estimate_extra_admissions(
        monthly_referral_volume=monthly_referral_volume,
        baseline_conversion_rate=baseline_conversion_rate,
        improved_conversion_rate=improved_conversion_rate,
    )

    monthly_revenue_lift = extra_admissions * revenue_per_admission

    return {
        "revenue_per_admission": round(revenue_per_admission, 2),
        "extra_admissions_per_month": round(extra_admissions, 2),
        "monthly_revenue_lift": round(monthly_revenue_lift, 2),
        "annualized_revenue_lift": round(monthly_revenue_lift * 12, 2),
    }


def format_currency(value: float) -> str:
    return f"${value:,.0f}"
