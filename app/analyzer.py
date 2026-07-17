from __future__ import annotations

import math
import statistics
import time
from typing import Iterable
from uuid import uuid4

from app.constants import (
    ANALYSIS_VERSION,
    GRADE_SCORE,
    MIN_ACTIONS_FOR_TREND,
    MIN_COMPLETENESS_FOR_UP,
    PEAK_SPEED_CAUTION_DPS,
    ROM_TARGET_DEG,
)
from app.schemas import (
    ActionData,
    AnalysisMetrics,
    AnalysisResponse,
    BodyPart,
    DataQuality,
    DataQualityStatus,
    DifficultyDecision,
    DifficultyRecommendation,
    RiskFlag,
    SafetyStatus,
    SessionAnalysisInput,
)


def _round(value: float | None, digits: int = 3) -> float | None:
    return round(value, digits) if value is not None and math.isfinite(value) else None


def _mean(values: Iterable[float]) -> float | None:
    items = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    return statistics.fmean(items) if items else None


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _grade_score(action: ActionData) -> float | None:
    if action.grade:
        score = GRADE_SCORE.get(action.grade.upper())
        if score is not None:
            return score
    if action.result is not None:
        return 100.0 if action.result else 0.0
    return None


def _coefficient_consistency(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    average = statistics.fmean(values)
    if average == 0:
        return None
    coefficient = statistics.pstdev(values) / abs(average)
    return _clamp(100.0 * (1.0 - min(coefficient, 1.0)))


def _quaternion_angle_deg(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    dot = abs(sum(x * y for x, y in zip(a, b)))
    dot = max(-1.0, min(1.0, dot))
    return math.degrees(2.0 * math.acos(dot))


def _sample_velocities(action: ActionData) -> list[tuple[int, float]]:
    samples = sorted(action.samples, key=lambda item: item.timestamp_ms)
    explicit = [
        (sample.timestamp_ms, sample.angular_velocity_dps)
        for sample in samples
        if sample.angular_velocity_dps is not None
    ]
    if len(explicit) >= 2:
        return [(timestamp, abs(float(value))) for timestamp, value in explicit]

    velocities: list[tuple[int, float]] = []
    for previous, current in zip(samples, samples[1:]):
        delta_seconds = (current.timestamp_ms - previous.timestamp_ms) / 1000.0
        if delta_seconds <= 0:
            continue
        angle_delta: float | None = None
        if previous.angle_deg is not None and current.angle_deg is not None:
            angle_delta = abs(current.angle_deg - previous.angle_deg)
        else:
            previous_q = (previous.qx, previous.qy, previous.qz, previous.qw)
            current_q = (current.qx, current.qy, current.qz, current.qw)
            if all(value is not None for value in previous_q + current_q):
                angle_delta = _quaternion_angle_deg(
                    tuple(float(value) for value in previous_q),
                    tuple(float(value) for value in current_q),
                )
        if angle_delta is not None:
            velocities.append((current.timestamp_ms, angle_delta / delta_seconds))
    return velocities


def _smoothness_and_peak(actions: list[ActionData]) -> tuple[float | None, float | None]:
    all_peaks: list[float] = [
        action.peak_angular_velocity_dps
        for action in actions
        if action.peak_angular_velocity_dps is not None
    ]
    jerks: list[float] = []
    for action in actions:
        velocities = _sample_velocities(action)
        if velocities:
            all_peaks.append(max(value for _, value in velocities))
        for previous, current in zip(velocities, velocities[1:]):
            delta_seconds = (current[0] - previous[0]) / 1000.0
            if delta_seconds > 0:
                jerks.append(abs(current[1] - previous[1]) / delta_seconds)
    peak = max(all_peaks) if all_peaks else None
    if not jerks:
        return None, peak
    mean_jerk = statistics.fmean(jerks)
    smoothness = 100.0 / (1.0 + mean_jerk / 300.0)
    return _clamp(smoothness), peak


def _fatigue_index(actions: list[ActionData]) -> float | None:
    scores = [score for action in actions if (score := _grade_score(action)) is not None]
    if len(scores) < MIN_ACTIONS_FOR_TREND:
        return None
    chunk = max(1, len(scores) // 3)
    first = statistics.fmean(scores[:chunk])
    last = statistics.fmean(scores[-chunk:])
    if first <= 0:
        return 0.0
    return max(0.0, min(1.0, (first - last) / first))


def _rest_ratio(session: SessionAnalysisInput) -> float | None:
    ordered = sorted(
        [
            action
            for action in session.actions
            if action.started_at_ms is not None and action.ended_at_ms is not None
        ],
        key=lambda action: action.started_at_ms or 0,
    )
    if len(ordered) < 2:
        return None
    active_ms = sum(max((action.ended_at_ms or 0) - (action.started_at_ms or 0), 0) for action in ordered)
    rest_ms = sum(
        max((current.started_at_ms or 0) - (previous.ended_at_ms or 0), 0)
        for previous, current in zip(ordered, ordered[1:])
    )
    total = active_ms + rest_ms
    return rest_ms / total if total > 0 else None


def _data_quality(session: SessionAnalysisInput) -> DataQuality:
    actions = session.actions
    flags = list(dict.fromkeys(session.normalization_flags))
    if not actions:
        flags.append("NO_ACTION_DATA")
    if 0 < len(actions) < 3:
        flags.append("INSUFFICIENT_ACTIONS")

    has_result = any(action.result is not None or action.grade is not None for action in actions)
    has_duration = any(action.duration_ms is not None for action in actions)
    has_rom = any(action.rom_deg is not None for action in actions)
    has_speed = any(
        action.peak_angular_velocity_dps is not None or len(_sample_velocities(action)) >= 1
        for action in actions
    )
    has_timestamps = any(
        action.started_at_ms is not None and action.ended_at_ms is not None for action in actions
    )
    has_samples = any(len(action.samples) >= 2 for action in actions)

    if actions and not has_rom:
        flags.append("MISSING_ROM")
    if actions and not has_speed:
        flags.append("MISSING_SPEED")
    if actions and not has_timestamps:
        flags.append("MISSING_ACTION_TIMESTAMPS")
    if actions and not has_samples:
        flags.append("MISSING_SENSOR_SEQUENCE")
    if (
        session.self_report.pain_after_0_10 is None
        and session.self_report.fatigue_after_0_10 is None
    ):
        flags.append("MISSING_SELF_REPORT")

    total_from_counts = session.action_count
    if total_from_counts is not None and actions and total_from_counts != len(actions):
        flags.append("ACTION_COUNT_MISMATCH")

    completeness = (
        (0.20 if actions else 0.0)
        + (0.15 if has_result else 0.0)
        + (0.15 if has_duration else 0.0)
        + (0.20 if has_rom else 0.0)
        + (0.15 if has_speed else 0.0)
        + (0.10 if has_timestamps else 0.0)
        + (0.05 if has_samples else 0.0)
    )
    if completeness >= 0.75:
        status = DataQualityStatus.GOOD
    elif completeness >= 0.35 or total_from_counts:
        status = DataQualityStatus.PARTIAL
    else:
        status = DataQualityStatus.INSUFFICIENT

    return DataQuality(
        status=status,
        completeness=round(completeness, 2),
        valid_action_count=len(actions),
        sensor_sample_count=sum(len(action.samples) for action in actions),
        flags=list(dict.fromkeys(flags)),
    )


def _risks(
    session: SessionAnalysisInput,
    peak_speed: float | None,
    fatigue_index: float | None,
    data_quality: DataQuality,
) -> list[RiskFlag]:
    risks: list[RiskFlag] = []
    report = session.self_report
    if report.pain_after_0_10 is not None:
        pain_increase = None
        if report.pain_before_0_10 is not None:
            pain_increase = report.pain_after_0_10 - report.pain_before_0_10
        if report.pain_after_0_10 >= 7 or (pain_increase is not None and pain_increase >= 3):
            risks.append(
                RiskFlag(
                    code="PAIN_INCREASE_HIGH",
                    severity="HIGH",
                    message="운동 후 통증 수치가 높거나 크게 증가했습니다.",
                    evidence={
                        "pain_before": report.pain_before_0_10,
                        "pain_after": report.pain_after_0_10,
                    },
                )
            )
    if report.swelling is True:
        risks.append(
            RiskFlag(
                code="SWELLING_REPORTED",
                severity="HIGH",
                message="운동 후 부종이 보고되었습니다.",
            )
        )
    speed_limit = PEAK_SPEED_CAUTION_DPS[session.primary_part.value]
    if peak_speed is not None and peak_speed > speed_limit:
        risks.append(
            RiskFlag(
                code="PEAK_SPEED_HIGH",
                severity="MEDIUM",
                message="최대 움직임 속도가 현재 설정된 주의 기준을 넘었습니다.",
                evidence={"peak_dps": round(peak_speed, 1), "threshold_dps": speed_limit},
            )
        )
    if fatigue_index is not None and fatigue_index >= 0.35:
        risks.append(
            RiskFlag(
                code="PERFORMANCE_DROP_HIGH",
                severity="MEDIUM",
                message="세션 후반 수행도가 초반보다 크게 감소했습니다.",
                evidence={"fatigue_index": round(fatigue_index, 3)},
            )
        )
    if report.fatigue_after_0_10 is not None and report.fatigue_after_0_10 >= 8:
        risks.append(
            RiskFlag(
                code="FATIGUE_REPORTED_HIGH",
                severity="MEDIUM",
                message="사용자가 높은 피로도를 보고했습니다.",
                evidence={"fatigue_after": report.fatigue_after_0_10},
            )
        )
    if data_quality.status == DataQualityStatus.INSUFFICIENT:
        risks.append(
            RiskFlag(
                code="DATA_UNRELIABLE",
                severity="INFO",
                message="분석에 필요한 동작 데이터가 부족해 결과 신뢰도가 낮습니다.",
                evidence={"completeness": data_quality.completeness},
            )
        )
    return risks


def _safety(risks: list[RiskFlag]) -> tuple[SafetyStatus, float]:
    penalty = {"HIGH": 35.0, "MEDIUM": 15.0, "INFO": 3.0}
    score = _clamp(100.0 - sum(penalty.get(risk.severity, 5.0) for risk in risks))
    if any(risk.severity == "HIGH" for risk in risks):
        return SafetyStatus.WARNING, score
    if any(risk.severity == "MEDIUM" for risk in risks):
        return SafetyStatus.CAUTION, score
    return SafetyStatus.SAFE, score


def _difficulty(
    session: SessionAnalysisInput,
    success_rate: float | None,
    accuracy: float | None,
    fatigue: float | None,
    safety_status: SafetyStatus,
    safety_score: float,
    data_quality: DataQuality,
) -> DifficultyRecommendation:
    reasons: list[str] = []
    decision = DifficultyDecision.MAINTAIN
    reported_pain = session.self_report.pain_after_0_10

    if safety_status == SafetyStatus.WARNING:
        decision = DifficultyDecision.DOWN
        reasons.append("SAFETY_WARNING")
    elif reported_pain is not None and reported_pain >= 7:
        decision = DifficultyDecision.DOWN
        reasons.append("PAIN_HIGH")
    elif success_rate is not None and success_rate < 0.50:
        decision = DifficultyDecision.DOWN
        reasons.append("SUCCESS_RATE_LOW")
    elif fatigue is not None and fatigue >= 0.40:
        decision = DifficultyDecision.DOWN
        reasons.append("FATIGUE_HIGH")
    elif (
        success_rate is not None
        and success_rate >= 0.85
        and accuracy is not None
        and accuracy >= 80
        and safety_score >= 85
        and (fatigue is None or fatigue < 0.20)
        and data_quality.completeness >= MIN_COMPLETENESS_FOR_UP
    ):
        decision = DifficultyDecision.UP
        reasons.extend(["SUCCESS_RATE_HIGH", "ACCURACY_HIGH", "SAFETY_STABLE"])
    else:
        reasons.append("CURRENT_LEVEL_APPROPRIATE")
        if data_quality.completeness < MIN_COMPLETENESS_FOR_UP:
            reasons.append("DATA_QUALITY_LIMITED")

    current = session.difficulty
    recommended = current
    if current is not None:
        recommended = current + 1 if decision == DifficultyDecision.UP else current
        recommended = max(1, current - 1) if decision == DifficultyDecision.DOWN else recommended

    return DifficultyRecommendation(
        decision=decision,
        current_level=current,
        recommended_level=recommended,
        reason_codes=reasons,
    )


def _weighted_score(values: list[tuple[float | None, float]]) -> int:
    available = [(value, weight) for value, weight in values if value is not None]
    if not available:
        return 0
    numerator = sum(float(value) * weight for value, weight in available)
    denominator = sum(weight for _, weight in available)
    return int(round(_clamp(numerator / denominator)))


def analyze_session(session: SessionAnalysisInput) -> AnalysisResponse:
    actions = session.actions
    data_quality = _data_quality(session)

    action_successes = [action.result for action in actions if action.result is not None]
    if action_successes:
        successful = sum(1 for value in action_successes if value)
        failed = sum(1 for value in action_successes if not value)
        total = len(action_successes)
    else:
        successful = session.success_count or 0
        failed = session.fail_count or 0
        total = session.action_count if session.action_count is not None else successful + failed
    success_rate = successful / total if total > 0 else None

    grade_scores = [score for action in actions if (score := _grade_score(action)) is not None]
    accuracy = _mean(grade_scores)
    durations = [action.duration_ms for action in actions if action.duration_ms is not None]
    rom_values = [action.rom_deg for action in actions if action.rom_deg is not None]
    average_duration = _mean(durations)
    average_rom = _mean(rom_values)
    rom_target = ROM_TARGET_DEG[session.primary_part.value]
    rom_achievement = _clamp((average_rom / rom_target) * 100.0) if average_rom is not None else None

    duration_consistency = _coefficient_consistency([float(value) for value in durations])
    rom_consistency = _coefficient_consistency([float(value) for value in rom_values])
    consistency = _mean(
        [value for value in (duration_consistency, rom_consistency) if value is not None]
    )
    smoothness, peak_speed = _smoothness_and_peak(actions)
    fatigue = _fatigue_index(actions)
    rest_ratio = _rest_ratio(session)

    risks = _risks(session, peak_speed, fatigue, data_quality)
    safety_status, safety_score = _safety(risks)
    recommendation = _difficulty(
        session,
        success_rate,
        accuracy,
        fatigue,
        safety_status,
        safety_score,
        data_quality,
    )

    score = _weighted_score(
        [
            (success_rate * 100.0 if success_rate is not None else None, 0.30),
            (accuracy, 0.25),
            (rom_achievement, 0.20),
            (consistency, 0.10),
            (smoothness, 0.05),
            (safety_score, 0.10),
        ]
    )
    if total <= 0:
        score = 0

    reason_codes = list(recommendation.reason_codes)
    coaching: list[str] = []
    if safety_status == SafetyStatus.WARNING:
        feedback = "통증 또는 안전 위험 신호가 있어 난이도를 낮추고 상태를 확인해야 합니다."
        coaching.append("불편감이 지속되면 운동을 중단하고 담당 전문가와 상의하세요.")
    elif data_quality.status == DataQualityStatus.INSUFFICIENT:
        feedback = "동작 데이터가 부족해 정확한 평가가 어렵습니다. 센서 기록을 확인해 주세요."
        coaching.append("다음 세션부터 동작별 각도, 속도, 시작·종료 시각을 함께 기록하세요.")
    elif recommendation.decision == DifficultyDecision.UP:
        feedback = "수행 정확도와 성공률이 안정적이어서 다음 난이도로 올릴 수 있습니다."
        coaching.append("현재 동작 범위와 속도를 유지하면서 한 단계 높은 난이도를 시도하세요.")
    elif recommendation.decision == DifficultyDecision.DOWN:
        feedback = "현재 수행도 또는 피로 신호를 고려해 난이도를 한 단계 낮추는 것이 좋습니다."
        coaching.append("반복 횟수를 줄이고 정확한 자세와 충분한 휴식에 집중하세요.")
    else:
        feedback = "현재 난이도를 유지하면서 일정한 속도와 동작 범위를 반복하세요."
        coaching.append("동작마다 같은 범위와 속도를 유지하는 데 집중하세요.")

    if rom_achievement is not None and rom_achievement < 70:
        coaching.append("통증이 없는 범위에서 움직임의 크기를 조금씩 넓혀 보세요.")
        reason_codes.append("ROM_ACHIEVEMENT_LOW")
    if consistency is not None and consistency < 65:
        coaching.append("빠르게 반복하기보다 각 동작의 속도를 일정하게 맞춰 보세요.")
        reason_codes.append("CONSISTENCY_LOW")
    if fatigue is not None and fatigue >= 0.25:
        coaching.append("후반 수행도가 감소했으므로 세트 사이 휴식 시간을 늘려 보세요.")
        reason_codes.append("FATIGUE_TREND")

    grade_distribution = {grade: 0 for grade in GRADE_SCORE}
    unknown_count = 0
    for action in actions:
        grade = action.grade.upper() if action.grade else None
        if grade in grade_distribution:
            grade_distribution[grade] += 1
        else:
            unknown_count += 1
    if unknown_count:
        grade_distribution["UNKNOWN"] = unknown_count

    metrics = AnalysisMetrics(
        total_actions=int(total or 0),
        successful_actions=successful,
        failed_actions=failed,
        success_rate=_round(success_rate),
        accuracy_score=_round(accuracy, 1),
        average_duration_ms=_round(average_duration, 1),
        average_rom_deg=_round(average_rom, 1),
        rom_achievement=_round(rom_achievement, 1),
        peak_angular_velocity_dps=_round(peak_speed, 1),
        consistency_score=_round(consistency, 1),
        smoothness_score=_round(smoothness, 1),
        fatigue_index=_round(fatigue),
        rest_ratio=_round(rest_ratio),
        safety_score=_round(safety_score, 1) or 0.0,
    )

    return AnalysisResponse(
        analysis_id=str(uuid4()),
        history_id=session.history_id,
        analyzed_at_ms=int(time.time() * 1000),
        analysis_version=ANALYSIS_VERSION,
        schema_version=session.schema_version,
        game_id=session.game_id,
        body_part=session.primary_part,
        side=session.side,
        score=score,
        safety_status=safety_status,
        feedback_message=feedback,
        difficulty_recommend=recommendation.decision,
        data_quality=data_quality,
        metrics=metrics,
        difficulty=recommendation,
        risk_flags=risks,
        coaching_messages=list(dict.fromkeys(coaching)),
        reason_codes=list(dict.fromkeys(reason_codes)),
        chart_data={
            "success_rate": _round(success_rate * 100.0, 1) if success_rate is not None else None,
            "accuracy": _round(accuracy, 1),
            "rom_achievement": _round(rom_achievement, 1),
            "consistency": _round(consistency, 1),
            "smoothness": _round(smoothness, 1),
            "safety": _round(safety_score, 1),
        },
        distribution_data=grade_distribution,
        stats={
            "rom_target_deg": rom_target,
            "speed_caution_threshold_dps": PEAK_SPEED_CAUTION_DPS[session.primary_part.value],
            "raw_action_count": len(actions),
        },
    )
