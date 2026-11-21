from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

PriorityType = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
StatusType = Literal["OPEN", "IN_PROGRESS", "BLOCKED", "DONE", "CANCELLED"]


class WorkOrderCreate(BaseModel):
    code: str = Field(..., min_length=3, max_length=40)
    title: str = Field(..., min_length=3, max_length=150)
    area: str = Field(..., min_length=2, max_length=80)
    priority: PriorityType = "MEDIUM"
    description: Optional[str] = None


class StatusTransition(BaseModel):
    new_status: StatusType
    note: Optional[str] = Field(default=None, max_length=255)
    changed_by: str = Field(default="analyst", min_length=2, max_length=80)


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    previous_status: Optional[str]
    new_status: str
    note: Optional[str]
    changed_by: str
    changed_at: datetime


class WorkOrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    title: str
    area: str
    priority: str
    status: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime


class WorkOrderDetail(WorkOrderRead):
    audit_logs: List[AuditLogRead] = []
