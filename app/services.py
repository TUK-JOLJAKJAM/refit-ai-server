from app.schemas import ActionData, AnalysisResponse
from typing import List


class AnalysisService:
    @staticmethod
    def analyze_movement(game_id: str, actions: List[ActionData]) -> dict:
        # 데모 발표를 위한 임시 데이터 분석 로직 (Pass-through)
        # 나중에 여기에 각도 계산, 안정성 평가 로직이 들어감.

        return {
            "score": 85,
            "rom_achievement": 92.5,
            "stability_score": 80,
            "difficulty_recommend": "MAINTAIN",
            "feedback_message": f"{game_id} 수행 결과: 자세가 안정적입니다. 현재 강도를 유지하세요."
        }