from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.database import get_db
from app.models import RateLimitRule
from app.schemas import RateLimitRuleCreate, RateLimitRuleUpdate, RateLimitRuleResponse
from app.services.rule_cache import rule_cache

router = APIRouter(prefix="/api/rules", tags=["Rules"])

@router.post("", response_model=RateLimitRuleResponse, status_code=status.HTTP_201_CREATED, summary="Create a rate limit rule")
async def create_rule(rule_in: RateLimitRuleCreate, db: AsyncSession = Depends(get_db)):
    """Create a new rate limit rule for a client ID."""
    db_rule = RateLimitRule(
        client_id=rule_in.client_id,
        endpoint_pattern=rule_in.endpoint_pattern,
        max_requests=rule_in.max_requests,
        window_seconds=rule_in.window_seconds,
        plan_tier=rule_in.plan_tier.value
    )
    db.add(db_rule)
    await db.commit()
    await db.refresh(db_rule)
    
    # Invalidate cache for this client
    await rule_cache.invalidate(rule_in.client_id)
    
    return db_rule

@router.get("/{client_id}", response_model=List[RateLimitRuleResponse], summary="List all rules for a client")
async def get_rules(client_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve all rate limit rules associated with a specific client ID."""
    stmt = select(RateLimitRule).where(RateLimitRule.client_id == client_id)
    result = await db.execute(stmt)
    rules = result.scalars().all()
    return rules

@router.put("/{rule_id}", response_model=RateLimitRuleResponse, summary="Update a rule")
async def update_rule(rule_id: int, rule_in: RateLimitRuleUpdate, db: AsyncSession = Depends(get_db)):
    """Update an existing rate limit rule."""
    stmt = select(RateLimitRule).where(RateLimitRule.id == rule_id)
    result = await db.execute(stmt)
    db_rule = result.scalar_one_or_none()
    
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")
        
    update_data = rule_in.model_dump(exclude_unset=True)
    if "plan_tier" in update_data and update_data["plan_tier"] is not None:
        update_data["plan_tier"] = update_data["plan_tier"].value
        
    for key, value in update_data.items():
        setattr(db_rule, key, value)
        
    await db.commit()
    await db.refresh(db_rule)
    
    # Invalidate cache
    await rule_cache.invalidate(db_rule.client_id)
    
    return db_rule

@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a rule")
async def delete_rule(rule_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a rate limit rule by ID."""
    stmt = select(RateLimitRule).where(RateLimitRule.id == rule_id)
    result = await db.execute(stmt)
    db_rule = result.scalar_one_or_none()
    
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")
        
    client_id = db_rule.client_id
    await db.delete(db_rule)
    await db.commit()
    
    # Invalidate cache
    await rule_cache.invalidate(client_id)
