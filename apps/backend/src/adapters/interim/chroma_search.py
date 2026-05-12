"""ChromaDB（インメモリ）による VectorSearchPort 実装。

DataSource（Supabase or JSON）から起動時にドキュメントをロードして
ChromaDB に投入する。
"""
from __future__ import annotations

from threading import Lock

import chromadb
from sentence_transformers import SentenceTransformer

from src.adapters.interim.data_source import DataSource
from src.domain.schemas import SearchHit


class ChromaDBAdapter:
    def __init__(
        self,
        data_source: DataSource,
        collection_name: str = "project_zero",
        embedding_model: str = "all-MiniLM-L6-v2",
    ) -> None:
        self._data_source = data_source
        self._collection_name = collection_name
        self._embedding_model_name = embedding_model
        self._client: chromadb.ClientAPI | None = None
        self._model: SentenceTransformer | None = None
        self._collection: chromadb.Collection | None = None
        self._lock = Lock()

    def _ensure_ready(self) -> tuple[chromadb.Collection, SentenceTransformer]:
        with self._lock:
            if self._collection is not None and self._model is not None:
                return self._collection, self._model

            self._client = chromadb.Client()
            self._model = SentenceTransformer(self._embedding_model_name)
            self._collection = self._client.get_or_create_collection(
                self._collection_name, metadata={"hnsw:space": "cosine"}
            )

            data = self._data_source.load_documents()
            if data and self._collection.count() == 0:
                ids = [item["id"] for item in data]
                texts = [item["content"] for item in data]
                metas = [{"source": item["source"]} for item in data]
                embs = self._model.encode(texts).tolist()
                self._collection.add(
                    ids=ids, embeddings=embs, documents=texts, metadatas=metas
                )
            print(
                f"[ChromaDB] loaded {len(data)} docs "
                f"(collection.count={self._collection.count()})",
                flush=True,
            )
            return self._collection, self._model

    def search(self, query: str, n: int = 5) -> list[SearchHit]:
        collection, model = self._ensure_ready()
        vec = model.encode(query).tolist()
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
