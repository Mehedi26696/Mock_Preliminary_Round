# QueueStorm Warmup Ticket Sorter

Small FastAPI service for the SUST CSE Carnival 2026 Codex Community Hackathon mock preliminary warmup.

## What it does

- `GET /health` returns service health.
- `POST /sort-ticket` classifies one customer support ticket.
- Uses deterministic rules, so no LLM key or GPU is required.
- Flags phishing/social-engineering and critical cases for human review.

## Local setup

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

Open:

- Health: `http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`

## Run tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest -q
```

## Run with Docker

Build the image:

```bash
cd backend
docker build -t queuestorm-backend .
```

Run the container:

```bash
docker run --rm -p 8000:8000 queuestorm-backend
```

Then check `http://localhost:8000/health`.

## Example request

```bash
curl -X POST http://localhost:8000/sort-ticket \
  -H "Content-Type: application/json" \
  -d '{"ticket_id":"T-001","channel":"app","locale":"en","message":"I sent 5000 taka to a wrong number this morning, please help me get it back"}'
```

## Example response

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

## Deploy on Render

1. Push this repository to GitHub.
2. Create a new Render Web Service from the repository.
3. Set Root Directory to `backend`.
4. Use these settings:
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. After deployment, submit the Render HTTPS URL as the live API base URL.

## GitHub CI/CD

The workflow at `.github/workflows/backend-ci-cd.yml` runs on pushes and pull requests to `main` or `master`.

It does three things:

1. Installs backend dependencies and runs `pytest`.
2. Builds the backend Docker image.
3. On pushes to `main` or `master`, triggers a Render deploy if the GitHub secret `RENDER_DEPLOY_HOOK_URL` is configured.

To enable Render CD:

1. In Render, open your Web Service.
2. Copy the Deploy Hook URL.
3. In GitHub, go to repository Settings > Secrets and variables > Actions.
4. Add a repository secret named `RENDER_DEPLOY_HOOK_URL`.

## Submission notes

- LLM used: No
- GPU required: No
- Secrets required: No
- Known issue: This is a rules-based classifier, so unusual wording may need more keyword coverage.
