import time
import uuid

from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware

EMAIL = "24f2000793@ds.study.iitm.ac.in"
ALLOWED_ORIGIN = "https://dash-cbnlp2.example.com"

app = FastAPI()

# CORSMiddleware automatically handles preflight (OPTIONS) requests:
# - returns ACAO header only for the allowed origin
# - returns no ACAO header (and effectively rejects) any other origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_tracing_headers(request: Request, call_next):
    start = time.perf_counter()
    request_id = str(uuid.uuid4())
    response = await call_next(request)
    elapsed = time.perf_counter() - start
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{elapsed:.6f}"
    return response


@app.get("/stats")
async def stats(values: str = Query(...)):
    nums = [int(v.strip()) for v in values.split(",") if v.strip() != ""]
    count = len(nums)
    total = sum(nums)
    mn = min(nums) if nums else 0
    mx = max(nums) if nums else 0
    mean = (total / count) if count else 0.0
    return {
        "email": EMAIL,
        "count": count,
        "sum": total,
        "min": mn,
        "max": mx,
        "mean": mean,
    }
