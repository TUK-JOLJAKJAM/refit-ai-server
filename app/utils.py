from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import uuid4

from app.schemas import AnalysisResponse, SessionAnalysisInput


class DataLogger:
    """Optional local JSONL logging for dataset development.

    Disabled by default because rehabilitation sessions may contain sensitive data.
    Enable only in an approved development environment with REFIT_LOG_RAW_DATA=true.
    """

    @classmethod
    def save(cls, session: SessionAnalysisInput, result: AnalysisResponse) -> None:
        if os.getenv("REFIT_LOG_RAW_DATA", "false").lower() != "true":
            return
        log_dir = Path(os.getenv("REFIT_LOG_DIR", "data_logs"))
        log_dir.mkdir(parents=True, exist_ok=True)
        record = {
            "session": session.model_dump(mode="json"),
            "analysis": result.model_dump(mode="json"),
        }
        path = log_dir / f"{session.history_id}_{uuid4().hex[:8]}.json"
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
