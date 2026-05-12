"""分析結果のインメモリ KnowledgeStore。

F1〜F4 ローカル動作確認用。F5 デプロイ承認後に Supabase Postgres 実装へ差し替える。
"""
from __future__ import annotations

from threading import Lock

from src.domain.schemas import AnalysisResult


class InMemoryAnalysisStore:
    def __init__(self) -> None:
        self._data: dict[str, AnalysisResult] = {}
        self._lock = Lock()

    def save_analysis(self, result: AnalysisResult) -> None:
        with self._lock:
            self._data[result.analysis_id] = result

    def get_analysis(self, analysis_id: str) -> AnalysisResult | None:
        with self._lock:
            return self._data.get(analysis_id)
