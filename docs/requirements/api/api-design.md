# API設計書

> DB設計・要件定義書v2・IPO一覧から作成

## API一覧

| # | エンドポイント | メソッド | 機能 | 対応テーブル |
|---|--------------|---------|------|------------|
| 1 | /api/reports/structurize | POST | LLM構造化 | failure_modes（READ） |
| 2 | /api/reports | POST | データ保存 | failure_reports（INSERT）, failure_modes（READ/INSERT） |
| 3 | /api/reports | GET | 検索結果一覧取得（キーワード検索・フィルタ・ソート・ページネーション） | failure_reports（READ）, failure_modes（JOIN） |
| 4 | /api/reports/:id | GET | 詳細表示 | failure_reports（READ）, failure_modes（JOIN） |
| 5 | /api/reports/sample | POST | サンプルデータ投入 | failure_reports（INSERT）, failure_modes（READ/INSERT） |
| 6 | /api/dashboard/summary | GET | サマリー統計（KPI） | failure_reports（READ） |
| 7 | /api/dashboard/failure-modes | GET | 故障モード別内訳 | failure_reports（READ）, failure_modes（JOIN） |
| 8 | /api/dashboard/trend | GET | 月次トレンド | failure_reports（READ） |
| 9 | /api/dashboard/cost-top10 | GET | コストTOP10 | failure_reports（READ） |
| 10 | /api/dashboard/suggestions | POST | 示唆出し | failure_reports（READ）, failure_modes（READ） |
| 11 | /api/failure-modes | GET | 故障モード一覧取得 | failure_modes（READ） |

## 認証・認可

| 項目 | 内容 |
|------|------|
| 認証方式 | なし（MVP、ローカル環境のみ） |
| トークン有効期限 | - |
| デフォルト権限 | 全エンドポイントにフルアクセス |

※ MVPではローカル環境での動作のため認証は不要。将来的にデプロイ時はJWT等を検討。

