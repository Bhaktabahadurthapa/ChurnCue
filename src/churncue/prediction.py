"""Safe artifact loading, customer scoring, and weekly risk movement."""

from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from churncue.config import Settings, get_settings
from churncue.database import ExperimentStore
from churncue.explanations import risk_factors
from churncue.schemas import ScoredCustomer, risk_level
from churncue.security import ChurnCueError, validate_rows


def _load_artifact(experiment_id: str, settings: Settings) -> dict[str, Any]:
    experiment = ExperimentStore(settings).get(experiment_id)
    artifact = Path(experiment["model_artifact_path"]).resolve()
    allowed_dir = Path(settings.artifact_dir).resolve()
    if allowed_dir not in artifact.parents or not artifact.is_file():
        raise ChurnCueError("model artifact is unavailable")
    try:
        return joblib.load(artifact)
    except Exception as error:  # joblib formats have several load exceptions
        raise ChurnCueError("model artifact could not be loaded") from error


def score_rows(
    experiment_id: str, rows: list[dict[str, Any]], settings: Settings | None = None
) -> list[dict[str, Any]]:
    settings = settings or get_settings()
    validate_rows(rows, settings=settings)
    artifact = _load_artifact(experiment_id, settings)
    frame = pd.DataFrame(rows)
    missing = [name for name in artifact["feature_names"] if name not in frame]
    for name in missing:
        frame[name] = None
    features = frame[artifact["feature_names"]]
    try:
        probabilities = artifact["pipeline"].predict_proba(features)[:, 1]
    except (TypeError, ValueError) as error:
        raise ChurnCueError("customer rows do not match the trained feature schema") from error
    results = []
    for index, (record, probability) in enumerate(zip(rows, probabilities, strict=True)):
        customer_id = record.get("customer_id")
        if not isinstance(customer_id, str) or not customer_id.startswith("CUST-"):
            raise ChurnCueError(f"row {index} has an invalid anonymous customer_id")
        try:
            revenue = max(0.0, float(record.get("monthly_revenue", 0)))
        except (TypeError, ValueError) as error:
            raise ChurnCueError(f"row {index} has invalid monthly_revenue") from error
        previous = record.get("previous_risk")
        try:
            previous_value = None if previous is None else float(previous)
        except (TypeError, ValueError) as error:
            raise ChurnCueError(f"row {index} has invalid previous_risk") from error
        result = ScoredCustomer(
            customer_id=customer_id,
            churn_probability=round(float(probability), 6),
            risk_level=risk_level(float(probability)),
            monthly_revenue=round(revenue, 2),
            annual_revenue_at_risk=round(revenue * 12 * float(probability), 2),
            top_risk_factors=risk_factors(record)[:3],
            previous_risk=previous_value,
        )
        scored = result.model_dump()
        # These are non-PII routing dimensions used by the review UI. Keep the
        # customer row itself inside the service; only compact scored fields are returned.
        for field in ("plan", "renewal_days"):
            if field in record:
                scored[field] = record[field]
        results.append(scored)
    return results


def compare_risk(scored_customers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    validate_rows(scored_customers, allowed_sequence_fields={"top_risk_factors"})
    comparisons = []
    for index, row in enumerate(scored_customers):
        try:
            current = float(row["churn_probability"])
            previous = float(row["previous_risk"])
        except (KeyError, TypeError, ValueError) as error:
            raise ChurnCueError(
                f"row {index} requires valid churn_probability and previous_risk"
            ) from error
        if not 0 <= current <= 1 or not 0 <= previous <= 1:
            raise ChurnCueError(f"row {index} risk probabilities must be between 0 and 1")
        change = round(current - previous, 6)
        movement = (
            "Increased" if change > 0.001 else "Decreased" if change < -0.001 else "Unchanged"
        )
        comparisons.append(
            {
                "customer_id": row.get("customer_id"),
                "current_risk": round(current, 6),
                "previous_risk": round(previous, 6),
                "risk_change": change,
                "movement_category": movement,
                "newly_at_risk": previous < 0.45 <= current,
            }
        )
    return comparisons
