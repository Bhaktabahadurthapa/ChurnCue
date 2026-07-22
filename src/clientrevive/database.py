"""SQLite experiment metadata persistence."""

import json
import sqlite3
from pathlib import Path
from typing import Any

from clientrevive.config import Settings, get_settings
from clientrevive.security import ClientReviveError

SCHEMA = """
CREATE TABLE IF NOT EXISTS experiments (
    experiment_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    target_column TEXT NOT NULL,
    model_metrics TEXT NOT NULL,
    recommended_model TEXT NOT NULL,
    model_artifact_path TEXT NOT NULL,
    dataset_row_count INTEGER NOT NULL CHECK(dataset_row_count > 0)
)
"""


class ExperimentStore:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.path = Path(self.settings.database_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    def save(self, record: dict[str, Any]) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO experiments VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    record["experiment_id"],
                    record["created_at"],
                    record["target_column"],
                    json.dumps(record["model_metrics"], sort_keys=True),
                    record["recommended_model"],
                    record["model_artifact_path"],
                    record["dataset_row_count"],
                ),
            )

    def get(self, experiment_id: str) -> dict[str, Any]:
        if not experiment_id or len(experiment_id) > 100:
            raise ClientReviveError("invalid experiment_id")
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM experiments WHERE experiment_id = ?", (experiment_id,)
            ).fetchone()
        if row is None:
            raise ClientReviveError("experiment was not found")
        result = dict(row)
        result["model_metrics"] = json.loads(result["model_metrics"])
        return result
