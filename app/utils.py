# app/utils.py
import os
import csv
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
        # 1. 저장 디렉토리 생성
        if not os.path.exists(cls.LOG_DIR):
            os.makedirs(cls.LOG_DIR)

        # 2. 파일명 생성 (게임ID_날짜시간.csv)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(cls.LOG_DIR, f"{game_id}_{timestamp}.csv")

        # 3. 데이터 쓰기
        try:
            with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                # 헤더 작성
                writer.writerow(
                    ["action_type", "action_dir", "duration", "angle_max", "speed_max", "hold_time", "result"])

                # 데이터 행 작성
                for action in actions:
                    writer.writerow([
                        action.action_type, action.action_dir, action.duration,
                        action.angle_max, action.speed_max, action.hold_time, action.result
                    ])
            print(f"Log saved: {file_path}")
        except Exception as e:
            print(f"Failed to save log: {e}")