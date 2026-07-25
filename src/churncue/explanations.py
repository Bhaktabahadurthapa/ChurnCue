"""Deterministic evidence-based reason codes (associations, not causal claims)."""

from typing import Any


def risk_factors(record: dict[str, Any]) -> list[str]:
    checks = [
        ("usage_drop_percent", 30, "Product usage decreased significantly", "gte"),
        ("payment_failures_90d", 2, "Multiple payment failures", "gte"),
        ("unresolved_tickets", 1, "Customer has unresolved support tickets", "gte"),
        ("days_since_last_login", 21, "Customer has not logged in recently", "gte"),
        ("renewal_days", 30, "Renewal date is approaching", "lte"),
        ("satisfaction_score", 5, "Satisfaction score is low", "lte"),
    ]
    factors: list[str] = []
    for field, threshold, reason, operation in checks:
        try:
            value = float(record.get(field))
        except (TypeError, ValueError):
            continue
        if (operation == "gte" and value >= threshold) or (
            operation == "lte" and value <= threshold
        ):
            factors.append(reason)
    return factors or ["No individual operational threshold was triggered"]


def _next_best_action(record: dict[str, Any], factors: list[str]) -> str:
    """Choose a bounded, explainable playbook from observed operational signals."""
    if "Multiple payment failures" in factors:
        return "Route to billing support and confirm payment recovery before renewal outreach."
    if "Unresolved support tickets" in factors:
        return "Assign a support owner and close the oldest unresolved issue before the check-in."
    if "Customer has not logged in recently" in factors:
        return "Invite the customer to a guided reactivation session with a success manager."
    if "Renewal date is approaching" in factors:
        return "Schedule a value-review meeting and confirm the renewal plan this week."
    if "Product usage decreased significantly" in factors:
        return "Share an adoption plan focused on the workflows with the largest usage decline."
    if "Satisfaction score is low" in factors:
        return "Ask for a human-led feedback conversation and document the recovery plan."
    return "Review the account context manually before selecting an outreach motion."


def _contact_window(record: dict[str, Any]) -> str:
    try:
        renewal_days = float(record.get("renewal_days"))
    except (TypeError, ValueError):
        return "Review this week"
    if renewal_days <= 30:
        return "Within 1 business day"
    if renewal_days <= 90:
        return "Within 5 business days"
    return "This month"


def explain_record(record: dict[str, Any]) -> dict[str, Any]:
    factors = risk_factors(record)
    return {
        "customer_id": str(record.get("customer_id", "unknown")),
        "reason_codes": factors,
        "next_best_action": _next_best_action(record, factors),
        "recommended_contact_window": _contact_window(record),
        "interpretation": (
            "These reasons describe observed risk signals associated with the model score; "
            "they do not establish causation."
        ),
    }
