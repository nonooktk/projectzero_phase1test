"""POST /api/v1/analyses: SSE で検索パイプライン進捗を配信。
GET /api/v1/analyses/{id}: 完了済み分析結果を取得。
"""
from __future__ import annotations

import asyncio
import json
import logging
import traceback
from collections.abc import AsyncGenerator

from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

logger = logging.getLogger(__name__)

from src.application.analyze_idea import AnalyzeIdeaUseCase
from src.domain.schemas import AnalysisResult, AnalyzeRequest, StageEventPayload
from src.infra.container import (
    get_data_source,
    get_graph,
    get_llm,
    get_store,
    get_vector_search,
)

router = APIRouter(prefix="/api/v1", tags=["analyses"])


def _build_usecase() -> AnalyzeIdeaUseCase:
    return AnalyzeIdeaUseCase(
        llm=get_llm(),
        vector_search=get_vector_search(),
        graph=get_graph(),
        store=get_store(),
        data_source=get_data_source(),
    )


@router.post("/analyses")
async def create_analysis(req: AnalyzeRequest) -> EventSourceResponse:
    usecase = _build_usecase()

    async def event_gen() -> AsyncGenerator[dict, None]:
        try:
            async for payload in usecase.stream(req.theme):
                if isinstance(payload, StageEventPayload):
                    print(
                        f"[SSE OUT] stage={payload.stage} status={payload.status}",
                        flush=True,
                    )
                    yield {
                        "event": "stage",
                        "data": payload.model_dump_json(exclude_none=True),
                    }
                elif isinstance(payload, AnalysisResult):
                    data = payload.model_dump_json(exclude_none=True)
                    print(
                        f"[SSE OUT] result analysis_id={payload.analysis_id} "
                        f"bytes={len(data)}",
                        flush=True,
                    )
                    yield {"event": "result", "data": data}
        except Exception as e:  # noqa: BLE001
            tb = traceback.format_exc()
            logger.error("analysis pipeline failed:\n%s", tb)
            print(f"\n[ANALYSIS ERROR]\n{tb}\n", flush=True)
            yield {
                "event": "error",
                "data": json.dumps(
                    {"error": type(e).__name__, "message": str(e), "traceback": tb}
                ),
            }
        finally:
            print("[SSE OUT] done", flush=True)
            yield {"event": "done", "data": "{}"}

    return EventSourceResponse(event_gen())


@router.get("/analyses/{analysis_id}", response_model=AnalysisResult)
async def get_analysis(analysis_id: str) -> AnalysisResult:
    res = get_store().get_analysis(analysis_id)
    if res is None:
        raise HTTPException(status_code=404, detail="analysis not found")
    return res
