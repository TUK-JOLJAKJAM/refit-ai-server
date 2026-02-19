# app/utils.py
import os
import csv
import numpy as np
from datetime import datetime
from app.schemas import ActionData
from typing import List

class DataLogger:
    LOG_DIR = "ml_models/data_logs"

    @classmethod
    def save_to_csv(cls, game_id: str, actions: List[ActionData]):
        """
        분석 요청 데이터를 CSV 파일로 저장하여 추후 분석 및 기준값 조정에 활용합니다.
        """
        if not os.path.exists(cls.LOG_DIR):
            os.makedirs(cls.LOG_DIR)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(cls.LOG_DIR, f"{game_id}_{timestamp}.csv")

        try:
            with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["action_type", "action_dir", "duration", "angle_max", "speed_max", "hold_time", "result"])

                for action in actions:
                    writer.writerow([
                        action.action_type, action.action_dir, action.duration,
                        action.angle_max, action.speed_max, action.hold_time, action.result
                    ])
            print(f"Log saved: {file_path}")
        except Exception as e:
            print(f"Failed to save log: {e}")


class SensorFilter:
    """
    아두이노 센서 데이터의 노이즈를 제거하고 정제하는 필터 클래스입니다.
    """
    # EMA 필터 계수: 0.3 (낮을수록 부드럽지만 반응이 느림, 높을수록 원본에 가까움)
    ALPHA = 0.3

    @classmethod
    def apply_ema_smoothing(cls, actions: List[ActionData]) -> List[ActionData]:
        """
        지수 이동 평균(EMA)을 사용하여 연속된 동작들의 각도 데이터를 부드럽게 보정합니다.
        유니티의 Lerp와 유사한 원리로 작동합니다.
        """
        if not actions:
            return []

        smoothed_actions = []
        # 첫 번째 데이터는 그대로 사용
        prev_angle = actions[0].angle_max

        for action in actions:
            # EMA 공식: (현재값 * α) + (이전 보정값 * (1 - α))
            new_angle = (action.angle_max * cls.ALPHA) + (prev_angle * (1 - cls.ALPHA))
            action.angle_max = round(new_angle, 2)
            smoothed_actions.append(action)
            prev_angle = new_angle

        return smoothed_actions

    @classmethod
    def filter_outliers(cls, actions: List[ActionData], threshold_multiplier: float = 2.0) -> List[ActionData]:
        """
        중앙값(Median) 기반의 표준편차 검사를 통해, 기구 오작동 등으로 인해
        갑자기 튀는 비정상적인 각도 값을 제거합니다.
        """
        if len(actions) < 3:  # 데이터가 너무 적으면 이상치 판단 불가
            return actions

        angles = [a.angle_max for a in actions]
        median = np.median(angles)
        std = np.std(angles)

        # 중앙값에서 표준편차의 2배 이상 벗어난 값은 하드웨어 노이즈로 간주
        filtered_actions = [
            action for action in actions
            if abs(action.angle_max - median) <= (std * threshold_multiplier)
        ]

        return filtered_actions