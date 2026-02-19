from pydantic import BaseModel
from typing import List, Optional

# 1. 개별 동작 데이터 (데이터 시트의 변수들 반영)
class ActionData(BaseModel):
    action_type: int              # 동작 종류 (0: 전방굴곡, 1: 스쿼트 등)
    action_dir: Optional[int] = 0 # 방향 (0: 상, 1: 하 등)
    body_part: Optional[int] = 0  # 부위 (0: 양쪽, 1: 왼쪽 등)
    duration: float               # 소요 시간
    angle_max: float              # 최고 각도
    speed_max: float              # 최고 속도
    hold_time: Optional[float] = 0.0 # 버틴 시간 (몬스터타워용)
    result: Optional[bool] = True    # 성공/이탈 여부

# 2. 분석 요청 (백엔드 -> AI)
class AnalysisRequest(BaseModel):
    user_id: int
    game_id: str                  # "Game_Shoulder_FireWood" 등
    actions: List[ActionData]     # 수행한 동작 리스트

# 3. 분석 결과 (AI -> 백엔드)
class AnalysisResponse(BaseModel):
    score: int                    # 최종 점수
    rom_achievement: float        # ROM 달성률 (%)
    stability_score: int          # 안정성 점수
    difficulty_recommend: str      # 차기 난이도 (UP, MAINTAIN, DOWN)
    feedback_message: str         # 사용자 피드백 메시지