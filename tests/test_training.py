from pathlib import Path

import pytest

from clientrevive.database import ExperimentStore
from clientrevive.security import ClientReviveError
from clientrevive.training import train_model_suite


def test_all_models_metrics_and_persistence(trained):
    settings, result = trained
    assert set(result["models_trained"]) == {
        "logistic_regression",
        "random_forest",
        "gradient_boosting",
    }
    assert result["train_row_count"] == 400
    assert result["test_row_count"] == 100
    for metrics in result["metrics"].values():
        assert all(
            0 <= metrics[key] <= 1 for key in ["accuracy", "precision", "recall", "f1", "roc_auc"]
        )
        assert sum(metrics["confusion_matrix"].values()) == 100
    saved = ExperimentStore(settings).get(result["experiment_id"])
    assert saved["recommended_model"] == result["recommended_model"]
    assert Path(saved["model_artifact_path"]).is_file()


def test_small_dataset_rejected(demo_rows, tmp_path):
    from clientrevive.config import Settings

    settings = Settings(database_path=tmp_path / "db.sqlite", artifact_dir=tmp_path / "artifacts")
    with pytest.raises(ClientReviveError, match="at least 20"):
        train_model_suite(demo_rows[:10], settings=settings)
