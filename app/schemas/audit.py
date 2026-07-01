from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class AuditLogBase(BaseModel):
    user_id: Optional[uuid.UUID] = Field(None, examples=["user-uuid-1"])
    company_id: Optional[uuid.UUID] = Field(None, examples=["company-uuid-1"])
    entity_type: str = Field(..., max_length=100, examples=["Company"])
    entity_id: Optional[uuid.UUID] = Field(None, examples=["entity-uuid-1"])
    action: str = Field(..., max_length=100, examples=["CREATE"])
    old_values: Optional[Dict[str, Any]] = Field(None, examples=[{"status": "INACTIVE"}])
    new_values: Optional[Dict[str, Any]] = Field(None, examples=[{"status": "ACTIVE"}])
    ip_address: Optional[str] = Field(None, max_length=45, examples=["192.168.1.1"])
    user_agent: Optional[str] = Field(None, max_length=512, examples=["Mozilla/5.0..."])


class AuditLogCreate(AuditLogBase):
    pass


class AuditLogResponse(AuditLogBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    timestamp: datetime


class AuditLogListResponse(BaseModel):
    audit_logs: List[AuditLogResponse]
