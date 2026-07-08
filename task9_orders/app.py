import time
import uuid
from typing import Optional

from fastapi import FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

T = 59            # total orders in catalog
R = 18            # requests allowed per 10s window
WINDOW = 10

IDEMPOTENCY_STORE: dict = {}
RATE_BUCKETS: dict = {}


@app.middleware("http")
async def rate_limit_orders(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)
    if request.url.path == "/orders":
        client_id = request.headers.get("X-Client-Id", "anonymous")
        now = time.time()
        bucket = RATE_BUCKETS.setdefault(client_id, [])
        bucket[:] = [t for t in bucket if now - t < WINDOW]
        if len(bucket) >= R:
            return JSONResponse(
                status_code=429,
                content={"detail": "rate limit exceeded"},
                headers={
                    "Retry-After": str(WINDOW),
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "*",
                    "Access-Control-Allow-Headers": "*",
                },
            )
        bucket.append(now)
    return await call_next(request)


@app.post("/orders")
async def create_order(
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
):
    if idempotency_key and idempotency_key in IDEMPOTENCY_STORE:
        return JSONResponse(status_code=201, content=IDEMPOTENCY_STORE[idempotency_key])

    order = {"id": str(uuid.uuid4())}
    if idempotency_key:
        IDEMPOTENCY_STORE[idempotency_key] = order
    return JSONResponse(status_code=201, content=order)


@app.get("/orders")
async def list_orders(limit: int = 10, cursor: Optional[str] = None):
    start = int(cursor) if cursor else 0
    ids = list(range(1, T + 1))
    page_ids = ids[start:start + limit]
    items = [{"id": i} for i in page_ids]
    next_cursor = str(start + limit) if (start + limit) < T else None
    return {"items": items, "next_cursor": next_cursor}
