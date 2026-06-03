# Inbound Carrier Sales — Technical Challenge

**Prepared by:** Amritanshi Saxena | **Date:** June 2026

Backend API and React operations dashboard for an AI voice agent that handles inbound carrier load sales. Carriers call in, the agent verifies them via FMCSA, matches them to available loads, negotiates a rate, and books it. Every call is logged and visualized on a live dashboard.

The voice agent runs on the HappyRobot platform. This repo is the data layer it talks to — load search, call logging, and the analytics dashboard.

## Live Demo

- **Dashboard:** https://carrier-sales-technical-challenge.onrender.com/
- **API Docs:** https://carrier-sales-technical-challenge.onrender.com/docs
- **Health Check:** https://carrier-sales-technical-challenge.onrender.com/health
- **HappyRobot Workflow:** https://platform.happyrobot.ai/fdeamritanshisaxena/workflows/io14uwgjyb6n/editor/6r2dr6pzc0p4

## FDE Challenge Objectives

### Objective 1: Inbound Use Case Implementation
- AI voice agent configured on HappyRobot platform with full conversation flow
- FMCSA carrier verification via QCMobile API (checks `allowedToOperate` + authority status)
- Load search
- Rate negotiation 
- Automatic call transfer on agreement
- Post-call data extraction: outcome, sentiment, MC number, agreed rate, negotiation rounds

### Objective 2: Custom Analytics Dashboard
- React SPA with 8 KPIs, 7 interactive charts, and a recent calls table
- HappyRobot API integration for call duration, run volume, and agent reliability
- Detail modal for each call showing full record including transcript
- Direct link to HappyRobot workflow from dashboard header

### Objective 3: Deployment & Infrastructure
- Dockerized multi-stage build (Node for React + Python for FastAPI)
- Deployed on Render with automatic HTTPS
- Supabase PostgreSQL for persistent data
- API key authentication on all data endpoints
- No credentials exposed in the browser — all external API calls happen server-side

## How a Call Works

```
Carrier calls in
      |
      v
AI Agent answers, greets the carrier, asks for MC number
      |
      v
FMCSA Verification ---- Not eligible? -> Politely declines, ends call
      |
      v (eligible)
Agent asks: where are you headed? what equipment?
      |
      v
Load Search ---- No match? -> Offers to check another lane
      |
      v (match found)
Agent pitches the load: route, times, rate, commodity
      |
      v
Negotiation (up to 3 rounds, max 15% above listed rate)
      |
      |-- Agreed -> "Transferring you to a sales rep to finalize"
      |-- No agreement -> Politely declines, ends call
      +-- Carrier declines -> Thanks them, ends call
      |
      v
Post-call: AI extracts data, classifies outcome & sentiment
      |
      v
Call logged -> Dashboard updates automatically
```

## System Architecture

```
Carrier calls in
       |
HappyRobot Voice Agent
       |
       |-- verify_carrier tool -----> FMCSA API (carrier eligibility)
       |-- search_loads tool -------> This API (GET /loads)
       |-- negotiation -------------> Handled by strict agent prompt rules
       |-- post-call webhook -------> This API (POST /calls)
       |
FastAPI Backend (Python)
       |-- GET  /api/dashboard  Dashboard data (JSON, consumed by React)
       |-- GET  /loads          Search available freight
       |-- POST /calls          Log completed call data
       |-- GET  /metrics        Aggregated stats (JSON)
       |-- GET  /health         Liveness check
       |-- /    (static)        Serves React SPA build
       |
  Supabase PostgreSQL (loads + calls)
       |
React Dashboard (Vite + Tailwind + Chart.js)
       |-- Fetches /api/dashboard on load
       |-- 8 KPIs, 7 charts, recent calls table with detail modal
       |-- HappyRobot API data (call duration, runs, agent reliability)
```

## Features

### Carrier Verification
Every carrier is verified in real time using the FMCSA QCMobile API. The system checks:
- Is the carrier authorized to operate (`allowedToOperate`)?
- Do they have active for-hire authority (common or contract)?

Both must be true. This mirrors how a real broker vets carriers before tendering a load.

### Load Search
Carriers describe where they want to go and what equipment they're running. The system searches available loads with fuzzy matching — "Texas" matches "Dallas, TX", full state names are converted to abbreviations ("Minneapolis, Minnesota" finds "Minneapolis, MN"), and equipment types are flexible. If multiple loads match, the agent pitches the highest-value one first.

### Negotiation
The agent follows broker-defined pricing rules:
- Maximum rate: 15% above the listed loadboard rate
- If the carrier's ask is within budget: accept
- If above: counter with a midpoint offer, capped at the ceiling
- Up to 3 rounds of back-and-forth
- After 3 rounds with no agreement: walk away politely

