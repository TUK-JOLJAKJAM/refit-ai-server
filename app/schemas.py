# app/schemas.py
from pydantic import BaseModel
from typing import List, Dict, Any, Optional


# --- 수신용 데이터 (From Unity/Spring) ---
class ActionData(BaseModel):
    action_type: str
    action_dir: str
    duration: float
    angle_max: float
    speed_max: float
    hold_time: float
    result: bool


class AnalysisRequest(BaseModel):
    game_id: str
    actions: List[ActionData]


# --- 송신용 데이터 (To Spring -> To React) ---
class AnalysisResponse(BaseModel):
    # 1. 핵심 요약 (Spring DB 저장 및 리액트 헤더용)
    score: int
    safety_status: str
    feedback_message: str

    # 2. 시각화 전용 데이터 (리액트 차트 컴포넌트로 직결)
    # 리액트 담당자가 "data.chart_data"만 참조하면 바로 그래프를 그릴 수 있게 함
    chart_data: Dict[str, int]
    distribution_data: Dict[str, int]

    # 3. 메타 정보 및 추천 난이도
    difficulty_recommend: str
    stats: Dict[str, Any]  # 분석 로그용 상세 수치