import pytest

from churncue.prediction import compare_risk, score_rows
from churncue.schemas import risk_level
from churncue.security import ChurnCueError


@pytest.mark.parametrize(
    "probability,expected",
    [
        (0.0, "Low"),
        (0.4499, "Low"),
        (0.45, "Medium"),
        (0.7499, "Medium"),
        (0.75, "High"),
        (1.0, "High"),
    ],
)
def test_risk_boundaries(probability, expected):
    assert risk_level(probability) == expected


def test_scoring_probability_and_revenue(trained, demo_rows):
    settings, training = trained
    scores = score_rows(training["experiment_id"], demo_rows[:12], settings)
    assert len(scores) == 12
    assert all(0 <= row["churn_probability"] <= 1 for row in scores)
    for row in scores:
        assert row["annual_revenue_at_risk"] == pytest.approx(
            row["monthly_revenue"] * 12 * row["churn_probability"], abs=0.02
        )


def test_weekly_movement_and_newly_at_risk():
    rows = [
        {"customer_id": "CUST-1", "churn_probability": 0.5, "previous_risk": 0.4},
        {"customer_id": "CUST-2", "churn_probability": 0.2, "previous_risk": 0.4},
        {"customer_id": "CUST-3", "churn_probability": 0.4, "previous_risk": 0.4},
    ]
    result = compare_risk(rows)
    assert [row["movement_category"] for row in result] == ["Increased", "Decreased", "Unchanged"]
    assert result[0]["newly_at_risk"] is True


def test_malformed_prediction_rows(trained, demo_rows):
    settings, training = trained
    bad = dict(demo_rows[0], customer_id="real-person")
    with pytest.raises(ChurnCueError, match="customer_id"):
        score_rows(training["experiment_id"], [bad], settings)
    with pytest.raises(ChurnCueError, match="requires valid"):
        compare_risk([{"customer_id": "CUST-1", "churn_probability": 0.5}])
