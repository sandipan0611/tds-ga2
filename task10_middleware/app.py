import os
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

EMAIL = "24f2000793@ds.study.iitm.ac.in"
ALLOWED_ORIGIN = "https://app-i0zto9.example.com"
EXAM_PAGE_ORIGIN = "https://exam.sanand.workers.dev"

B = 14  # requests per window
WINDOW = 10

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN, EXAM_PAGE_ORIGIN, "https://tds.s-anand.net"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

RATE_BUCKETS: dict = {}


@app.middleware("http")
async def context_and_rate_limit(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)

    client_id = request.headers.get("X-Client-Id", "anonymous")
    now = time.time()
    bucket = RATE_BUCKETS.setdefault(client_id, [])
    bucket[:] = [t for t in bucket if now - t < WINDOW]

    request_id = request.headers.get("X-Request-ID") or request.headers.get("x-request-id") or str(uuid.uuid4())

    if len(bucket) >= B:
        origin = request.headers.get("Origin")
        headers = {
            "X-Request-ID": request_id,
        }
        if origin in [ALLOWED_ORIGIN, EXAM_PAGE_ORIGIN, "https://tds.s-anand.net"]:
            headers["Access-Control-Allow-Origin"] = origin
            headers["Access-Control-Allow-Headers"] = "*"
            headers["Access-Control-Allow-Methods"] = "*"
            headers["Access-Control-Expose-Headers"] = "X-Request-ID, Retry-After"
        return JSONResponse(
            status_code=429, 
            content={"detail": "rate limit exceeded"},
            headers=headers
        )
        
    bucket.append(now)
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    
    # Expose X-Request-ID header to the browser's CORS request
    origin = request.headers.get("Origin")
    if origin in [ALLOWED_ORIGIN, EXAM_PAGE_ORIGIN, "https://tds.s-anand.net"]:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Expose-Headers"] = "X-Request-ID, Retry-After"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"
    return response


@app.get("/ping")
async def ping(request: Request):
    return {"email": EMAIL, "request_id": request.state.request_id}