The carrier never sees the ceiling or the formula. The agent negotiates naturally while staying within the broker's margins.

### Call Classification
After every call, the system automatically classifies:
- **Outcome**: booked, declined, no agreement, or not eligible
- **Sentiment**: positive, neutral, or negative

Along with extracted data: MC number, carrier name, load ID, agreed rate, and negotiation rounds.

## Dashboard

**Key Performance Indicators (8):**
- Total calls (from HappyRobot runs)
- Booking rate
- Avg margin delta (agreed vs loadboard rate)
- Avg agreed rate on booked loads
- Avg negotiation rounds
- FMCSA rejected count
- Avg call duration (from HappyRobot)
- Agent reliability (completed vs failed runs)

**Charts (7):**
- Call outcomes breakdown (doughnut)
- Carrier sentiment distribution (doughnut)
- Runs over time — last 7 days (bar, from HappyRobot API)
- Completed vs failed runs — agent reliability (doughnut, from HappyRobot API)
- Pickup time patterns by time of day (grouped bar)
- Equipment type booking distribution (stacked bar)
- Distance vs rate correlation (scatter)

**Recent Calls Table:**
Last 15 calls with timestamps, MC numbers, carrier names, outcomes, agreed rates, negotiation rounds, sentiment, call duration, run status, and a detail modal for each call.

Built with React 18, Vite, Tailwind CSS, and react-chartjs-2. No API keys are exposed in the browser — all HappyRobot and database calls happen server-side.

## Project Structure

```
carrier_sales_technical_challenge/
├── Dockerfile                  # Multi-stage build (React + Python)
├── backend/
│   ├── main.py                 # FastAPI app — API routes + static serving
│   ├── db.py                   # Database layer (Supabase PostgreSQL)
│   ├── auth.py                 # API key authentication
│   ├── config.py               # Settings from environment variables
│   ├── schemas.py              # Pydantic models + validators
│   ├── loads.json              # Seed data — 10 sample loads
│   ├── seed_calls.py           # Script to populate sample call data
│   ├── requirements.txt        # Python dependencies
│   └── .env.example            # Environment variable template
└── frontend/
    ├── package.json            # React dependencies
    ├── vite.config.js          # Vite + dev proxy config
    ├── tailwind.config.js      # Custom color palette + fonts
    ├── index.html              # Entry point
    └── src/
        ├── main.jsx            # React root
        ├── index.css           # Tailwind + custom styles
        ├── App.jsx             # Layout, data fetching, header
        └── components/
            ├── KPIGrid.jsx     # 8 KPI cards
            ├── Charts.jsx      # 7 charts (react-chartjs-2)
            ├── CallsTable.jsx  # Recent calls table
            └── DetailModal.jsx # Call detail popup
```

## Tech Stack

### Backend
- **Python 3.12 + FastAPI** — REST API framework
- **Uvicorn** — ASGI server
- **Pydantic** — request/response validation and settings management
- **psycopg2** — PostgreSQL database driver
- **httpx** — async HTTP client for HappyRobot API calls
- **Supabase PostgreSQL** — persistent database (connection pooler for IPv4)

### Frontend
- **React 18** — component-based UI
- **Vite** — build tool with hot module replacement
- **Tailwind CSS** — utility-first styling with custom design tokens
- **Chart.js 4 + react-chartjs-2** — interactive charts (doughnut, bar, scatter)
- **PostCSS + Autoprefixer** — CSS build pipeline

### External APIs
- **HappyRobot Platform** — AI voice agent (conversation, call flow)
- **HappyRobot v2 API** — run metrics, call duration, agent reliability
- **FMCSA QCMobile API** — federal carrier verification (via HappyRobot tool node)

### Infrastructure
- **Docker** — multi-stage containerization (Node build + Python runtime)
- **Render** — cloud deployment with automatic HTTPS
- **GitHub** — version control and CI trigger

## Run Locally

You need two terminals:

**Terminal 1 — Backend (port 8000):**
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then fill in your values
uvicorn main:app --reload
```

**Terminal 2 — Frontend (port 5173):**
```bash
cd frontend
npm install
npm run dev
```

- Dashboard: http://localhost:5173
- API docs: http://localhost:8000/docs

To populate the dashboard with sample data:
```bash
python seed_calls.py
```

## Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `API_KEY` | Yes | Key sent in the `X-API-Key` header |
| `DATABASE_URL` | Yes | Postgres connection string (Supabase pooler URL) |
| `HAPPYROBOT_API_KEY` | No | HappyRobot platform API key for run metrics |
| `HAPPYROBOT_USE_CASE_ID` | No | HappyRobot use case ID for filtering runs |

## API Endpoints

All endpoints except `/health` and `/api/dashboard` require the `X-API-Key` header.

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/dashboard` | All dashboard data (metrics, calls, charts, HR data) |
| `GET` | `/loads` | Search loads by origin, destination, equipment_type |
| `POST` | `/calls` | Store a completed call record |
| `GET` | `/metrics` | Aggregated call metrics (JSON) |
| `GET` | `/health` | Liveness check |

