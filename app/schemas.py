# app/schemas.py
from pydantic import BaseModel
from typing import List, Optional, Dict

# --- 백엔드에서 받는 데이터 (Unity 센서 데이터) ---
class ActionData(BaseModel):
    action_type: str    # 동작 종류 (예: Swing)
    action_dir: str     # 동작 방향 (예: Forward, Backward)
    duration: float     # 동작 지속 시간 (초)
    angle_max: float    # 최대 가동 범위 (도)
    speed_max: float    # 최대 속도
    hold_time: float    # 버티기 시간 (초)
    result: bool        # 게임 내 성공 여부

class AnalysisRequest(BaseModel):
    game_id: str
    actions: List[ActionData]

# --- AI 서버가 계산해서 돌려주는 결과 데이터 ---
class AnalysisResponse(BaseModel):
    score: int                  # 최종 종합 점수
    rom_achievement: float      # 가동 범위(ROM) 달성률 (%)
    stability_score: int        # 동작의 정확도/안정성 점수 (%)
    safety_status: str          # [추가] 안전 상태 (SAFE, WARNING)
    difficulty_recommend: str   # 난이도 조절 추천 (UP, MAINTAIN, DOWN)
    feedback_message: str       # 사용자 맞춤형 피드백 문구
    stats: Optional[Dict] = None # [추가] 게임별 세부 통계 (Good 횟수, 위험 동작 횟수 등)