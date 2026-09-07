from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum

class PlanTier(str, Enum):
    FREE = "FREE"
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"

class RateLimitRuleCreate(BaseModel):
    client_id: str = Field(..., min_length=1, description="API client identifier")
    endpoint_pattern: str = Field(..., min_length=1, description="Endpoint pattern, e.g., '/api/orders/*' or '*'")
    max_requests: int = Field(..., gt=0, description="Max allowed requests in the window")
    window_seconds: int = Field(..., gt=0, description="Size of the sliding window in seconds")
    plan_tier: PlanTier = Field(default=PlanTier.FREE, description="Plan tier for this rule")

    class Config:
        json_schema_extra = {
            "example": {
                "client_id": "client_123",
                "endpoint_pattern": "/demo/orders",
                "max_requests": 10,
                "window_seconds": 60,
                "plan_tier": "FREE"
            }
        }

class RateLimitRuleUpdate(BaseModel):
    endpoint_pattern: Optional[str] = Field(None, min_length=1)
    max_requests: Optional[int] = Field(None, gt=0)
    window_seconds: Optional[int] = Field(None, gt=0)
    plan_tier: Optional[PlanTier] = None

class RateLimitRuleResponse(BaseModel):
    id: int
    client_id: str
    endpoint_pattern: str
    max_requests: int
    window_seconds: int
    plan_tier: PlanTier
    created_at: datetime

    class Config:
        from_attributes = True

class UsageResponse(BaseModel):
    endpoint_pattern: str
    current_count: int
    max_requests: int
    remaining_quota: int
    window_seconds: int
