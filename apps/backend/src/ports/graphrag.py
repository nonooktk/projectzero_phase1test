from __future__ import annotations

from typing import Protocol

from src.domain.schemas import ContextBundle, GraphEdge, GraphNode, SearchHit


class GraphRAGPort(Protocol):
    def get_neighbors(self, node_ids: list[str], depth: int = 1) -> list[GraphNode]: ...

    def build_context(self, hits: list[SearchHit]) -> ContextBundle: ...

    def subgraph(
        self, seed_ids: list[str], depth: int = 1
    ) -> tuple[list[GraphNode], list[GraphEdge]]: ...
