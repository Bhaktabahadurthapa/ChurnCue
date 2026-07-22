"""Dataset validation and leakage-safe preprocessing."""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from churncue.security import ChurnCueError

IDENTIFIER_COLUMNS = {"customer_id"}
LEAKAGE_COLUMNS = {"churn_probability", "predicted_churn", "risk_level", "annual_revenue_at_risk"}


@dataclass(frozen=True)
class PreparedData:
    features: pd.DataFrame
    target: pd.Series
    feature_names: list[str]
    numerical: list[str]
    categorical: list[str]
    warnings: list[str]


def prepare_training_data(frame: pd.DataFrame, target_column: str) -> PreparedData:
    if frame.empty:
        raise ChurnCueError("dataset must contain at least one row")
    if not target_column or len(target_column) > 100:
        raise ChurnCueError("target_column is invalid")
    if target_column not in frame.columns:
        raise ChurnCueError(f"target column '{target_column}' is missing")
    if frame.columns.duplicated().any():
        raise ChurnCueError("dataset contains duplicate column names")
    target = pd.to_numeric(frame[target_column], errors="coerce")
    if target.isna().any() or not set(target.unique()).issubset({0, 1}):
        raise ChurnCueError("target must contain only 0 and 1 with no missing values")
    if target.nunique() < 2:
        raise ChurnCueError("target must contain both classes")
    excluded = IDENTIFIER_COLUMNS | LEAKAGE_COLUMNS | {target_column}
    features = frame.drop(columns=[c for c in excluded if c in frame.columns]).copy()
    if features.empty:
        raise ChurnCueError("dataset has no usable model features")
    numerical = features.select_dtypes(include=[np.number, "bool"]).columns.tolist()
    categorical = [column for column in features.columns if column not in numerical]
    if not numerical and not categorical:
        raise ChurnCueError("dataset has no supported model features")
    warnings = [f"Excluded leakage-prone column: {c}" for c in LEAKAGE_COLUMNS & set(frame)]
    return PreparedData(
        features, target.astype(int), list(features.columns), numerical, categorical, warnings
    )


def build_preprocessor(numerical: list[str], categorical: list[str]) -> ColumnTransformer:
    transformers: list[tuple[str, Pipeline, list[str]]] = []
    if numerical:
        transformers.append(
            (
                "numeric",
                Pipeline(
                    [("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]
                ),
                numerical,
            )
        )
    if categorical:
        transformers.append(
            (
                "categorical",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
                    ]
                ),
                categorical,
            )
        )
    return ColumnTransformer(transformers=transformers, remainder="drop")
