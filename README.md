# Inbound Carrier Sales — HappyRobot FDE Challenge

A backend that powers an AI voice agent for inbound carrier load sales. Carriers call
in, the agent verifies them against FMCSA, matches them to a load, negotiates the rate,
and books it — and every call is captured on an operations dashboard.

This repo is the **API + dashboard**. The voice agent itself is built on the HappyRobot
platform and calls this API during live calls.

## Architecture

\`\`\`
HappyRobot agent (their cloud)
        │  (HTTPS, X-API-Key)
        ▼
  This FastAPI service ──────────────► Ops dashboard ( GET / )
        │
        ├── GET  /verify-carrier   FMCSA eligibility (active for-hire authority)
        ├── GET  /loads            search available loads
        ├── POST /evaluate-offer   deterministic, server-side negotiation
        ├── POST /calls            store completed calls (from post-call webhook)
        └── GET  /metrics          aggregated stats for the dashboard
        │
        ▼
     SQLite (loads, negotiation_sessions, calls)
\`\`\`

Key design decisions:
- **Negotiation logic is deterministic and server-side** (negotiation.py), not done by
  the LLM. Round-counting is tracked in the DB so it doesn't depend on the model counting.
- **FMCSA eligibility requires active operating authority**, not just allowedToOperate,
  mirroring how a real broker vets a carrier (fmcsa.py). Falls back to a mock verifier
  if the FMCSA API is unavailable, so a live call never breaks on a slow government API.
- **Dashboard renders server-side**, so no API key is exposed in the browser. Data
  endpoints stay key-protected.
- **Single service** serves both the carrier-facing API and the dashboard — one container.

## Run locally

\`\`\`bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
python -m pip install -r requirements.txt
cp .env.example .env            # then set API_KEY; FMCSA_WEBKEY optional
python -m uvicorn main:app --reload
\`\`\`

- Dashboard: http://localhost:8000/
- API docs:  http://localhost:8000/docs

Optionally seed sample calls to preview the dashboard:
\`\`\`bash
python seed_calls.py
\`\`\`

## Environment variables

| Variable | Required | Purpose |
|----------|----------|---------|
| API_KEY | yes | Key callers must send in the X-API-Key header. |
| FMCSA_WEBKEY | no | FMCSA QCMobile webKey. Blank = mock verifier. |
| USE_MOCK_FMCSA | no | Fall back to mock if FMCSA errors (default true). |
| BROKER_MAX_UPLIFT | no | Negotiation ceiling = loadboard_rate × (1 + this). Default 0.15. |
| MAX_NEGOTIATION_ROUNDS | no | Max carrier counter-offers. Default 3. |

## Deploy (Render)

1. Push this repo to GitHub.
2. On Render: New → Web Service → connect the repo.
3. Render auto-detects the Dockerfile. Set the environment variables above
   (API_KEY, FMCSA_WEBKEY) in the Render dashboard — do NOT commit them.
4. Deploy. Render builds the container, serves it over HTTPS, and provides a public URL.

The container reads $PORT from the platform, so it runs unchanged on Render, Cloud Run,
AWS, or anywhere that runs a container.

### Reproduce the deployment

\`\`\`bash
docker build -t carrier-sales .
docker run -p 8000:8000 -e API_KEY=your-key -e FMCSA_WEBKEY=your-fmcsa-key carrier-sales
\`\`\`

## Notes

- On a free hosting tier the filesystem is ephemeral, so calls reset on redeploy and
  loads re-seed on startup. For production, attach a persistent volume or use a managed
  database (e.g. Postgres) — the data layer is isolated in db.py to make that swap easy.