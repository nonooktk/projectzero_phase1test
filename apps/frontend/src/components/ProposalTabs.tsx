"use client";
import { useState } from "react";
import clsx from "clsx";

import type { Proposal } from "@/lib/types";

export function ProposalTabs({ proposals }: { proposals: Proposal[] }) {
  const [active, setActive] = useState(0);
  if (proposals.length === 0) return null;
  const p = proposals[active];
  return (
    <div className="rounded-xl border border-border bg-panel/80 backdrop-blur p-5">
      <div className="flex items-center justify-between mb-4">
        <span className="font-mono text-[11px] text-magenta tracking-[0.3em]">
          /// PROPOSALS
        </span>
        <span className="font-mono text-[11px] text-sub">{proposals.length} OPTIONS</span>
      </div>
      <div className="flex gap-2 border-b border-border">
        {proposals.map((pp, i) => (
          <button
            key={i}
            onClick={() => setActive(i)}
            className={clsx(
              "px-4 py-2 text-sm font-mono transition-colors border-b-2 -mb-px",
              active === i
                ? "border-magenta text-magenta"
                : "border-transparent text-sub hover:text-text",
            )}
          >
            CASE {i + 1}
          </button>
        ))}
      </div>
      <div className="mt-4 space-y-4">
        <div>
          <h3 className="text-lg font-semibold tracking-wide">{p.title}</h3>
          <p className="mt-2 text-sm text-text/90 leading-relaxed">{p.summary}</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <ScoreRow label="TIMING" score={p.timing_score} reason={p.timing_reason} />
          <ScoreRow label="TECH FIT" score={p.tech_fit_score} reason={p.tech_fit_reason} />
        </div>
        <div className="rounded-lg border border-warning/30 bg-warning/5 p-3">
          <div className="font-mono text-[10px] text-warning tracking-widest">BOTTLENECK</div>
          <div className="mt-1 text-sm">{p.bottleneck}</div>
          <div className="mt-2 text-xs text-sub">
            <span className="text-success">▶ SOLUTION:</span> {p.bottleneck_solution}
          </div>
        </div>
        {p.next_actions.length > 0 && (
          <div>
            <div className="font-mono text-[10px] text-cyan tracking-widest mb-2">
              NEXT ACTIONS
            </div>
            <ul className="space-y-2">
              {p.next_actions.map((na, idx) => (
                <li
                  key={idx}
                  className="text-sm flex gap-3 border-l-2 border-cyan/40 pl-3"
                >
                  <span className="font-mono text-cyan whitespace-nowrap">
                    [{idx + 1}]
                  </span>
                  <div>
                    <div className="font-semibold">{na.person}</div>
                    <div className="text-sub">{na.action}</div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

function ScoreRow({
  label,
  score,
  reason,
}: {
  label: string;
  score: string;
  reason: string;
}) {
  return (
    <div className="rounded-lg border border-border bg-bg/40 p-3">
      <div className="flex items-center justify-between">
        <span className="font-mono text-[10px] text-sub tracking-widest">{label}</span>
        <span className="font-mono text-xl text-cyan">{score}</span>
      </div>
      <p className="mt-2 text-xs text-text/80 leading-relaxed">{reason}</p>
    </div>
  );
}
