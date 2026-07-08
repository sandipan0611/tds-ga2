import os

import redis.asyncio as redis
from fastapi import FastAPI

app = FastAPI()

r = redis.Redis(
    host=os.environ.get("REDIS_HOST", "redis"),
    port=int(os.environ.get("REDIS_PORT", 6379)),
    decode_responses=True,
)


@app.post("/hit/{key}")
async def hit(key: str):
    count = await r.incr(f"counter:{key}")
    return {"key": key, "count": count}


@app.get("/count/{key}")
async def count(key: str):
    val = await r.get(f"counter:{key}")
    return {"key": key, "count": int(val) if val else 0}


@app.get("/healthz")
async def healthz():
    try:
        pong = await r.ping()
        return {"status": "ok", "redis": "up" if pong else "down"}
    except Exception:
        return {"status": "ok", "redis": "down"}
