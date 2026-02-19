# app/logic/shoulder.py
from app.schemas import ActionData
from app.constants import (
    FIREWOOD_ROM_GOAL,
    FIREWOOD_DURATION_FAST,
    FIREWOOD_DURATION_GOOD_MAX,
    FIREWOOD_SPEED_LIMIT,
    FIREWOOD_MIN_ANGLE_THRESHOLD
)


class ShoulderLogic:
    @staticmethod
    def analyze_firewood(actions: list[ActionData]):
        if not actions:
            return {"score": 0, "feedback": "측정된 데이터가 없습니다."}

        valid_actions_data = []
        total_rom_achievement = 0.0
        good_count = 0
        fast_count = 0
        slow_count = 0
        unsafe_count = 0

        for action in actions:
            # 1. 필터링: 내려치는 동작만 분석하며, 미세한 떨림은 무시
            if action.action_dir != "Forward" or action.angle_max < FIREWOOD_MIN_ANGLE_THRESHOLD:
                continue

            valid_actions_data.append(action)

            # 2. 타이밍 판정 (유니티 ScoreManager 로직 이식)
            if action.duration < FIREWOOD_DURATION_FAST:
                fast_count += 1
            elif action.duration <= FIREWOOD_DURATION_GOOD_MAX:
                good_count += 1
            else:
                slow_count += 1

            # 3. 안전 검사 (데이터 시트 기준)
            if action.speed_max > FIREWOOD_SPEED_LIMIT:
                unsafe_count += 1

            # 4. ROM 성취도 계산 (유니티 81도 기준)
            achievement = min(action.angle_max / FIREWOOD_ROM_GOAL, 1.0)
            total_rom_achievement += achievement

        if not valid_actions_data:
            return {"score": 0, "feedback": "유효한 재활 동작이 감지되지 않았습니다."}

        total_valid = len(valid_actions_data)

        # 5. 점수 산출 (성취도 60%, 타이밍 30%, 안전성 10%)
        avg_rom = (total_rom_achievement / total_valid) * 100
        timing_accuracy = (good_count / total_valid) * 100
        safety_score = max(100 - (unsafe_count / total_valid * 100), 0)

        final_score = int((avg_rom * 0.6) + (timing_accuracy * 0.3) + (safety_score * 0.1))

        # 6. 피드백 메시지
        if unsafe_count > 0:
            feedback = "주의: 부상 방지를 위해 조금 더 천천히 휘둘러주세요."
        elif fast_count > good_count:
            feedback = "속도를 조금 줄이면 재활 효과가 더 좋아집니다."
        elif avg_rom < 70:
            feedback = "가동 범위를 조금 더 넓혀서 크게 움직여 보세요."
        else:
            feedback = "완벽합니다! 이상적인 속도와 각도로 운동 중입니다."

        return {
            "score": final_score,
            "rom_achievement": round(avg_rom, 1),
            "stability_score": int(timing_accuracy),
            "safety_status": "WARNING" if unsafe_count > 0 else "SAFE",
            "difficulty_recommend": "UP" if final_score > 90 else "MAINTAIN",
            "feedback_message": feedback,
            "stats": {
                "total_valid_actions": total_valid,
                "good_timing": good_count,
                "unsafe_actions": unsafe_count
            }
        }