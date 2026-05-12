"use client";
import { useEffect, useState } from "react";
import clsx from "clsx";

/**
 * 総経過タイマー。
 * - running=true の間は performance.now で 100ms ごとに更新
 * - running=false かつ finalMs があれば確定値を表示
 * - どちらでもなければ 00.00 s
 */
export function TotalTimer({
  running,
  finalMs,
}: {
  running: boolean;
  finalMs?: number;
}) {
  const [startedAt, setStartedAt] = useState<number | null>(null);
  const [nowMs, setNowMs] = useState(0);

  useEffect(() => {
    if (running) {
      const t0 = performance.now();
      setStartedAt(t0);
      setNowMs(0);
      const id = window.setInterval(() => {
        setNowMs(performance.now() - t0);
      }, 100);
      return () => window.clearInterval(id);
    }
    // running が false に切り替わったタイミングで履歴はそのまま保持。
    // 次回 running=true で startedAt 更新。
  }, [running]);

  const displayMs = running
    ? nowMs
    : finalMs !== undefined
      ? finalMs
      : startedAt
        ? nowMs
        : 0;

  return (
    <span
      className={clsx(
        "font-mono text-sm tracking-widest tabular-nums",
        running ? "text-cyan animate-pulse-glow" : "text-sub",
      )}
    >
      {(displayMs / 1000).toFixed(2)} s
    </span>
  );
}
