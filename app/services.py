# app/services.py
from app.schemas import AnalysisRequest, AnalysisResponse
from app.logic.shoulder import ShoulderLogic

class AnalysisService:
    @staticmethod
    def analyze_movement(request: AnalysisRequest) -> AnalysisResponse:
        """
        요청받은 game_id에 따라 적절한 분석 로직을 매칭하고 결과를 반환합니다.
        """
        game_id = request.game_id
        actions = request.actions

        # 1. 어깨 관련 게임 (장작패기)
        if game_id == "Game_Shoulder_FireWood":
            # ShoulderLogic은 이미 최신 스키마 규격의 dict를 반환합니다.
            result = ShoulderLogic.analyze_firewood(actions)

        # 2. 하체, 손목, 허리 등 미구현 게임들을 위한 기본 응답 구조
        # 리액트 담당자가 차트에서 에러가 나지 않도록 빈 구조를 채워줍니다.
        else:
            message = "분석 로직 준비 중입니다."
            if game_id == "Game_LowerBody_MonsterTower":
                message = "하체 분석 로직 준비 중입니다."
            elif "Wrist" in game_id:
                message = "손목 분석 로직 준비 중입니다."
            elif "Waist" in game_id:
                message = "허리 분석 로직 준비 중입니다."

            result = {
                "score": 0,
                "safety_status": "SAFE",
                "feedback_message": message,
                "chart_data": {"가동범위(ROM)": 0, "동작정확도": 0, "안전성": 0},
                "distribution_data": {"적정속도(Good)": 0, "너무빠름(Fast)": 0, "너무느림(Slow)": 0},
                "difficulty_recommend": "MAINTAIN",
                "stats": {"total_valid": 0}
            }

        # 딕셔너리 결과를 AnalysisResponse 객체로 변환하여 반환
        return AnalysisResponse(**result)