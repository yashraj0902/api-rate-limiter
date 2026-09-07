from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Index
from app.database import Base

class RateLimitRule(Base):
    __tablename__ = "rate_limit_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String, index=True, nullable=False)
    endpoint_pattern = Column(String, nullable=False)
    max_requests = Column(Integer, nullable=False)
    window_seconds = Column(Integer, nullable=False)
    plan_tier = Column(String, default="FREE", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_rule_client_endpoint', 'client_id', 'endpoint_pattern'),
    )

class RequestLog(Base):
    __tablename__ = "request_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String, index=True, nullable=False)
    endpoint = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)

    __table_args__ = (
        Index('idx_log_client_endpoint_time', 'client_id', 'endpoint', 'timestamp'),
    )
