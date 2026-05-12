"use client";
import { useState } from "react";

type Preset = {
  label: string;
  target_market: string;
  assets: string;
  idea_detail: string;
};

const PRESETS: Preset[] = [
  {
    label: "BEMS（ビルエネルギー管理）",
    target_market: "国内の中規模オフィスビル・商業施設オーナー",
    assets: "省エネ制御アルゴリズム / フレキシブル薄膜太陽電池技術",
    idea_detail:
      "ビルエネルギー管理（BEMS）で新事業を考えたい。過去の BEMS 事業（proj_001）の知見と保有技術を活用し、再参入の可能性を評価したい。",
  },
  {
    label: "医療機器（MEMS / シリコーン）",
    target_market: "国内外の医療機器メーカー・医療機関",
    assets: "医療用生体適合性シリコーン材料 / 薬機法認証済の品質保証体制",
    idea_detail:
      "医療機器向けに自社の生体適合性シリコーン材料を活かしたい。薬機法認証済の体制を強みに、横展開のアプローチを評価したい。",
  },
  {
    label: "ウェアラブル（B2C → B2B2C）",
    target_market: "国内スマートフォン向けウェアラブルユーザー",
    assets: "バイオセンサー部材技術 / 過去 PJ（proj_008）の知見",
    idea_detail:
      "スマートフォン向けウェアラブルに参入したい。過去 B2C 参入で失敗した経緯を踏まえ、B2B2C を含む転換アプローチを評価してほしい。",
  },
];

export function IdeaForm({
  onSubmit,
  running,
}: {
  onSubmit: (theme: string) => void;
  running: boolean;
}) {
  const [targetMarket, setTargetMarket] = useState("");
  const [assets, setAssets] = useState("");
  const [ideaDetail, setIdeaDetail] = useState("");
  const [warn, setWarn] = useState<string | null>(null);

  const applyPreset = (p: Preset) => {
    setTargetMarket(p.target_market);
    setAssets(p.assets);
    setIdeaDetail(p.idea_detail);
    setWarn(null);
  };

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (running) return;
        if (!ideaDetail.trim()) {
          setWarn("「提供価値・事業アイデアの詳細」は必須です。");
          return;
        }
        setWarn(null);
        const theme = [
          `【想定顧客/市場】${targetMarket.trim() || "未入力"}`,
          `【活用アセット】${assets.trim() || "未入力"}`,
          `【アイデア概要】${ideaDetail.trim()}`,
        ].join("\n");
        onSubmit(theme);
      }}
      className="rounded-xl border border-border bg-panel/80 backdrop-blur p-6 shadow-glow-cyan"
    >
      <div className="flex items-center gap-2">
        <span className="font-mono text-[11px] text-cyan tracking-[0.3em]">/// INPUT</span>
        <span className="font-mono text-[11px] text-sub">IDEA &gt; ANALYZE</span>
      </div>
      <h2 className="mt-2 text-xl font-semibold tracking-wide">💡 ビジネスアイデアの入力</h2>

      <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="font-mono text-[10px] text-sub tracking-widest">
            TARGET MARKET / 想定顧客
          </label>
          <input
            type="text"
            value={targetMarket}
            onChange={(e) => setTargetMarket(e.target.value)}
            placeholder="例：欧州の大規模農業法人"
            className="mt-1 w-full bg-bg/60 border border-border rounded-lg p-2.5 font-mono text-sm
                       text-text placeholder:text-sub/60 focus:outline-none focus:border-cyan
                       focus:shadow-glow-cyan transition-shadow"
          />
        </div>
        <div>
          <label className="font-mono text-[10px] text-sub tracking-widest">
            ASSETS / 活用したい自社アセット・コア技術
          </label>
          <input
            type="text"
            value={assets}
            onChange={(e) => setAssets(e.target.value)}
            placeholder='例：100%植物由来ポリマー「Green Planet」'
            className="mt-1 w-full bg-bg/60 border border-border rounded-lg p-2.5 font-mono text-sm
                       text-text placeholder:text-sub/60 focus:outline-none focus:border-cyan
                       focus:shadow-glow-cyan transition-shadow"
          />
        </div>
      </div>

      <div className="mt-4">
        <label className="font-mono text-[10px] text-sub tracking-widest">
          IDEA DETAIL / 提供価値・事業アイデアの詳細 <span className="text-error">*</span>
        </label>
        <textarea
          value={ideaDetail}
          onChange={(e) => setIdeaDetail(e.target.value)}
          rows={4}
          placeholder="例：環境規制強化を背景に、農業用マルチフィルムとして展開。haあたり300ユーロの廃棄コストを削減し..."
          className="mt-1 w-full bg-bg/60 border border-border rounded-lg p-3 font-mono text-sm
                     text-text placeholder:text-sub/60 focus:outline-none focus:border-cyan
                     focus:shadow-glow-cyan transition-shadow"
        />
      </div>

      <div className="mt-4">
        <div className="font-mono text-[10px] text-sub tracking-widest mb-2">PRESETS</div>
        <div className="flex flex-wrap gap-2">
          {PRESETS.map((p) => (
            <button
              key={p.label}
              type="button"
              onClick={() => applyPreset(p)}
              className="text-xs font-mono px-3 py-1 rounded-full border border-border
                         text-sub hover:text-cyan hover:border-cyan transition-colors"
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {warn && (
        <div className="mt-4 rounded-lg border border-warning/50 bg-warning/10 p-3 font-mono text-xs text-warning">
          ⚠ {warn}
        </div>
      )}

      <div className="mt-5 flex justify-end">
        <button
          type="submit"
          disabled={running}
          className="px-6 py-2 rounded-lg bg-cyan/10 border border-cyan text-cyan font-mono
                     hover:bg-cyan hover:text-bg hover:shadow-glow-cyan transition-all
                     disabled:opacity-30 disabled:cursor-not-allowed"
        >
          {running ? "ANALYZING..." : "投資判断AIによる分析スタート ▶"}
        </button>
      </div>
    </form>
  );
}
