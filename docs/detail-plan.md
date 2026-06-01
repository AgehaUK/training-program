# 実装計画

## 概要

このドキュメントは、Vertical Slice Architecture（VSA）に基づいた実装計画です。
まず基盤を構築し、その後各スライスを順序通りに実装することで、早期の動作確認と段階的な進捗を実現します。

**プロジェクト**: 故障報告構造化・分析システム
**技術スタック**: Next.js 14（フロント）+ FastAPI（バック）+ PostgreSQL（Docker）+ FAISS（ベクトル検索）
**スコープ**: ローカル環境（デプロイ不要）

---

## 機能スライス一覧と実装順序

### Phase 0: Foundation（プロジェクト基盤構築）

プロジェクト開始時に全体で必須となる基盤処理を実装。

---

#### Slice 0-1: プロジェクトセットアップとコア構造構築

- **概要**: フロントエンド・バックエンドの骨格構築、Docker 開発環境の整備
- **スキル**: `/foundation-project-setup`
- **実装内容**:
  - `docker-compose.yml`（PostgreSQL + FastAPI + Next.js）
  - `frontend/`（Next.js 14 + Tailwind CSS）ディレクトリ構造
  - `backend/`（FastAPI）ディレクトリ構造
  - 共通レイアウト（ヘッダー、ナビゲーション: データ入力 / ダッシュボード / 検索）
  - 環境変数設定（`.env`）

**チェックリスト**:
- [ ] `docker compose up` で全サービスが起動する
- [ ] `http://localhost:3000` でフロントエンドが表示される
- [ ] `http://localhost:8000/docs` で FastAPI Swagger が表示される
- [ ] ナビゲーションで3画面に遷移できる

---

#### Slice 0-2: データベース設計と基盤の実装

- **概要**: PostgreSQL スキーマ作成、Alembic マイグレーション、ORM モデル実装
- **スキル**: `/foundation-database-setup`
- **実装内容**:
  - `failure_modes` テーブル（マスタ）
  - `failure_reports` テーブル（コアデータ）
  - インデックス（`occurred_at`, `failure_mode_id`, `equipment_name`）
  - SQLAlchemy ORM モデル
  - Alembic マイグレーションファイル

**チェックリスト**:
- [ ] マイグレーション実行で2テーブルが作成される
- [ ] DB 接続が確認できる
- [ ] ORM モデルが定義されている

---

#### Slice 0-3: マイグレーションとシーダーの作成

- **概要**: 初期データ投入、テスト用ファクトリー、FAISS インデックス基盤
- **スキル**: `/foundation-migration-seeder`
- **実装内容**:
  - `failure_modes` シード（劣化・破損・動作不良・漏れ・過熱・腐食・摩耗・電気系統故障・その他）
  - サンプル故障レポート 15〜20件（多様な設備・故障モードを網羅）
  - モデルファクトリー（pytest 用ダミーデータ生成）
  - FAISS インデックスの初期化・保存・ロード基盤（`backend/app/services/vector_store.py`）

**チェックリスト**:
- [ ] シーダー実行で `failure_modes` に9件投入される
- [ ] サンプルデータ 15〜20件が投入される
- [ ] FAISS インデックスのビルド・保存・ロードが動作する

---

### Phase 1: コア機能（Foundation に依存）

---

#### Slice 1: 故障データ構造化（データ入力画面 - 入力〜構造化）

- **概要**: 自由記述テキスト → LLM API → 構造化JSON の一連の流れを実装
- **スキル**: `/fullstack-integration`
- **対象画面**: データ入力画面（テキストエリア〜構造化結果表示）
- **関連データ**: `failure_modes`（READ）
- **実装内容**:
  - `POST /api/reports/structurize` API（FastAPI）
  - LLM API 呼び出しサービス（`backend/app/services/llm_service.py`）
    - `failure_modes` マスタをプロンプトに含め、故障モードを正規化
    - Structured Output で型安全なJSON抽出
  - フロントエンド: テキストエリア + 構造化ボタン + ローディング + 結果カード表示
  - Pydantic スキーマ（リクエスト・レスポンス型定義）

**TDD サイクル**:
- 🔴 `test_structurize_api.py`（モックLLMでAPIのI/Oを検証）
- 🟢 LLMサービス実装 → APIエンドポイント実装
- 🔵 プロンプトの最適化、エラーハンドリング整備

**チェックリスト**:
- [ ] テキスト入力 → 構造化ボタンクリック → JSON結果が画面に表示される
- [ ] LLMが8項目（発生日, 設備名, 現象, 原因, 対策, コスト, 停止時間, 故障モード）を抽出できる
- [ ] APIテストがパスしている

---

#### Slice 2: データ保存・サンプル投入（データ入力画面 - 完成）

- **概要**: 構造化結果の確認・編集 → DB保存、サンプルデータ一括投入
- **スキル**: `/fullstack-integration`
- **対象画面**: データ入力画面（編集フォーム〜保存、サンプル投入ボタン）
- **関連データ**: `failure_reports`（INSERT）、`failure_modes`（READ/INSERT）、FAISS インデックス（UPDATE）
- **実装内容**:
  - `POST /api/reports` API（DB保存 + FAISS インデックス更新）
  - `POST /api/reports/sample` API（サンプルデータ一括構造化・保存）
  - `GET /api/failure-modes` API（故障モード一覧）
  - フロントエンド: 編集フォーム（故障モードドロップダウン含む）+ 保存ボタン + サンプル投入ボタン
  - Repository 層（`FailureReportRepository`）

