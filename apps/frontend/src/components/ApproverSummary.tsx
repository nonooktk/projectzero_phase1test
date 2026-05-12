"use client";
export function ApproverSummary({ summary }: { summary: string }) {
  if (!summary) return null;
  return (
    <div className="relative rounded-xl border border-magenta/40 bg-panel/90 backdrop-blur p-6 shadow-glow-magenta">
      <div className="absolute -top-3 left-4 px-2 bg-bg">
        <span className="font-mono text-[11px] text-magenta tracking-[0.3em]">
          /// APPROVER SUMMARY
        </span>
      </div>
      <div className="font-mono text-[10px] text-sub tracking-widest mb-2">
        FOR: 黒崎 CDO
      </div>
      <p className="text-sm leading-relaxed whitespace-pre-wrap text-text">{summary}</p>
    </div>
  );
}
