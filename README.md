# ReFit AI Analysis Server

Unity 재활 게임 세션 또는 Spring `GameHistoryDetailResponse` JSON을 받아 수행도, ROM, 일관성, 피로 추세, 안전 신호와 다음 난이도를 분석하는 FastAPI 서버입니다.

## 현재 지원 기능

- 새 정형 세션 스키마와 현재 Unity/Spring 레거시 JSON 동시 지원
- 성공률, 정확도, 평균 동작시간, ROM 달성도, 속도, 일관성 계산
- 연속 센서 샘플이 있으면 움직임 부드러움과 속도 계산
- 세션 초반/후반 점수 하락 기반 피로 추세 계산
- 통증, 부종, 과속, 수행도 급락 위험 플래그
- 난이도 `UP`, `MAINTAIN`, `DOWN` 및 사유 코드
- React 차트에 바로 사용할 `chart_data`, `distribution_data`
- 데이터가 부족해도 실패하지 않고 품질 플래그로 표시

> 현재 임계값은 제품 개발용 초기 규칙이며 의료 진단 기준이 아닙니다. 실제 센서 데이터와 재활 전문가 검토로 보정해야 합니다.

## 로컬 실행

Python 3.10 이상이 필요합니다.

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

macOS/Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

실행 후 확인:

- API 문서: http://localhost:8000/docs
- 상태 확인: http://localhost:8000/health
- 분석 API: `POST http://localhost:8000/api/v1/analyze_session`
- 샘플 입력: `GET http://localhost:8000/api/v1/demo_session`

## 테스트

```bash
pytest -q
```

## Docker

```bash
docker build -t refit-ai-server .
docker run --rm -p 8000:8000 refit-ai-server
```

## 지원 요청 형식

### 1. 새 정형 스키마

```json
{
  "schema_version": "1.0",
  "history_id": "session-uuid",
  "game_id": "ADVENTURE_FIGHT",
  "primary_part": "SHOULDER",
  "side": "BOTH",
  "difficulty": 2,
  "actions": [
    {
      "action_id": "1",
      "action_type": "ATTACK",
      "direction": "FORWARD",
      "started_at_ms": 1784250001000,
      "ended_at_ms": 1784250002200,
      "result": true,
      "grade": "GOOD",
      "rom_deg": 76.2,
      "peak_angular_velocity_dps": 135.4
    }
  ]
}
```

### 2. Spring 게임 히스토리 상세 응답

`gameId`, `primaryPart`, `gameData`, `bodyPartSummaries` 같은 camelCase 필드를 그대로 전송할 수 있습니다. 현재 Unity의 다음 레거시 값도 자동 파싱합니다.

```json
{
  "attackGrade, GyroQuaternion, attackTime": "Good, (0.0, 0.2, 0.0, 0.98), 0.42"
}
```

이 형식에는 ROM과 속도가 없으므로 결과의 `data_quality.flags`에 `MISSING_ROM`, `MISSING_SPEED`가 표시됩니다.

## 환경 변수

`.env.example` 참고:

- `CORS_ORIGINS`: 허용할 React 주소 목록
- `REFIT_LOG_RAW_DATA`: 민감한 원본 데이터 로깅 여부, 기본값 `false`
- `REFIT_LOG_DIR`: 개발용 데이터 저장 위치
- `PORT`: 서버 포트
