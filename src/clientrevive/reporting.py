"""Revenue-at-risk aggregation and Slack-ready (never sent) reporting."""

from typing import Any

from clientrevive.prediction import compare_risk
from clientrevive.schemas import ScoredCustomer
from clientrevive.security import ClientReviveError, validate_rows


def rescue_report(scored_customers: list[dict[str, Any]]) -> dict[str, Any]:
    validate_rows(scored_customers, allowed_sequence_fields={"top_risk_factors"})
    try:
        validated = [ScoredCustomer.model_validate(row).model_dump() for row in scored_customers]
    except ValueError as error:
        raise ClientReviveError("scored customer records are malformed") from error
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
        f"ClientRevive weekly review: {len(high_risk)} high-risk and {len(newly_at_risk)} "
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
