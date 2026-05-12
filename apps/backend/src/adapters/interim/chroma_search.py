"""ChromaDB（インメモリ）による VectorSearchPort 実装。

DataSource（Supabase or JSON）から起動時にドキュメントをロードして
ChromaDB に投入する。Embedding は OpenAI Embeddings（text-embedding-3-small）
を使用し、torch / sentence-transformers の起動コストとメモリを排除する。

NOTE: chromadb 自体も大きいので初回呼び出し時に遅延 import する。
"""
from __future__ import annotations

from threading import Lock
from typing import Any

from src.adapters.interim.data_source import DataSource
from src.domain.schemas import SearchHit


class ChromaDBAdapter:
    def __init__(
        self,
        data_source: DataSource,
        openai_api_key: str,
        collection_name: str = "project_zero",
        embedding_model: str = "text-embedding-3-small",
    ) -> None:
        self._data_source = data_source
        self._collection_name = collection_name
        self._embedding_model_name = embedding_model
        self._openai_api_key = openai_api_key
        self._client: Any = None
        self._openai: Any = None
        self._collection: Any = None
        self._lock = Lock()

    def _embed(self, texts: list[str]) -> list[list[float]]:
        # OpenAI Embeddings はバッチ呼び出し可能。トークン数制限に注意。
        res = self._openai.embeddings.create(model=self._embedding_model_name, input=texts)
        return [d.embedding for d in res.data]

    def _ensure_ready(self) -> Any:
        with self._lock:
            if self._collection is not None:
                return self._collection

            import chromadb
            from openai import OpenAI

            self._openai = OpenAI(api_key=self._openai_api_key)
            self._client = chromadb.Client()
            self._collection = self._client.get_or_create_collection(
                self._collection_name, metadata={"hnsw:space": "cosine"}
            )

            data = self._data_source.load_documents()
            if data and self._collection.count() == 0:
                ids = [item["id"] for item in data]
                texts = [item["content"] for item in data]
                metas = [{"source": item["source"]} for item in data]
                embs = self._embed(texts)
                self._collection.add(
                    ids=ids, embeddings=embs, documents=texts, metadatas=metas
                )
            print(
                f"[ChromaDB] loaded {len(data)} docs "
                f"(collection.count={self._collection.count()})",
                flush=True,
            )
            return self._collection

    def search(self, query: str, n: int = 5) -> list[SearchHit]:
        collection = self._ensure_ready()
        vec = self._embed([query])[0]
        raw = collection.query(query_embeddings=[vec], n_results=n)

        hits: list[SearchHit] = []
        for hid, doc, dist, meta in zip(
            raw["ids"][0], raw["documents"][0], raw["distances"][0], raw["metadatas"][0]
        ):
            hits.append(
                SearchHit(
                    id=hid,
                    content=doc,
                    score=round(1 - float(dist), 4),
                    source=meta["source"],
                )
            )
        return hits
