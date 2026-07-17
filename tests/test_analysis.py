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
