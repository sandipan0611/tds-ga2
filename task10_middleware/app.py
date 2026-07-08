import os
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

EMAIL = "24f2000793@ds.study.iitm.ac.in"
ALLOWED_ORIGIN = "https://app-i0zto9.example.com"

# The exam page itself needs to be able to call /ping to verify your service.
# Set EXAM_PAGE_ORIGIN as an env var to the real origin shown on the assignment
# page (e.g. https://tds.s-anand.net) if the grader runs from a different origin.
EXAM_PAGE_ORIGIN = os.environ.get("EXAM_PAGE_ORIGIN", "https://tds.s-anand.net")

B = 14  # requests per window
WINDOW = 10

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN, EXAM_PAGE_ORIGIN],
    allow_methods=["*"],
    allow_headers=["*"],
)

RATE_BUCKETS: dict = {}


@app.middleware("http")
async def context_and_rate_limit(request: Request, call_next):
    client_id = request.headers.get("X-Client-Id", "anonymous")
    now = time.time()
    bucket = RATE_BUCKETS.setdefault(client_id, [])
    bucket[:] = [t for t in bucket if now - t < WINDOW]
    if len(bucket) >= B:
        return JSONResponse(status_code=429, content={"detail": "rate limit exceeded"})
    bucket.append(now)

    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/ping")
async def ping(request: Request):
    return {"email": EMAIL, "request_id": request.state.request_id}
