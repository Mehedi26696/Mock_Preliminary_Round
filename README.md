# QueueStorm Warmup Ticket Sorter

Submission for the **SUST CSE Carnival 2026 Codex Community Hackathon - Mock Preliminary Round**.

This is a small FastAPI web service that receives one customer support ticket and returns a structured classification for CRM triage.

## Live Service

Base URL:

```text
https://mock-preliminary-backend.onrender.com
```

Useful links:

- Health: `https://mock-preliminary-backend.onrender.com/health`
- API docs: `https://mock-preliminary-backend.onrender.com/docs`
- Ticket sorting endpoint: `https://mock-preliminary-backend.onrender.com/sort-ticket`

## Requirement Coverage

| Requirement | Status |
| --- | --- |
| Public HTTPS endpoint | Done |
| `GET /health` endpoint | Done |
| `POST /sort-ticket` endpoint | Done |
| JSON request and response | Done |
| `case_type` enum | Done |
| `severity` enum | Done |
| `department` enum | Done |
| Agent summary | Done |
| Human review flag for phishing or critical cases | Done |
| Confidence score from `0` to `1` | Done |
| No GPU dependency | Done |
| No secrets committed to repository | Done |
| Deployment runbook | Done |
| Automated tests | Done |
| Docker support | Done |

## Approach

The solution uses a deterministic rules-based classifier instead of an LLM. This keeps the service fast, reproducible, and free from API key or GPU requirements.

The classifier checks ticket messages for category-specific keywords, assigns severity, chooses the responsible department, and returns a short neutral summary. Phishing and social-engineering reports are always marked as `critical` and require human review.

## API Specification

### `GET /health`

Returns a simple health response.

Example response:

```json
{
  "status": "ok"
}
```

### `POST /sort-ticket`

Accepts one CRM ticket.

Example request:

```json
{
  "ticket_id": "T-001",
  "channel": "app",
  "locale": "en",
  "message": "I sent 5000 taka to a wrong number this morning, please help me get it back"
}
```

Example response:

```json
{
  "ticket_id": "T-001",
  "case_type": "wrong_transfer",
  "severity": "high",
  "department": "dispute_resolution",
  "agent_summary": "Customer reports sending money to the wrong recipient and requests help with recovery.",
  "human_review_required": false,
  "confidence": 0.8
}
```

## Supported Values

### `case_type`

- `wrong_transfer`
- `payment_failed`
- `refund_request`
- `phishing_or_social_engineering`
- `other`

### `severity`

- `low`
- `medium`
- `high`
- `critical`

### `department`

- `customer_support`
- `dispute_resolution`
- `payments_ops`
- `fraud_risk`

## Public Sample Case Results

The deployed Render API was tested against the public sample cases.

| # | Message | Expected case_type | Expected severity | Result |
| --- | --- | --- | --- | --- |
| 1 | `I sent 3000 to wrong number` | `wrong_transfer` | `high` | Pass |
| 2 | `Payment failed but balance deducted` | `payment_failed` | `high` | Pass |
| 3 | `Someone called asking my OTP, is that bKash?` | `phishing_or_social_engineering` | `critical` | Pass |
| 4 | `Please refund my last transaction, I changed my mind` | `refund_request` | `low` | Pass |
| 5 | `App crashed when I opened it` | `other` | `low` | Pass |

## Project Structure

```text
.
├── .github/workflows/backend-ci-cd.yml
├── backend
│   ├── Dockerfile
│   ├── Procfile
│   ├── main.py
│   ├── pytest.ini
│   ├── requirements-dev.txt
│   ├── requirements.txt
│   └── tests
│       └── test_main.py
└── README.md
```

## Local Runbook

From the repository root:

```bash
cd backend
python -m venv venv
```

Activate the virtual environment.

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements-dev.txt
```

Run the service:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Local URLs:

- Root: `http://localhost:8000/`
- Health: `http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`

## Run Tests

```bash
cd backend
pytest -q
```

Current test coverage includes:

- Root endpoint
- Health endpoint
- All public sample cases
- Phishing human review behavior
- Safety check that summaries do not request sensitive information

## Docker Runbook

Build:

```bash
cd backend
docker build -t queuestorm-backend .
```

Run:

```bash
docker run --rm -p 8000:8000 queuestorm-backend
```

Check:

```text
http://localhost:8000/health
```

## Render Deployment

Render Web Service configuration:

```text
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
```

The repository can also be deployed as a Docker service because `backend/Dockerfile` is included.

## CI/CD

GitHub Actions workflow:

```text
.github/workflows/backend-ci-cd.yml
```

The workflow runs on pushes and pull requests to `main` or `master`.

It performs:

1. Installs backend dependencies.
2. Runs `pytest`.
3. Builds the backend Docker image.
4. Optionally triggers Render deployment if `RENDER_DEPLOY_HOOK_URL` is configured as a GitHub Actions secret.

## Safety Rule

The `agent_summary` is generated from fixed neutral templates. It never asks the customer to share PIN, OTP, password, or full card number.

## Submission Information

- Team name: use registered team name in the submission form
- GitHub repository URL: submit this public repository URL
- Live API base URL: `https://mock-preliminary-backend.onrender.com`
- Deployment platform: Render
- LLM used: No
- GPU required: No
- Secrets in repository: No
- Known issues or blockers: Rules-based classifier; unusual wording may require adding more keyword coverage.
