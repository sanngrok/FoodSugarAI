"""Privacy helpers for glucose-related logs.

These helpers are intentionally conservative: request logs should keep enough
shape for debugging without storing raw health time series or event details.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

SENSITIVE_GLUCOSE_KEYS = {
    "readings",
    "glucose",
    "glucose_mg_dl",
    "meals",
    "carbs_g",
    "bolus",
    "insulin_units",
    "basal",
    "rate_units_per_hour",
    "patient_id",
    "patient_id_numeric",
    "timestamp",
    "biosignals",
    "gsr_current",
    "skin_temperature_current",
    "acceleration_current",
}


def mask_glucose_payload_for_log(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return a masked copy that is safe to write to application logs."""
    masked: dict[str, Any] = {}
    for key, value in payload.items():
        if key in {"readings", "meals", "bolus", "basal"} and isinstance(value, list):
            masked[f"{key}_count"] = len(value)
            masked[key] = "[masked]"
        elif key in SENSITIVE_GLUCOSE_KEYS:
            masked[key] = "[masked]"
        elif isinstance(value, Mapping):
            masked[key] = mask_glucose_payload_for_log(value)
        elif isinstance(value, list):
            masked[key] = [
                mask_glucose_payload_for_log(item) if isinstance(item, Mapping) else item
                for item in value
            ]
        else:
            masked[key] = value
    return masked
