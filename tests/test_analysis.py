from app.demo import build_demo_session
from app.services import AnalysisService


def test_demo_metrics_and_recommendation() -> None:
    result = AnalysisService.analyze(build_demo_session())
    assert result.score >= 80
    assert result.metrics.total_actions == 6
    assert result.metrics.success_rate == 1.0
    assert result.data_quality.status == "GOOD"


def test_high_pain_generates_warning_and_down_recommendation() -> None:
    payload = build_demo_session()
    payload["self_report"]["pain_after_0_10"] = 8
    result = AnalysisService.analyze(payload)
    assert result.safety_status == "WARNING"
    assert result.difficulty_recommend == "DOWN"
    assert any(flag.code == "PAIN_INCREASE_HIGH" for flag in result.risk_flags)


def test_no_data_never_returns_a_high_performance_score() -> None:
    result = AnalysisService.analyze({})
    assert result.score == 0
    assert result.data_quality.status == "INSUFFICIENT"


def test_sensor_sequence_drives_rom_speed_and_assessability() -> None:
    now = 1_780_000_000_000
    actions = []
    for index in range(3):
        started = now + index * 2_000
        actions.append(
            {
                "actionId": str(index + 1),
                "actionType": "ATTACK",
                "exerciseCode": "SHOULDER_FLEXION",
                "startedAtMs": started,
                "endedAtMs": started + 1_000,
                "success": True,
                "attackGrade": "GOOD",
                "samples": [
                    {"timestampMs": started, "qx": 0, "qy": 0, "qz": 0, "qw": 1},
                    {"timestampMs": started + 300, "qx": 0, "qy": 0, "qz": 0.2588, "qw": 0.9659},
                    {"timestampMs": started + 600, "qx": 0, "qy": 0, "qz": 0.5, "qw": 0.8660},
                    {"timestampMs": started + 1_000, "qx": 0, "qy": 0, "qz": 0.0872, "qw": 0.9962},
                ],
            }
        )

    result = AnalysisService.analyze(
        {
            "historyId": "sensor-v2",
            "gameId": "Adventure",
            "primaryPart": "SHOULDER",
            "startedAtMs": now,
            "endedAtMs": now + 7_000,
            "actionCount": 3,
            "bodyPartSummaries": [{"bodyPart": "SHOULDER", "side": "BOTH"}],
            "selfReport": {"painBefore0to10": 1, "painAfter0to10": 1},
            "gameData": actions,
        }
    )

    assert result.data_quality.assessable is True
    assert result.data_quality.status == "GOOD"
    assert result.metrics.average_rom_deg is not None
    assert result.metrics.average_rom_deg >= 59
    assert result.metrics.peak_angular_velocity_dps is not None
    assert result.safety_status == "SAFE"


def test_missing_rehabilitation_evidence_cannot_return_safe_or_high_score() -> None:
    payload = {
        "historyId": "legacy-waist",
        "gameId": "Adventure",
        "primaryPart": "WAIST",
        "startedAtMs": 2026071705310795,
        "endedAtMs": 2026071705463256,
        "actionCount": 4,
        "successCount": 4,
        "failCount": 0,
        "bodyPartSummaries": [
            {
                "bodyPart": "SHOULDER",
                "side": "BOTH",
                "pain0to10": 0,
                "fatigue0to10": 0,
            }
        ],
        "gameData": [
            {"attackGrade, GyroQuaternion, attackTime": "Perfect, (0, 0, 0, 1), 0.1"}
            for _ in range(4)
        ],
    }

    result = AnalysisService.analyze(payload)

    assert result.body_part == "WAIST"
    assert result.safety_status == "UNKNOWN"
    assert result.data_quality.assessable is False
    assert result.score <= 65


def test_partial_sensor_coverage_cannot_be_marked_assessable() -> None:
    payload = build_demo_session()
    for action in payload["actions"][2:]:
        action["samples"] = []

    result = AnalysisService.analyze(payload)

    assert result.data_quality.coverage["samples"] < 0.6
    assert result.data_quality.assessable is False
    assert "MISSING_SENSOR_SEQUENCE" in result.data_quality.flags
    assert result.safety_status == "UNKNOWN"
    assert result.score <= 70
