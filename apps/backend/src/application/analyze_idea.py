"""AnalyzeIdeaUseCase: 検索パイプラインを 6 ステージで実行する。

各ステージで AsyncGenerator から StageEventPayload を yield することで、
API 層が SSE としてフロントに流す。最終ステージで AnalysisResult を保存・返却する。
"""
from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import AsyncGenerator
from concurrent.futures import ThreadPoolExecutor

from src.adapters.interim.chroma_search import ChromaDBAdapter
from src.adapters.interim.data_source import DataSource
from src.adapters.interim.memory_store import InMemoryAnalysisStore
from src.adapters.interim.networkx_graph import NetworkXAdapter
from src.adapters.interim.openai_llm import OpenAILLMAdapter
from src.domain.schemas import (
    AnalysisResult,
    ContextBundle,
    GraphPayload,
    SearchHit,
    Stage1Result,
    Stage2Result,
    StageEventPayload,
)


def _decide_verdict(stage1: Stage1Result) -> str:
    """mvp/analyzer.py のルールベース GO/NO 判定を踏襲。"""
    if stage1.internal.score == "×":
        return "NO（社内適合スコアが×のため投資不可）"
    if stage1.internal.score == "△":
        return "条件付きGO（社内適合スコアが△のため、障壁解決を前提に投資検討可）"
    if stage1.external.score in ("△", "×"):
        return "条件付きGO（外部環境スコアが低いため、市場変化を確認しながら進める）"
    return "GO（全軸スコアが◎○のため即時推進可）"


def _enrich_internal_context(
    context: ContextBundle, hits: list[SearchHit], internal_records: dict[str, dict]
) -> ContextBundle:
    """conditions_now / reusable_assets / lessons_learned を internal_context に追記。"""
    if not internal_records:
        return context
    all_records = internal_records

    lines: list[str] = []
    for h in hits:
        if h.source != "internal":
            continue
        rec = all_records.get(h.id)
        if not rec:
            continue
        block = [f"【{rec.get('name', h.id)}】"]
        conds = rec.get("conditions_now", {})
        if conds:
            block.append(
                "  再参入条件チェック: "
                + " / ".join(f"{k}:{v.get('status', '')}" for k, v in conds.items())
            )
        assets = rec.get("reusable_assets", [])
        if assets:
            block.append("  活用可能資産: " + ", ".join(assets))
        lessons = rec.get("lessons_learned", "")
        if lessons:
            block.append(f"  教訓: {lessons}")
        if len(block) > 1:
            lines.append("\n".join(block))

    if not lines:
        return context
    appended = (context.internal_context or "") + "\n\n【過去PJ詳細（GO/NO判断用）】\n" + "\n\n".join(
        lines
    )
    return context.model_copy(update={"internal_context": appended})


