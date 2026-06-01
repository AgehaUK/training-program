"""
ダッシュボード API ルーター

Presentation Layer
"""
from datetime import date as date_type
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories.dashboard_repository import DashboardRepository
from app.schemas.dashboard import (
    CostRanking,
    CostTop10Response,
    FailureModeBreakdownResponse,
    FailureModeCount,
    MonthlyTrend,
    SummaryData,
    SummaryResponse,
    TrendResponse,
)
from app.services.llm_service import llm_service


class SuggestionsRequest(BaseModel):
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    equipment_name: Optional[str] = None
    failure_mode_id: Optional[int] = None


class SuggestionsResponse(BaseModel):
    success: bool
    data: str

from app.core.auth import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"], dependencies=[Depends(get_current_user)])


def _parse_date(d: Optional[str]) -> Optional[date_type]:
    return date_type.fromisoformat(d) if d else None


@router.get("/summary", response_model=SummaryResponse)
async def get_summary(
    from_date: Optional[str] = Query(None, alias="from_date"),
    to_date: Optional[str] = Query(None, alias="to_date"),
    equipment_name: Optional[str] = Query(None),
    failure_mode_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
) -> SummaryResponse:
    repo = DashboardRepository(db)
    data = repo.get_summary(
        _parse_date(from_date), _parse_date(to_date), equipment_name, failure_mode_id
    )
    return SummaryResponse(success=True, data=SummaryData(**data))


@router.get("/failure-modes", response_model=FailureModeBreakdownResponse)
async def get_failure_mode_breakdown(
    from_date: Optional[str] = Query(None, alias="from_date"),
    to_date: Optional[str] = Query(None, alias="to_date"),
    equipment_name: Optional[str] = Query(None),
    failure_mode_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
) -> FailureModeBreakdownResponse:
    repo = DashboardRepository(db)
    data = repo.get_failure_mode_breakdown(
        _parse_date(from_date), _parse_date(to_date), equipment_name, failure_mode_id
    )
    return FailureModeBreakdownResponse(
        success=True,
        data=[FailureModeCount(**item) for item in data],
    )


@router.get("/trend", response_model=TrendResponse)
async def get_trend(
    from_date: Optional[str] = Query(None, alias="from_date"),
    to_date: Optional[str] = Query(None, alias="to_date"),
    equipment_name: Optional[str] = Query(None),
    failure_mode_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
) -> TrendResponse:
    repo = DashboardRepository(db)
    data = repo.get_monthly_trend(
        _parse_date(from_date), _parse_date(to_date), equipment_name, failure_mode_id
    )
    return TrendResponse(
        success=True,
        data=[MonthlyTrend(**item) for item in data],
    )


@router.post("/suggestions", response_model=SuggestionsResponse)
async def get_suggestions(
    request: SuggestionsRequest,
    db: Session = Depends(get_db),
) -> SuggestionsResponse:
    repo = DashboardRepository(db)
    summary = repo.get_summary(
        _parse_date(request.from_date), _parse_date(request.to_date),
        request.equipment_name, request.failure_mode_id,
    )
    failure_modes = repo.get_failure_mode_breakdown(
        _parse_date(request.from_date), _parse_date(request.to_date),
        request.equipment_name, request.failure_mode_id,
    )
    trend = repo.get_monthly_trend(
        _parse_date(request.from_date), _parse_date(request.to_date),
        request.equipment_name, request.failure_mode_id,
    )
    try:
        text = llm_service.generate_suggestions(summary, failure_modes, trend)
    except Exception as e:
        raise HTTPException(status_code=500, detail={"code": "LLM_ERROR", "message": str(e)})
    return SuggestionsResponse(success=True, data=text)


@router.get("/cost-top10", response_model=CostTop10Response)
async def get_cost_top10(
    from_date: Optional[str] = Query(None, alias="from_date"),
    to_date: Optional[str] = Query(None, alias="to_date"),
    equipment_name: Optional[str] = Query(None),
    failure_mode_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
) -> CostTop10Response:
    repo = DashboardRepository(db)
    data = repo.get_cost_top10(
        _parse_date(from_date), _parse_date(to_date), equipment_name, failure_mode_id
    )
    return CostTop10Response(
        success=True,
        data=[CostRanking(**item) for item in data],
    )
