from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.schemas import UsageResponse
from app.services.rule_cache import rule_cache
from app.services.sliding_window import get_window_count_and_oldest

router = APIRouter(prefix="/api/usage", tags=["Usage"])

@router.get("/{client_id}", response_model=List[UsageResponse], summary="Get current usage for a client")
async def get_usage(client_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns current request count and remaining quota for each endpoint pattern
    configured for this client.
    """
    rules = await rule_cache.get_rules(client_id)
    usage_list = []
    
    for rule in rules:
        count, _ = await get_window_count_and_oldest(
            client_id, rule.endpoint_pattern, rule.window_seconds
        )
        
        remaining = max(0, rule.max_requests - count)
        
        usage_list.append(UsageResponse(
            endpoint_pattern=rule.endpoint_pattern,
            current_count=count,
            max_requests=rule.max_requests,
            remaining_quota=remaining,
            window_seconds=rule.window_seconds
        ))
        
    return usage_list
