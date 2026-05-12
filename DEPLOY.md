# デプロイ手順（Vercel + Render Free + Supabase Free）

ローカル動作確認とユーザー承認が完了したので、無料枠の暫定環境にデプロイする。

| 層 | サービス | URL（デプロイ後に確定） |
|---|---|---|
| フロント | Vercel Hobby | `https://<project>.vercel.app` |
| バックエンド | Render Free Web Service | `https://tech0-search-backend.onrender.com` |
| データ | Supabase Free | 既に設定済み |

---

## 0. 前提

- GitHub アカウントを持っている
- Supabase に `rag_*` / `graph_*` テーブルが投入済み（ローカルで `/health/data` 確認済み）
- `.env` のキーを手元に控えている（OpenAI / Supabase）

---

## 1. GitHub に push

```bash
cd /Users/mitsuru/Desktop/youken_sep/tech0-search_claudecode

# Git 初期化
git init
git add .
git status         # .env が含まれていないことを必ず確認
git commit -m "feat: tech0-search v4 (claude full implementation)"

# GitHub で空リポジトリを作成し、その URL を控える（例: github.com/yourname/tech0-search）
git branch -M main
git remote add origin https://github.com/<yourname>/tech0-search.git
git push -u origin main
```

> ⚠ `.gitignore` で `.env` は除外済み。`git status` で `.env` がリストアップされていないことを必ず確認すること。

---

## 2. Render（バックエンド）デプロイ

### 2.1 サインアップ・新規 Blueprint

1. https://render.com にサインアップ（GitHub 連携）
2. ダッシュボード → 「New +」→「Blueprint」
3. 該当 GitHub リポジトリを選択
4. Render が `render.yaml` を検出して `tech0-search-backend` を提案 → Apply

### 2.2 環境変数を設定（Render UI）

サービス → Environment タブで以下を設定（`sync: false` のキー）:

| キー | 値 |
|---|---|
| `OPENAI_API_KEY` | `sk-...`（手元の実キー） |
| `SUPABASE_URL` | `https://xxxx.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | `eyJ...` |
| `SUPABASE_ANON_KEY` | `eyJ...` |
| `SUPABASE_DB_URL` | `postgresql://...` |
| `CORS_ORIGINS` | 後で Vercel URL を入れる。最初は `*` で仮置きしても可 |

### 2.3 初回デプロイ確認

1. Logs タブでビルドを監視（5〜10 分）。`Application startup complete.` が出れば成功
2. ブラウザで `https://tech0-search-backend.onrender.com/health` → `{"status":"ok"}`
3. `https://tech0-search-backend.onrender.com/health/data` → `source_type: "supabase"` と件数

> ⚠ Render Free は **15 分非アクティブで停止 / 初回 30 秒のコールドスタート**。デモ前にウォームアップ叩く運用。

---

## 3. Vercel（フロントエンド）デプロイ

### 3.1 新規 Project

1. https://vercel.com にサインアップ（GitHub 連携）
2. ダッシュボード → 「Add New...」→「Project」
3. 該当 GitHub リポジトリを選択 → Import

### 3.2 Project 設定

| 項目 | 値 |
|---|---|
| Framework Preset | Next.js |
| Root Directory | **`apps/frontend`** ← 必須 |
| Build Command | （デフォルト = `next build`） |
| Install Command | `npm install --legacy-peer-deps` |
| Output Directory | （デフォルト） |

### 3.3 環境変数

Vercel Project Settings → Environment Variables:

| キー | 値 |
|---|---|
| `NEXT_PUBLIC_API_URL` | `https://tech0-search-backend.onrender.com` |

3 環境（Production / Preview / Development）すべてに付与。

### 3.4 デプロイ

「Deploy」ボタンで開始。2〜3 分で `https://<project>.vercel.app` が払い出される。

---

## 4. CORS 設定（Render に戻る）

Vercel の URL が確定したら、Render の `CORS_ORIGINS` を実際の Vercel URL に更新する。

```
CORS_ORIGINS=https://<project>.vercel.app
```

→ Render サービスを Manual Deploy（Settings → Deploy → Deploy latest commit）で再起動。

---

## 5. 本番 E2E 確認

1. `https://<project>.vercel.app` を開く
2. プリセット「BEMS（ビルエネルギー管理）」→ 投資判断 AI による分析スタート
3. PIPELINE 6 ステージが順に done になり、SCORE / APPROVER SUMMARY / PROPOSALS / 3C / GRAPH が表示されることを確認
4. 他 2 プリセット（医療／ウェアラブル）でも実行

### 既知の挙動

- **初回コールドスタート**：Render Free が 15 分非アクティブだとスリープ。最初の 1 回は API 応答に 30〜60 秒かかる
- **ChromaDB 再構築**：プロセス起動毎にメモリ上に展開（数秒〜十数秒）
- **LLM**：Stage1 + Stage2 で 10〜25 秒

---

## 6. トラブルシュート

| 症状 | 原因 | 対処 |
|---|---|---|
| `/health` が 502 | Render プロセス未起動 | Logs で `pip install` 失敗・メモリ不足を確認 |
| `/health/data` が `source_type: "json"` | Supabase env 未設定 | Render の Environment を確認 |
| CORS エラー（ブラウザ Console） | `CORS_ORIGINS` 未更新 | Vercel URL を入れて Render 再起動 |
| Vercel ビルドが ESLint で失敗 | `eslint-config-next` の peer | `npm install --legacy-peer-deps` が install command に入っているか確認 |
| ChromaDB のメモリ不足（Render 512MB） | sentence-transformers が大きい | OpenAI Embeddings に切替 or Supabase pgvector への移行を検討（将来） |

---

## 7. デプロイ後の運用ルール

| ルール | 内容 |
|---|---|
| 月額予算上限 | OpenAI ダッシュボードで $5/月の hard limit を設定 |
| 認証 | 暫定環境では認証なし。社内限定 URL の共有のみ。実機密データは投入しない |
| 週次ピング | Supabase Free が 7 日無アクセスで一時停止するため、週 1 回はアクセスする |
| ロールバック | Git で前コミットにタグを打ち、Render／Vercel の「Rollback to previous deploy」で戻す |
