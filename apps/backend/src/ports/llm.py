"""LLM Port。OpenAI／AzureOpenAI／Gemini など Adapter を差し替え可能にする。"""
from __future__ import annotations

from typing import Protocol

from src.domain.schemas import AxisAnalysis, ContextBundle, Stage1Result, Stage2Result, Tier2Analysis


class LLMPort(Protocol):
    def stage1(self, theme: str, context: ContextBundle) -> Stage1Result: ...

    def stage2_tier1(
        self,
        theme: str,
        stage1: Stage1Result,
        full_context: str,
        go_no_verdict: str,
    ) -> Stage2Result: ...

    def stage2_tier2(
        self,
        theme: str,
        stage1: Stage1Result,
        full_context: str,
    ) -> Tier2Analysis: ...

    # Stage1 を 1 軸ずつ呼ぶ用（SSE で進捗を細かく流すため）
    def stage1_single_axis(
        self, theme: str, axis: str, axis_context: str
    ) -> AxisAnalysis: ...
