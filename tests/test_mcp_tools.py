import pytest

from clientrevive.explanations import explain_record
from clientrevive.reporting import rescue_report
from clientrevive.security import ClientReviveError, validate_rows
from clientrevive.server import health_check, profile_dataset


def test_health_and_profile(demo_rows):
    assert health_check()["status"] == "healthy"
    profile = profile_dataset(demo_rows[:20])
    assert profile["row_count"] == 20
    assert profile["target_distribution"]
    assert "monthly_revenue" in profile["numerical_summaries"]


def test_profile_warns_for_missing_target(demo_rows):
    rows = [{k: v for k, v in row.items() if k != "churned"} for row in demo_rows[:3]]
    assert "missing" in profile_dataset(rows)["validation_warnings"][0]


def test_explanation_is_evidence_based():
    result = explain_record(
        {
            "customer_id": "CUST-1",
            "usage_drop_percent": 50,
            "payment_failures_90d": 2,
            "unresolved_tickets": 3,
            "renewal_days": 10,
            "satisfaction_score": 3,
        }
    )
    assert "Product usage decreased significantly" in result["reason_codes"]
    assert "do not establish causation" in result["interpretation"]


def test_report_calculations_and_no_send():
    rows = [
        {
            "customer_id": "CUST-1",
            "churn_probability": 0.8,
            "risk_level": "High",
            "monthly_revenue": 100,
            "annual_revenue_at_risk": 960,
            "top_risk_factors": ["Low usage"],
            "previous_risk": 0.3,
        },
        {
            "customer_id": "CUST-2",
            "churn_probability": 0.5,
            "risk_level": "Medium",
            "monthly_revenue": 50,
            "annual_revenue_at_risk": 300,
            "top_risk_factors": ["Renewal"],
            "previous_risk": 0.5,
        },
    ]
    report = rescue_report(rows)
    assert report["high_risk_count"] == 1
    assert report["newly_at_risk_count"] == 1
    assert report["monthly_revenue_at_risk"] == 105
    assert report["annual_revenue_at_risk"] == 1260
    assert report["slack_message_sent"] is False


def test_input_limits_and_malformed_values():
    with pytest.raises(ClientReviveError, match="at least one"):
        validate_rows([])
    with pytest.raises(ClientReviveError, match="scalar"):
        validate_rows([{"nested": {"unsafe": True}}])
    with pytest.raises(ClientReviveError, match="string limit"):
        validate_rows([{"value": "x" * 201}])
    with pytest.raises(ClientReviveError, match="malformed"):
        rescue_report([{"customer_id": "CUST-1"}])
