"use client";
import type { Tier2 } from "@/lib/types";

export function Tier2Panel({ tier2 }: { tier2: Tier2 | null }) {
  if (!tier2) return null;
  return (
    <div className="rounded-xl border border-border bg-panel/80 backdrop-blur p-5">
      <div className="font-mono text-[11px] text-cyan tracking-[0.3em] mb-4">
        /// 3C ANALYSIS
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card title="CUSTOMER" body={tier2.customer.summary} insights={tier2.customer.key_insights} />
        <Card
          title="COMPETITOR"
          body={tier2.competitor.summary}
          insights={[
            ...(tier2.competitor.white_space
              ? [`WhiteSpace: ${tier2.competitor.white_space}`]
              : []),
            ...(tier2.competitor.our_advantage
              ? [`OurEdge: ${tier2.competitor.our_advantage}`]
              : []),
            ...tier2.competitor.key_insights,
          ]}
        />
        <Card
          title="COMPANY"
          body={tier2.company.summary}
          insights={[
            ...tier2.company.reusable_assets,
            ...tier2.company.key_persons.map((k) => `${k.name}: ${k.role}`),
            ...(tier2.company.lessons_learned ? [`Lessons: ${tier2.company.lessons_learned}`] : []),
          ]}
        />
      </div>
    </div>
  );
}

function Card({
  title,
  body,
  insights,
}: {
  title: string;
  body: string;
  insights: string[];
}) {
  return (
    <div className="rounded-lg border border-border bg-bg/40 p-4">
      <div className="font-mono text-[10px] text-magenta tracking-widest">{title}</div>
      <p className="mt-2 text-sm text-text/90 leading-relaxed">{body}</p>
      {insights.length > 0 && (
        <ul className="mt-3 space-y-1">
          {insights.map((s, i) => (
            <li key={i} className="text-xs text-sub border-l-2 border-magenta/40 pl-2">
              {s}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
