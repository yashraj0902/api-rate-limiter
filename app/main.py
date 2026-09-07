from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import delete
from datetime import datetime, timedelta
import asyncio
from contextlib import asynccontextmanager

from app.database import engine, Base, AsyncSessionLocal
from app.models import RequestLog
from app.middleware.rate_limiter import RateLimiterMiddleware
from app.routers import rules, usage, demo


# Background task for cleanup
async def cleanup_request_logs():
    """
    Periodically clean up old RequestLog rows.
    We use 1 hour as a safe default for maximum window size if not tracking dynamically.
    """
    cutoff = datetime.utcnow() - timedelta(hours=1)
    async with AsyncSessionLocal() as session:
        stmt = delete(RequestLog).where(RequestLog.timestamp < cutoff)
        await session.execute(stmt)
        await session.commit()

scheduler = AsyncIOScheduler()
scheduler.add_job(
    cleanup_request_logs,
    trigger=IntervalTrigger(minutes=15),
    id='cleanup_request_logs_job',
    name='Clean up old request logs',
    replace_existing=True
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    scheduler.start()
    yield
    # Shutdown
    scheduler.shutdown()

app = FastAPI(
    title="API Rate Limiter Service",
    description="A FastAPI application that enforces per-client, per-endpoint request rate limits using a sliding-window algorithm.",
    version="1.0.0",
    lifespan=lifespan
)

# Custom exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        errors.append({
            "loc": error["loc"],
            "msg": error["msg"],
            "type": error["type"]
        })
    return JSONResponse(
        status_code=400,
        content={"detail": "Invalid input", "errors": errors}
    )

app.add_middleware(RateLimiterMiddleware)

app.include_router(rules.router)
app.include_router(usage.router)
app.include_router(demo.router)

@app.get("/api/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok"}
