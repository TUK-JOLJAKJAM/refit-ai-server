# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import AnalysisRequest, AnalysisResponse
from app.services import AnalysisService
from app.utils import DataLogger  # 데이터 로그 저장을 위해 추가
import uvicorn

app = FastAPI(
    title="ReFit AI Analysis Server",
    description="재활 게임 센서 데이터 분석을 위한 전용 AI 서버",
    version="1.1.0"
)

# 1. CORS 설정: React와의 원활한 통신을 위해 반드시 필요합니다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    return {"status": "online", "message": "ReFit AI Server is running"}


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_rehab_data(request: AnalysisRequest):
    try:
        # 2. [데이터 자산화] 분석 전 원본 데이터를 저장합니다.
        # 이는 AI 담당자로서 추후 모델 고도화를 위한 핵심 데이터셋이 됩니다.
        DataLogger.save_to_csv(request.game_id, request.actions)

        # 3. 분석 서비스 호출 (객체 전체를 전달하여 확장성 확보)
        result = AnalysisService.analyze_movement(request)
        return result

    except Exception as e:
        # 에러 발생 시 상세 내용을 로깅합니다.
        print(f"Analysis Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)