## 共通エラーレスポンス形式

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "エラーの説明"
  }
}
```

## エンドポイント詳細

---

### 1. LLM構造化

- **Method**: POST
- **Path**: `/api/reports/structurize`
- **目的**: 自由記述テキストをLLM APIで構造化JSONに変換する
- **対応テーブル**: failure_modes（READ: 故障モードマスタをプロンプトに含める）

#### リクエスト

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| text | string | Yes | 自由記述の故障報告テキスト |

**リクエスト例**:
```json
{
  "text": "2023年12月5日、温度センサー故障。停止3時間、部品代5万円"
}
```

#### レスポンス（成功）

```json
{
  "success": true,
  "data": {
    "occurred_at": "2023-12-05",
    "equipment_name": "温度センサー",
    "symptom": "温度センサー故障",
    "cause": null,
    "action_taken": null,
    "cost": 50000,
    "downtime_hours": 3.0,
    "failure_mode": "動作不良"
  }
}
```

#### レスポンス（エラー）

| ステータス | 意味 | エラーコード |
|-----------|------|------------|
| 400 | テキストが空または未指定 | EMPTY_TEXT |
| 500 | LLM API呼び出し失敗 | LLM_API_ERROR |
| 502 | LLM APIからの不正レスポンス | LLM_PARSE_ERROR |

---

### 2. データ保存

- **Method**: POST
- **Path**: `/api/reports`
- **目的**: 構造化済みの故障データをDBに保存する
- **対応テーブル**: failure_reports（INSERT）, failure_modes（READ/INSERT）

#### リクエスト

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| original_text | string | Yes | 元の自由記述テキスト |
| occurred_at | string (date) | Yes | 故障発生日（YYYY-MM-DD） |
| equipment_name | string | Yes | 設備名 |
| symptom | string | Yes | 現象・症状 |
| cause | string | No | 原因 |
| action_taken | string | No | 対策・修理内容 |
| cost | integer | No | コスト（円） |
| downtime_hours | float | No | 停止時間（時間） |
| failure_mode | string | Yes | 故障モード名 |

**リクエスト例**:
```json
{
  "original_text": "2023年12月5日、温度センサー故障。停止3時間、部品代5万円",
  "occurred_at": "2023-12-05",
  "equipment_name": "温度センサー",
  "symptom": "温度センサー故障",
  "cause": null,
  "action_taken": null,
  "cost": 50000,
  "downtime_hours": 3.0,
  "failure_mode": "動作不良"
}
```

#### レスポンス（成功）

```json
{
  "success": true,
  "data": {
    "id": 1,
    "message": "故障レコードを保存しました"
  }
}
```

#### レスポンス（エラー）

| ステータス | 意味 | エラーコード |
|-----------|------|------------|
| 400 | 必須項目の不足 | VALIDATION_ERROR |
| 400 | 日付形式不正 | INVALID_DATE |
| 500 | DB保存失敗 | DB_ERROR |

---

### 3. 検索結果一覧取得

- **Method**: GET
- **Path**: `/api/reports`
- **目的**: キーワード検索・フィルタ・ソート・ページネーションで故障事例を取得する
- **対応テーブル**: failure_reports（READ）, failure_modes（JOIN）

#### リクエスト（クエリパラメータ）

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| keyword | string | No | 検索キーワード（設備名, 現象, 原因, 対策をLIKE検索） |
| from | string (date) | No | 期間フィルタ開始日（YYYY-MM-DD） |
| to | string (date) | No | 期間フィルタ終了日（YYYY-MM-DD） |
| failure_mode_id | integer | No | 故障モードIDでフィルタ |
| cost_min | integer | No | コスト下限フィルタ |
| cost_max | integer | No | コスト上限フィルタ |
| sort | string | No | ソートカラム（occurred_at, cost, downtime_hours）。デフォルト: occurred_at |
| order | string | No | ソート方向（asc, desc）。デフォルト: desc |
| page | integer | No | ページ番号。デフォルト: 1 |
| per_page | integer | No | 1ページあたりの件数。デフォルト: 20 |

**リクエスト例**:
```
GET /api/reports?keyword=温度センサー&from=2023-01-01&sort=cost&order=desc&page=1
```

#### レスポンス（成功）

```json
{
  "success": true,
  "data": {
    "reports": [
      {
        "id": 1,
        "occurred_at": "2023-12-05",
        "equipment_name": "温度センサー",
        "symptom": "温度センサー故障",
        "cause": null,
        "cost": 50000,
        "downtime_hours": 3.0,
        "failure_mode": "動作不良"
      }
    ],
    "total": 1,
    "page": 1,
    "per_page": 20
  }
}
```

#### レスポンス（エラー）

| ステータス | 意味 | エラーコード |
|-----------|------|------------|
| 400 | 不正なクエリパラメータ | INVALID_PARAM |
| 500 | DB検索失敗 | DB_ERROR |

---

### 4. 詳細表示

- **Method**: GET
- **Path**: `/api/reports/:id`
- **目的**: 指定IDの故障レコードの全項目を取得する
- **対応テーブル**: failure_reports（READ）, failure_modes（JOIN）

#### リクエスト

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| id | integer (path) | Yes | 故障レコードID |

#### レスポンス（成功）

```json
{
  "success": true,
  "data": {
    "id": 1,
    "original_text": "2023年12月5日、温度センサー故障。停止3時間、部品代5万円",
    "occurred_at": "2023-12-05",
    "equipment_name": "温度センサー",
    "symptom": "温度センサー故障",
    "cause": null,
    "action_taken": null,
    "cost": 50000,
    "downtime_hours": 3.0,
    "failure_mode": "動作不良",
    "source": "manual",
    "created_at": "2026-02-18T10:00:00Z"
  }
}
```

#### レスポンス（エラー）

| ステータス | 意味 | エラーコード |
|-----------|------|------------|
| 404 | 指定IDのレコードが存在しない | NOT_FOUND |
| 500 | DB検索失敗 | DB_ERROR |

---

### 5. サンプルデータ投入

- **Method**: POST
- **Path**: `/api/reports/sample`
- **目的**: デモ用サンプル故障報告テキストを一括でLLM構造化・保存する
- **対応テーブル**: failure_reports（INSERT）, failure_modes（READ/INSERT）

#### リクエスト

パラメータなし（サーバー側で事前定義されたサンプルデータを使用）

#### レスポンス（成功）

```json
{
  "success": true,
  "data": {
    "inserted_count": 15,
    "message": "15件のサンプルデータを投入しました"
  }
}
```

#### レスポンス（エラー）

| ステータス | 意味 | エラーコード |
|-----------|------|------------|
| 500 | LLM API呼び出し失敗 | LLM_API_ERROR |
| 500 | DB保存失敗 | DB_ERROR |

---

### 6. サマリー統計（KPI）

- **Method**: GET
- **Path**: `/api/dashboard/summary`
- **目的**: 総故障件数・総コスト・平均停止時間のKPIを返す
- **対応テーブル**: failure_reports（READ）

#### リクエスト（クエリパラメータ）

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| from | string (date) | No | 期間フィルタ開始日 |
| to | string (date) | No | 期間フィルタ終了日 |
| equipment_name | string | No | 設備名フィルタ |
| failure_mode_id | integer | No | 故障モードIDフィルタ |

#### レスポンス（成功）

```json
{
  "success": true,
  "data": {
    "total_count": 150,
    "total_cost": 12500000,
    "avg_downtime_hours": 4.2
  }
}
```

---

### 7. 故障モード別内訳

- **Method**: GET
- **Path**: `/api/dashboard/failure-modes`
- **目的**: 故障モード別の発生件数を返す（円グラフ用）
- **対応テーブル**: failure_reports（READ）, failure_modes（JOIN）

#### リクエスト（クエリパラメータ）

フィルタパラメータはサマリー統計と同一（from, to, equipment_name, failure_mode_id）

#### レスポンス（成功）

```json
{
  "success": true,
  "data": [
    { "failure_mode": "劣化", "count": 45 },
    { "failure_mode": "破損", "count": 32 },
    { "failure_mode": "動作不良", "count": 28 },
    { "failure_mode": "漏れ", "count": 20 },
    { "failure_mode": "過熱", "count": 15 }
  ]
}
```

---

### 8. 月次トレンド

- **Method**: GET
- **Path**: `/api/dashboard/trend`
- **目的**: 月別の故障発生件数を返す（折れ線グラフ用）
- **対応テーブル**: failure_reports（READ）

#### リクエスト（クエリパラメータ）

フィルタパラメータはサマリー統計と同一

#### レスポンス（成功）

```json
{
  "success": true,
  "data": [
    { "month": "2023-01", "count": 12 },
    { "month": "2023-02", "count": 8 },
    { "month": "2023-03", "count": 15 }
  ]
}
```

---

### 9. コストTOP10

- **Method**: GET
- **Path**: `/api/dashboard/cost-top10`
- **目的**: コストが高い設備のランキングTOP10を返す（棒グラフ用）
- **対応テーブル**: failure_reports（READ）

#### リクエスト（クエリパラメータ）

フィルタパラメータはサマリー統計と同一

#### レスポンス（成功）

```json
{
  "success": true,
  "data": [
    { "equipment_name": "コンプレッサーA", "total_cost": 2500000 },
    { "equipment_name": "温度センサーB", "total_cost": 1800000 },
    { "equipment_name": "ポンプC", "total_cost": 1200000 }
  ]
}
```

---

### 10. 示唆出し

- **Method**: POST
- **Path**: `/api/dashboard/suggestions`
- **目的**: 集計データをLLM APIに送信し、改善施策の示唆を生成する
- **対応テーブル**: failure_reports（READ）, failure_modes（READ）

#### リクエスト（クエリパラメータ）

フィルタパラメータはサマリー統計と同一

#### レスポンス（成功）

```json
{
  "success": true,
  "data": {
    "suggestions": [
      "温度センサー故障が全体の30%を占めています。定期交換サイクルを6ヶ月→4ヶ月に短縮することで、年間約180万円のコスト削減が見込まれます。",
      "コンプレッサーAのコストが突出しています。根本原因は劣化が主因のため、予防保全計画の見直しを推奨します。"
    ]
  }
}
```

#### レスポンス（エラー）

| ステータス | 意味 | エラーコード |
|-----------|------|------------|
| 500 | LLM API呼び出し失敗 | LLM_API_ERROR |

---

### 11. 故障モード一覧取得

- **Method**: GET
- **Path**: `/api/failure-modes`
- **目的**: 故障モードマスタの一覧を取得する（フィルタ選択肢・編集ドロップダウン用）
- **対応テーブル**: failure_modes（READ）

#### リクエスト

パラメータなし

#### レスポンス（成功）

```json
{
  "success": true,
  "data": [
    { "id": 1, "name": "劣化" },
    { "id": 2, "name": "破損" },
    { "id": 3, "name": "動作不良" },
    { "id": 4, "name": "漏れ" },
    { "id": 5, "name": "過熱" }
  ]
}
```

---

## 次のステップ

→ 設計フェーズ完了。Build フェーズに進む。
