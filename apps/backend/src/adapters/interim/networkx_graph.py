"""NetworkX による GraphRAGPort 実装。

DataSource（Supabase or JSON）から nodes／edges を取得してメモリ上に構築。
"""
from __future__ import annotations

import networkx as nx

from src.adapters.interim.data_source import DataSource
from src.domain.schemas import ContextBundle, GraphEdge, GraphNode, SearchHit


class NetworkXAdapter:
    def __init__(self, data_source: DataSource) -> None:
        self._data_source = data_source
        self._g: nx.Graph | None = None

    def _ensure_graph(self) -> nx.Graph:
        if self._g is not None:
            return self._g

        g = nx.Graph()
        for node in self._data_source.load_graph_nodes():
            g.add_node(node["id"], **node)
        for edge in self._data_source.load_graph_edges():
            g.add_edge(edge["source"], edge["target"], relation=edge["relation"])
        print(
            f"[NetworkX] loaded {g.number_of_nodes()} nodes / "
            f"{g.number_of_edges()} edges",
            flush=True,
        )
        self._g = g
        return g

    def get_neighbors(self, node_ids: list[str], depth: int = 1) -> list[GraphNode]:
        g = self._ensure_graph()
        seen: set[str] = set()
        out: list[GraphNode] = []
        frontier = set(node_ids)
        for _ in range(depth):
            next_frontier: set[str] = set()
            for nid in frontier:
                if nid not in g:
                    continue
                for nb in g.neighbors(nid):
                    if nb in seen or nb in node_ids:
                        continue
                    seen.add(nb)
                    attrs = g.nodes[nb]
                    out.append(
                        GraphNode(
                            id=nb,
                            label=attrs.get("label", nb),
                            type=attrs.get("type", "unknown"),
                        )
                    )
                    next_frontier.add(nb)
            frontier = next_frontier
        return out

    def build_context(self, hits: list[SearchHit]) -> ContextBundle:
        g = self._ensure_graph()
        external = [h for h in hits if h.source == "external"]
        internal = [h for h in hits if h.source == "internal"]
        persons = [h for h in hits if h.source == "persons"]

        # 隣接ノードから漏れたキーマンを補完（mvp の build_context 同等）
        all_ids = [h.id for h in hits]
        person_ids = {h.id for h in persons}
        extra_person_lines: list[str] = []
        for src in all_ids:
            if src not in g:
                continue
            for nb in g.neighbors(src):
                attrs = g.nodes[nb]
                if attrs.get("type") != "person":
                    continue
                if nb in person_ids:
                    continue
                relation = g[src][nb].get("relation", "")
                label = attrs.get("label", nb)
                extra_person_lines.append(f"{label}（{relation}）")

        ext_text = "【外部情報】\n" + "\n".join(h.content for h in external) if external else ""
        int_text = "【社内情報】\n" + "\n".join(h.content for h in internal) if internal else ""
        org_lines = [h.content for h in persons] + extra_person_lines
        org_text = "【キーマン】\n" + "\n".join(org_lines) if org_lines else ""

        return ContextBundle(
            external_context=ext_text,
            internal_context=int_text,
            org_context=org_text,
        )

    def subgraph(
        self, seed_ids: list[str], depth: int = 1
    ) -> tuple[list[GraphNode], list[GraphEdge]]:
        g = self._ensure_graph()
        keep: set[str] = set()
        for sid in seed_ids:
            if sid not in g:
                continue
            keep.add(sid)
            for nb in nx.single_source_shortest_path_length(g, sid, cutoff=depth):
                keep.add(nb)

        nodes = [
            GraphNode(
                id=nid,
                label=g.nodes[nid].get("label", nid),
                type=g.nodes[nid].get("type", "unknown"),
            )
            for nid in keep
        ]
        edges: list[GraphEdge] = []
        seen_edges: set[tuple[str, str]] = set()
        for u, v, data in g.edges(data=True):
            if u in keep and v in keep:
                key = tuple(sorted((u, v)))
                if key in seen_edges:
                    continue
                seen_edges.add(key)
                edges.append(GraphEdge(source=u, target=v, relation=data.get("relation", "")))
        return nodes, edges
