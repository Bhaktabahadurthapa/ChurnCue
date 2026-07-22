from inspect import signature

import pytest

from churncue import server
from churncue.config import Settings
from churncue.explanations import explain_record
from churncue.reporting import rescue_report
from churncue.security import ChurnCueError, validate_rows
from scripts.generate_demo_data import generate_demo_data


@pytest.fixture(autouse=True)
def clear_runtime_state():
    server.DATASETS.clear()
    server.SCORE_RUNS.clear()
    yield
    server.DATASETS.clear()
    server.SCORE_RUNS.clear()


@pytest.fixture()
def isolated_server(tmp_path, monkeypatch):
    demo_path = tmp_path / "demo.csv"
    generate_demo_data().to_csv(demo_path, index=False)
    settings = Settings(
        database_path=tmp_path / "experiments.db",
        artifact_dir=tmp_path / "artifacts",
        demo_data_path=demo_path,
    )
    monkeypatch.setattr(server, "settings", settings)
    return settings


def test_demo_loader_defaults_to_context_safe_size(isolated_server):
    loaded = server.load_demo_dataset()
    assert loaded["record_count"] == 50
    assert loaded["summary"]["column_count"] == 14
    assert len(server.DATASETS[loaded["dataset_id"]]) == 50
    assert server.load_demo_dataset(limit=10)["record_count"] == 10
    with pytest.raises(ChurnCueError, match="between 1 and 50"):
        server.load_demo_dataset(limit=51)


def test_mcp_tool_arguments_use_identifiers():
    expected = {
        server.profile_dataset: ["dataset_id", "target_column"],
        server.train_models: ["dataset_id", "target_column"],
        server.score_customers: ["dataset_id", "experiment_id"],
        server.compare_weekly_risk: ["score_run_id"],
        server.explain_risk: ["score_run_id", "customer_id"],
        server.generate_rescue_report: ["score_run_id"],
    }
    for tool, argument_names in expected.items():
        assert list(signature(tool).parameters) == argument_names


def test_health_and_profile(isolated_server):
    health = server.health_check()
    assert health["service"] == "ChurnCue"
    assert health["status"] == "healthy"
    loaded = server.load_demo_dataset()
    profile = server.profile_dataset(loaded["dataset_id"])
    assert profile["row_count"] == 50
    assert profile["target_distribution"]
    assert "monthly_revenue" in profile["numerical_summaries"]


def test_profile_warns_for_missing_target(demo_rows):
    rows = [{k: v for k, v in row.items() if k != "churned"} for row in demo_rows[:3]]
    server.DATASETS["missing-target"] = rows
    assert "missing" in server.profile_dataset("missing-target")["validation_warnings"][0]


def test_identifier_workflow(isolated_server):
    loaded = server.load_demo_dataset()
    dataset_id = loaded["dataset_id"]
    training = server.train_models(dataset_id)
    scoring = server.score_customers(dataset_id, training["experiment_id"])

    assert set(scoring) == {"score_run_id", "totals", "top_risk_preview"}
    assert scoring["totals"]["customers_scored"] == 50
    assert len(scoring["top_risk_preview"]) <= 10

    score_run_id = scoring["score_run_id"]
    comparison = server.compare_weekly_risk(score_run_id)
    assert comparison["totals"]["customers_compared"] == 50
    customer_id = scoring["top_risk_preview"][0]["customer_id"]
    explanation = server.explain_risk(score_run_id, customer_id)
    assert explanation["customer_id"] == customer_id
    report = server.generate_rescue_report(score_run_id)
    assert report["total_customers"] == 50
    assert report["slack_message_sent"] is False


def test_unknown_runtime_identifiers_are_rejected():
    with pytest.raises(ChurnCueError, match="dataset_id is unknown or expired"):
        server.profile_dataset("missing")
    with pytest.raises(ChurnCueError, match="score_run_id is unknown or expired"):
        server.generate_rescue_report("missing")


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
    with pytest.raises(ChurnCueError, match="at least one"):
        validate_rows([])
    with pytest.raises(ChurnCueError, match="scalar"):
        validate_rows([{"nested": {"unsafe": True}}])
    with pytest.raises(ChurnCueError, match="string limit"):
        validate_rows([{"value": "x" * 201}])
    with pytest.raises(ChurnCueError, match="malformed"):
        rescue_report([{"customer_id": "CUST-1"}])
