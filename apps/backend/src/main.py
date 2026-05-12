"""FastAPI エントリーポイント。F0 段階では /health のみ。F1 で API ルータを登録する。"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.analyses import router as analyses_router
from src.api.graph import router as graph_router
from src.infra.settings import get_settings

settings = get_settings()

app = FastAPI(
    title="Tech0 Search API",
    version="0.1.0",
    description="新規事業判断支援システム（暫定環境・Claude 全実装版）",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyses_router)
app.include_router(graph_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/data")
async def health_data() -> dict[str, object]:
    """データソース疎通確認。Supabase の投入状況を見たい時に使う。"""
    from src.adapters.interim.data_source import SupabaseDataSource
    from src.infra.container import get_data_source

    ds = get_data_source()
    return {
        "source_type": "supabase" if isinstance(ds, SupabaseDataSource) else "json",
        "documents": len(ds.load_documents()),
        "graph_nodes": len(ds.load_graph_nodes()),
        "graph_edges": len(ds.load_graph_edges()),
        "internal_records": len(ds.load_internal_records()),
    }