class AnalyzeIdeaUseCase:
    def __init__(
        self,
        llm: OpenAILLMAdapter,
        vector_search: ChromaDBAdapter,
        graph: NetworkXAdapter,
        store: InMemoryAnalysisStore,
        data_source: DataSource,
    ) -> None:
        self._llm = llm
        self._vs = vector_search
        self._graph = graph
        self._store = store
        self._data_source = data_source
        self._internal_records_cache: dict[str, dict] | None = None

    def _internal_records(self) -> dict[str, dict]:
        if self._internal_records_cache is None:
            self._internal_records_cache = self._data_source.load_internal_records()
        return self._internal_records_cache

    async def stream(self, theme: str) -> AsyncGenerator[StageEventPayload | AnalysisResult, None]:
        loop = asyncio.get_running_loop()
        t0 = time.perf_counter()

        def elapsed() -> int:
            return int((time.perf_counter() - t0) * 1000)

        # --- VECTORIZE ---（プロンプト分解。固定テンプレート）
        yield StageEventPayload(stage="VECTORIZE", status="running", elapsed_ms=elapsed())
        # 3 軸クエリは MVP 同様、テーマをそのまま使う（個別分解は MVP 未実装）
        await asyncio.sleep(0)
        yield StageEventPayload(
            stage="VECTORIZE",
            status="done",
            elapsed_ms=elapsed(),
            message="3 軸クエリを準備",
        )

        # --- CHROMA SEARCH ---
        yield StageEventPayload(stage="CHROMA", status="running", elapsed_ms=elapsed())
        # MVP と同じ n=5 で揃える。ノード爆発を避けるため過剰取得を控える。
        hits: list[SearchHit] = await loop.run_in_executor(None, self._vs.search, theme, 5)
        yield StageEventPayload(
            stage="CHROMA",
            status="done",
            elapsed_ms=elapsed(),
            hits=hits,
            message=f"{len(hits)} 件ヒット",
        )

        # --- GRAPH EXPAND ---
        yield StageEventPayload(stage="GRAPH", status="running", elapsed_ms=elapsed())
        neighbor_nodes = await loop.run_in_executor(
            None, self._graph.get_neighbors, [h.id for h in hits], 1
        )
        yield StageEventPayload(
            stage="GRAPH",
            status="done",
            elapsed_ms=elapsed(),
            nodes=neighbor_nodes,
            message=f"{len(neighbor_nodes)} ノード展開",
        )

        # --- CONTEXT BUILD ---
        yield StageEventPayload(stage="CONTEXT", status="running", elapsed_ms=elapsed())
        context = await loop.run_in_executor(None, self._graph.build_context, hits)
        context = _enrich_internal_context(context, hits, self._internal_records())
        yield StageEventPayload(stage="CONTEXT", status="done", elapsed_ms=elapsed())

        # --- LLM STAGE1 ---
        yield StageEventPayload(stage="LLM_STAGE1", status="running", elapsed_ms=elapsed())
        # 3 軸を並列実行しつつ、各軸完了時に message でステータス通知（将来拡張）
        stage1 = await loop.run_in_executor(None, self._llm.stage1, theme, context)
        yield StageEventPayload(
            stage="LLM_STAGE1",
            status="done",
            elapsed_ms=elapsed(),
            message=(
                f"ext={stage1.external.score} / int={stage1.internal.score} / "
                f"org={stage1.org.score}"
            ),
        )

        # --- LLM STAGE2 ---
        yield StageEventPayload(stage="LLM_STAGE2", status="running", elapsed_ms=elapsed())
        verdict = _decide_verdict(stage1)
        full_context = "\n\n".join(
            [context.external_context, context.internal_context, context.org_context]
        )

        with ThreadPoolExecutor(max_workers=2) as ex:
            f_tier1 = ex.submit(self._llm.stage2_tier1, theme, stage1, full_context, verdict)
            f_tier2 = ex.submit(self._llm.stage2_tier2, theme, stage1, full_context)
            stage2 = await loop.run_in_executor(None, f_tier1.result)
            tier2 = await loop.run_in_executor(None, f_tier2.result)
        stage2 = stage2.model_copy(update={"tier2": tier2})
        yield StageEventPayload(stage="LLM_STAGE2", status="done", elapsed_ms=elapsed())

        # --- Graph payload（hits を seed に depth=1 で subgraph 抽出） ---
        # MVP に合わせ、グラフはヒット 5 件を seed とした depth=1 範囲に限定する。
        proposal_related = self._collect_proposal_related_ids(stage2, hits, neighbor_nodes)
        seed_ids = list({h.id for h in hits})
        sub_nodes, sub_edges = self._graph.subgraph(seed_ids, depth=1)

        result = AnalysisResult(
            analysis_id=str(uuid.uuid4()),
            theme=theme,
            stage1=stage1,
            stage2=stage2,
            graph=GraphPayload(
                nodes=sub_nodes,
                edges=sub_edges,
                seed_ids=seed_ids,
                proposal_related_ids=proposal_related,
            ),
            elapsed_ms=elapsed(),
        )
        self._store.save_analysis(result)
        yield result

    @staticmethod
    def _collect_proposal_related_ids(
        stage2: Stage2Result, hits: list[SearchHit], neighbors: list
    ) -> list[str]:
        # 簡易: 提案 next_actions に登場する person 名で hits/neighbors を突合し、
        # マッチしたノード id を proposal_related に分類。
        names: set[str] = set()
        for p in stage2.proposals:
            for na in p.next_actions:
                if na.person:
                    names.add(na.person)
        related: set[str] = set()
        # hits の content と neighbor の label に person 名が含まれていれば関連扱い
        for h in hits:
            if any(n in h.content for n in names):
                related.add(h.id)
        for n in neighbors:
            if any(name in n.label for name in names):
                related.add(n.id)
        return sorted(related)
