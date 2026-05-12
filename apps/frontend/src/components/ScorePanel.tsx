"use client";
import { motion } from "framer-motion";
import clsx from "clsx";

import type { Score, Stage1Result } from "@/lib/types";

const AXIS_LABEL: Record<keyof Stage1Result, string> = {
  external: "今やるべきか",
  internal: "自社でやれるか",
  org: "誰とやるか",
};

const AXIS_SUB: Record<keyof Stage1Result, string> = {
  external: "EXTERNAL",
  internal: "INTERNAL",
  org: "ORG",
};

function scoreColor(s: Score) {
  if (s === "◎") return "text-success border-success/60 shadow-[0_0_18px_rgba(0,255,163,0.35)]";
  if (s === "○") return "text-cyan border-cyan/60 shadow-glow-cyan";
  if (s === "△") return "text-warning border-warning/60";
  if (s === "×") return "text-error border-error/60";
  return "text-sub border-border";
}

export function ScorePanel({ stage1 }: { stage1: Stage1Result }) {
  const axes: (keyof Stage1Result)[] = ["external", "internal", "org"];
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {axes.map((axis, i) => {
        const a = stage1[axis];
        return (
          <motion.div
            key={axis}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.08 }}
            className="rounded-xl border border-border bg-panel/80 backdrop-blur p-5"
          >
            <div className="flex items-center justify-between">
              <span className="font-mono text-[10px] text-cyan tracking-[0.3em]">
                {AXIS_SUB[axis]}
              </span>
              <div
                className={clsx(
                  "h-12 w-12 rounded-full border flex items-center justify-center font-mono text-2xl",
                  scoreColor(a.score),
                )}
              >
                {a.score}
              </div>
            </div>
            <div className="mt-2 text-sm text-sub">{AXIS_LABEL[axis]}</div>
            <div className="mt-3 text-sm leading-relaxed text-text/90 whitespace-pre-wrap break-words">
              {a.reason}
            </div>
            {a.key_points.length > 0 && (
              <ul className="mt-3 space-y-1.5">
                {a.key_points.map((kp, idx) => (
                  <li
                    key={idx}
                    className="text-xs text-sub border-l-2 border-cyan/40 pl-2 leading-relaxed whitespace-pre-wrap break-words"
                  >
                    {kp}
                  </li>
                ))}
              </ul>
            )}
          </motion.div>
        );
      })}
    </div>
  );
}
