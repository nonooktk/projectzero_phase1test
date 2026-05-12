# CLAUDE.md

このファイルは Claude Code（claude.ai/code）がこのフォルダで作業する際の指示書である。

## 概要（v4：Claude 全実装版）

このフォルダは **Tech0 Search 暫定実装プロジェクト**である。Streamlit MVP（`mvp_streamlit/`）を Next.js + FastAPI + Supabase + ChromaDB + NetworkX に移行し、**Claude が全実装を担当**する。プロンプトは `mvp_streamlit/llm/prompts.py` を流用し、テクノロジー感のあるダーク UI で検索処理を視覚化、関連ノードを Graph 表示する。

| 観点 | 内容 |
|---|---|
| 主体 | **Claude が全実装**（ユーザーは仕様レビュー＋承認） |
| 利用シーン | Claude Code または チャットからこのフォルダを開いて作業する |
| 期間 | 1〜2 セッション（数時間〜半日） |
| ゴール | ローカル `docker compose up` で E2E（アイデア入力 → 検索可視化 → Graph 表示 → GO/NO 判定）が動く |
| デプロイ | **ローカル動作確認＋ユーザー承認後**に Vercel／Render／Supabase へ |
| スコープ外 | 性能 SLO・本番認証（Entra ID）・監査ログ厳格化・楽観ロック・負荷試験 |

過去版（学習スコープ）は `archive/` に保存（`IMPLEMENTATION_PLAN_INTERIM_v3.md`／`LEARNING_ACTION_PLAN_v1.md`）。

## 起動時の必読資料

| 順序 | ファイル | 読む目的 |
|---|---|---|
| 必須① | `IMPLEMENTATION_PLAN_INTERIM.md` | v4 本体。アーキテクチャ・5 フェーズ実行プラン・デザイン方針 |
| 必須② | `mvp_streamlit/llm/prompts.py` | 流用するプロンプト本体（Stage1／Stage2／Tier2） |
| 必須③ | `mvp_streamlit/CLAUDE.md` | MVP の設計意図・データフロー・JSON スキーマ |
| 必須④ | `mvp_streamlit/data/*.json`／`data/graph/*.json` | 投入データ |
| 補助 | `../03_PROJECT_ZERO_要件定義書_ver07.docx`／`../04_PROJECT_ZERO_仕様設計書_ver03.docx` | 本番要件（参照のみ・編集不可） |

## 実装ルール

| ルール | 内容 |
|---|---|
| プロンプト | `mvp_streamlit/llm/prompts.py` をそのまま import or コピー流用。改変は最小 |
| アーキテクチャ | Port-Adapter（薄め）。Service ↔ Adapter 直結を許容、Azure 移行時にリファクタ |
| デザイン | ダーク基調（bg `#0A0E1A`）＋ ネオン（cyan `#00E5FF`／magenta `#FF2D95`）＋ JetBrains Mono ＋ HUD グリッド |
| 検索可視化 | SSE で各ステージ（VECTORIZE → CHROMA → GRAPH → CONTEXT → LLM1 → LLM2）の状態を配信、フロントでタイムライン表示 |
| Graph | react-force-graph-2d。ノードタイプ別配色、提案関連ノードはパルス |
| 編集対象 | `tech0-search_claudecode/` 配下のみ。親ディレクトリの docx は読むのみ |

## コード生成ルール

| ルール | 内容 |
|---|---|
| 行数 | 機能単位で必要十分。学習配慮の 20 行制限は撤廃 |
| ファイル分割 | 責務単位で適切に分割。1 ファイル肥大化を避ける |
| 型注釈 | 公開 IF（Port／Pydantic スキーマ）は厳密、内部は必要十分 |
| コメント | WHY のみ。自明な行にコメントしない |
| テスト | Pydantic スキーマと UseCase に最低 1 本ずつ。網羅は不要 |

## 出力フォーマット

| 項目 | ルール |
|---|---|
| 言語 | 日本語、言い切り型 |
| コードフェンス | 言語指定必須 |
| 比較・選定・差分 | 表で表現 |
| 進捗報告 | 各フェーズ完了時に「何ができたか／次に何をするか」を 2〜3 行で報告 |

## デプロイガードレール

| ステップ | 動作 |
|---|---|
| F5 直前 | ローカルで E2E 動作確認できる状態にした上で **ユーザー承認待ち** |
| 承認後 | Vercel／Render Free／Supabase Free へデプロイ |
| 環境変数 | `.env.example` に必須キー列挙。実キーはユーザーが各サービス UI で設定 |

## 更新ポリシー

スコープや採用技術を変更する際は以下の順序を守る。

```
① ユーザーに更新提案（変更点・理由・影響範囲）
② ユーザー承認
③ 該当 MD ファイル編集
④ 変更サマリを応答末尾に記載
```

## 関連ファイル

| ファイル | 役割 |
|---|---|
| `IMPLEMENTATION_PLAN_INTERIM.md` | v4 実行プラン |
| `README.md` | プロジェクト起点の案内 |
| `mvp_streamlit/` | 流用元 MVP（プロンプト・データ・ロジック） |
| `data/`／`supabase/` | 投入データ・Supabase スキーマ |
| `scripts/seed_supabase.py` | Supabase 初期投入スクリプト |
| `archive/` | 過去版（v1／v2／v3 ＋ LEARNING_ACTION_PLAN_v1） |
| `../03_PROJECT_ZERO_要件定義書_ver07.docx`／`../04_PROJECT_ZERO_仕様設計書_ver03.docx` | 本番要件・仕様（読むのみ） |
