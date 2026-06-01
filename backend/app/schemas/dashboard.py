from typing import List

from pydantic import BaseModel


class SummaryData(BaseModel):
    total_count: int
    total_cost: int
    avg_downtime_hours: float


class SummaryResponse(BaseModel):
    success: bool
    data: SummaryData


class FailureModeCount(BaseModel):
    failure_mode: str
    count: int


class FailureModeBreakdownResponse(BaseModel):
    success: bool
    data: List[FailureModeCount]


class MonthlyTrend(BaseModel):
    month: str
    count: int


class TrendResponse(BaseModel):
    success: bool
    data: List[MonthlyTrend]


class CostRanking(BaseModel):
    equipment_name: str
    total_cost: int


class CostTop10Response(BaseModel):
    success: bool
    data: List[CostRanking]