**TDD サイクル**:
- 🔴 `test_report_repository.py`、`test_reports_api.py`
- 🟢 Repository 実装 → API実装 → フロント保存フロー実装
- 🔵 エラーハンドリング、バリデーション整備

**チェックリスト**:
- [ ] 構造化結果を確認・編集して保存できる
- [ ] サンプル投入ボタンで複数件が一括保存される
- [ ] 保存時に FAISS インデックスが更新される
- [ ] テストがパスしている

---

### Phase 2: 分析・可視化（Slice 2 に依存）

---

#### Slice 3: ダッシュボード（集計・グラフ・KPI）

- **概要**: 構造化データを集計し、KPI・円グラフ・折れ線・棒グラフで可視化
- **スキル**: `/fullstack-integration`
- **対象画面**: ダッシュボード画面
- **関連データ**: `failure_reports`（READ）、`failure_modes`（JOIN）
- **実装内容**:
  - `GET /api/dashboard/summary` API（KPI: 総件数, 総コスト, 平均停止時間）
  - `GET /api/dashboard/failure-modes` API（故障モード別件数）
  - `GET /api/dashboard/trend` API（月次トレンド）
  - `GET /api/dashboard/cost-top10` API（コストTOP10）
  - フィルタリング（期間・設備名・故障モード）対応
  - フロントエンド: Recharts 等でグラフ描画、フィルターバー

**TDD サイクル**:
- 🔴 `test_dashboard_api.py`（各集計APIの正確性を検証）
- 🟢 集計クエリ実装 → API実装 → フロントグラフ実装
- 🔵 フィルタリング整備、グラフのUI調整

**チェックリスト**:
- [ ] 4種のグラフ（円/折れ線/棒/KPI）が表示される
- [ ] フィルターで絞り込みが反映される
- [ ] テストがパスしている

---

#### Slice 4: 示唆出し（LLM）

- **概要**: 集計データを LLM に送信し、改善施策の示唆テキストを生成
- **スキル**: `/fullstack-integration`
- **対象画面**: ダッシュボード画面（示唆カード）
- **関連データ**: 集計結果（非永続）
- **実装内容**:
  - `POST /api/dashboard/suggestions` API
  - 集計データを構造化プロンプトに変換するサービス
  - フロントエンド: 示唆カード（ローディング → テキスト表示）

**TDD サイクル**:
- 🔴 `test_suggestions_api.py`（モックLLMで示唆生成を検証）
- 🟢 示唆生成サービス実装 → API実装 → フロント表示
- 🔵 プロンプト最適化

**チェックリスト**:
- [ ] ダッシュボードに示唆テキストが表示される
- [ ] テストがパスしている

---

### Phase 3: 検索（Slice 2 に依存）

---

#### Slice 5: FAISS ベクトル検索・詳細表示（検索画面）

- **概要**: FAISS を使った類似事例検索、一覧・詳細表示、フィルタ・ソート
- **スキル**: `/fullstack-integration`
- **対象画面**: 検索画面
- **関連データ**: `failure_reports`（READ）、`failure_modes`（JOIN）、FAISS インデックス（READ）
- **実装内容**:
  - `GET /api/reports` API（FAISS ベクトル検索 + フィルタ + ソート + ページネーション）
    - キーワードを Embedding API でベクトル化 → FAISS で類似度検索 → IDリスト取得 → DB から詳細取得
  - `GET /api/reports/:id` API（詳細取得）
  - FAISS 検索サービス（`backend/app/services/vector_store.py`）
  - フロントエンド: 検索ボックス + 結果テーブル + フィルターパネル + ソート + 詳細モーダル

**TDD サイクル**:
- 🔴 `test_vector_store.py`（FAISS 検索精度の検証）、`test_search_api.py`
- 🟢 FAISS 検索サービス実装 → API実装 → フロント検索UI実装
- 🔵 検索精度チューニング、ページネーション整備

**チェックリスト**:
- [ ] キーワードで類似事例が検索できる（表記揺れも対応）
- [ ] フィルタ・ソートが動作する
- [ ] 詳細モーダルで全項目が表示される
- [ ] FAISS テストがパスしている

---

## 依存関係マップ

```
Slice 0-1 ──┐
             ├──→ Slice 0-2 ──→ Slice 0-3
Slice 0-2 ──┘                      │
                                   ↓
                              Slice 1（構造化）
                                   │
                                   ↓
                              Slice 2（保存）
                               ↙        ↘
              Slice 3（ダッシュボード）  Slice 5（FAISS検索）
                   │
                   ↓
              Slice 4（示唆出し）
```

**注**: 全スライスは Slice 0-1 〜 0-3（Foundation）完了後に進行。

---

## アーキテクチャ参照

- **Vertical Slice Architecture（VSA）**: `.claude/rules/vsa-guide.md`
- **3レイヤードアーキテクチャ**: `.claude/rules/three-layer-architecture.md`
- **TDD ガイド**: `.claude/rules/tdd-guide.md`

## 計画の変更

計画を変更する場合は `/planner` を再度実行してください。

---

生成日時: 2026-02-18
