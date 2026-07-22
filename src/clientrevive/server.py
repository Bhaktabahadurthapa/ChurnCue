"""ClientRevive Ops MCP tools and Streamable HTTP entrypoint."""

import logging
from datetime import UTC, datetime
from typing import Any

import pandas as pd
from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from clientrevive import __version__
from clientrevive.config import get_settings
from clientrevive.database import ExperimentStore
from clientrevive.explanations import explain_record
from clientrevive.prediction import compare_risk, score_rows
from clientrevive.reporting import rescue_report
from clientrevive.security import ClientReviveError, validate_rows
from clientrevive.training import train_model_suite

settings = get_settings()
logging.basicConfig(
    level=settings.log_level.upper(),
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
)
logger = logging.getLogger("clientrevive")

mcp = FastMCP(
    "ClientRevive Ops",
    instructions="Deterministic customer-renewal risk analysis. Never sends external messages.",
    host=settings.host,
    port=settings.port,
    streamable_http_path="/mcp",
    stateless_http=True,
    json_response=True,
)


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return frame.astype(object).where(pd.notna(frame), None).to_dict(orient="records")


@mcp.custom_route("/health", methods=["GET"])
async def http_health(_: Request) -> JSONResponse:
    return JSONResponse(health_check())


@mcp.tool()
def health_check() -> dict[str, Any]:
    """Return service health and transport metadata."""
    return {
        "service": "ClientRevive Ops",
        "version": __version__,
        "status": "healthy",
        "transport": "streamable-http",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@mcp.tool()
def load_demo_dataset(limit: int | None = None) -> list[dict[str, Any]]:
    """Load anonymous synthetic demo data, subject to a safe row limit."""
    selected_limit = settings.max_demo_rows if limit is None else limit
    if not 1 <= selected_limit <= settings.max_demo_rows:
        raise ClientReviveError(f"limit must be between 1 and {settings.max_demo_rows}")
    try:
        frame = pd.read_csv(settings.demo_data_path, nrows=selected_limit)
    except (FileNotFoundError, OSError, pd.errors.ParserError) as error:
        logger.error("demo_dataset_unavailable")
        raise ClientReviveError("demo dataset is unavailable") from error
    return _records(frame)


@mcp.tool()
def profile_dataset(rows: list[dict[str, Any]], target_column: str = "churned") -> dict[str, Any]:
    """Return deterministic data quality and descriptive statistics."""
    validate_rows(rows)
    if not target_column or len(target_column) > 100:
        raise ClientReviveError("target_column is invalid")
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
def train_models(rows: list[dict[str, Any]], target_column: str = "churned") -> dict[str, Any]:
    """Train and persist three deterministic classifiers; metrics come from scikit-learn."""
    result = train_model_suite(rows, target_column)
    logger.info("training_complete experiment_id=%s rows=%d", result["experiment_id"], len(rows))
    return result


@mcp.tool()
def score_customers(experiment_id: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Score customers using the recommended persisted pipeline."""
    return score_rows(experiment_id, rows)


@mcp.tool()
def compare_weekly_risk(scored_customers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compare current model probability with each customer's previous risk."""
    return compare_risk(scored_customers)


@mcp.tool()
def explain_risk(experiment_id: str, customer_record: dict[str, Any]) -> dict[str, Any]:
    """Return deterministic observed signals; reasons are not claims of causality."""
    ExperimentStore().get(experiment_id)
    validate_rows([customer_record])
    return explain_record(customer_record)


@mcp.tool()
def generate_rescue_report(scored_customers: list[dict[str, Any]]) -> dict[str, Any]:
    """Prepare an operational report and Slack preview without sending anything."""
    return rescue_report(scored_customers)


def main() -> None:
    logger.info("service_start transport=streamable-http endpoint=/mcp")
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
