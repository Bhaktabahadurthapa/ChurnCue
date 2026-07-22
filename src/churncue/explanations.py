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


def explain_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "customer_id": str(record.get("customer_id", "unknown")),
        "reason_codes": risk_factors(record),
        "interpretation": (
            "These reasons describe observed risk signals associated with the model score; "
            "they do not establish causation."
        ),
    }
