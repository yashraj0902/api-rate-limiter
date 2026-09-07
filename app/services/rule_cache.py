import time
from typing import List, Dict, Optional
import asyncio
from sqlalchemy.future import select
from app.models import RateLimitRule
from app.database import AsyncSessionLocal
from app.schemas import RateLimitRuleResponse

class RuleCache:
    def __init__(self, ttl_seconds: int = 30):
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, List[RateLimitRuleResponse]] = {}
        self._last_update: Dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def _fetch_rules_for_client(self, client_id: str) -> List[RateLimitRuleResponse]:
        async with AsyncSessionLocal() as session:
            stmt = select(RateLimitRule).where(RateLimitRule.client_id == client_id)
            result = await session.execute(stmt)
            db_rules = result.scalars().all()
            return [RateLimitRuleResponse.model_validate(r) for r in db_rules]

    async def get_rules(self, client_id: str) -> List[RateLimitRuleResponse]:
        now = time.time()
        async with self._lock:
            last_update = self._last_update.get(client_id, 0)
            if now - last_update > self.ttl_seconds:
                rules = await self._fetch_rules_for_client(client_id)
                self._cache[client_id] = rules
                self._last_update[client_id] = now
            return self._cache.get(client_id, [])

    def match_rule(self, rules: List[RateLimitRuleResponse], endpoint: str) -> Optional[RateLimitRuleResponse]:
        exact_match = None
        wildcard_matches = []
        global_match = None

        for rule in rules:
            pattern = rule.endpoint_pattern
            if pattern == endpoint:
                exact_match = rule
            elif pattern == "*":
                global_match = rule
            elif pattern.endswith("*"):
                prefix = pattern[:-1]
                if endpoint.startswith(prefix):
                    wildcard_matches.append(rule)

        if exact_match:
            return exact_match
        
        if wildcard_matches:
            return max(wildcard_matches, key=lambda r: len(r.endpoint_pattern))
            
        return global_match

    async def invalidate(self, client_id: str):
        async with self._lock:
            if client_id in self._cache:
                del self._cache[client_id]
            if client_id in self._last_update:
                del self._last_update[client_id]

rule_cache = RuleCache(ttl_seconds=30)
