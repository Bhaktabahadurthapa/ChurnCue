"""Deterministic training, evaluation, artifact storage, and experiment tracking."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import joblib
import pandas as pd
from sklearn.base import ClassifierMixin
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from churncue.config import Settings, get_settings
from churncue.database import ExperimentStore
from churncue.preprocessing import build_preprocessor, prepare_training_data
from churncue.security import ChurnCueError, validate_rows


def _models(random_state: int) -> dict[str, ClassifierMixin]:
    return {
        "logistic_regression": LogisticRegression(
            max_iter=1_000, random_state=random_state, solver="liblinear"
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=160, max_depth=8, min_samples_leaf=2, random_state=random_state, n_jobs=-1
        ),
        "gradient_boosting": GradientBoostingClassifier(random_state=random_state),
    }


def _metrics(target: pd.Series, predicted: Any, probability: Any) -> dict[str, Any]:
    tn, fp, fn, tp = confusion_matrix(target, predicted, labels=[0, 1]).ravel()
    return {
        "accuracy": round(float(accuracy_score(target, predicted)), 6),
        "precision": round(float(precision_score(target, predicted, zero_division=0)), 6),
        "recall": round(float(recall_score(target, predicted, zero_division=0)), 6),
        "f1": round(float(f1_score(target, predicted, zero_division=0)), 6),
        "roc_auc": round(float(roc_auc_score(target, probability)), 6),
        "confusion_matrix": {
            "true_negative": int(tn),
            "false_positive": int(fp),
            "false_negative": int(fn),
            "true_positive": int(tp),
        },
    }


def train_model_suite(
    rows: list[dict[str, Any]], target_column: str = "churned", settings: Settings | None = None
) -> dict[str, Any]:
    settings = settings or get_settings()
    validate_rows(rows, settings=settings)
    if len(rows) < 20:
        raise ChurnCueError("at least 20 rows are required for a reliable stratified split")
    prepared = prepare_training_data(pd.DataFrame(rows), target_column)
    class_counts = prepared.target.value_counts()
    if class_counts.min() < 2:
        raise ChurnCueError("each target class must contain at least two rows")
    try:
        x_train, x_test, y_train, y_test = train_test_split(
            prepared.features,
            prepared.target,
            test_size=0.2,
            stratify=prepared.target,
            random_state=settings.random_state,
        )
    except ValueError as error:
        raise ChurnCueError(
            "dataset cannot be split safely; add more rows per target class"
        ) from error

    metrics: dict[str, dict[str, Any]] = {}
    pipelines: dict[str, Pipeline] = {}
    for name, estimator in _models(settings.random_state).items():
        pipeline = Pipeline(
            [
                ("preprocessor", build_preprocessor(prepared.numerical, prepared.categorical)),
                ("model", estimator),
            ]
        )
        pipeline.fit(x_train, y_train)
        predictions = pipeline.predict(x_test)
        probabilities = pipeline.predict_proba(x_test)[:, 1]
        metrics[name] = _metrics(y_test, predictions, probabilities)
        pipelines[name] = pipeline

    recommended = max(metrics, key=lambda name: (metrics[name]["roc_auc"], metrics[name]["f1"]))
    experiment_id = f"exp-{uuid4().hex}"
    created_at = datetime.now(UTC).isoformat()
    artifact_dir = Path(settings.artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = (artifact_dir / f"{experiment_id}.joblib").resolve()
    joblib.dump(
        {
            "pipeline": pipelines[recommended],
            "model_name": recommended,
            "feature_names": prepared.feature_names,
            "target_column": target_column,
        },
        artifact_path,
    )
    ExperimentStore(settings).save(
        {
            "experiment_id": experiment_id,
            "created_at": created_at,
            "target_column": target_column,
            "model_metrics": metrics,
            "recommended_model": recommended,
            "model_artifact_path": str(artifact_path),
            "dataset_row_count": len(rows),
        }
    )
    return {
        "experiment_id": experiment_id,
        "models_trained": list(metrics),
        "metrics": metrics,
        "recommended_model": recommended,
        "train_row_count": len(x_train),
        "test_row_count": len(x_test),
        "warnings": prepared.warnings,
    }
