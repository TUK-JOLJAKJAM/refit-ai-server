from __future__ import annotations

import re
from typing import Any
from uuid import uuid4

from app.schemas import SessionAnalysisInput


LEGACY_ACTION_RE = re.compile(
    r"^\s*(?P<grade>[A-Za-z]+)\s*,\s*"
    r"\((?P<qx>-?[\d.]+)\s*,\s*(?P<qy>-?[\d.]+)\s*,\s*"
    r"(?P<qz>-?[\d.]+)\s*,\s*(?P<qw>-?[\d.]+)\)\s*,\s*"
    r"(?P<duration>-?[\d.]+)\s*$"
)


def _pick(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
    return default


def _as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: Any) -> int | None:
    number = _as_float(value)
    return int(number) if number is not None else None


def _as_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes", "success"}:
        return True
    if normalized in {"false", "0", "no", "fail", "failure"}:
        return False
    return None


def _epoch_ms(value: Any, flags: list[str]) -> int | None:
    timestamp = _as_int(value)
    if timestamp is None:
        return None
    if 946_684_800_000 <= timestamp <= 4_102_444_800_000:
        return timestamp
    if "LEGACY_NON_EPOCH_TIMESTAMP" not in flags:
        flags.append("LEGACY_NON_EPOCH_TIMESTAMP")
    return None


def _normalize_sample(sample: dict[str, Any]) -> dict[str, Any] | None:
    timestamp = _as_int(_pick(sample, "timestamp_ms", "timestampMs", "t_ms", "tMs"))
    if timestamp is None:
        return None
    return {
        "timestamp_ms": timestamp,
        "angle_deg": _as_float(_pick(sample, "angle_deg", "angleDeg")),
        "angular_velocity_dps": _as_float(
            _pick(sample, "angular_velocity_dps", "angularVelocityDps")
        ),
        "qx": _as_float(sample.get("qx")),
        "qy": _as_float(sample.get("qy")),
        "qz": _as_float(sample.get("qz")),
        "qw": _as_float(sample.get("qw")),
    }


def _normalize_structured_action(raw: dict[str, Any], index: int) -> dict[str, Any]:
    duration_ms = _as_float(_pick(raw, "duration_ms", "durationMs"))
    if duration_ms is None:
        duration_seconds = _as_float(raw.get("duration"))
        duration_ms = duration_seconds * 1000.0 if duration_seconds is not None else None

    hold_time_ms = _as_float(_pick(raw, "hold_time_ms", "holdTimeMs"))
    if hold_time_ms is None:
        hold_seconds = _as_float(_pick(raw, "hold_time", "holdTime"))
        hold_time_ms = hold_seconds * 1000.0 if hold_seconds is not None else None

    grade = _pick(raw, "grade", "attackGrade")
    result = _as_bool(_pick(raw, "result", "success"))
    if result is None and grade is not None:
        result = str(grade).upper() != "MISS"

    samples = []
    for sample in _pick(raw, "samples", "sensorSamples", default=[]) or []:
        if isinstance(sample, dict):
            normalized = _normalize_sample(sample)
            if normalized is not None:
                samples.append(normalized)

    return {
        "action_id": str(_pick(raw, "action_id", "actionId", default=index + 1)),
        "action_type": str(_pick(raw, "action_type", "actionType", default="UNKNOWN")),
        "exercise_code": str(
            _pick(raw, "exercise_code", "exerciseCode", default="UNKNOWN")
        ),
        "direction": str(
            _pick(raw, "direction", "action_dir", "actionDir", default="UNKNOWN")
        ),
        "started_at_ms": _as_int(_pick(raw, "started_at_ms", "startedAtMs")),
        "ended_at_ms": _as_int(_pick(raw, "ended_at_ms", "endedAtMs")),
        "duration_ms": duration_ms,
        "result": result,
        "grade": str(grade).upper() if grade is not None else None,
        "angle_start_deg": _as_float(_pick(raw, "angle_start_deg", "angleStartDeg")),
        "angle_end_deg": _as_float(_pick(raw, "angle_end_deg", "angleEndDeg")),
        "angle_max_deg": _as_float(
            _pick(raw, "angle_max_deg", "angleMaxDeg", "angle_max")
        ),
        "rom_deg": _as_float(_pick(raw, "rom_deg", "romDeg", "rom_angle")),
        "mean_angular_velocity_dps": _as_float(
            _pick(raw, "mean_angular_velocity_dps", "meanAngularVelocityDps")
        ),
        "peak_angular_velocity_dps": _as_float(
            _pick(raw, "peak_angular_velocity_dps", "peakAngularVelocityDps", "speed_max")
        ),
        "hold_time_ms": hold_time_ms,
        "reaction_time_ms": _as_float(
            _pick(raw, "reaction_time_ms", "reactionTimeMs")
        ),
        "samples": samples,
    }


