import time
import uuid
from collections import deque

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

EMAIL = "24f2000793@ds.study.iitm.ac.in"

app = FastAPI()

START_TIME = time.time()
REQUEST_COUNT = 0
LOGS = deque(maxlen=2000)


@app.middleware("http")
async def log_and_count(request: Request, call_next):
    global REQUEST_COUNT
    REQUEST_COUNT += 1
    request_id = str(uuid.uuid4())
    response = await call_next(request)
    LOGS.append(
        {
            "level": "info",
            "ts": time.time(),
            "path": request.url.path,
            "request_id": request_id,
        }
    )
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/work")
async def work(n: int = 1):
    total = 0
    for i in range(max(n, 0)):
        total += i
    return {"email": EMAIL, "done": n}


@app.get("/metrics")
async def metrics():
    text = (
        "# HELP http_requests_total Total HTTP requests received\n"
        "# TYPE http_requests_total counter\n"
        f"http_requests_total {REQUEST_COUNT}\n"
    )
    return PlainTextResponse(text)


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "uptime_s": time.time() - START_TIME}


@app.get("/logs/tail")
async def logs_tail(limit: int = 10):
    return list(LOGS)[-limit:]
