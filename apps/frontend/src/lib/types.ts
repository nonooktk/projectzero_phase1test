// バックエンド Pydantic スキーマと対応する型定義。
export type Score = "◎" | "○" | "△" | "×" | "－";
export type StageName =
  | "VECTORIZE"
  | "CHROMA"
  | "GRAPH"
  | "CONTEXT"
  | "LLM_STAGE1"
  | "LLM_STAGE2";
export type StageStatus = "pending" | "running" | "done" | "error";

export type SearchHit = {
  id: string;
  content: string;
  score: number;
  source: "external" | "internal" | "persons";
};

export type GraphNode = { id: string; label: string; type: string };
export type GraphEdge = { source: string; target: string; relation: string };

export type AxisAnalysis = { score: Score; reason: string; key_points: string[] };
export type Stage1Result = {
  external: AxisAnalysis;
  internal: AxisAnalysis;
  org: AxisAnalysis;
};

export type NextAction = { person: string; action: string };
export type Proposal = {
  title: string;
  summary: string;
  timing_score: Score;
  timing_reason: string;
  tech_fit_score: Score;
  tech_fit_reason: string;
  bottleneck: string;
  bottleneck_solution: string;
  next_actions: NextAction[];
};

export type Tier2 = {
  customer: { summary: string; key_insights: string[] };
  competitor: {
    summary: string;
    white_space: string;
    our_advantage: string;
    key_insights: string[];
  };
  company: {
    summary: string;
    reusable_assets: string[];
    key_persons: { name: string; role: string }[];
    lessons_learned: string;
  };
};

export type Stage2Result = {
  proposals: Proposal[];
  approver_summary: string;
  tier2: Tier2 | null;
};

export type GraphPayload = {
  nodes: GraphNode[];
  edges: GraphEdge[];
  seed_ids: string[];
  proposal_related_ids: string[];
};

export type AnalysisResult = {
  analysis_id: string;
  theme: string;
  stage1: Stage1Result;
  stage2: Stage2Result;
  graph: GraphPayload;
  elapsed_ms: number;
};

export type StageEventPayload = {
  stage: StageName;
  status: StageStatus;
  elapsed_ms: number;
  hits?: SearchHit[];
  nodes?: GraphNode[];
  tokens?: number;
  error?: string;
  message?: string;
};