def _normalize_legacy_action(raw: dict[str, Any], index: int) -> dict[str, Any] | None:
    for key, value in raw.items():
        if "attackGrade" not in str(key) or not isinstance(value, str):
            continue
        match = LEGACY_ACTION_RE.match(value)
        if match is None:
            return None
        grade = match.group("grade").upper()
        duration_ms = max(float(match.group("duration")) * 1000.0, 0.0)
        return {
            "action_id": str(index + 1),
            "action_type": "ATTACK",
            "direction": "UNKNOWN",
            "duration_ms": duration_ms,
            "result": grade != "MISS",
            "grade": grade,
            "samples": [
                {
                    "timestamp_ms": 0,
                    "qx": float(match.group("qx")),
                    "qy": float(match.group("qy")),
                    "qz": float(match.group("qz")),
                    "qw": float(match.group("qw")),
                }
            ],
        }
    return None


def _normalize_actions(payload: dict[str, Any], flags: list[str]) -> list[dict[str, Any]]:
    raw_actions = _pick(payload, "actions", "game_data", "gameData", default=[]) or []
    actions: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_actions):
        if not isinstance(raw, dict):
            continue
        legacy = _normalize_legacy_action(raw, index)
        if legacy is not None:
            actions.append(legacy)
            if "LEGACY_COMPOSITE_ACTION" not in flags:
                flags.append("LEGACY_COMPOSITE_ACTION")
            continue
        actions.append(_normalize_structured_action(raw, index))
    return actions


