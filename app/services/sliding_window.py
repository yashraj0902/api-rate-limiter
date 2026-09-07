from datetime import datetime, timedelta
from sqlalchemy import select, func
from app.models import RequestLog
from app.database import AsyncSessionLocal
import math

async def get_window_count_and_oldest(client_id: str, endpoint: str, window_seconds: int) -> tuple[int, datetime]:
    """
    Returns the count of requests in the sliding window and the timestamp of the oldest request in that window.
    """
    now = datetime.utcnow()
    window_start = now - timedelta(seconds=window_seconds)

    async with AsyncSessionLocal() as session:
        # Count requests
        count_stmt = select(func.count(RequestLog.id)).where(
            RequestLog.client_id == client_id,
            RequestLog.endpoint == endpoint,
            RequestLog.timestamp >= window_start
        )
        count_result = await session.execute(count_stmt)
        count = count_result.scalar() or 0

        # Oldest timestamp to compute reset
        oldest_stmt = select(func.min(RequestLog.timestamp)).where(
            RequestLog.client_id == client_id,
            RequestLog.endpoint == endpoint,
            RequestLog.timestamp >= window_start
        )
        oldest_result = await session.execute(oldest_stmt)
        oldest_timestamp = oldest_result.scalar()

        return count, oldest_timestamp

async def log_request(client_id: str, endpoint: str):
    async with AsyncSessionLocal() as session:
        log_entry = RequestLog(client_id=client_id, endpoint=endpoint)
        session.add(log_entry)
        await session.commit()
