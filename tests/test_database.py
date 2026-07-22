import pytest

from churncue.database import ExperimentStore
from churncue.security import ChurnCueError


def test_missing_experiment_is_safe(trained):
    settings, _ = trained
    with pytest.raises(ChurnCueError, match="not found"):
        ExperimentStore(settings).get("exp-missing")
