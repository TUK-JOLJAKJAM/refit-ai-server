from fastapi import FastAPI, HTTPException
from app.schemas import AnalysisRequest, AnalysisResponse
from app.services import AnalysisService  # 곧 채울 예정...
import uvicorn

# 1. FastAPI 앱 객체 생성
app = FastAPI(
    title="ReFit AI Analysis Server",
    description="재활 게임 센서 데이터 분석을 위한 전용 AI 서버",
    version="1.0.0"
)

# 2. 헬스 체크 엔드포인트 (서버가 살아있는지 확인용)
@app.get("/")
def health_check():
    return {"status": "online", "message": "ReFit AI Server is running"}

# 3. 핵심 분석 엔드포인트
@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_rehab_data(request: AnalysisRequest):
    """
    백엔드로부터 게임 데이터를 받아 AI 분석 결과를 반환합니다.
    - 대상 게임: 장작패기, 몬스터타워, 별자리그리기 등 6종
    """
    try:
        # 데이터 시트 기반 분석 서비스 호출
        # AI 로직이 여기서 실행됩니다.
        result = AnalysisService.analyze_movement(request.game_id, request.actions)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 4. 서버 직접 실행 (로컬 테스트용)
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)