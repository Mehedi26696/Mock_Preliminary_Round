from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_root() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_public_sample_cases() -> None:
    cases = [
        ("T-001", "I sent 3000 to wrong number", "wrong_transfer", "high"),
        ("T-002", "Payment failed but balance deducted", "payment_failed", "high"),
        (
            "T-003",
            "Someone called asking my OTP, is that bKash?",
            "phishing_or_social_engineering",
            "critical",
        ),
        (
            "T-004",
            "Please refund my last transaction, I changed my mind",
            "refund_request",
            "low",
        ),
        ("T-005", "App crashed when I opened it", "other", "low"),
    ]

    for ticket_id, message, expected_case_type, expected_severity in cases:
        response = client.post(
            "/sort-ticket",
            json={"ticket_id": ticket_id, "message": message},
        )

        body = response.json()
        assert response.status_code == 200
        assert body["ticket_id"] == ticket_id
        assert body["case_type"] == expected_case_type
        assert body["severity"] == expected_severity
        assert 0 <= body["confidence"] <= 1


def test_phishing_requires_human_review() -> None:
    response = client.post(
        "/sort-ticket",
        json={
            "ticket_id": "T-999",
            "message": "A caller asked for my OTP and account password.",
        },
    )

    body = response.json()
    assert response.status_code == 200
    assert body["case_type"] == "phishing_or_social_engineering"
    assert body["severity"] == "critical"
    assert body["department"] == "fraud_risk"
    assert body["human_review_required"] is True


def test_summary_does_not_request_sensitive_information() -> None:
    response = client.post(
        "/sort-ticket",
        json={
            "ticket_id": "T-1000",
            "message": "Someone asked me to share my PIN.",
        },
    )

    summary = response.json()["agent_summary"].lower()
    forbidden_phrases = [
        "share pin",
        "share otp",
        "send pin",
        "send otp",
        "provide pin",
        "provide otp",
        "give pin",
        "give otp",
    ]
    assert not any(phrase in summary for phrase in forbidden_phrases)
