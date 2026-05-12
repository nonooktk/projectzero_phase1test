from __future__ import annotations

from typing import Protocol

from src.domain.schemas import SearchHit


class VectorSearchPort(Protocol):
    def search(self, query: str, n: int = 5) -> list[SearchHit]: ...
