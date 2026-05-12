"""OpenAI Chat Completions API による LLM Adapter。

mvp_streamlit/llm/analyzer.py のロジックを LLMPort 準拠で再実装。
プロンプトは src/prompts.py（mvp_streamlit/llm/prompts.py のコピー）を流用。
"""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor

from openai import OpenAI

from src.domain.schemas import (
    AxisAnalysis,
    ContextBundle,
    Stage1Result,
    Stage2Result,
    Tier2Analysis,
)
from src.prompts import (
    AXIS_NAMES,
    STAGE1_SYSTEM_PROMPT,
    STAGE1_USER_PROMPT_TEMPLATE,
    STAGE2_SYSTEM_PROMPT,
    STAGE2_TIER1_USER_PROMPT_TEMPLATE,
    STAGE2_TIER2_SYSTEM_PROMPT,
    STAGE2_TIER2_USER_PROMPT_TEMPLATE,
)

_AXIS_CONTEXT_KEYS = {
    "external": "external_context",
    "internal": "internal_context",
    "org": "org_context",
}

# LLM が返す揺らぎを Score Literal に正規化する。
# 〇 = U+3007（漢数字ゼロ）／○ = U+25CB（白丸）／◯ = U+25EF（大きな白丸）など
_SCORE_NORMALIZE = {
    "◎": "◎",
    "○": "○",
    "〇": "○",
    "◯": "○",
    "△": "△",
    "▲": "△",
    "×": "×",
    "✕": "×",
    "✖": "×",
    "ｘ": "×",
    "Ｘ": "×",
    "x": "×",
    "X": "×",
    "－": "－",
    "-": "－",
    "—": "－",
    "ー": "－",
}


def _normalize_score(s: str | None) -> str:
    if not s:
        return "－"
    s = s.strip()
    return _SCORE_NORMALIZE.get(s, "－")


def _escape(text: str) -> str:
    # str.format の {} 衝突回避（analyzer.py 同等処理）
    return text.replace("{", "{{").replace("}", "}}")


class OpenAILLMAdapter:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def _chat(self, system: str, user: str) -> dict:
        # 結果の揺らぎを抑えるため temperature=0 で確定動作させる。
        res = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        return json.loads(res.choices[0].message.content or "{}")

    def stage1_single_axis(self, theme: str, axis: str, axis_context: str) -> AxisAnalysis:
        prompt = STAGE1_USER_PROMPT_TEMPLATE.format(
            theme=theme,
            axis_name=AXIS_NAMES[axis],
            context=_escape(axis_context or "（情報なし）"),
        )
        raw = self._chat(STAGE1_SYSTEM_PROMPT, prompt)
        return AxisAnalysis(
            score=_normalize_score(raw.get("score")),
            reason=raw.get("reason", ""),
            key_points=raw.get("key_points", []),
        )

    def stage1(self, theme: str, context: ContextBundle) -> Stage1Result:
        # 3 軸を並列実行（analyzer.py と同じ ThreadPoolExecutor 戦略）
        ctx_map = {
            "external": context.external_context,
            "internal": context.internal_context,
            "org": context.org_context,
        }
        with ThreadPoolExecutor(max_workers=3) as ex:
            futures = {
                axis: ex.submit(self.stage1_single_axis, theme, axis, ctx_map[axis])
                for axis in ctx_map
            }
            results = {axis: f.result() for axis, f in futures.items()}
        return Stage1Result(**results)

    def stage2_tier1(
        self,
        theme: str,
        stage1: Stage1Result,
        full_context: str,
        go_no_verdict: str,
    ) -> Stage2Result:
        prompt = STAGE2_TIER1_USER_PROMPT_TEMPLATE.format(
            theme=theme,
            go_no_verdict=go_no_verdict,
            external_score=stage1.external.score,
            external_reason=stage1.external.reason,
            external_key_points="、".join(stage1.external.key_points),
            internal_score=stage1.internal.score,
            internal_reason=stage1.internal.reason,
            internal_key_points="、".join(stage1.internal.key_points),
            org_score=stage1.org.score,
            org_reason=stage1.org.reason,
            org_key_points="、".join(stage1.org.key_points),
            full_context=_escape(full_context),
        )
        raw = self._chat(STAGE2_SYSTEM_PROMPT, prompt)
        proposals_raw = raw.get("proposals", []) or []
        for p in proposals_raw:
            if isinstance(p, dict):
                if "timing_score" in p:
                    p["timing_score"] = _normalize_score(p.get("timing_score"))
                if "tech_fit_score" in p:
                    p["tech_fit_score"] = _normalize_score(p.get("tech_fit_score"))
        return Stage2Result(
            proposals=proposals_raw,
            approver_summary=raw.get("approver_summary", ""),
        )

    def stage2_tier2(
        self,
        theme: str,
        stage1: Stage1Result,
        full_context: str,
    ) -> Tier2Analysis:
        prompt = STAGE2_TIER2_USER_PROMPT_TEMPLATE.format(
            theme=theme,
            external_score=stage1.external.score,
            external_reason=stage1.external.reason,
            internal_score=stage1.internal.score,
            internal_reason=stage1.internal.reason,
            org_score=stage1.org.score,
            org_reason=stage1.org.reason,
            full_context=_escape(full_context),
        )
        raw = self._chat(STAGE2_TIER2_SYSTEM_PROMPT, prompt)
        return Tier2Analysis(**raw)
