"use client";
import { motion } from "framer-motion";
import clsx from "clsx";

import { STAGES, type StageState } from "@/hooks/useAnalysisSSE";
import type { StageName } from "@/lib/types";

const LABEL: Record<StageName, string> = {
  VECTORIZE: "VECTORIZE",
  CHROMA: "CHROMA",
  GRAPH: "GRAPH",
  CONTEXT: "CONTEXT",
  LLM_STAGE1: "LLM /1",
  LLM_STAGE2: "LLM /2",
};

const ICON: Record<StageName, string> = {
  VECTORIZE: "⌗",
  CHROMA: "◇",
  GRAPH: "✧",
  CONTEXT: "≡",
  LLM_STAGE1: "△",
  LLM_STAGE2: "▲",
};

export function PipelineView({ stages }: { stages: StageState }) {
  return (
    <div className="rounded-xl border border-border bg-panel/80 backdrop-blur p-5">
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <span className="font-mono text-[11px] text-cyan tracking-[0.3em]">
          /// PIPELINE
        </span>
        <span className="font-mono text-[11px] text-sub flex items-center gap-3">
          <span>
            DONE {Object.values(stages).filter((s) => s.status === "done").length}/
            {STAGES.length}
          </span>
          <span>SSE STREAM · LIVE</span>
        </span>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {STAGES.map((s, i) => {
          const st = stages[s];
          const status = st.status;
          return (
            <motion.div
              key={s}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className={clsx(
                "relative rounded-lg border p-3 transition-all",
                status === "pending" && "border-border bg-bg/40",
                status === "running" &&
                  "border-cyan bg-cyan/5 shadow-glow-cyan animate-pulse-glow",
                status === "done" && "border-success/60 bg-success/5",
                status === "error" && "border-error bg-error/10",
              )}
            >
              <div className="flex items-center justify-between">
                <span className="text-lg font-mono text-cyan">{ICON[s]}</span>
                <StatusDot status={status} />
              </div>
              <div className="mt-2 font-mono text-xs tracking-wider text-text">{LABEL[s]}</div>
              <div className="mt-1 font-mono text-[10px] text-sub">
                {(st.elapsed_ms / 1000).toFixed(2).padStart(6, "0")} s
              </div>
              {st.message && (
                <div className="mt-2 font-mono text-[10px] text-sub line-clamp-2">
                  {st.message}
                </div>
              )}
              {st.hits && st.hits.length > 0 && (
                <div className="mt-1 font-mono text-[10px] text-cyan">
                  hits: {st.hits.length}
                </div>
              )}
              {st.nodes && st.nodes.length > 0 && (
                <div className="mt-1 font-mono text-[10px] text-magenta">
                  nodes: {st.nodes.length}
                </div>
              )}
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}

function StatusDot({ status }: { status: string }) {
  const color =
    status === "running"
      ? "bg-cyan"
      : status === "done"
        ? "bg-success"
        : status === "error"
          ? "bg-error"
          : "bg-sub/40";
  return (
    <span className="flex h-2 w-2">
      <span
        className={clsx(
          "relative inline-flex rounded-full h-2 w-2",
          color,
          status === "running" && "animate-ping",
        )}
      />
    </span>
  );
}
