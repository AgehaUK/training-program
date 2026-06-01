from typing import Dict, List, Optional

from pydantic import BaseModel


class ReportCreateRequest(BaseModel):
    original_text: str
    occurred_at: str  # "YYYY-MM-DD"
    equipment_name: str
    symptom: str
    cause: Optional[str] = None
    action_taken: Optional[str] = None
    cost: Optional[int] = None
    downtime_hours: Optional[float] = None
    failure_mode: str


class ReportCreateResponse(BaseModel):
    success: bool
    data: Dict


class FailureModeItem(BaseModel):
    id: int
    name: str


class FailureModeListResponse(BaseModel):
    success: bool
    data: List[FailureModeItem]


class SampleInsertResponse(BaseModel):
    success: bool
    data: Dict


class CsvImportResponse(BaseModel):
    success: bool
    data: Dict
