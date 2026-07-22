import pandas as pd
import pytest

from churncue.preprocessing import build_preprocessor, prepare_training_data
from churncue.security import ChurnCueError


def test_identifiers_target_and_leakage_are_removed(demo_rows):
    frame = pd.DataFrame(demo_rows)
    frame["churn_probability"] = 0.9
    prepared = prepare_training_data(frame, "churned")
    assert "customer_id" not in prepared.features
    assert "churned" not in prepared.features
    assert "churn_probability" not in prepared.features
    assert "plan" in prepared.categorical
    assert "monthly_revenue" in prepared.numerical
    assert prepared.warnings


def test_preprocessor_handles_missing_values(demo_rows):
    prepared = prepare_training_data(pd.DataFrame(demo_rows[:40]), "churned")
    frame = prepared.features.copy()
    frame.loc[0, "monthly_revenue"] = None
    frame.loc[1, "plan"] = None
    transformed = build_preprocessor(prepared.numerical, prepared.categorical).fit_transform(frame)
    assert transformed.shape[0] == 40
    assert not pd.isna(transformed).any()


@pytest.mark.parametrize(
    "frame,message",
    [
        (pd.DataFrame(), "at least one"),
        (pd.DataFrame({"x": [1, 2]}), "missing"),
        (pd.DataFrame({"x": [1, 2], "churned": [1, 1]}), "both classes"),
        (pd.DataFrame({"x": [1, 2], "churned": [0, 3]}), "only 0 and 1"),
    ],
)
def test_invalid_training_data(frame, message):
    with pytest.raises(ChurnCueError, match=message):
        prepare_training_data(frame, "churned")
