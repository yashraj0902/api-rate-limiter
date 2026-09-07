from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.services.rule_cache import rule_cache
from app.services.sliding_window import get_window_count_and_oldest, log_request
import datetime
import math

class RateLimiterMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith("/demo"):
            return await call_next(request)

        client_id = request.headers.get("X-API-Key")
        if not client_id:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing X-API-Key header"}
            )

        endpoint = request.url.path

        # 2 & 3. Get rules from cache and find best match
        rules = await rule_cache.get_rules(client_id)
        rule = rule_cache.match_rule(rules, endpoint)

        if not rule:
            return await call_next(request)

        # 4. Compute sliding window count
        count, oldest_timestamp = await get_window_count_and_oldest(
            client_id, endpoint, rule.window_seconds
        )

        now = datetime.datetime.utcnow()
        reset_seconds = rule.window_seconds
        if oldest_timestamp:
            elapsed = (now - oldest_timestamp).total_seconds()
            reset_seconds = max(0, int(math.ceil(rule.window_seconds - elapsed)))

        # 5. Check if limit exceeded
        if count >= rule.max_requests:
            headers = {
                "X-RateLimit-Limit": str(rule.max_requests),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_seconds)
            }
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers=headers
            )

        # 6. Log request and proceed
        await log_request(client_id, endpoint)
        
        response = await call_next(request)
        
        # Attach headers
        response.headers["X-RateLimit-Limit"] = str(rule.max_requests)
        remaining = max(0, rule.max_requests - count - 1)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_seconds)

        return response
