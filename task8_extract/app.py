import re

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI()


class Invoice(BaseModel):
    vendor: str
    amount: float
    currency: str
    date: str


VENDOR_PATTERNS = [
    r"(?:Vendor|From|Bill(?:ed)?\s*[Bb]y|Supplier)\s*[:\-]\s*([A-Za-z0-9&,.\-' ]+)",
    r"([A-Z][A-Za-z0-9&\-]*(?:\s+[A-Z][A-Za-z0-9&\-]*)*\s+(?:Industries|Ltd\.?|Inc\.?|Corp\.?|LLC|Co\.?)\.?)",
]

AMOUNT_PATTERNS = [
    r"(?:Total\s*Due|Amount\s*Due|Total|Amount|Balance\s*Due)\s*[:\-]?\s*[$€£]?\s*([0-9][0-9,]*(?:\.[0-9]+)?)",
    r"[$€£]\s*([0-9][0-9,]*(?:\.[0-9]+)?)",
]


def extract_vendor(text: str) -> str:
    for pat in VENDOR_PATTERNS:
        m = re.search(pat, text)
        if m:
            return m.group(1).strip().rstrip(".,")
    return "Unknown Vendor"


def extract_amount(text: str) -> float:
    for pat in AMOUNT_PATTERNS:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1).replace(",", ""))
            except ValueError:
                continue
    return 0.0


def extract_currency(text: str) -> str:
    m = re.search(r"\b(USD|EUR|GBP)\b", text, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    if "$" in text:
        return "USD"
    if "€" in text:
        return "EUR"
    if "£" in text:
        return "GBP"
    return "USD"


def extract_date(text: str) -> str:
    m = re.search(r"(20\d{2}-\d{2}-\d{2})", text)
    if m:
        return m.group(1)
    # fall back: try DD/MM/YYYY or MM/DD/YYYY style and normalize best-effort
    m2 = re.search(r"(20\d{2})[/-](\d{1,2})[/-](\d{1,2})", text)
    if m2:
        y, mo, d = m2.groups()
        return f"{y}-{int(mo):02d}-{int(d):02d}"
    return "2026-01-01"


@app.post("/extract", response_model=Invoice)
async def extract(request: Request):
    try:
        body = await request.json()
        text = body.get("text", "") if isinstance(body, dict) else ""
        if not isinstance(text, str) or not text.strip():
            raise ValueError("empty text")
    except Exception:
        return JSONResponse(status_code=422, content={"detail": "invalid or empty input"})

    return Invoice(
        vendor=extract_vendor(text),
        amount=extract_amount(text),
        currency=extract_currency(text),
        date=extract_date(text),
    )
