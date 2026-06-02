# Inbound Carrier Sales Automation — Build Description

**Prepared for:** Acme Logistics
**Prepared by:** Amritanshi Saxena
**Date:** June 2026

---

## Executive Summary

Acme Logistics handles a high volume of inbound carrier calls daily. Reps manually verify carriers, search for matching loads, negotiate rates, and log call outcomes — a process that's slow, inconsistent, and hard to track at scale.

This solution automates the entire inbound carrier sales flow using an AI voice agent built on the HappyRobot platform. When a carrier calls in, the system:

- Verifies their MC number against the federal FMCSA database in real time
- Searches available loads based on the carrier's origin, destination, and equipment
- Negotiates a fair rate within broker-defined rules
- Logs every call with outcome classification and sentiment analysis
- Displays live operations metrics on a custom analytics dashboard

The result: faster call handling, consistent pricing, full visibility into carrier interactions, and reps freed up to focus on relationship-building instead of repetitive screening.

---

## How a Call Works

```
Carrier calls in
      │
      ▼
AI Agent answers, greets the carrier, asks for MC number
      │
      ▼
FMCSA Verification ──── Not eligible? → Politely declines, ends call
      │
      ▼ (eligible)
Agent asks: where are you headed? what equipment?
      │
      ▼
Load Search ──── No match? → Offers to check another lane
      │
      ▼ (match found)
Agent pitches the load: route, times, rate, commodity
      │
      ▼
Negotiation (up to 3 rounds, max 15% above listed rate)
      │
      ├── Agreed → "Transferring you to a sales rep to finalize"
      ├── No agreement → Politely declines, ends call
      └── Carrier declines → Thanks them, ends call
      │
      ▼
Post-call: AI extracts data, classifies outcome & sentiment
      │
      ▼
Call logged → Dashboard updates automatically
```

---

## Features

### Carrier Verification
Every carrier is verified in real time using the FMCSA QCMobile API. The system checks two things:
- Is the carrier authorized to operate (`allowedToOperate`)?
- Do they have active for-hire authority (common or contract)?

Both must be true. This mirrors how a real broker vets carriers before tendering a load — federal approval alone isn't enough.

### Load Search
Carriers describe where they want to go and what equipment they're running. The system searches available loads with fuzzy matching — "Texas" matches "Dallas, TX", partial city names work, and equipment types are flexible. If multiple loads match, the agent pitches the highest-value one first.

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
- **Sentiment**: positive, neutral, or negative (based on the carrier's language)

Along with extracted data: MC number, carrier name, load ID, agreed rate, and negotiation rounds.

### Live Dashboard
A custom-built operations dashboard (not HappyRobot's built-in analytics) shows:

**Key Performance Indicators:**
- Total inbound calls
- Booking rate (% of calls that result in a booked load)
- Average margin delta (agreed rate vs. loadboard rate)
- Average negotiation rounds
- FMCSA rejection count
- Average agreed rate on booked loads

**Charts:**
- Call outcomes breakdown (booked, declined, no agreement, not eligible)
- Carrier sentiment distribution
- Daily bookings over the past 7 days
- Why calls didn't book (non-booked reasons)
- Pickup time patterns (which times of day get booked vs. not)
- Equipment type booking distribution
- Distance vs. rate correlation (does mileage affect booking?)

**Recent Calls Table:**
The last 15 calls with timestamps, MC numbers, carrier names, outcomes, agreed rates, negotiation rounds, and sentiment — all auto-populated from live call data.

---

## Technical Architecture

### Current Build (Proof of Concept)

```
HappyRobot Platform (voice agent)
      │
      ├── verify_carrier tool ──→ FMCSA API
      ├── search_loads tool ────→ Backend API (GET /loads)
      ├── Negotiation ──────────→ Agent prompt rules
      └── Post-call webhook ───→ Backend API (POST /calls)

Backend API (FastAPI + Python)
      │
      └── Supabase PostgreSQL (loads + calls tables)
      │
      └── Dashboard (GET /) — server-rendered HTML
```

**Tech stack:**
- Python 3.12 + FastAPI (backend API)
- Supabase PostgreSQL (persistent database)
- Jinja2 + Tailwind CSS + Chart.js (dashboard)
- Docker (containerization)
- Render (cloud deployment, automatic HTTPS)

### Production Architecture (Roadmap)

For a production deployment at scale, the system would evolve into:

```
Load Balancer
      │
      ├── Loads API Service (handles load search, auto-scales independently)
      ├── Calls & Metrics Service (call logging, analytics, webhooks)
      ├── HappyRobot Proxy Service (keeps platform credentials server-side)
      ├── Dashboard Frontend (React/Next.js, CDN-hosted)
      └── Webhook Worker (async call processing, retry logic, dead letter queue)
              │
      Managed PostgreSQL + Redis (caching, rate limiting)
```

Additional production considerations:
- HappyRobot MCP connectors for direct integration with the broker's TMS and CRM (no custom API middleware needed)
- Horizontal scaling — each service scales independently based on call volume
- Monitoring and alerting (Datadog, PagerDuty) on call success rates and API latency
- Audit logging for compliance

---

## Deployment & Security

### Security
- All data endpoints require API key authentication (`X-API-Key` header)
- HTTPS enforced automatically via Render's SSL termination
- Secrets stored in environment variables, never committed to code
- Dashboard rendered server-side — no API keys or credentials reach the browser
- All request bodies validated with Pydantic schemas (prevents injection, malformed data)

### Accessing the Deployment
- **Dashboard:** https://carrier-sales-technical-challenge.onrender.com/
- **API docs:** https://carrier-sales-technical-challenge.onrender.com/docs
- **Health check:** https://carrier-sales-technical-challenge.onrender.com/health

### Reproducing the Deployment

1. Clone the repository
2. Set two environment variables: `API_KEY` and `DATABASE_URL` (Postgres connection string)
3. Build and run:
   ```
   docker build -t carrier-sales .
   docker run -p 8000:8000 -e API_KEY=your-key -e DATABASE_URL=your-postgres-url carrier-sales
   ```
4. Works on any container platform: Render, AWS ECS, Google Cloud Run, Fly.io, Railway

---

## Future Improvements

- **TMS/CRM integration via MCP connectors** — connect directly to the broker's existing systems instead of maintaining a separate loads database
- **Voice tone analysis** — current sentiment classification uses the transcript text; integrating audio-level tone analysis would improve accuracy
- **Multi-language support** — handle carriers who prefer Spanish or other languages
- **Real-time dashboard updates** — WebSocket connection so the dashboard refreshes live as calls come in, no page reload needed
- **Automated follow-up** — send carriers a booking confirmation email or SMS after a successful call
- **Load recommendation engine** — suggest alternative loads when the carrier's first choice isn't available, based on their past booking patterns

---

## Summary

This solution takes a manual, time-consuming process and automates it end-to-end. Carriers get faster service, reps get better data, and the brokerage gets consistent pricing and full visibility into every inbound interaction.

The system is built to work today as a proof of concept and designed to scale into production with the broker's existing tools and workflows.