def _normalize_body_context(payload: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    primary_part = str(_pick(payload, "primary_part", "primaryPart", default="UNKNOWN")).upper()
    side = str(_pick(payload, "side", default="NONE")).upper()
    summaries = _pick(payload, "body_part_summaries", "bodyPartSummaries", default=[]) or []
    selected: dict[str, Any] = {}
    for item in summaries:
        if not isinstance(item, dict):
            continue
        item_part = str(_pick(item, "body_part", "bodyPart", default="UNKNOWN")).upper()
        if item_part == primary_part:
            selected = item
            break
    if selected:
        primary_part = str(_pick(selected, "body_part", "bodyPart", default=primary_part)).upper()
        side = str(_pick(selected, "side", default=side)).upper()
    return primary_part, side, selected


def normalize_request(payload: dict[str, Any]) -> SessionAnalysisInput:
    flags: list[str] = []
    primary_part, side, body_summary = _normalize_body_context(payload)
    session_summary = _pick(payload, "session_summary", "sessionSummary", default={}) or {}
    profile_raw = _pick(payload, "profile", "userProfile", default={}) or {}
    self_report_raw = _pick(payload, "self_report", "selfReport", default={}) or {}
    raw_body_metrics = body_summary.get("metrics", {}) if isinstance(body_summary, dict) else {}
    body_metrics = raw_body_metrics if isinstance(raw_body_metrics, dict) else {}
    difficulty = _as_int(
        _pick(
            payload,
            "difficulty",
            "difficultyLevel",
            default=_pick(session_summary, "stageLevel", "stage_level"),
        )
    )
    if difficulty is not None and not 1 <= difficulty <= 100:
        difficulty = None

    pain_before = _as_int(
        _pick(
            self_report_raw,
            "pain_before_0_10",
            "painBefore0to10",
            default=_pick(session_summary, "pain_before_0_10", "painBefore0to10"),
        )
    )
    pain_after = _as_int(
        _pick(
            self_report_raw,
            "pain_after_0_10",
            "painAfter0to10",
            default=_pick(body_summary, "pain0to10", "pain_0_10", default=None),
        )
    )
    fatigue_after = _as_int(
        _pick(
            self_report_raw,
            "fatigue_after_0_10",
            "fatigueAfter0to10",
            default=_pick(body_summary, "fatigue0to10", "fatigue_0_10", default=None),
        )
    )
    stiffness_after = _as_int(
        _pick(
            self_report_raw,
            "stiffness_after_0_10",
            "stiffnessAfter0to10",
            default=_pick(body_summary, "stiffness0to10", "stiffness_0_10", default=None),
        )
    )

    normalized = {
        "schema_version": str(_pick(payload, "schema_version", "schemaVersion", default="1.0")),
        "history_id": str(
            _pick(payload, "history_id", "historyId", "session_id", "sessionId", default=uuid4())
        ),
        "user_id": _pick(payload, "user_id", "userId"),
        "game_id": str(_pick(payload, "game_id", "gameId", default="UNKNOWN_GAME")),
        "game_name": _pick(payload, "game_name", "gameName"),
        "game_version": _pick(payload, "game_version", "gameVersion"),
        "primary_part": primary_part
        if primary_part in {"SHOULDER", "BICEPS_BRACHII", "WAIST", "WRIST", "LEG"}
        else "UNKNOWN",
        "side": side if side in {"L", "R", "BOTH", "NONE"} else "NONE",
        "difficulty": difficulty,
        "started_at_ms": _epoch_ms(_pick(payload, "started_at_ms", "startedAtMs"), flags),
        "ended_at_ms": _epoch_ms(_pick(payload, "ended_at_ms", "endedAtMs"), flags),
        "score": _as_int(payload.get("score")),
        "action_count": _as_int(_pick(payload, "action_count", "actionCount")),
        "success_count": _as_int(_pick(payload, "success_count", "successCount")),
        "fail_count": _as_int(_pick(payload, "fail_count", "failCount")),
        "session_summary": session_summary,
        "profile": {
            "age_group": _pick(profile_raw, "age_group", "ageGroup"),
            "height_cm": _as_float(_pick(profile_raw, "height_cm", "heightCm")),
            "weight_kg": _as_float(_pick(profile_raw, "weight_kg", "weightKg")),
            "dominant_hand": _pick(profile_raw, "dominant_hand", "dominantHand"),
            "diagnosis_tags": _pick(profile_raw, "diagnosis_tags", "diagnosisTags", default=[]) or [],
            "pain_baseline_0_10": _as_int(
                _pick(profile_raw, "pain_baseline_0_10", "painBaseline0to10")
            ),
            "baseline_rom_deg": _as_float(
                _pick(
                    profile_raw,
                    "baseline_rom_deg",
                    "baselineRomDeg",
                    default=_pick(body_metrics, "baseline_rom_deg", "baselineRomDeg"),
                )
            ),
            "target_rom_deg": _as_float(
                _pick(
                    profile_raw,
                    "target_rom_deg",
                    "targetRomDeg",
                    default=_pick(
                        session_summary,
                        "target_rom_deg",
                        "targetRomDeg",
                        default=_pick(body_metrics, "target_rom_deg", "targetRomDeg"),
                    ),
                )
            ),
        },
        "self_report": {
            "pain_before_0_10": pain_before,
            "pain_after_0_10": pain_after,
            "stiffness_after_0_10": stiffness_after,
            "fatigue_after_0_10": fatigue_after,
            "swelling": _as_bool(
                _pick(self_report_raw, "swelling", default=body_summary.get("swelling"))
            ),
        },
        "actions": _normalize_actions(payload, flags),
        "normalization_flags": flags,
    }
    return SessionAnalysisInput.model_validate(normalized)
