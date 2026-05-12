from __future__ import annotations

from typing import Protocol

from src.domain.schemas import AnalysisResult


class KnowledgeStorePort(Protocol):
    def save_analysis(self, result: AnalysisResult) -> None: ...

    def get_analysis(self, analysis_id: str) -> AnalysisResult | None: ...
