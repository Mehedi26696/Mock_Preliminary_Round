from enum import Enum
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field


app = FastAPI(title="QueueStorm Warmup Ticket Sorter")


class Channel(str, Enum):
    app = "app"
    sms = "sms"
    call_center = "call_center"
    merchant_portal = "merchant_portal"


class Locale(str, Enum):
    bn = "bn"
    en = "en"
    mixed = "mixed"


class CaseType(str, Enum):
    wrong_transfer = "wrong_transfer"
    payment_failed = "payment_failed"
    refund_request = "refund_request"
    phishing_or_social_engineering = "phishing_or_social_engineering"
    other = "other"


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Department(str, Enum):
    customer_support = "customer_support"
    dispute_resolution = "dispute_resolution"
    payments_ops = "payments_ops"
    fraud_risk = "fraud_risk"


class TicketRequest(BaseModel):
    ticket_id: str
    channel: Optional[Channel] = None
    locale: Optional[Locale] = None
    message: str = Field(..., min_length=1)


class TicketResponse(BaseModel):
    ticket_id: str
    case_type: CaseType
    severity: Severity
    department: Department
    agent_summary: str
    human_review_required: bool
    confidence: float = Field(..., ge=0, le=1)


KEYWORDS = {
    CaseType.phishing_or_social_engineering: [
        "otp",
        "pin",
        "password",
        "passcode",
        "verification code",
        "secret code",
        "scam",
        "scammer",
        "fraud",
        "fake",
        "phishing",
        "called asking",
        "asked for",
        "share code",
        "account blocked",
        "bkash agent",
    ],
    CaseType.wrong_transfer: [
        "wrong number",
        "wrong recipient",
        "wrong account",
        "wrong person",
        "mistakenly sent",
        "sent by mistake",
        "sent money to wrong",
        "ভুল নম্বর",
        "ভুলে পাঠ",
    ],
    CaseType.payment_failed: [
        "payment failed",
        "transaction failed",
        "failed but balance",
        "balance deducted",
        "money deducted",
        "amount deducted",
        "charged but",
        "paid but failed",
        "cash out failed",
        "send money failed",
    ],
    CaseType.refund_request: [
        "refund",
        "return my money",
        "money back",
        "changed my mind",
        "cancel transaction",
        "reverse transaction",
        "reversal",
    ],
}


def normalize(message: str) -> str:
    return " ".join(message.lower().split())


def classify(message: str) -> tuple[CaseType, float]:
    text = normalize(message)
    scores = {
        case_type: sum(1 for keyword in keywords if keyword in text)
        for case_type, keywords in KEYWORDS.items()
    }

    if scores[CaseType.phishing_or_social_engineering]:
        return CaseType.phishing_or_social_engineering, confidence_from_score(
            scores[CaseType.phishing_or_social_engineering], base=0.82
        )
    if scores[CaseType.wrong_transfer]:
        return CaseType.wrong_transfer, confidence_from_score(
            scores[CaseType.wrong_transfer], base=0.80
        )
    if scores[CaseType.payment_failed]:
        return CaseType.payment_failed, confidence_from_score(
            scores[CaseType.payment_failed], base=0.80
        )
    if scores[CaseType.refund_request]:
        return CaseType.refund_request, confidence_from_score(
            scores[CaseType.refund_request], base=0.76
        )
    return CaseType.other, 0.62


def confidence_from_score(score: int, base: float) -> float:
    return min(0.95, round(base + (score - 1) * 0.04, 2))


def choose_severity(case_type: CaseType, message: str) -> Severity:
    text = normalize(message)

    if case_type == CaseType.phishing_or_social_engineering:
        return Severity.critical

    urgent_terms = ["urgent", "emergency", "all my money", "salary", "rent"]
    if any(term in text for term in urgent_terms):
        return Severity.high

    if case_type in {CaseType.wrong_transfer, CaseType.payment_failed}:
        return Severity.high

    if case_type == CaseType.refund_request:
        contested_terms = ["unauthorized", "wrong", "not received", "deducted", "merchant"]
        if any(term in text for term in contested_terms):
            return Severity.medium
        return Severity.low

    return Severity.low


def choose_department(case_type: CaseType, severity: Severity) -> Department:
    if case_type == CaseType.phishing_or_social_engineering:
        return Department.fraud_risk
    if case_type == CaseType.payment_failed:
        return Department.payments_ops
    if case_type == CaseType.wrong_transfer:
        return Department.dispute_resolution
    if case_type == CaseType.refund_request and severity != Severity.low:
        return Department.dispute_resolution
    return Department.customer_support


def summarize(case_type: CaseType, message: str) -> str:
    clean_message = " ".join(message.strip().split())
    if len(clean_message) > 160:
        clean_message = clean_message[:157].rstrip() + "..."

    summaries = {
        CaseType.phishing_or_social_engineering: "Customer reports a suspicious contact or request for sensitive account information.",
        CaseType.wrong_transfer: "Customer reports sending money to the wrong recipient and requests help with recovery.",
        CaseType.payment_failed: "Customer reports a failed payment or transaction where the balance may have been deducted.",
        CaseType.refund_request: "Customer requests a refund or reversal for a previous transaction.",
        CaseType.other: "Customer reports an issue that does not match the main ticket categories.",
    }

    if case_type == CaseType.other:
        return f"{summaries[case_type]} Message: {clean_message}"
    return summaries[case_type]


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "ok", "service": "QueueStorm Warmup Ticket Sorter"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/sort-ticket", response_model=TicketResponse)
def sort_ticket(ticket: TicketRequest) -> TicketResponse:
    case_type, confidence = classify(ticket.message)
    severity = choose_severity(case_type, ticket.message)
    department = choose_department(case_type, severity)
    human_review_required = (
        severity == Severity.critical
        or case_type == CaseType.phishing_or_social_engineering
    )

    return TicketResponse(
        ticket_id=ticket.ticket_id,
        case_type=case_type,
        severity=severity,
        department=department,
        agent_summary=summarize(case_type, ticket.message),
        human_review_required=human_review_required,
        confidence=confidence,
    )
