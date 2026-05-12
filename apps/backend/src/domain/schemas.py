"""ドメイン層 Pydantic スキーマ。API IF と Port IF の境界で使う共通型。"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Score = Literal["◎", "○", "△", "×", "－"]
StageName = Literal["VECTORIZE", "CHROMA", "GRAPH", "CONTEXT", "LLM_STAGE1", "LLM_STAGE2"]
StageStatus = Literal["pending", "running", "done", "error"]


class AnalyzeRequest(BaseModel):
    theme: str = Field(..., min_length=1, max_length=2000)


class SearchHit(BaseModel):
    id: str
    content: str
    score: float
    source: Literal["external", "internal", "persons"]


class GraphNode(BaseModel):
    id: str
    label: str
    type: str  # technology / past_project / person / market など


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str


class ContextBundle(BaseModel):
    external_context: str = ""
    internal_context: str = ""
    org_context: str = ""


class AxisAnalysis(BaseModel):
    score: Score = "－"
    reason: str = ""
    key_points: list[str] = Field(default_factory=list)


class Stage1Result(BaseModel):
    external: AxisAnalysis
    internal: AxisAnalysis
    org: AxisAnalysis


class NextAction(BaseModel):
    person: str = ""
    action: str = ""


class Proposal(BaseModel):
    # LLM が一部フィールドを欠落させても result を返せるよう全てデフォルト付き
    title: str = ""
    summary: str = ""
    timing_score: Score = "－"
    timing_reason: str = ""
    tech_fit_score: Score = "－"
    tech_fit_reason: str = ""
    bottleneck: str = ""
    bottleneck_solution: str = ""
    next_actions: list[NextAction] = Field(default_factory=list)


class Tier2Customer(BaseModel):
    summary: str = ""
    key_insights: list[str] = Field(default_factory=list)


class Tier2Competitor(BaseModel):
    summary: str = ""
    white_space: str = ""
    our_advantage: str = ""
    key_insights: list[str] = Field(default_factory=list)


class Tier2KeyPerson(BaseModel):
    name: str = ""
    role: str = ""


class Tier2Company(BaseModel):
    summary: str = ""
    reusable_assets: list[str] = Field(default_factory=list)
    key_persons: list[Tier2KeyPerson] = Field(default_factory=list)
    lessons_learned: str = ""


class Tier2Analysis(BaseModel):
    customer: Tier2Customer = Field(default_factory=Tier2Customer)
    competitor: Tier2Competitor = Field(default_factory=Tier2Competitor)
    company: Tier2Company = Field(default_factory=Tier2Company)


class Stage2Result(BaseModel):
    proposals: list[Proposal] = Field(default_factory=list)
    approver_summary: str = ""
    tier2: Tier2Analysis | None = None


class GraphPayload(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    seed_ids: list[str] = Field(default_factory=list)
    proposal_related_ids: list[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    analysis_id: str
    theme: str
    stage1: Stage1Result
    stage2: Stage2Result
    graph: GraphPayload
    elapsed_ms: int = 0


# SSE イベントペイロード
class StageEventPayload(BaseModel):
    stage: StageName
    status: StageStatus
    elapsed_ms: int = 0
    hits: list[SearchHit] | None = None
    nodes: list[GraphNode] | None = None
    tokens: int | None = None
    error: str | None = None
    message: str | None = None
