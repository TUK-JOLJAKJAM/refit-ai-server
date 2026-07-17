from __future__ import annotations

import logging
import os
from typing import Any

from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from app.demo import build_demo_session
from app.schemas import AnalysisResponse
from app.services import AnalysisService


logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("refit-ai-server")

app = FastAPI(
    title="ReFit AI Analysis Server",
    description="재활 게임 세션의 수행도, 피로, 안전 신호와 난이도를 분석합니다.",
    version="2.0.0",
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,https://tuk-joljakjam.github.io",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "refit-ai-server",
        "status": "online",
        "docs": "/docs",
        "analysis_endpoint": "/api/v1/analyze_session",
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy", "version": app.version}


@app.get("/api/v1/demo_session")
def demo_session() -> dict[str, Any]:
    return build_demo_session()


def _run_analysis(payload: dict[str, Any]) -> AnalysisResponse:
    try:
        return AnalysisService.analyze(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Session analysis failed")
        raise HTTPException(status_code=500, detail="분석 처리 중 서버 오류가 발생했습니다.") from exc


@app.post("/api/v1/analyze_session", response_model=AnalysisResponse)
def analyze_session(payload: dict[str, Any] = Body(...)) -> AnalysisResponse:
    """Analyze either the canonical ReFit schema or Spring GameHistory detail JSON."""
    return _run_analysis(payload)


@app.post("/analyze", response_model=AnalysisResponse, deprecated=True)
def analyze_legacy(payload: dict[str, Any] = Body(...)) -> AnalysisResponse:
    """Backward-compatible alias for the original endpoint."""
    return _run_analysis(payload)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=True)
