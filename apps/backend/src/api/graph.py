"""GET /api/v1/graph/{analysis_id}: 分析結果に紐づくサブグラフを返す。"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.domain.schemas import GraphPayload
from src.infra.container import get_store

router = APIRouter(prefix="/api/v1", tags=["graph"])


@router.get("/graph/{analysis_id}", response_model=GraphPayload)
async def get_graph_payload(analysis_id: str) -> GraphPayload:
    res = get_store().get_analysis(analysis_id)
    if res is None:
        raise HTTPException(status_code=404, detail="analysis not found")
    return res.graph
