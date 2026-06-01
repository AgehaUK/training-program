from typing import Optional

from pydantic import BaseModel, field_validator


class StructurizeRequest(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def text_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must not be empty")
        return v


class StructurizedResult(BaseModel):
    occurred_at: Optional[str] = None
    equipment_name: Optional[str] = None
    symptom: Optional[str] = None
    cause: Optional[str] = None
    action_taken: Optional[str] = None
    cost: Optional[int] = None
    downtime_hours: Optional[float] = None
    failure_mode: Optional[str] = None


class StructurizeResponse(BaseModel):
    success: bool
    data: StructurizedResult
