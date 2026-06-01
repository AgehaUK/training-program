"""
故障報告 API ルーター

Presentation Layer
"""
import csv
import io
from datetime import date as date_type
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories.failure_mode_repository import FailureModeRepository
from app.repositories.failure_report_repository import FailureReportRepository
from app.schemas.report import (
    CsvImportResponse,
    FailureModeItem,
    FailureModeListResponse,
    ReportCreateRequest,
    ReportCreateResponse,
    SampleInsertResponse,
)
from app.schemas.search import (
    ReportDetailItem,
    ReportDetailResponse,
    ReportListData,
    ReportListItem,
    ReportListResponse,
)
from app.schemas.structurize import StructurizeRequest, StructurizeResponse, StructurizedResult
from app.services.llm_service import llm_service

from app.core.auth import get_current_user
from app.services.vector_store import vector_store

router = APIRouter(prefix="/api/reports", tags=["reports"], dependencies=[Depends(get_current_user)])
failure_modes_router = APIRouter(prefix="/api/failure-modes", tags=["failure-modes"], dependencies=[Depends(get_current_user)])

# ---------------------------------------------------------------------------
# サンプルテキスト（POST /api/reports/sample 用）
# ---------------------------------------------------------------------------

SAMPLE_TEXTS = [
    "2025年1月10日、コンプレッサーB号機の吐出圧力が規定値を下回り警報発報。バルブパッキン劣化が原因。パッキン交換で対応。停止2時間、費用1.5万円。",
    "2025年2月5日、油圧プレスC号機の油圧シリンダーからオイル漏れ発生。Oリング破損が原因。Oリング交換後復旧。停止6時間、費用3万円。",
    "2025年3月20日、搬送コンベア3号ラインにてチェーン切断。過負荷が原因。チェーン全交換。停止8時間、費用12万円。",
    "2025年4月8日、冷却水ポンプDにて流量低下。インペラー摩耗が原因。ポンプ交換。停止3時間、費用8万円。",
    "2025年5月15日、CNCマシニングセンタE号機の主軸ベアリングに異音。ベアリング摩耗。交換後正常稼働。停止5時間、費用15万円。",
]


# ---------------------------------------------------------------------------
# エンドポイント
# ---------------------------------------------------------------------------


@router.post("/structurize", response_model=StructurizeResponse)
async def structurize(
    request: StructurizeRequest,
    db: Session = Depends(get_db),
) -> StructurizeResponse:
    """自由記述テキストを LLM API で構造化する"""
    mode_repo = FailureModeRepository(db)
    failure_mode_names = [fm.name for fm in mode_repo.get_all()]

    try:
        result = llm_service.structurize(request.text, failure_mode_names)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"code": "LLM_API_ERROR", "message": str(e)},
        )

    return StructurizeResponse(
        success=True,
        data=StructurizedResult(**result.model_dump()),
    )


@router.post("", response_model=ReportCreateResponse)
async def create_report(
    request: ReportCreateRequest,
    db: Session = Depends(get_db),
) -> ReportCreateResponse:
    """構造化済み故障データを DB に保存する"""
    try:
        occurred_at = date_type.fromisoformat(request.occurred_at)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_DATE", "message": "日付形式が不正です（YYYY-MM-DD）"},
        )

    mode_repo = FailureModeRepository(db)
    failure_mode = mode_repo.find_or_create_by_name(request.failure_mode)

    report_repo = FailureReportRepository(db)
    try:
        report = report_repo.create(
            original_text=request.original_text,
            occurred_at=occurred_at,
            equipment_name=request.equipment_name,
            symptom=request.symptom,
            cause=request.cause,
            action_taken=request.action_taken,
            cost=request.cost,
            downtime_hours=request.downtime_hours,
            failure_mode_id=failure_mode.id,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"code": "DB_ERROR", "message": str(e)},
        )

    # FAISSインデックスに追加
    try:
        parts = [
            request.equipment_name or "",
            request.symptom or "",
            request.cause or "",
            request.action_taken or "",
        ]
        index_text = " ".join(p for p in parts if p)
        vector_store.add(report.id, index_text)
    except Exception:
        pass  # インデックス失敗は無視（検索精度に影響するが保存は成功）

    return ReportCreateResponse(
        success=True,
        data={"id": report.id, "message": "故障レコードを保存しました"},
    )


