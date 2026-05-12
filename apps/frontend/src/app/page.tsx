"use client";
import { motion } from "framer-motion";

import { ApproverSummary } from "@/components/ApproverSummary";
import { GraphView } from "@/components/GraphView";
import { IdeaForm } from "@/components/IdeaForm";
import { PipelineView } from "@/components/PipelineView";
import { ProposalTabs } from "@/components/ProposalTabs";
import { ScorePanel } from "@/components/ScorePanel";
import { Tier2Panel } from "@/components/Tier2Panel";
import { TotalTimer } from "@/components/TotalTimer";
import { useAnalysisSSE } from "@/hooks/useAnalysisSSE";

export default function HomePage() {
  const { stages, result, error, running, submit } = useAnalysisSSE();
  const started =
    running ||
    !!result ||
    Object.values(stages).some((s) => s.status !== "pending");

  return (
    <main className="min-h-screen px-4 md:px-8 py-6 max-w-7xl mx-auto">
      <header className="flex items-center justify-between mb-6">
        <div>
          <div className="font-mono text-[11px] text-cyan tracking-[0.4em]">
            PROJECT ZERO // v0.1
          </div>
          <h1 className="text-3xl font-bold tracking-wider mt-1">Tech0 Search</h1>
          <p className="text-sub text-sm mt-1">
            アイデア入力 → 検索可視化 → GO/NO 判定
          </p>
        </div>
        <div className="hidden md:flex flex-col items-end font-mono text-[10px] text-sub tracking-widest gap-1">
          <span>STATUS: {running ? "RUNNING" : result ? "READY" : "IDLE"}</span>
          <span className="flex items-center gap-2">
            <span>ELAPSED:</span>
            <TotalTimer running={running} finalMs={result?.elapsed_ms} />
          </span>
        </div>
      </header>

      <IdeaForm onSubmit={submit} running={running} />

      {started && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-6"
        >
          <PipelineView stages={stages} />
        </motion.div>
      )}

      {error && (
        <div className="mt-4 rounded-lg border border-error bg-error/10 p-4">
          <div className="font-mono text-[11px] text-error tracking-[0.3em] mb-2">
            /// ERROR
          </div>
          <pre className="font-mono text-xs text-error mb-2 whitespace-pre-wrap break-all max-h-96 overflow-auto">
            {error}
          </pre>
          {error.toLowerCase().includes("fetch") && (
            <div className="text-xs text-sub leading-relaxed">
              バックエンド API（http://localhost:8000）に接続できません。
              uvicorn が起動しているか確認してください。
            </div>
          )}
        </div>
      )}

      {result && (
        <motion.section
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="mt-6 space-y-6"
        >
          <ScorePanel stage1={result.stage1} />
          <ApproverSummary summary={result.stage2.approver_summary} />
          <ProposalTabs proposals={result.stage2.proposals} />
          <Tier2Panel tier2={result.stage2.tier2} />
          <GraphView graph={result.graph} />
        </motion.section>
      )}
    </main>
  );
}
