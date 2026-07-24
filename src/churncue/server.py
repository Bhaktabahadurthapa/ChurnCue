"""ChurnCue MCP tools and Streamable HTTP entrypoint."""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pandas as pd
from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from churncue import __version__
from churncue.config import get_settings
from churncue.explanations import explain_record
from churncue.prediction import compare_risk, score_rows
from churncue.reporting import portfolio_insights, rescue_report
from churncue.security import ChurnCueError, validate_rows
from churncue.training import train_model_suite

settings = get_settings()
logging.basicConfig(
    level=settings.log_level.upper(),
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
)
logger = logging.getLogger("churncue")

DATASETS: dict[str, list[dict[str, Any]]] = {}
SCORE_RUNS: dict[str, dict[str, Any]] = {}

mcp = FastMCP(
    "ChurnCue",
    instructions="Deterministic customer-renewal risk analysis. Never sends external messages.",
    host=settings.host,
    port=settings.port,
    streamable_http_path="/mcp",
    stateless_http=True,
    json_response=True,
)


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return frame.astype(object).where(pd.notna(frame), None).to_dict(orient="records")


def _get_dataset(dataset_id: str) -> list[dict[str, Any]]:
    try:
        return DATASETS[dataset_id]
    except (KeyError, TypeError) as error:
        raise ChurnCueError("dataset_id is unknown or expired") from error


def _get_score_run(score_run_id: str) -> dict[str, Any]:
    try:
        return SCORE_RUNS[score_run_id]
    except (KeyError, TypeError) as error:
        raise ChurnCueError("score_run_id is unknown or expired") from error


@mcp.custom_route("/health", methods=["GET"])
async def http_health(_: Request) -> JSONResponse:
    return JSONResponse(health_check())


