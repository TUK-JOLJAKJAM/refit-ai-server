🏋️‍♂️ ReFit AI Analysis Server
ReFit 프로젝트의 핵심 엔진으로, 게임 기반 재활 훈련 중 발생하는 센서 데이터를 실시간으로 분석하여 의학적 지능형 피드백을 제공하는 AI 서버입니다.

🌟 프로젝트 개요
본 서버는 사용자가 재활 게임을 수행하는 동안 전달되는 고해상도 센서 데이터를 분석합니다. 단순히 게임의 성공 여부를 넘어서, 유니티 엔진의 물리 수치와 동기화된 정밀 분석을 통해 해부학적 관절 가동 범위(ROM)를 산출하고 움직임의 질(Quality)을 평가합니다.

🛠 주요 기능
1. 정밀 데이터 전처리 (Sensor Data Refinement)

이상치 제거 (Outlier Filtering): 중앙값(Median) 기반 필터를 통해 하드웨어 오작동으로 인한 비정상적인 스파이크 노이즈를 차단합니다.

수치 평활화 (Smoothing): 지수 이동 평균(EMA) 알고리즘을 적용하여 센서의 미세한 떨림을 보정하고 부드러운 움직임 데이터를 확보합니다.

2. 의학적 가동 범위(ROM) 및 품질 분석

물리 엔진 동기화: 유니티 엔진의 실제 오브젝트 회전 범위(예: 장작패기 81°)를 기준으로 정밀한 ROM 성취도를 계산합니다.

타이밍 기반 숙련도 평가: 단순 속도가 아닌, 타격 지점 통과 시간(0.12s~0.24s)을 분석하여 재활 목적에 부합하는 안정적인 동작 여부를 판정합니다.

3. 안전 우선 지능형 피드백 (Safety-First Logic)

위험 동작 감지: 데이터 시트 기반의 안전 속도 임계값(Speed Limit)을 초과할 경우 즉각적인 WARNING 상태와 함께 감속 피드백을 생성합니다.

시각화 최적화 리포트: 백엔드(Spring)와 프론트엔드(React)에서 추가 가공 없이 즉시 차트를 그릴 수 있도록 정제된 JSON 구조(chart_data, distribution_data)를 제공합니다.

🎮 분석 엔진 현황
현재 각 부위별 게임 로직은 유니티 엔진의 스크립트 레벨 분석을 통해 고도화되고 있습니다.

장작패기 (어깨) - [구현 완료]: 내려치는 동작(Forward)의 각도 범위(81°) 및 타격 타이밍 분석.

몬스터타워 (하체): 스쿼트 깊이(각도) 및 버티기 시간 기반의 근지구력 평가 로직 (유니티 동기화 예정).

기타 게임 (손목/허리): 각 부위별 센서 매핑 수식 및 전문가 시스템 규칙 적용 예정.

🏗 기술 스택
Language: Python 3.10+

Framework: FastAPI (Asynchronous High-performance Framework)

Data Processing: NumPy (Digital Signal Processing)

Validation: Pydantic v2 (Strict Data Modeling)

Architecture: Modular Expert System with Data Filtering Pipeline

👥 담당 역할
AI & Data Analysis Lead:

아두이노 센서 데이터 정제 파이프라인(EMA, Outlier Filter) 구축.

유니티 C# 스크립트 역공학을 통한 분석 임계값(Threshold) 동기화.

REST API 기반의 시각화 친화적 리포트 아키텍처 설계.

© 2026 TUK-JOLJAKJAM. All rights reserved.