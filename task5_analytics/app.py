from typing import List, Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

EMAIL = "24f2000793@ds.study.iitm.ac.in"
API_KEY = "ak_enh1nivvnkjbefjc0kco5qx0"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Event(BaseModel):
    user: str
    amount: float
    ts: int


class Batch(BaseModel):
    events: List[Event]


@app.post("/analytics")
async def analytics(batch: Batch, x_api_key: Optional[str] = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="unauthorized")

    events = batch.events
    total_events = len(events)
    unique_users = len({e.user for e in events})

    positive_totals: dict = {}
    for e in events:
        if e.amount > 0:
            positive_totals[e.user] = positive_totals.get(e.user, 0.0) + e.amount

    revenue = sum(positive_totals.values())
    top_user = max(positive_totals, key=positive_totals.get) if positive_totals else None

    return {
        "email": EMAIL,
        "total_events": total_events,
        "unique_users": unique_users,
        "revenue": revenue,
        "top_user": top_user,
    }
