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

CUR_TOKEN = r"(?:USD|EUR|GBP|[$€£])"
NUM = r"([0-9][0-9,]*(?:\.[0-9]+)?)"

AMOUNT_PATTERNS = [
    # "Total Due: USD 5,980.43" / "Amount Due: $5980.43" / "Total: 5980.43"
    rf"(?:Total\s*Due|Amount\s*Due|Grand\s*Total|Total|Amount|Balance\s*Due|Due)\s*[:\-]?\s*{CUR_TOKEN}?\s*{NUM}",
    # "USD 5980.43" / "$5,980.43" appearing anywhere
    rf"{CUR_TOKEN}\s*{NUM}",
    # "5980.43 USD" / "5,980.43 $"
    rf"{NUM}\s*{CUR_TOKEN}",
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
                val = float(m.group(1).replace(",", ""))
                if val > 0:
                    return val
            except ValueError:
                continue
    # Fallback: no keyword/currency match found — take the largest
    # decimal-looking number in the text (invoice totals are usually
    # the largest and only 2-decimal-place figure present).
    candidates = re.findall(r"[0-9][0-9,]*\.[0-9]{2}\b", text)
    if candidates:
        vals = [float(c.replace(",", "")) for c in candidates]
        return max(vals)
    # Last resort: any integer-looking number
    candidates_int = re.findall(r"\b[0-9]{2,}\b", text)
    if candidates_int:
        return float(max(int(c) for c in candidates_int))
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


MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9, "oct": 10,
    "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}


def extract_date(text: str) -> str:
    m = re.search(r"(20\d{2}-\d{2}-\d{2})", text)
    if m:
        return m.group(1)
    # DD/MM/YYYY or MM/DD/YYYY or YYYY/MM/DD with slashes/dots/dashes
    m2 = re.search(r"(20\d{2})[/.-](\d{1,2})[/.-](\d{1,2})", text)
    if m2:
        y, mo, d = m2.groups()
        return f"{y}-{int(mo):02d}-{int(d):02d}"
    m3 = re.search(r"(\d{1,2})[/.-](\d{1,2})[/.-](20\d{2})", text)
    if m3:
        a, b, y = m3.groups()
        return f"{y}-{int(a):02d}-{int(b):02d}"
    # "12 July 2026" / "July 12, 2026" style
    m4 = re.search(
        r"(\d{1,2})\s+([A-Za-z]+)\s+(20\d{2})", text
    )
    if m4:
        d, mon, y = m4.groups()
        mo = MONTHS.get(mon.lower())
        if mo:
            return f"{y}-{mo:02d}-{int(d):02d}"
    m5 = re.search(r"([A-Za-z]+)\s+(\d{1,2}),?\s+(20\d{2})", text)
    if m5:
        mon, d, y = m5.groups()
        mo = MONTHS.get(mon.lower())
        if mo:
            return f"{y}-{mo:02d}-{int(d):02d}"
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