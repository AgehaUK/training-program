# 故障分析システム（Failure Analysis System）

製造・設備保全の現場で発生する**故障報告を AI で構造化・蓄積し、検索・分析・示唆出し**まで行うフルスタックWebアプリケーション。
要件定義からフロント／バックエンド実装、テスト、までを一貫して制作しました。

---

## 主な機能

| 機能 | 概要 |
|------|------|
| データ入力 | 自由記述の故障報告を LLM で構造化（故障モード・原因・対策・コスト等を抽出） |
| 検索 | ベクトル類似度（埋め込み + numpy）による意味検索、一覧／詳細表示 |
| ダッシュボード | 故障モード内訳・トレンド・コスト上位10件を可視化（recharts）、AIによる示唆出し |
| CSVインポート | 既存の故障データを一括取り込み |
| 認証・ユーザー管理 | JWT 認証（python-jose）、パスワードハッシュ（passlib/bcrypt）、管理者によるユーザー管理 |

## 技術スタック

**フロントエンド**
- Next.js 16 / React 19 / TypeScript
- Tailwind CSS v4 / recharts / sonner（トースト）/ axios
- App Router、AuthGuard によるルート保護、認証コンテキスト

**バックエンド**
- FastAPI / Pydantic v2 / SQLAlchemy
- レイヤード構成（api / services / repositories / models / schemas / core）
- ベクトルストア（numpy ベースの類似度検索）
- LLM 連携（Anthropic Claude。APIキー未設定時はモックにフォールバック）
- pytest による API・リポジトリの自動テスト一式

**データベース**
- PostgreSQL（SQLAlchemy 経由）

## アーキテクチャのポイント

- **関心の分離**: API 層は薄く保ち、ビジネスロジックを services / repositories に分離
- **テスタビリティ**: 外部依存（LLM）をモック可能にし、API・リポジトリ層を pytest でカバー
- **段階的設計**: 画面仕様・DB設計・API設計を整備

## ディレクトリ構成

```
training_program/
├── backend/          # FastAPI バックエンド
│   ├── app/
│   │   ├── api/          # ルーター（auth / users / reports / dashboard）
│   │   ├── services/     # vector_store, llm_service
│   │   ├── repositories/ # データアクセス層
│   │   ├── models/       # SQLAlchemy モデル
│   │   ├── schemas/      # Pydantic スキーマ
│   │   └── core/         # 認証など共通処理
│   ├── tests/        # pytest テスト
│   ├── data/         # ベクトルインデックス
│   └── requirements.txt
├── frontend/         # Next.js フロントエンド
│   └── src/
│       ├── app/          # 画面（login / search / input / dashboard / admin）
│       ├── components/   # HeaderNav, AuthGuard
│       └── lib/          # api クライアント, auth-context
├── docs/             # 要件定義・設計ドキュメント（ペルソナ/ジャーニー/画面仕様/DB/API）
└── slides/           # プレゼン資料（PPTX / HTML）+ 画面スクリーンショット
```

## 主なAPIエンドポイント

```
POST   /login                      # ログイン（JWT 発行）
GET    /me                         # ログインユーザー情報
POST   /reports/structurize        # 自由記述を LLM で構造化
POST   /reports                    # 故障報告の登録
GET    /reports                    # 検索（ベクトル類似度）
GET    /reports/{id}               # 詳細
POST   /reports/import-csv         # CSV 一括インポート
GET    /dashboard/summary          # サマリー
GET    /dashboard/failure-modes    # 故障モード内訳
GET    /dashboard/trend            # トレンド
GET    /dashboard/cost-top10       # コスト上位10
POST   /dashboard/suggestions      # AI 示唆出し
```

## セットアップ

### バックエンド
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # DATABASE_URL / SECRET_KEY を設定。ANTHROPIC_API_KEY は任意
uvicorn app.main:app --reload
```

### フロントエンド
```bash
cd frontend
npm install
cp .env.example .env.local  # NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

### テスト
```bash
cd backend && pytest
```

---

## スクリーンショット

`slides/screenshots/` に主要画面のキャプチャを収録しています（ログイン / データ入力 / 検索一覧・詳細 / ダッシュボード / ユーザー管理）。