@mcp.tool()
def health_check() -> dict[str, Any]:
    """Return service health and transport metadata."""
    return {
        "service": "ChurnCue",
        "version": __version__,
        "status": "healthy",
        "transport": "streamable-http",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@mcp.tool()
def load_demo_dataset(limit: int | None = None) -> dict[str, Any]:
    """Store anonymous demo data and return a compact dataset reference."""
    selected_limit = settings.max_demo_rows if limit is None else limit
    if not 1 <= selected_limit <= settings.max_demo_rows:
        raise ChurnCueError(f"limit must be between 1 and {settings.max_demo_rows}")
    try:
        frame = pd.read_csv(settings.demo_data_path, nrows=selected_limit)
    except (FileNotFoundError, OSError, pd.errors.ParserError) as error:
        logger.error("demo_dataset_unavailable")
        raise ChurnCueError("demo dataset is unavailable") from error
    rows = _records(frame)
    dataset_id = str(uuid4())
    DATASETS[dataset_id] = rows
    return {
        "dataset_id": dataset_id,
        "record_count": len(rows),
        "summary": {
            "column_count": len(frame.columns),
            "column_names": frame.columns.tolist(),
            "missing_value_count": int(frame.isna().sum().sum()),
            "plan_distribution": {
                str(key): int(value) for key, value in frame["plan"].value_counts().items()
            },
            "target_distribution": {
                str(key): int(value) for key, value in frame["churned"].value_counts().items()
            },
        },
    }


@mcp.tool()
def profile_dataset(dataset_id: str, target_column: str = "churned") -> dict[str, Any]:
    """Return deterministic data quality and descriptive statistics."""
    rows = _get_dataset(dataset_id)
    validate_rows(rows, settings=settings)
    if not target_column or len(target_column) > 100:
        raise ChurnCueError("target_column is invalid")
    frame = pd.DataFrame(rows)
    warnings: list[str] = []
    if target_column not in frame:
        warnings.append(f"Target column '{target_column}' is missing")
        distribution: dict[str, int] = {}
    else:
        distribution = {
            str(key): int(value)
            for key, value in frame[target_column].value_counts(dropna=False).items()
        }
        values = set(pd.to_numeric(frame[target_column], errors="coerce").dropna().unique())
        if not values.issubset({0, 1}):
            warnings.append("Target contains values other than 0 and 1")
    if frame.isna().any().any():
        warnings.append("Dataset contains missing values; training will impute feature values")
    if frame.duplicated().any():
        warnings.append("Dataset contains duplicate rows")
    numeric = (
        frame.select_dtypes(include="number").describe().round(4).replace({float("nan"): None})
    )
    summaries = {column: values for column, values in numeric.to_dict().items()}
    return {
        "row_count": len(frame),
        "column_count": len(frame.columns),
        "column_names": frame.columns.tolist(),
        "data_types": {column: str(dtype) for column, dtype in frame.dtypes.items()},
        "missing_value_counts": {
            column: int(value) for column, value in frame.isna().sum().items()
        },
        "duplicate_count": int(frame.duplicated().sum()),
        "target_distribution": distribution,
        "numerical_summaries": summaries,
        "validation_warnings": warnings,
    }


@mcp.tool()
def train_models(dataset_id: str, target_column: str = "churned") -> dict[str, Any]:
    """Train and persist three deterministic classifiers; metrics come from scikit-learn."""
    rows = _get_dataset(dataset_id)
    result = train_model_suite(rows, target_column, settings=settings)
    logger.info("training_complete experiment_id=%s rows=%d", result["experiment_id"], len(rows))
    return result


@mcp.tool()
def score_customers(dataset_id: str, experiment_id: str) -> dict[str, Any]:
    """Score a stored dataset and return a compact score-run reference."""
    rows = _get_dataset(dataset_id)
    scored_customers = score_rows(experiment_id, rows, settings=settings)
    score_run_id = str(uuid4())
    SCORE_RUNS[score_run_id] = {
        "dataset_id": dataset_id,
        "experiment_id": experiment_id,
        "scored_customers": scored_customers,
    }
    risk_counts = {
        level: sum(row["risk_level"] == level for row in scored_customers)
        for level in ("High", "Medium", "Low")
    }
    at_risk = [row for row in scored_customers if row["risk_level"] in {"High", "Medium"}]
    preview = sorted(
        scored_customers,
        key=lambda row: (row["churn_probability"], row["annual_revenue_at_risk"]),
        reverse=True,
    )[:10]
    return {
        "score_run_id": score_run_id,
        "totals": {
            "customers_scored": len(scored_customers),
            "risk_distribution": risk_counts,
            "annual_revenue_at_risk": round(
                sum(row["annual_revenue_at_risk"] for row in at_risk), 2
            ),
        },
        "top_risk_preview": preview,
    }


@mcp.tool()
def compare_weekly_risk(score_run_id: str) -> dict[str, Any]:
    """Summarize weekly risk movement for a stored score run."""
    comparisons = compare_risk(_get_score_run(score_run_id)["scored_customers"])
    movement_counts = {
        movement: sum(row["movement_category"] == movement for row in comparisons)
        for movement in ("Increased", "Decreased", "Unchanged")
    }
    preview = sorted(comparisons, key=lambda row: abs(row["risk_change"]), reverse=True)[:10]
    return {
        "score_run_id": score_run_id,
        "totals": {
            "customers_compared": len(comparisons),
            "movement_distribution": movement_counts,
            "newly_at_risk": sum(row["newly_at_risk"] for row in comparisons),
        },
        "top_changes_preview": preview,
    }


@mcp.tool()
def explain_risk(score_run_id: str, customer_id: str) -> dict[str, Any]:
    """Return deterministic observed signals; reasons are not claims of causality."""
    score_run = _get_score_run(score_run_id)
    rows = _get_dataset(score_run["dataset_id"])
    source = next((row for row in rows if row.get("customer_id") == customer_id), None)
    scored = next(
        (row for row in score_run["scored_customers"] if row.get("customer_id") == customer_id),
        None,
    )
    if source is None or scored is None:
        raise ChurnCueError("customer_id was not found in the score run")
    return {
        "score_run_id": score_run_id,
        "churn_probability": scored["churn_probability"],
        "risk_level": scored["risk_level"],
        **explain_record(source),
    }


@mcp.tool()
def generate_rescue_report(score_run_id: str) -> dict[str, Any]:
    """Prepare an operational report and Slack preview without sending anything."""
    report = rescue_report(_get_score_run(score_run_id)["scored_customers"])
    return {"score_run_id": score_run_id, **report}


@mcp.tool()
def get_portfolio_insights(score_run_id: str) -> dict[str, Any]:
    """Return plan and renewal-window segments for prioritizing the rescue queue."""
    insights = portfolio_insights(_get_score_run(score_run_id)["scored_customers"])
    return {"score_run_id": score_run_id, **insights}


def main() -> None:
    logger.info("service_start transport=streamable-http endpoint=/mcp")
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
