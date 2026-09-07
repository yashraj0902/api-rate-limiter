# API Rate Limiter Service

A production-ready FastAPI application that enforces per-client, per-endpoint request rate limits using a sliding-window algorithm, similar to real API platforms like Stripe or GitHub.

This project is built using:
- **FastAPI** for high performance and auto-generated OpenAPI docs.
- **PostgreSQL** for persistent storage.
- **SQLAlchemy (asyncpg)** for asynchronous ORM.
- **Pydantic** for validation.

## Architecture & Design Decisions

### Why Sliding Window?
A simple **fixed-window** algorithm (e.g., reset counter every minute) suffers from the "boundary-burst" problem. If a user is allowed 10 requests/minute, they can send 10 requests at 12:00:59 and another 10 requests at 12:01:01, resulting in 20 requests in a 2-second span. 

The **sliding-window log** algorithm prevents this by recording the exact timestamp of every request. The rate limit is strictly enforced based on the number of requests in the rolling `window_seconds` preceding the current time.

### In-Memory Rule Cache
Checking the database for rate-limit rules on every request adds significant latency. To optimize this:
- An in-memory cache `RuleCache` is implemented inside the FastAPI middleware.
- Rules are cached with a short TTL (Time-to-Live), avoiding DB round-trips for the majority of requests.
- When rules are updated via the REST API, the cache is selectively invalidated for that specific client.

### Background Cleanup Task
Since every request creates a log entry in `RequestLog`, the database can grow unbounded.
- An asynchronous `APScheduler` background job runs every 15 minutes.
- It deletes all `RequestLog` rows older than a safe threshold (e.g., 1 hour), ensuring the database size remains stable.

```text
+-------------------+       +-------------------+       +-------------------+
|  Client Request   | ----> |   FastAPI App     | ----> |  Rule Cache (RAM) |
| (X-API-Key: xyz)  |       |   (Middleware)    |       +-------------------+
+-------------------+       +-------------------+                |
                                     |                           v
                                     v                  +-------------------+
                            +-------------------+       | PostgreSQL (DB)   |
                            |   Demo Router     |       | - RateLimitRules  |
                            |   Rules Router    | <---> | - RequestLogs     |
                            +-------------------+       +-------------------+
```

## Setup & Running

1. **Start PostgreSQL Database**
   Ensure you have a PostgreSQL server running locally or remotely. Create a database named `rate_limiter`.

2. **Install Dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Environment Variables**
   Create a `.env` file (optional, defaults to docker compose credentials):
   ```ini
   DATABASE_URL=postgresql+asyncpg://limiter_user:limiter_password@localhost:5432/rate_limiter
   ```

4. **Run the Server**
   ```bash
   uvicorn app.main:app --reload
   ```

## API Documentation

Once the server is running, visit http://localhost:8000/docs to view the Swagger UI.

## Examples

### 1. Create a Rate Limit Rule
```bash
curl -X 'POST' \
  'http://localhost:8000/api/rules' \
  -H 'Content-Type: application/json' \
  -d '{
  "client_id": "client_123",
  "endpoint_pattern": "/demo/orders*",
  "max_requests": 2,
  "window_seconds": 60,
  "plan_tier": "FREE"
}'
```

### 2. Make Requests to the Demo Endpoint
```bash
# Request 1 (Success)
curl -i -H "X-API-Key: client_123" http://localhost:8000/demo/orders

# Request 2 (Success)
curl -i -H "X-API-Key: client_123" http://localhost:8000/demo/orders

# Request 3 (Rate Limited - 429 Too Many Requests)
curl -i -H "X-API-Key: client_123" http://localhost:8000/demo/orders
```
Notice the headers on the 429 response:
- `X-RateLimit-Limit: 2`
- `X-RateLimit-Remaining: 0`
- `X-RateLimit-Reset: <seconds until oldest request expires>`
