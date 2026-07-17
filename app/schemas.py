from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BodyPart(str, Enum):
    SHOULDER = "SHOULDER"
    WAIST = "WAIST"
    WRIST = "WRIST"
    LEG = "LEG"
    UNKNOWN = "UNKNOWN"


class BodySide(str, Enum):
    L = "L"
    R = "R"
    BOTH = "BOTH"
    NONE = "NONE"


class DifficultyDecision(str, Enum):
    UP = "UP"
    MAINTAIN = "MAINTAIN"
    DOWN = "DOWN"


class SafetyStatus(str, Enum):
    SAFE = "SAFE"
    CAUTION = "CAUTION"
    WARNING = "WARNING"


class DataQualityStatus(str, Enum):
    GOOD = "GOOD"
    PARTIAL = "PARTIAL"
    INSUFFICIENT = "INSUFFICIENT"


class SensorSample(BaseModel):
    model_config = ConfigDict(extra="ignore")

    timestamp_ms: int
    angle_deg: float | None = None
    angular_velocity_dps: float | None = None
    qx: float | None = None
    qy: float | None = None
    qz: float | None = None
    qw: float | None = None


class ActionData(BaseModel):
    model_config = ConfigDict(extra="allow")

    action_id: str
    action_type: str = "UNKNOWN"
    direction: str = "UNKNOWN"
    started_at_ms: int | None = None
    ended_at_ms: int | None = None
    duration_ms: float | None = Field(default=None, ge=0)
    result: bool | None = None
    grade: str | None = None

    angle_start_deg: float | None = None
    angle_end_deg: float | None = None
    angle_max_deg: float | None = None
    rom_deg: float | None = Field(default=None, ge=0)
    mean_angular_velocity_dps: float | None = Field(default=None, ge=0)
    peak_angular_velocity_dps: float | None = Field(default=None, ge=0)
    hold_time_ms: float | None = Field(default=None, ge=0)
    samples: list[SensorSample] = Field(default_factory=list)

    @model_validator(mode="after")
    def fill_derived_values(self) -> "ActionData":
        if self.duration_ms is None and self.started_at_ms is not None and self.ended_at_ms is not None:
            self.duration_ms = max(float(self.ended_at_ms - self.started_at_ms), 0.0)
        if self.rom_deg is None and self.angle_start_deg is not None and self.angle_end_deg is not None:
            self.rom_deg = abs(self.angle_end_deg - self.angle_start_deg)
        if self.rom_deg is None and self.angle_max_deg is not None:
            self.rom_deg = abs(self.angle_max_deg)
        return self


class UserContext(BaseModel):
    model_config = ConfigDict(extra="ignore")

    age_group: str | None = None
    height_cm: float | None = Field(default=None, gt=0, le=300)
    weight_kg: float | None = Field(default=None, gt=0, le=500)
    dominant_hand: str | None = None
    diagnosis_tags: list[str] = Field(default_factory=list)
    pain_baseline_0_10: int | None = Field(default=None, ge=0, le=10)


class SelfReport(BaseModel):
    model_config = ConfigDict(extra="ignore")

    pain_before_0_10: int | None = Field(default=None, ge=0, le=10)
    pain_after_0_10: int | None = Field(default=None, ge=0, le=10)
    stiffness_after_0_10: int | None = Field(default=None, ge=0, le=10)
    fatigue_after_0_10: int | None = Field(default=None, ge=0, le=10)
    swelling: bool | None = None


class SessionAnalysisInput(BaseModel):
    model_config = ConfigDict(extra="allow")

    schema_version: str = "1.0"
    history_id: str
    user_id: str | None = None
    game_id: str
    game_name: str | None = None
    game_version: str | None = None
    primary_part: BodyPart = BodyPart.UNKNOWN
    side: BodySide = BodySide.NONE
    difficulty: int | None = Field(default=None, ge=1, le=100)
    started_at_ms: int | None = None
    ended_at_ms: int | None = None
    score: int | None = None
    action_count: int | None = Field(default=None, ge=0)
    success_count: int | None = Field(default=None, ge=0)
    fail_count: int | None = Field(default=None, ge=0)
    session_summary: dict[str, Any] = Field(default_factory=dict)
    profile: UserContext = Field(default_factory=UserContext)
    self_report: SelfReport = Field(default_factory=SelfReport)
    actions: list[ActionData] = Field(default_factory=list)
    normalization_flags: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_time_order(self) -> "SessionAnalysisInput":
        if (
            self.started_at_ms is not None
            and self.ended_at_ms is not None
            and self.ended_at_ms < self.started_at_ms
        ):
            raise ValueError("ended_at_ms must be greater than or equal to started_at_ms")
        return self


class DataQuality(BaseModel):
    status: DataQualityStatus
    completeness: float = Field(ge=0, le=1)
    valid_action_count: int
    sensor_sample_count: int
    flags: list[str]


class AnalysisMetrics(BaseModel):
    total_actions: int
    successful_actions: int
    failed_actions: int
    success_rate: float | None = None
    accuracy_score: float | None = None
    average_duration_ms: float | None = None
    average_rom_deg: float | None = None
    rom_achievement: float | None = None
    peak_angular_velocity_dps: float | None = None
    consistency_score: float | None = None
    smoothness_score: float | None = None
    fatigue_index: float | None = None
    rest_ratio: float | None = None
    safety_score: float


class RiskFlag(BaseModel):
    code: str
    severity: str
    message: str
    evidence: dict[str, Any] = Field(default_factory=dict)


class DifficultyRecommendation(BaseModel):
    decision: DifficultyDecision
    current_level: int | None = None
    recommended_level: int | None = None
    reason_codes: list[str]


class AnalysisResponse(BaseModel):
    analysis_id: str
    history_id: str
    analyzed_at_ms: int
    analysis_version: str
    schema_version: str
    game_id: str
    body_part: BodyPart
    side: BodySide

    score: int
    safety_status: SafetyStatus
    feedback_message: str
    difficulty_recommend: DifficultyDecision

    data_quality: DataQuality
    metrics: AnalysisMetrics
    difficulty: DifficultyRecommendation
    risk_flags: list[RiskFlag]
    coaching_messages: list[str]
    reason_codes: list[str]
    chart_data: dict[str, float | None]
    distribution_data: dict[str, int]
    stats: dict[str, Any]
