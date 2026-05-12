# Tech0 Search — 暫定実装プロジェクト（v4）

Streamlit MVP（`mvp_streamlit/`）を Next.js + FastAPI + Supabase + ChromaDB + NetworkX に移行する暫定実装プロジェクト。**Claude が全実装を担当**し、ユーザーは仕様レビュー＋デプロイ承認を行う。

## ファイル構成

| ファイル | 役割 |
|---|---|
| `CLAUDE.md` | Claude 作業指示書（v4） |
| `IMPLEMENTATION_PLAN_INTERIM.md` | 実装プラン本体（v4：5 フェーズ） |
| `mvp_streamlit/` | 流用元 MVP（プロンプト・データ・ロジック・変更しない） |
| `data/` | `external.json`／`internal.json`／`persons.json`／`graph/` |
| `supabase/migrations/` | Supabase スキーマ |
| `scripts/` | データ投入スクリプト |
| `archive/` | 過去版（v1：300 名 PoC／v2：MVP 反映／v3：学習版／LEARNING_ACTION_PLAN_v1） |

## 主要要件

- プロンプト: `mvp_streamlit/llm/prompts.py` を流用
- フロント: ダーク基調 HUD ＋ ネオンアクセントでテクノロジー感を演出
- 検索処理: SSE で各ステージ（VECTORIZE → CHROMA → GRAPH → CONTEXT → LLM1 → LLM2）をリアルタイム可視化
- 関連ノード: `react-force-graph-2d` で Graph 表示

## 5 フェーズ実行プラン

| Phase | 内容 |
|---|---|
| F0 | 初期化（monorepo・docker-compose・CI） |
| F1 | バックエンド（Port-Adapter・FastAPI・SSE・データ投入） |
| F2 | フロントエンド（ダーク HUD デザイン・画面骨格） |
| F3 | SSE パイプラインビュー |
| F4 | Graph 表示 |
| F5 | E2E → ユーザー承認 → デプロイ |

## ローカル起動

### 前提

- Docker Desktop が動作している
- `.env` に `OPENAI_API_KEY` を設定（`.env.example` 参照）

### 起動

```bash
cp .env.example .env  # 既に .env があれば不要
# .env の OPENAI_API_KEY を実キーに書き換える

cd infra
docker compose up --build
```

| URL | 内容 |
|---|---|
| http://localhost:3000 | Next.js フロントエンド |
| http://localhost:8000/health | FastAPI ヘルスチェック |
| http://localhost:8000/docs | FastAPI OpenAPI ドキュメント |

### 動作確認手順

1. http://localhost:3000 を開く
2. プリセット「ビルエネルギー管理で新事業を考えたい」を選び `EXECUTE ▶`
3. PIPELINE の 6 ステージが順に `running → done` で点灯することを確認
4. SCORE / APPROVER SUMMARY / PROPOSALS / 3C ANALYSIS / RELATION GRAPH が表示されることを確認
5. Graph のノードクリック・ホバー・ズームが動くことを確認
6. 他 2 シナリオ（医療／ウェアラブル）でも実行

### 既知の挙動

- 初回 ChromaDB ロード（sentence-transformers の初回ダウンロード含む）は 30 秒〜1 分かかる
- LLM Stage1 ＋ Stage2 の合計で 10〜25 秒（OpenAI API レイテンシ依存）

## デプロイ

ローカル動作確認＋ユーザー承認後、Vercel／Render Free／Supabase Free にデプロイ。

| 項目 | 設定ファイル | 詳細 |
|---|---|---|
| Render Blueprint | `render.yaml` | バックエンド宣言 |
| Vercel | `apps/frontend/vercel.json` | Next.js プロジェクト設定 |
| 手順書 | **`DEPLOY.md`** | GitHub push → Render → Vercel → CORS → E2E |

実行手順は `DEPLOY.md` を参照。
