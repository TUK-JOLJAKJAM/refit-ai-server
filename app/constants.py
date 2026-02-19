# app/constants.py

# --- 3.1 장작패기 (Unity 엔진 및 하드웨어 안전 기준 통합) ---

# 1. 가동 범위 (AxeRotationController.cs 기반)
FIREWOOD_ROM_GOAL = 81.0          # 유니티 도끼 회전 범위 (12 ~ -69도)
FIREWOOD_MIN_ANGLE_THRESHOLD = 10.0  # 노이즈 필터링용 최소 각도

# 2. 타이밍 기준 (ScoreManager.cs 기반)
FIREWOOD_DURATION_FAST = 0.12     # 0.12초 미만은 너무 빠름 (Fast)
FIREWOOD_DURATION_GOOD_MAX = 0.24 # 0.12~0.24초 사이가 재활에 최적인 Good 타이밍

# 3. 안전 및 안정성 기준 (데이터 시트 기반)
FIREWOOD_SPEED_LIMIT = 10.0       # 최대 속도가 10을 넘으면 부상 위험 경고