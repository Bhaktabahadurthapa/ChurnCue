"""Revenue-at-risk aggregation and Slack-ready (never sent) reporting."""

from typing import Any

from churncue.prediction import compare_risk
from churncue.schemas import ScoredCustomer
from churncue.security import ChurnCueError, validate_rows


def rescue_report(scored_customers: list[dict[str, Any]]) -> dict[str, Any]:
    validate_rows(scored_customers, allowed_sequence_fields={"top_risk_factors"})
    try:
        validated = [ScoredCustomer.model_validate(row).model_dump() for row in scored_customers]
    except ValueError as error:
        raise ChurnCueError("scored customer records are malformed") from error
    movements = compare_risk(validated)
    movement_by_id = {row["customer_id"]: row for row in movements}
    high_risk = [row for row in validated if row["risk_level"] == "High"]
    newly_at_risk = [
        row for row in validated if movement_by_id[row["customer_id"]]["newly_at_risk"]
    ]
    at_risk = [row for row in validated if row["risk_level"] in {"High", "Medium"}]
    top = sorted(at_risk, key=lambda row: row["annual_revenue_at_risk"], reverse=True)[:10]
    annual = round(sum(row["annual_revenue_at_risk"] for row in at_risk), 2)
    monthly = round(annual / 12, 2)
    actions = [
        "Assign an owner to each newly-at-risk account within one business day.",
        "Review payment and unresolved-support signals before contacting the customer.",
        "Prepare a value-recovery plan for high-revenue accounts approaching renewal.",
        "Require human approval before posting the prepared Slack notification.",
    ]
    summary = (
        f"ChurnCue weekly review: {len(high_risk)} high-risk and {len(newly_at_risk)} "
        f"newly-at-risk customers. Estimated annual revenue at risk: ${annual:,.2f}. "
        "Review the priority queue and approve outreach actions."
    )
    return {
        "total_customers": len(validated),
        "high_risk_count": len(high_risk),
        "newly_at_risk_count": len(newly_at_risk),
        "monthly_revenue_at_risk": monthly,
        "annual_revenue_at_risk": annual,
        "top_priority_customers": top,
        "recommended_operational_actions": actions,
        "slack_ready_summary": summary,
        "slack_message_sent": False,
    }


def portfolio_insights(scored_customers: list[dict[str, Any]]) -> dict[str, Any]:
    """Return compact, deterministic segments for an executive review screen."""
    validate_rows(scored_customers, allowed_sequence_fields={"top_risk_factors"})
    try:
        validated = [
            ScoredCustomer.model_validate(row).model_dump() | row for row in scored_customers
        ]
    except ValueError as error:
        raise ChurnCueError("scored customer records are malformed") from error

    def segment(label: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
        at_risk = [row for row in rows if row["risk_level"] in {"High", "Medium"}]
        return {
            "segment": label,
            "customer_count": len(rows),
            "at_risk_count": len(at_risk),
            "annual_revenue_at_risk": round(
                sum(row["annual_revenue_at_risk"] for row in at_risk), 2
            ),
            "average_churn_probability": round(
                sum(row["churn_probability"] for row in rows) / len(rows), 4
            ) if rows else 0,
        }

    plans = sorted({str(row.get("plan", "Unknown")) for row in validated})
    plan_segments = [
        segment(
            plan,
            [row for row in validated if str(row.get("plan", "Unknown")) == plan],
        )
        for plan in plans
    ]
    renewal_bands = {
        "0-30 days": lambda value: value <= 30,
        "31-90 days": lambda value: 31 <= value <= 90,
        "91+ days": lambda value: value > 90,
    }
    renewal_segments = []
    for label, predicate in renewal_bands.items():
        rows = []
        for row in validated:
            try:
                if predicate(float(row.get("renewal_days", 9999))):
                    rows.append(row)
            except (TypeError, ValueError):
                continue
        renewal_segments.append(segment(label, rows))
    largest_exposure = max(
        plan_segments, key=lambda row: row["annual_revenue_at_risk"], default=None
    )
    return {
        "total_customers": len(validated),
        "plan_segments": plan_segments,
        "renewal_segments": renewal_segments,
        "largest_exposure_segment": largest_exposure,
        "recommended_focus": (
            f"Start with {largest_exposure['segment']} accounts"
            if largest_exposure
            else "Review the full queue"
        ),
    }