@router.post("/sample", response_model=SampleInsertResponse)
async def insert_sample(
    db: Session = Depends(get_db),
) -> SampleInsertResponse:
    """事前定義されたサンプルテキストを構造化・保存する"""
    mode_repo = FailureModeRepository(db)
    failure_mode_names = [fm.name for fm in mode_repo.get_all()]

    report_repo = FailureReportRepository(db)
    inserted = 0

    for text in SAMPLE_TEXTS:
        try:
            result = llm_service.structurize(text, failure_mode_names)
            data = result.model_dump()

            occurred_at_str = data.get("occurred_at")
            try:
                occurred_at = date_type.fromisoformat(occurred_at_str) if occurred_at_str else date_type.today()
            except ValueError:
                occurred_at = date_type.today()

            failure_mode_name = data.get("failure_mode") or "その他"
            failure_mode = mode_repo.find_or_create_by_name(failure_mode_name)

            report = report_repo.create(
                original_text=text,
                occurred_at=occurred_at,
                equipment_name=data.get("equipment_name") or "不明",
                symptom=data.get("symptom") or text[:50],
                cause=data.get("cause"),
                action_taken=data.get("action_taken"),
                cost=data.get("cost"),
                downtime_hours=data.get("downtime_hours"),
                failure_mode_id=failure_mode.id,
                source="sample",
            )
            index_text = " ".join(p for p in [
                data.get("equipment_name") or "",
                data.get("symptom") or "",
                data.get("cause") or "",
                data.get("action_taken") or "",
            ] if p)
            vector_store.add(report.id, index_text)
            inserted += 1
        except Exception:
            continue

    return SampleInsertResponse(
        success=True,
        data={"inserted_count": inserted, "message": f"{inserted}件のサンプルデータを投入しました"},
    )


# ---------------------------------------------------------------------------
# CSV インポート
# ---------------------------------------------------------------------------

# CSVカラム → DBフィールドのマッピング定義
_CSV_COLUMN_MAP = {
    "発生日時": "occurred_at",
    "設備名": "equipment_name",
    "現象記述": "symptom",
    "原因記述": "cause",
    "処置記述": "action_taken",
    "合計コスト_円": "cost",
    "停止時間_分": "downtime_minutes",
    "トラブル区分": "failure_mode",
}


@router.post("/import-csv", response_model=CsvImportResponse)
async def import_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> CsvImportResponse:
    """CSVファイルから故障レポートを一括インポートする"""
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail={"code": "INVALID_FILE", "message": ".csvファイルをアップロードしてください"})

    content = await file.read()
    try:
        text_content = content.decode("utf-8-sig")  # BOM付きUTF-8にも対応
    except UnicodeDecodeError:
        text_content = content.decode("shift_jis", errors="replace")

    mode_repo = FailureModeRepository(db)
    report_repo = FailureReportRepository(db)

    inserted = 0
    skipped = 0
    errors: list[str] = []
    faiss_batch: list[tuple[int, str]] = []

    reader = csv.DictReader(io.StringIO(text_content))
    for i, row in enumerate(reader, start=2):  # 2行目からデータ開始
        try:
            # 発生日時 → date
            raw_date = row.get("発生日時", "").strip()
            if not raw_date:
                skipped += 1
                continue
            occurred_at = date_type.fromisoformat(raw_date.split(" ")[0])

            # 設備名
            equipment_name = row.get("設備名", "").strip() or "不明"

            # 症状・原因・対策
            symptom = row.get("現象記述", "").strip() or "不明"
            cause = row.get("原因記述", "").strip() or None
            action_taken = row.get("処置記述", "").strip() or None

            # コスト（円）
            cost_str = row.get("合計コスト_円", "").strip()
            cost = int(float(cost_str)) if cost_str else None

            # 停止時間（分 → 時間に変換）
            downtime_str = row.get("停止時間_分", "").strip()
            downtime_hours = round(float(downtime_str) / 60, 2) if downtime_str else None

            # 故障モード（トラブル区分を使用）
            failure_mode_name = row.get("トラブル区分", "").strip() or "その他"
            failure_mode = mode_repo.find_or_create_by_name(failure_mode_name)

            # original_text（現象・原因・対策を結合）
            parts = [p for p in [symptom, cause, action_taken] if p]
            original_text = " / ".join(parts)

            report = report_repo.create(
                original_text=original_text,
                occurred_at=occurred_at,
                equipment_name=equipment_name,
                symptom=symptom,
                cause=cause,
                action_taken=action_taken,
                cost=cost,
                downtime_hours=downtime_hours,
                failure_mode_id=failure_mode.id,
                source="csv_import",
            )
            faiss_batch.append((report.id, " ".join(p for p in [equipment_name, symptom, cause or "", action_taken or ""] if p)))
            inserted += 1
        except Exception as e:
            skipped += 1
            if len(errors) < 5:
                errors.append(f"行{i}: {str(e)}")

    # FAISSインデックスをまとめて更新（1回だけ保存）
    try:
        vector_store.add_bulk(faiss_batch)
    except Exception:
        pass

    return CsvImportResponse(
        success=True,
        data={
            "inserted_count": inserted,
            "skipped_count": skipped,
            "message": f"{inserted}件をインポートしました（スキップ: {skipped}件）",
            "errors": errors,
        },
    )


