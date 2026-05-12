"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import dynamic from "next/dynamic";

import type { GraphPayload } from "@/lib/types";

// SSR 不可。クライアントで動的ロード。
const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), {
  ssr: false,
  loading: () => (
    <div className="h-full w-full flex items-center justify-center text-sub font-mono text-xs">
      loading graph...
    </div>
  ),
});

const TYPE_COLOR: Record<string, string> = {
  technology: "#00E5FF",
  past_project: "#FFB800",
  person: "#FF2D95",
  market: "#00FFA3",
  unknown: "#8B97B8",
};

type GNode = {
  id: string;
  label: string;
  type: string;
  isProposalRelated: boolean;
  isSeed: boolean;
};

const MAX_NODES = 60;

export function GraphView({ graph }: { graph: GraphPayload }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ w: 800, h: 520 });
  const [selected, setSelected] = useState<GNode | null>(null);
  const [tick, setTick] = useState(0);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // リサイズ：ResizeObserver で確実に追従
  useEffect(() => {
    if (!containerRef.current) return;
    const el = containerRef.current;
    const update = () => {
      const rect = el.getBoundingClientRect();
      setSize({
        w: Math.max(320, Math.floor(rect.width)),
        h: Math.max(420, Math.floor(rect.height)),
      });
    };
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, [mounted]);

  // パルス用フレーム
  useEffect(() => {
    let raf = 0;
    const loop = () => {
      setTick((t) => t + 1);
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, []);

  const data = useMemo(() => {
    const proposalSet = new Set(graph.proposal_related_ids);
    const seedSet = new Set(graph.seed_ids);

    // 提案関連 > seed > その他 の優先順位でキャップ。ノード爆発抑制。
    const ranked = [...graph.nodes].sort((a, b) => {
      const score = (id: string) =>
        (proposalSet.has(id) ? 2 : 0) + (seedSet.has(id) ? 1 : 0);
      return score(b.id) - score(a.id);
    });
    const kept = ranked.slice(0, MAX_NODES);
    const keptSet = new Set(kept.map((n) => n.id));

    const nodes: GNode[] = kept.map((n) => ({
      id: n.id,
      label: n.label,
      type: n.type,
      isProposalRelated: proposalSet.has(n.id),
      isSeed: seedSet.has(n.id),
    }));
    const links = graph.edges
      .filter((e) => keptSet.has(e.source) && keptSet.has(e.target))
      .map((e) => ({
        source: e.source,
        target: e.target,
        relation: e.relation,
      }));
    return { nodes, links };
  }, [graph]);

  const trimmed = graph.nodes.length - data.nodes.length;

  return (
    <div className="rounded-xl border border-border bg-panel/80 backdrop-blur p-5">
      <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
        <span className="font-mono text-[11px] text-cyan tracking-[0.3em]">
          /// RELATION GRAPH
        </span>
        <div className="flex flex-wrap gap-3 font-mono text-[10px] text-sub">
          {Object.entries(TYPE_COLOR)
            .filter(([k]) => k !== "unknown")
            .map(([k, c]) => (
              <span key={k} className="flex items-center gap-1">
                <span
                  className="inline-block h-2 w-2 rounded-full"
                  style={{ background: c }}
                />
                {k}
              </span>
            ))}
          <span className="flex items-center gap-1">
            <span className="inline-block h-2 w-2 rounded-full bg-magenta animate-pulse" />
            提案関連
          </span>
        </div>
      </div>

      <div className="mb-2 font-mono text-[10px] text-sub">
        nodes: {data.nodes.length}
        {trimmed > 0 && ` (+${trimmed} truncated)`} / edges: {data.links.length}
        {data.nodes.length === 0 && " — no related nodes"}
      </div>

      <div
        ref={containerRef}
        className="relative rounded-lg border border-border bg-bg/40 overflow-hidden"
        style={{ height: 520, width: "100%" }}
      >
        {data.nodes.length === 0 ? (
          <div className="h-full w-full flex items-center justify-center text-sub font-mono text-xs">
            ヒットしたノードがありません
          </div>
        ) : mounted ? (
          <ForceGraph2D
            width={size.w}
            height={size.h}
            graphData={data}
            backgroundColor="rgba(10,14,26,0)"
            cooldownTicks={200}
            nodeRelSize={5}
            linkColor={() => "rgba(139,151,184,0.4)"}
            linkWidth={1.2}
            onNodeClick={(node) => setSelected(node as GNode)}
            nodeCanvasObject={(node, ctx, scale) => {
              const n = node as GNode & { x: number; y: number };
              const baseColor = TYPE_COLOR[n.type] ?? TYPE_COLOR.unknown;
              const radius = n.isProposalRelated ? 8 : n.isSeed ? 6 : 4.5;

              if (n.isProposalRelated) {
                const pulse = 1 + 0.5 * Math.sin(tick / 8);
                ctx.beginPath();
                ctx.arc(n.x, n.y, radius * pulse, 0, 2 * Math.PI);
                ctx.fillStyle = `${baseColor}33`;
                ctx.fill();
              }

              ctx.beginPath();
              ctx.arc(n.x, n.y, radius, 0, 2 * Math.PI);
              ctx.fillStyle = baseColor;
              ctx.shadowColor = baseColor;
              ctx.shadowBlur = n.isProposalRelated ? 18 : 8;
              ctx.fill();
              ctx.shadowBlur = 0;

              const fontSize = Math.max(11, 13 / Math.max(scale, 1));
              ctx.font = `${fontSize}px JetBrains Mono, monospace`;
              ctx.fillStyle = "#E5ECFF";
              ctx.textAlign = "center";
              ctx.textBaseline = "top";
              ctx.fillText(n.label, n.x, n.y + radius + 2);
            }}
            nodePointerAreaPaint={(node, color, ctx) => {
              const n = node as GNode & { x: number; y: number };
              ctx.fillStyle = color;
              ctx.beginPath();
              ctx.arc(n.x, n.y, 10, 0, 2 * Math.PI);
              ctx.fill();
            }}
          />
        ) : null}
        {selected && (
          <aside className="absolute top-2 right-2 w-64 rounded-lg border border-cyan/50 bg-bg/90 p-3 shadow-glow-cyan">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[10px] text-cyan tracking-widest">NODE</span>
              <button
                onClick={() => setSelected(null)}
                className="text-sub hover:text-text text-xs"
              >
                ×
              </button>
            </div>
            <div className="mt-2 text-sm font-semibold">{selected.label}</div>
            <div className="mt-1 font-mono text-[10px] text-sub break-all">
              id: {selected.id} / type: {selected.type}
            </div>
            {selected.isProposalRelated && (
              <div className="mt-2 font-mono text-[10px] text-magenta">
                ★ PROPOSAL RELATED
              </div>
            )}
          </aside>
        )}
      </div>
    </div>
  );
}
