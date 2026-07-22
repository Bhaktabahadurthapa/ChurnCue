"""Input safety checks shared by all MCP-facing operations."""

from typing import Any

from clientrevive.config import Settings, get_settings


class ClientReviveError(ValueError):
    """A safe error whose message may be returned to an MCP client."""


def validate_rows(
    rows: list[dict[str, Any]],
    *,
    allow_empty: bool = False,
    allowed_sequence_fields: set[str] | None = None,
    settings: Settings | None = None,
) -> list[dict[str, Any]]:
    settings = settings or get_settings()
    allowed_sequence_fields = allowed_sequence_fields or set()
    if not isinstance(rows, list):
        raise ClientReviveError("rows must be a JSON array of objects")
    if not rows and not allow_empty:
        raise ClientReviveError("dataset must contain at least one row")
    if len(rows) > settings.max_input_rows:
        raise ClientReviveError(f"dataset exceeds the {settings.max_input_rows}-row limit")
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ClientReviveError(f"row {index} must be an object")
        if len(row) > 100:
            raise ClientReviveError(f"row {index} contains too many fields")
        for key, value in row.items():
            if not isinstance(key, str) or not key or len(key) > 100:
                raise ClientReviveError(f"row {index} contains an invalid field name")
            if isinstance(value, str) and len(value) > settings.max_string_length:
                raise ClientReviveError(f"row {index} field '{key}' exceeds the string limit")
            if key.lower() in {
                "name",
                "full_name",
                "email",
                "email_address",
                "phone",
                "phone_number",
            }:
                raise ClientReviveError(
                    f"row {index} contains prohibited customer PII field '{key}'"
                )
            if key in allowed_sequence_fields and isinstance(value, list):
                if len(value) > 10 or any(not isinstance(item, str) for item in value):
                    raise ClientReviveError(
                        f"row {index} field '{key}' contains invalid list values"
                    )
                continue
            if isinstance(value, (dict, list, tuple, set)):
                raise ClientReviveError(f"row {index} field '{key}' must be a scalar value")
    return rows