# ---------------------------------------------------------------------------
# 検索一覧・詳細
# ---------------------------------------------------------------------------


@router.get("", response_model=ReportListResponse)
async def search_reports(
    keyword: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    failure_mode_id: Optional[int] = Query(None),
    cost_min: Optional[int] = Query(None),
    cost_max: Optional[int] = Query(None),
    sort: str = Query("occurred_at"),
    order: str = Query("desc"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> ReportListResponse:
    """故障レポートをキーワード検索・フィルタリング・ページネーションで一覧取得する"""
    from_d = date_type.fromisoformat(from_date) if from_date else None
    to_d = date_type.fromisoformat(to_date) if to_date else None

    repo = FailureReportRepository(db)

    # キーワードがある場合はFAISSベクトル検索を使用
    if keyword:
        try:
            similar_ids = vector_store.search(keyword, top_k=200)
            reports, total = repo.search_by_ids(
                ids=similar_ids,
                from_date=from_d,
                to_date=to_d,
                failure_mode_id=failure_mode_id,
                cost_min=cost_min,
                cost_max=cost_max,
                page=page,
                per_page=per_page,
            )
        except Exception:
            # FAISSが使えない場合はSQLフォールバック
            reports, total = repo.search(
                keyword=keyword,
                from_date=from_d,
                to_date=to_d,
                failure_mode_id=failure_mode_id,
                cost_min=cost_min,
                cost_max=cost_max,
                sort=sort,
                order=order,
                page=page,
                per_page=per_page,
            )
    else:
        reports, total = repo.search(
            keyword=None,
            from_date=from_d,
            to_date=to_d,
            failure_mode_id=failure_mode_id,
            cost_min=cost_min,
            cost_max=cost_max,
            sort=sort,
            order=order,
            page=page,
            per_page=per_page,
        )

    items = [
        ReportListItem(
            id=r.id,
            occurred_at=str(r.occurred_at),
            equipment_name=r.equipment_name,
            symptom=r.symptom,
            cause=r.cause,
            cost=r.cost,
            downtime_hours=r.downtime_hours,
            failure_mode=r.failure_mode.name if r.failure_mode else None,
        )
        for r in reports
    ]

    return ReportListResponse(
        success=True,
        data=ReportListData(reports=items, total=total, page=page, per_page=per_page),
    )


@router.get("/{report_id}", response_model=ReportDetailResponse)
async def get_report(
    report_id: int,
    db: Session = Depends(get_db),
) -> ReportDetailResponse:
    """指定 ID の故障レポート詳細を返す"""
    repo = FailureReportRepository(db)
    report = repo.find_by_id(report_id)
    if report is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "指定されたレコードが見つかりません"},
        )

    return ReportDetailResponse(
        success=True,
        data=ReportDetailItem(
            id=report.id,
            original_text=report.original_text,
            occurred_at=str(report.occurred_at),
            equipment_name=report.equipment_name,
            symptom=report.symptom,
            cause=report.cause,
            action_taken=report.action_taken,
            cost=report.cost,
            downtime_hours=report.downtime_hours,
            failure_mode=report.failure_mode.name if report.failure_mode else None,
            source=report.source,
            created_at=str(report.created_at),
        ),
    )


# ---------------------------------------------------------------------------
# 故障モード一覧
# ---------------------------------------------------------------------------


@failure_modes_router.get("", response_model=FailureModeListResponse)
async def get_failure_modes(
    db: Session = Depends(get_db),
) -> FailureModeListResponse:
    """故障モードマスタの一覧を返す"""
    mode_repo = FailureModeRepository(db)
    modes = mode_repo.get_all()
    return FailureModeListResponse(
        success=True,
        data=[FailureModeItem(id=m.id, name=m.name) for m in modes],
    )
