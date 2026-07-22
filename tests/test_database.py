import pytest

from clientrevive.database import ExperimentStore
from clientrevive.security import ClientReviveError


def test_missing_experiment_is_safe(trained):
    settings, _ = trained
    with pytest.raises(ClientReviveError, match="not found"):
        ExperimentStore(settings).get("exp-missing")
