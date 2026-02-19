# app/logic/shoulder.py
from app.schemas import ActionData
from app.utils import SensorFilter
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
            return {"score": 0, "feedback": "측정 데이터가 없습니다."}

        # [필터링] 이상치 제거 및 EMA 보정 적용
        cleaned_actions = SensorFilter.filter_outliers(actions)
        cleaned_actions = SensorFilter.apply_ema_smoothing(cleaned_actions)

        valid_actions_data = []
        total_rom_achievement = 0.0
        good_count, fast_count, slow_count, unsafe_count = 0, 0, 0, 0

        for action in cleaned_actions:
            # 방향 및 최소각도 필터링
            if action.action_dir != "Forward" or action.angle_max < FIREWOOD_MIN_ANGLE_THRESHOLD:
                continue

            valid_actions_data.append(action)

            # 타이밍 및 안전 검사
            if action.duration < FIREWOOD_DURATION_FAST:
                fast_count += 1
            elif action.duration <= FIREWOOD_DURATION_GOOD_MAX:
                good_count += 1
            else:
                slow_count += 1

            if action.speed_max > FIREWOOD_SPEED_LIMIT: unsafe_count += 1

            # ROM 달성도
            total_rom_achievement += min(action.angle_max / FIREWOOD_ROM_GOAL, 1.0)

        if not valid_actions_data:
            return {"score": 0, "feedback": "유효한 동작이 감지되지 않았습니다."}

        total_valid = len(valid_actions_data)
        avg_rom = (total_rom_achievement / total_valid) * 100
        timing_accuracy = (good_count / total_valid) * 100
        safety_score = max(100 - (unsafe_count / total_valid * 100), 0)

        final_score = int((avg_rom * 0.6) + (timing_accuracy * 0.3) + (safety_score * 0.1))

        # 피드백 생성 로직
        if unsafe_count > 0:
            feedback = "주의: 부상 방지를 위해 조금 더 천천히 휘둘러주세요."
        elif avg_rom < 70:
            feedback = "가동 범위를 조금 더 넓혀서 크게 움직여 보세요."
        else:
            feedback = "완벽합니다! 이상적인 속도와 각도로 운동 중입니다."

        # Spring 서버를 거쳐 리액트로 전달될 최종 리포트 구조
        return {
            "score": final_score,
            "safety_status": "WARNING" if unsafe_count > 0 else "SAFE",
            "feedback_message": feedback,
            "chart_data": {
                "가동범위(ROM)": int(avg_rom),
                "동작정확도": int(timing_accuracy),
                "안전성": int(safety_score)
            },
            "distribution_data": {
                "적정속도(Good)": good_count,
                "너무빠름(Fast)": fast_count,
                "너무느림(Slow)": slow_count
            },
            "difficulty_recommend": "UP" if final_score > 90 else "MAINTAIN",
            "stats": {
                "total_valid": total_valid,
                "unsafe_actions": unsafe_count,
                "filtered_out": len(actions) - len(cleaned_actions)
            }
        }