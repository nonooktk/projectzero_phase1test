"""DI コンテナ。FastAPI Depends から Adapter 群を取り出すための簡易レジストリ。

データ取得元の選択ルール:
  1. `.env` に SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY が両方セットされていれば
     SupabaseDataSource を試す。テーブルから 1 件以上取得できればそれを採用。
  2. それ以外（または Supabase アクセス失敗・空）はローカル JSON にフォールバック。
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from src.adapters.interim.chroma_search import ChromaDBAdapter
from src.adapters.interim.data_source import (
    DataSource,
    JsonDataSource,
    SupabaseDataSource,
)
from src.adapters.interim.memory_store import InMemoryAnalysisStore
from src.adapters.interim.networkx_graph import NetworkXAdapter
from src.adapters.interim.openai_llm import OpenAILLMAdapter
from src.infra.settings import get_settings


def _candidate_paths(env_var: str, docker_path: str, local_subpath: tuple[str, ...]) -> list[Path]:
    out: list[Path] = []
    env = os.environ.get(env_var, "").strip()
    if env:
        out.append(Path(env))
    out.append(Path(docker_path))
    # apps/backend/src/infra/container.py → parents[4] が repo root
    repo_root = Path(__file__).resolve().parents[4]
    out.append(repo_root.joinpath(*local_subpath))
    return out


def _resolve_data_dir() -> Path:
    for c in _candidate_paths("SEED_DATA_DIR", "/app/seed_data", ("mvp_streamlit", "data")):
        if c.exists() and c.is_dir():
            return c
    raise FileNotFoundError("seed data directory not found")


def _resolve_graph_dir() -> Path:
    for c in _candidate_paths("GRAPH_DATA_DIR", "/app/extra_data/graph", ("data", "graph")):
        if c.exists() and c.is_dir():
            return c
    raise FileNotFoundError("graph data directory not found")


def _try_supabase() -> SupabaseDataSource | None:
    """Supabase が設定されていて、かつデータが投入済みなら採用する。"""
    s = get_settings()
    if not (s.supabase_url and s.supabase_service_role_key):
        return None
    try:
        ds = SupabaseDataSource(s.supabase_url, s.supabase_service_role_key)
        # 1 件でも取れるか確認（投入忘れ検出）
        docs = ds.load_documents()
        nodes = ds.load_graph_nodes()
        if not docs:
            print("[Supabase] no documents found in rag_* tables; falling back to JSON", flush=True)
            return None
        if not nodes:
            print("[Supabase] no rows in graph_nodes; falling back to JSON", flush=True)
            return None
        print(
            f"[Supabase] using as data source (docs={len(docs)}, nodes={len(nodes)})",
            flush=True,
        )
        return ds
    except Exception as e:  # noqa: BLE001
        print(f"[Supabase] failed to connect: {type(e).__name__}: {e} — falling back to JSON", flush=True)
        return None


@lru_cache
def get_data_source() -> DataSource:
    sb = _try_supabase()
    if sb is not None:
        return sb
    data_dir = _resolve_data_dir()
    graph_dir = _resolve_graph_dir()
    print(f"[JsonDataSource] data_dir={data_dir} graph_dir={graph_dir}", flush=True)
    return JsonDataSource(data_dir=data_dir, graph_dir=graph_dir)


@lru_cache
def get_llm() -> OpenAILLMAdapter:
    s = get_settings()
    return OpenAILLMAdapter(api_key=s.openai_api_key, model=s.openai_model)


@lru_cache
def get_vector_search() -> ChromaDBAdapter:
    s = get_settings()
    return ChromaDBAdapter(
        data_source=get_data_source(),
        collection_name=s.chroma_collection_name,
        embedding_model=s.embedding_model,
    )


@lru_cache
def get_graph() -> NetworkXAdapter:
    return NetworkXAdapter(data_source=get_data_source())


@lru_cache
def get_store() -> InMemoryAnalysisStore:
    return InMemoryAnalysisStore()
