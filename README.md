# API Rate Limiter Service

A FastAPI application that enforces per-client, per-endpoint request rate limits using a sliding-window algorithm, backed by PostgreSQL.

## Features
- **Sliding-Window Rate Limiting**: Accurately tracks requests over a rolling time window to prevent boundary-bursts.
- **In-Memory Cache**: Briefly caches rules to reduce database load.
- **Background Cleanup**: Automatically deletes old request logs to save space.

## Setup & Running

1. **Install Dependencies**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Database Setup**
   Make sure PostgreSQL is running. Copy `.env.example` to `.env` and update your database credentials.

3. **Run the Server**
   ```bash
   uvicorn app.main:app --reload
   ```

## Usage Examples

**1. Create a Rate Limit Rule**
```bash
curl -X 'POST' 'http://localhost:8000/api/rules' \
  -H 'Content-Type: application/json' \
  -d '{
  "client_id": "client_123",
  "endpoint_pattern": "/demo/orders*",
  "max_requests": 2,
  "window_seconds": 60,
  "plan_tier": "FREE"
}'
```

**2. Test the Rate Limit**
```bash
curl -i -H "X-API-Key: client_123" http://localhost:8000/demo/orders
```
Run this repeatedly. After 2 requests, you will receive a `429 Too Many Requests` error.
