# app/services.py (수정 버전)
from typing import List
from app.schemas import ActionData, AnalysisResponse
from app.logic.shoulder import ShoulderLogic
from app.utils import DataLogger  # 로거 추가


class AnalysisService:
    @staticmethod
    def analyze_movement(game_id: str, actions: List[ActionData]) -> AnalysisResponse:

        # [추가] 테스트를 위해 들어온 데이터를 무조건 파일로 저장합니다.
        DataLogger.save_to_csv(game_id, actions)

        # 1. 어깨 관련 게임 (장작패기)
        if game_id == "Game_Shoulder_FireWood":
            result = ShoulderLogic.analyze_firewood(actions)

        # 2. 하체 관련 게임 (몬스터타워)
        elif game_id == "Game_LowerBody_MonsterTower":
            # 아직 로직 미구현 상태이므로 기본 결과 반환 (추후 구현 예정)
            result = {
                "score": 0, "rom_achievement": 0.0, "stability_score": 0,
                "difficulty_recommend": "MAINTAIN", "feedback_message": "하체 분석 로직 준비 중입니다."
            }

        # 3. 손목 관련 게임 (별자리 그리기, 훈련 정리)
        elif game_id in ["Game_Wrist_Constellation", "Game_Wrist_Arrangement"]:
            result = {
                "score": 0, "rom_achievement": 0.0, "stability_score": 0,
                "difficulty_recommend": "MAINTAIN", "feedback_message": "손목 분석 로직 준비 중입니다."
            }

        # 4. 허리 관련 게임 (마을 지키기)
        elif game_id == "Game_Waist_Intercept":
            result = {
                "score": 0, "rom_achievement": 0.0, "stability_score": 0,
                "difficulty_recommend": "MAINTAIN", "feedback_message": "허리 분석 로직 준비 중입니다."
            }

        # 정의되지 않은 게임 ID 처리
        else:
            result = {
                "score": 0, "rom_achievement": 0.0, "stability_score": 0,
                "difficulty_recommend": "MAINTAIN", "feedback_message": "알 수 없는 게임 ID입니다."
            }

        # 딕셔너리 결과를 AnalysisResponse 객체로 변환하여 반환
        return AnalysisResponse(**result)