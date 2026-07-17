"""Compatibility wrapper around the unified session analyzer."""

from app.analyzer import analyze_session
from app.schemas import ActionData, SessionAnalysisInput


class ShoulderLogic:
    @staticmethod
    def analyze_firewood(actions: list[ActionData]) -> dict:
        session = SessionAnalysisInput(
            history_id="legacy-shoulder-session",
            game_id="Game_Shoulder_FireWood",
            primary_part="SHOULDER",
            side="BOTH",
            actions=actions,
        )
        return analyze_session(session).model_dump(mode="json")
