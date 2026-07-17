from __future__ import annotations

from typing import Any

from app.analyzer import analyze_session
from app.normalizers import normalize_request
from app.schemas import AnalysisResponse, SessionAnalysisInput
from app.utils import DataLogger


class AnalysisService:
    @staticmethod
    def normalize(payload: dict[str, Any]) -> SessionAnalysisInput:
        return normalize_request(payload)

    @staticmethod
    def analyze(payload: dict[str, Any]) -> AnalysisResponse:
        session = AnalysisService.normalize(payload)
        result = analyze_session(session)
        DataLogger.save(session, result)
        return result

    @staticmethod
    def analyze_movement(payload: Any) -> AnalysisResponse:
        """Compatibility wrapper for the original service name."""
        if hasattr(payload, "model_dump"):
            payload = payload.model_dump()
        return AnalysisService.analyze(dict(payload))
