"""OhioT1DM XML parsing utilities."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd


OHIO_TIMESTAMP_FORMAT = "%d-%m-%Y %H:%M:%S"
ENRICHED_EVENT_COLUMNS = [
    "carbs_current",
    "carbs_last_30m",
    "carbs_last_60m",
    "carbs_last_120m",
    "carbs_last_180m",
    "bolus_current",
    "bolus_last_30m",
    "bolus_last_60m",
    "bolus_last_120m",
    "bolus_last_180m",
    "basal_current",
    "basal_mean_60m",
    "basal_mean_120m",
    "exercise_active",
    "exercise_last_60m",
    "exercise_last_120m",
    "sleep_indicator",
    "hypo_event_current",
    "gsr_current",
    "skin_temperature_current",
    "acceleration_current",
    "day_of_week",
    "patient_id_numeric",
]


def _safe_timestamp(value: str | None) -> pd.Timestamp | pd.NaT:
    return pd.to_datetime(value, format=OHIO_TIMESTAMP_FORMAT, errors="coerce")


def _safe_float(value: str | None, default: float = 0.0) -> float:
    parsed = pd.to_numeric(value, errors="coerce")
    if pd.isna(parsed):
        return default
    return float(parsed)


def parse_ohiot1dm_xml(xml_path: str | Path, *, year: str | int | None = None, split: str | None = None) -> pd.DataFrame:
    """Parse one OhioT1DM XML file into CGM glucose rows.

    The returned frame contains only CGM glucose-level events and leaves other
    event types untouched so downstream forecasting stays focused and stable.
    """
    xml_path = Path(xml_path)
    root = ET.parse(xml_path).getroot()
    patient_id = str(root.attrib.get("id", xml_path.name.split("-")[0]))
    weight = root.attrib.get("weight")
    insulin_type = root.attrib.get("insulin_type")

    rows: list[dict[str, object]] = []
    glucose_node = root.find("glucose_level")
    if glucose_node is None:
        return pd.DataFrame(columns=[
            "timestamp",
            "glucose_mg_dl",
            "patient_id",
            "year",
            "split",
            "source_file",
            "weight",
            "insulin_type",
        ])

    for event in glucose_node.findall("event"):
        timestamp = _safe_timestamp(event.attrib.get("ts"))
        value = pd.to_numeric(event.attrib.get("value"), errors="coerce")
        if pd.isna(timestamp) or pd.isna(value):
            continue
        rows.append({
            "timestamp": timestamp,
            "glucose_mg_dl": float(value),
            "patient_id": patient_id,
            "year": str(year) if year is not None else "",
            "split": split or "",
            "source_file": str(xml_path),
            "weight": float(weight) if weight not in {None, ""} else None,
            "insulin_type": insulin_type or "",
        })

    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    return frame.sort_values(["patient_id", "timestamp"]).reset_index(drop=True)


def parse_ohiot1dm_directory(root_dir: str | Path) -> pd.DataFrame:
    """Parse all OhioT1DM XML files under year/train|test directories."""
    root_dir = Path(root_dir)
    frames: list[pd.DataFrame] = []
    for xml_path in sorted(root_dir.glob("*/*/*.xml")):
        year = xml_path.parent.parent.name
        split = xml_path.parent.name
        if split not in {"train", "test"}:
            continue
        frames.append(parse_ohiot1dm_xml(xml_path, year=year, split=split))
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True).sort_values(
        ["year", "split", "patient_id", "timestamp"]
    ).reset_index(drop=True)


def _metadata(root: ET.Element, xml_path: Path, year: str | int | None, split: str | None) -> dict[str, object]:
    weight = root.attrib.get("weight")
    return {
        "patient_id": str(root.attrib.get("id", xml_path.name.split("-")[0])),
        "year": str(year) if year is not None else "",
        "split": split or "",
        "source_file": str(xml_path),
        "weight": _safe_float(weight, default=np.nan) if weight not in {None, ""} else np.nan,
        "insulin_type": root.attrib.get("insulin_type", ""),
    }


def _point_events(
    root: ET.Element,
    section: str,
    value_attr: str,
    value_name: str,
    meta: dict[str, object],
    *,
    timestamp_attr: str = "ts",
) -> pd.DataFrame:
    node = root.find(section)
    rows: list[dict[str, object]] = []
    if node is None:
        return pd.DataFrame(columns=["timestamp", value_name, *meta.keys()])
    for event in node.findall("event"):
        timestamp = _safe_timestamp(event.attrib.get(timestamp_attr))
        if pd.isna(timestamp):
            continue
        rows.append({
            "timestamp": timestamp,
            value_name: _safe_float(event.attrib.get(value_attr)),
            **meta,
        })
    return pd.DataFrame(rows).sort_values("timestamp").reset_index(drop=True) if rows else pd.DataFrame(
        columns=["timestamp", value_name, *meta.keys()]
    )


def _interval_events(root: ET.Element, section: str, meta: dict[str, object]) -> pd.DataFrame:
    node = root.find(section)
    rows: list[dict[str, object]] = []
    if node is None:
        return pd.DataFrame(columns=["start_timestamp", "end_timestamp", *meta.keys()])
    for event in node.findall("event"):
        start_value = event.attrib.get("ts_begin") or event.attrib.get("tbegin") or event.attrib.get("ts")
        end_value = event.attrib.get("ts_end") or event.attrib.get("tend") or event.attrib.get("ts")
        start = _safe_timestamp(start_value)
        end = _safe_timestamp(end_value)
        if pd.isna(start):
            continue
        if pd.isna(end) or end < start:
            end = start
        rows.append({
            "start_timestamp": start,
            "end_timestamp": end,
            "event_type": event.attrib.get("type", section),
            "value": _safe_float(event.attrib.get("value"), default=1.0),
            **meta,
        })
    return pd.DataFrame(rows).sort_values("start_timestamp").reset_index(drop=True) if rows else pd.DataFrame(
        columns=["start_timestamp", "end_timestamp", "event_type", "value", *meta.keys()]
    )


def parse_ohiot1dm_event_frames(
    xml_path: str | Path,
    *,
    year: str | int | None = None,
    split: str | None = None,
) -> dict[str, pd.DataFrame]:
    """Parse one OhioT1DM XML file into typed event DataFrames."""
    xml_path = Path(xml_path)
    root = ET.parse(xml_path).getroot()
    meta = _metadata(root, xml_path, year, split)
    return {
        "glucose": parse_ohiot1dm_xml(xml_path, year=year, split=split),
        "meal": _point_events(root, "meal", "carbs", "carbs", meta),
        "bolus": _point_events(root, "bolus", "dose", "bolus_dose", meta, timestamp_attr="ts_begin"),
        "basal": _point_events(root, "basal", "value", "basal_rate", meta),
        "exercise": _interval_events(root, "exercise", meta),
        "sleep": _interval_events(root, "sleep", meta),
        "hypo_event": _interval_events(root, "hypo_event", meta),
        "basis_gsr": _point_events(root, "basis_gsr", "value", "gsr", meta),
        "basis_skin_temperature": _point_events(root, "basis_skin_temperature", "value", "skin_temperature", meta),
        "acceleration": _point_events(root, "acceleration", "value", "acceleration", meta),
    }


def _rolling_event_sum(base: pd.DataFrame, events: pd.DataFrame, value_column: str, output_prefix: str) -> pd.DataFrame:
    result = pd.DataFrame(index=base.index)
    windows = [5, 30, 60, 120, 180]
    if events.empty:
        for window in windows:
            result[f"{output_prefix}_{'current' if window == 5 else f'last_{window}m'}"] = 0.0
        return result

    event_values = events[["timestamp", value_column]].copy().sort_values("timestamp")
    event_values[value_column] = pd.to_numeric(event_values[value_column], errors="coerce").fillna(0.0)
    base_times = base[["timestamp"]].copy().sort_values("timestamp")
    for window in windows:
        rolled = event_values.set_index("timestamp")[value_column].rolling(f"{window}min", closed="both").sum()
        rolled = rolled.reset_index().rename(columns={value_column: "rolled_value", "timestamp": "event_timestamp"})
        merged = pd.merge_asof(
            base_times,
            rolled,
            left_on="timestamp",
            right_on="event_timestamp",
            direction="backward",
        )
        stale = (base_times["timestamp"] - merged["event_timestamp"]).dt.total_seconds() > window * 60
        values = merged["rolled_value"].fillna(0.0).mask(stale.fillna(True), 0.0)
        name = f"{output_prefix}_{'current' if window == 5 else f'last_{window}m'}"
        result.loc[base_times.index, name] = values.to_numpy()
    return result.sort_index()


def _asof_current(base: pd.DataFrame, events: pd.DataFrame, value_column: str, output_name: str) -> pd.Series:
    if events.empty:
        return pd.Series(0.0, index=base.index, name=output_name)
    base_times = base[["timestamp"]].copy().sort_values("timestamp")
    event_values = events[["timestamp", value_column]].copy().sort_values("timestamp")
    merged = pd.merge_asof(base_times, event_values, on="timestamp", direction="backward")
    values = merged[value_column].fillna(0.0)
    series = pd.Series(values.to_numpy(), index=base_times.index, name=output_name)
    return series.sort_index()


def _interval_features(base: pd.DataFrame, intervals: pd.DataFrame, prefix: str) -> pd.DataFrame:
    result = pd.DataFrame(0.0, index=base.index, columns=[f"{prefix}_active", f"{prefix}_last_60m", f"{prefix}_last_120m"])
    if intervals.empty:
        return result
    times = base["timestamp"]
    for row in intervals.itertuples(index=False):
        start = getattr(row, "start_timestamp")
        end = getattr(row, "end_timestamp")
        result.loc[(times >= start) & (times <= end), f"{prefix}_active"] = 1.0
        result.loc[(times >= start) & (times <= end + pd.Timedelta(minutes=60)), f"{prefix}_last_60m"] = 1.0
        result.loc[(times >= start) & (times <= end + pd.Timedelta(minutes=120)), f"{prefix}_last_120m"] = 1.0
    return result


def _sleep_indicator(base: pd.DataFrame, intervals: pd.DataFrame) -> pd.Series:
    result = pd.Series(0.0, index=base.index, name="sleep_indicator")
    if intervals.empty:
        return result
    times = base["timestamp"]
    for row in intervals.itertuples(index=False):
        result.loc[(times >= getattr(row, "start_timestamp")) & (times <= getattr(row, "end_timestamp"))] = 1.0
    return result


def enrich_ohiot1dm_xml(xml_path: str | Path, *, year: str | int | None = None, split: str | None = None) -> pd.DataFrame:
    """Create a leakage-safe enriched CGM table for one XML file.

    All event aggregates use only events at or before the current CGM timestamp.
    Future glucose values are added later as targets by the forecasting module,
    never as input features here.
    """
    frames = parse_ohiot1dm_event_frames(xml_path, year=year, split=split)
    base = frames["glucose"].copy()
    if base.empty:
        return base
    base["timestamp"] = pd.to_datetime(base["timestamp"])
    base = base.sort_values("timestamp").reset_index(drop=True)

    carbs = _rolling_event_sum(base, frames["meal"], "carbs", "carbs")
    bolus = _rolling_event_sum(base, frames["bolus"], "bolus_dose", "bolus")
    basal_current = _asof_current(base, frames["basal"], "basal_rate", "basal_current")
    exercise = _interval_features(base, frames["exercise"], "exercise")
    sleep = _sleep_indicator(base, frames["sleep"])
    hypo = _sleep_indicator(base, frames["hypo_event"]).rename("hypo_event_current")
    gsr = _asof_current(base, frames["basis_gsr"], "gsr", "gsr_current")
    skin = _asof_current(base, frames["basis_skin_temperature"], "skin_temperature", "skin_temperature_current")
    accel = _asof_current(base, frames["acceleration"], "acceleration", "acceleration_current")

    enriched = pd.concat([base, carbs, bolus, basal_current, exercise, sleep, hypo, gsr, skin, accel], axis=1)
    enriched["basal_mean_60m"] = enriched["basal_current"].rolling(window=12, min_periods=1).mean()
    enriched["basal_mean_120m"] = enriched["basal_current"].rolling(window=24, min_periods=1).mean()
    enriched["day_of_week"] = enriched["timestamp"].dt.dayofweek.astype(float)
    enriched["patient_id_numeric"] = pd.to_numeric(enriched["patient_id"], errors="coerce").fillna(0.0)
    for column in ENRICHED_EVENT_COLUMNS:
        if column not in enriched:
            enriched[column] = 0.0
    return enriched.sort_values("timestamp").reset_index(drop=True)


def enrich_ohiot1dm_directory(root_dir: str | Path) -> pd.DataFrame:
    root_dir = Path(root_dir)
    frames: list[pd.DataFrame] = []
    for xml_path in sorted(root_dir.glob("*/*/*.xml")):
        year = xml_path.parent.parent.name
        split = xml_path.parent.name
        if split not in {"train", "test"}:
            continue
        frames.append(enrich_ohiot1dm_xml(xml_path, year=year, split=split))
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True).sort_values(
        ["year", "split", "patient_id", "timestamp"]
    ).reset_index(drop=True)
