# Inbound Carrier Sales — HappyRobot FDE Challenge

Backend API and operations dashboard for an AI voice agent that handles inbound carrier load sales. Carriers call in, the agent verifies them via FMCSA, matches them to available loads, negotiates a rate, and books it. Every call is logged and visualized on a live dashboard.

The voice agent runs on the HappyRobot platform. This repo is the data layer it talks to — load search, call logging, and the analytics dashboard.

## How it works

```
Carrier calls in
       |
HappyRobot Voice Agent
       |
       |-- verify_carrier tool -----> FMCSA API (carrier eligibility)
       |-- search_loads tool -------> This API (GET /loads)
       |-- negotiation -------------> Handled by agent prompt rules
       |-- post-call webhook -------> This API (POST /calls)
       |
This FastAPI Service
       |-- GET  /loads          Search available freight
       |-- POST /calls          Log completed call data
       |-- GET  /metrics        Aggregated stats (JSON)
       |-- GET  /               Live ops dashboard
       |-- GET  /health         Liveness check
       |
  Supabase PostgreSQL (loads + calls)
```

The HappyRobot agent handles the conversation, FMCSA verification, and negotiation. This service handles data — loads, call storage, and the dashboard. The dashboard is built from scratch (not using HappyRobot's built-in analytics).

## Run locally

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then fill in your values
uvicorn main:app --reload
```

- Dashboard: http://localhost:8000/
- API docs: http://localhost:8000/docs

To populate the dashboard with sample data:

```bash
python seed_calls.py
```

## Environment variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `API_KEY` | Yes | — | Key that must be sent in the `X-API-Key` header |
| `DATABASE_URL` | Yes | — | Postgres connection string (Supabase pooler URL) |

Set these in a `.env` file locally, or in your hosting provider's environment settings for production.

## API endpoints

All endpoints except `/health` and `/` require the `X-API-Key` header.

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/loads` | Search loads by origin, destination, equipment_type |
| `POST` | `/calls` | Store a completed call record |
| `GET` | `/metrics` | Aggregated call metrics (JSON) |
| `GET` | `/` | Ops dashboard (HTML) |
| `GET` | `/health` | Liveness check |

## Dashboard

The dashboard at `/` shows:

- 6 KPIs: total calls, booking rate, avg margin delta, avg negotiation rounds, FMCSA rejected count, avg agreed rate
- Call outcomes breakdown (doughnut chart)
- Carrier sentiment breakdown (doughnut chart)
- Bookings per day over the last 7 days (bar chart)
- Non-booked call reasons (horizontal bar chart)
- Pickup time patterns by time of day (grouped bar chart)
- Equipment type booking distribution (stacked bar chart)
- Distance vs rate correlation (scatter plot)
- Recent calls table (last 15 calls)

Built with Jinja2 server-side rendering, Tailwind CSS, and Chart.js. No API key is exposed in the browser.

## Deploy to Render

1. Push this repo to GitHub
2. On Render: **New > Web Service** and connect the repo
3. Render auto-detects the Dockerfile. Set these environment variables in the Render dashboard:
   - `API_KEY` — your chosen API key
   - `DATABASE_URL` — your Supabase pooler connection string
4. Hit **Deploy**

Render provides HTTPS automatically. The container reads `$PORT` from the environment so it works on any container platform.

### Reproduce locally with Docker

```bash
docker build -t carrier-sales .
docker run -p 8000:8000 \
  -e API_KEY=your-key \
  -e DATABASE_URL=your-postgres-url \
  carrier-sales
```

### Reproduce on another provider

The Dockerfile works on any platform that runs containers (AWS ECS, Google Cloud Run, Fly.io, Railway, etc.). Just set the two environment variables and expose the port.

## Tech stack

- **Python 3.12 + FastAPI** — backend API
- **Supabase PostgreSQL** — persistent database
- **Jinja2 + Tailwind CSS + Chart.js** — dashboard
- **Docker** — containerization
- **Render** — cloud deployment
- **HappyRobot** — voice agent platform

## Security

- API key authentication on all data endpoints
- HTTPS via Render's automatic SSL
- Secrets stored in environment variables, never in code
- Dashboard rendered server-side so no credentials reach the browser
- Input validation via Pydantic on all request bodies
