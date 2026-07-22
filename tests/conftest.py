from pathlib import Path

import pytest

from clientrevive.config import Settings
from clientrevive.training import train_model_suite
from scripts.generate_demo_data import generate_demo_data


@pytest.fixture(scope="session")
def demo_rows():
    return generate_demo_data().to_dict(orient="records")


@pytest.fixture(scope="session")
def trained(tmp_path_factory, demo_rows):
    root = tmp_path_factory.mktemp("trained")
    settings = Settings(
        database_path=Path(root) / "experiments.db",
        artifact_dir=Path(root) / "artifacts",
        demo_data_path=Path(root) / "demo.csv",
    )
    result = train_model_suite(demo_rows, settings=settings)
    return settings, result
