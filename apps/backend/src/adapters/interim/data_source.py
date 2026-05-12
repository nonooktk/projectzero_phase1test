"""RAG 元データの取得元を抽象化。

- `JsonDataSource`: `mvp_streamlit/data/*.json` をローカル読み込み
- `SupabaseDataSource`: Supabase の `rag_*` ／ `graph_*` テーブルから取得
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol


class DataSource(Protocol):
    def load_documents(self) -> list[dict]:
        """ChromaDB に投入するドキュメント一覧。
        各要素は {id, content, source(external|internal|persons)}。
        """
        ...

    def load_graph_nodes(self) -> list[dict]:
        """{id, label, type} の一覧。"""
        ...

    def load_graph_edges(self) -> list[dict]:
        """{source, target, relation} の一覧。"""
        ...

    def load_internal_records(self) -> dict[str, dict]:
        """internal.json 相当の詳細レコードを id → record の dict で返す。
        conditions_now / reusable_assets / lessons_learned 等を含む。
        """
        ...


# ============================================================
# JSON ローカル実装
# ============================================================
class JsonDataSource:
    """`mvp_streamlit/data` と `data/graph` から読み込む。ローカル開発のフォールバック。"""

    def __init__(self, data_dir: str | Path, graph_dir: str | Path) -> None:
        self._data_dir = Path(data_dir)
        self._graph_dir = Path(graph_dir)

    def load_documents(self) -> list[dict]:
        out: list[dict] = []
        for filename, source in (
            ("external.json", "external"),
            ("internal.json", "internal"),
            ("persons.json", "persons"),
        ):
            path = self._data_dir / filename
            if not path.exists():
                continue
            for item in json.loads(path.read_text(encoding="utf-8")):
                out.append(
                    {
                        "id": item["id"],
                        "content": item["content"],
                        "source": source,
                    }
                )
        return out

    def load_graph_nodes(self) -> list[dict]:
        path = self._graph_dir / "nodes.json"
        if not path.exists():
            return []
        return json.loads(path.read_text(encoding="utf-8"))

    def load_graph_edges(self) -> list[dict]:
        path = self._graph_dir / "edges.json"
        if not path.exists():
            return []
        return json.loads(path.read_text(encoding="utf-8"))

    def load_internal_records(self) -> dict[str, dict]:
        path = self._data_dir / "internal.json"
        if not path.exists():
            return {}
        return {r["id"]: r for r in json.loads(path.read_text(encoding="utf-8"))}


# ============================================================
# Supabase 実装
# ============================================================
class SupabaseDataSource:
    """Supabase の RAG／グラフテーブルから取得する。

    対象テーブル:
      rag_external (id, content)
      rag_internal (id, content)
      rag_persons  (id, content)
      graph_nodes  (id, label, type)
      graph_edges  (source_id, target_id, relation)
    """

    def __init__(self, url: str, service_role_key: str) -> None:
        # supabase-py は import コストが大きいので遅延 import
        from supabase import create_client

        self._client = create_client(url, service_role_key)

    def _fetch(self, table: str, columns: str) -> list[dict]:
        res = self._client.table(table).select(columns).execute()
        return res.data or []

    def load_documents(self) -> list[dict]:
        out: list[dict] = []
        for table, source in (
            ("rag_external", "external"),
            ("rag_internal", "internal"),
            ("rag_persons", "persons"),
        ):
            for row in self._fetch(table, "id,content"):
                out.append(
                    {
                        "id": row["id"],
                        "content": row.get("content", ""),
                        "source": source,
                    }
                )
        return out

    def load_graph_nodes(self) -> list[dict]:
        return [
            {"id": r["id"], "label": r.get("label", r["id"]), "type": r.get("type", "unknown")}
            for r in self._fetch("graph_nodes", "id,label,type")
        ]

    def load_graph_edges(self) -> list[dict]:
        # Supabase 側のカラム名は source_id/target_id。内部表現に揃える。
        return [
            {
                "source": r["source_id"],
                "target": r["target_id"],
                "relation": r.get("relation", ""),
            }
            for r in self._fetch("graph_edges", "source_id,target_id,relation")
        ]

    def load_internal_records(self) -> dict[str, dict]:
        """rag_internal の `data` JSONB に internal.json 相当を保持している前提。
        scripts/seed_supabase.py で `data: r` として元 JSON 全体を格納している。
        """
        out: dict[str, dict] = {}
        for row in self._fetch("rag_internal", "id,data"):
            payload = row.get("data") or {}
            if isinstance(payload, dict) and payload:
                out[row["id"]] = payload
        # data カラムから取れない場合は project_conditions テーブルからも組み立て
        if not out:
            for row in self._fetch("rag_internal", "id"):
                out.setdefault(row["id"], {"id": row["id"]})
            for cond in self._fetch(
                "project_conditions", "project_id,condition_name,status_now,detail,year_assessed"
            ):
                rec = out.setdefault(cond["project_id"], {"id": cond["project_id"]})
                rec.setdefault("conditions_now", {})[cond["condition_name"]] = {
                    "status": cond["status_now"],
                    "detail": cond.get("detail", ""),
                    "year_assessed": cond.get("year_assessed"),
                }
        return out
