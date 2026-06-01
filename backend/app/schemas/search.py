from typing import List, Optional

from pydantic import BaseModel


class ReportListItem(BaseModel):
    id: int
    occurred_at: str
    equipment_name: str
    symptom: str
    cause: Optional[str] = None
    cost: Optional[int] = None
    downtime_hours: Optional[float] = None
    failure_mode: Optional[str] = None


class ReportListData(BaseModel):
    reports: List[ReportListItem]
    total: int
    page: int
    per_page: int


class ReportListResponse(BaseModel):
    success: bool
    data: ReportListData


class ReportDetailItem(BaseModel):
    id: int
    original_text: str
    occurred_at: str
    equipment_name: str
    symptom: str
    cause: Optional[str] = None
    action_taken: Optional[str] = None
    cost: Optional[int] = None
    downtime_hours: Optional[float] = None
    failure_mode: Optional[str] = None
    source: str
    created_at: str


class ReportDetailResponse(BaseModel):
    success: bool
    data: ReportDetailItem