## Deploy to Render

1. Push this repo to GitHub
2. On Render: **New > Web Service** and connect the repo
3. Set the **Dockerfile path** to `Dockerfile` (root, not backend/)
4. Set environment variables: `API_KEY`, `DATABASE_URL`, `HAPPYROBOT_API_KEY`, `HAPPYROBOT_USE_CASE_ID`
5. Hit **Deploy**

The Dockerfile is a multi-stage build: Stage 1 builds the React frontend, Stage 2 runs the Python backend and serves the React build as static files.

### Reproduce with Docker

```bash
docker build -t carrier-sales .
docker run -p 10000:10000 \
  -e API_KEY=your-key \
  -e DATABASE_URL=your-postgres-url \
  -e HAPPYROBOT_API_KEY=your-hr-key \
  -e HAPPYROBOT_USE_CASE_ID=your-use-case-id \
  carrier-sales
```

Works on any container platform: AWS ECS, Google Cloud Run, Fly.io, Railway, etc.

## Testing

```bash
# Health check
curl https://carrier-sales-technical-challenge.onrender.com/health

# Dashboard API (no auth needed)
curl https://carrier-sales-technical-challenge.onrender.com/api/dashboard

# Search loads (requires API key)
curl -H "X-API-Key: YOUR_KEY" \
  "https://carrier-sales-technical-challenge.onrender.com/loads?origin=Chicago"

# Get metrics (requires API key)
curl -H "X-API-Key: YOUR_KEY" \
  https://carrier-sales-technical-challenge.onrender.com/metrics
```

## CI/CD Pipeline

```
git push origin main
       |
       v
Render detects push (GitHub webhook)
       |
       v
Docker multi-stage build
  Stage 1: npm ci + npm run build (React)
  Stage 2: pip install + copy backend + copy React build
       |
       v
Health check (GET /health)
       |
       v
Live — zero-downtime deploy, old container replaced
```

- **Automatic:** every push to `main` triggers a build and deploy
- **No manual steps:** Render handles build, deploy, SSL renewal, and container lifecycle
- **Rollback:** previous deploy is retained in Render dashboard — one-click rollback if needed

## Performance

Measured on Render free tier (single container, cold starts after 15 min idle):

| Metric | Value |
|--------|-------|
| `/health` response | < 50ms |
| `/api/dashboard` response | ~ 1-2s (includes HR API call) |
| `/loads` search response | < 200ms |
| Dashboard initial load | ~ 2-3s (React bundle + API fetch) |
| Docker build time | ~ 60-90s |

Note: Render free tier spins down after inactivity — first request after idle takes ~30-50s for cold start. Production tier eliminates this.

## Security

- API key authentication on all data endpoints
- HTTPS via Render's automatic SSL
- Secrets stored in environment variables, never in code
- All API calls (HappyRobot, database) happen server-side — no credentials reach the browser
- Input validation via Pydantic on all request bodies
- CORS configured for development; production serves everything from one origin

## Production Roadmap

For a production deployment at scale, the system would evolve into:

```
Load Balancer
      |
      |-- Loads API Service (auto-scales independently)
      |-- Calls & Metrics Service (call logging, analytics, webhooks)
      |-- HappyRobot Proxy Service (keeps platform credentials server-side)
      |-- Dashboard Frontend (React, CDN-hosted)
      +-- Webhook Worker (async call processing, retry logic, dead letter queue)
              |
      Managed PostgreSQL + Redis (caching, rate limiting)
```

- HappyRobot MCP connectors for direct TMS/CRM integration
- Horizontal scaling per service based on call volume
- Monitoring and alerting on call success rates and API latency

## Future Improvements

- **TMS/CRM integration via MCP connectors** — connect directly to the broker's existing systems instead of maintaining a separate loads database
- **Voice tone analysis** — current sentiment classification uses transcript text; audio-level tone analysis would improve accuracy
- **Multi-language support** — handle carriers who prefer Spanish or other languages
- **Real-time dashboard updates** — WebSocket connection so the dashboard refreshes live as calls come in
- **Automated follow-up** — send carriers a booking confirmation email or SMS after a successful call
- **Load recommendation engine** — suggest alternative loads based on past booking patterns

## Author

**Amritanshi Saxena**
- **GitHub:** [amritanshisaxena](https://github.com/amritanshisaxena)
- **LinkedIn:** [amritanshi](https://www.linkedin.com/in/amritanshi/)
- **Email:** amritanshisaxena1@gmail.com
