# BankLens

**ET AI Hackathon submission** — a lender operations console for **borrower intelligence**: bank-statement-style monitoring (BSI), compiled risk **signals**, **omnichannel** outreach (WhatsApp / email), and an **immutable audit** trail. **Generative AI is mandatory**: after every BSI run the backend calls an **OpenAI-compatible** model to produce a narrative summary. The **rules engine remains the sole source of truth** for signals; Gen AI does not override deterministic outcomes.

---

## What BankLens does

- **Onboards and tracks customers** with consent-aware monitoring flags and loan snapshots (principal, EMI, DPD, inflow proxies, etc.).
- **Triggers BSI monitoring runs** that evaluate deterministic rules and persist outcomes; **Gen AI then generates a summary** for operators (audited; failures are recorded without blocking the run).
- **Surfaces signals** (e.g. late payment, salary proxy change, negative EOD patterns) for dashboards, monitoring queues, and notification-style views.
- **Sends outbound messages** via WhatsApp Cloud API or SMTP when credentials are set; otherwise records **mocked** deliveries for demos.
- **Enforces RBAC** (admin, analyst, compliance) with permission checks and **append-only audit** events for reviewer workflows.

The **React** dashboard (Vite, TypeScript, Tailwind, Recharts) talks to the **FastAPI** backend: dashboard KPIs, customer management, customer detail (overview, statement-style views, sync/BSI), monitoring, recovery queue, and signal-driven notifications.

---

## Repository layout

| Path | Description |
|------|-------------|
| `backend/` | FastAPI app, SQLAlchemy models, services (BSI, omnichannel, audit, **Gen AI**). |
| `frontend/` | SPA: auth, dashboard, customers, signals, recovery, notifications UI. |

---

## Tech stack

**Backend:** Python 3.11+, FastAPI, SQLAlchemy, SQLite by default, JWT auth, SlowAPI rate limits, Pydantic settings.

**Frontend:** React 19, TypeScript, Vite, Tailwind CSS v4, React Router, Recharts, Lucide icons.

**Integrations — Gen AI (required):** `OPENAI_API_KEY` and `GEN_AI_AFTER_BSI=true` (default). Optional: `OPENAI_BASE_URL` for Azure or other OpenAI-compatible endpoints. **Optional:** SMTP, Meta WhatsApp Cloud API.

---

## Prerequisites (local machine)

1. **Python** 3.11 or newer (`python --version`).
2. **Node.js** 20+ recommended (`node --version`) and **npm**.
3. **OpenAI API key** (or compatible provider key + base URL) — **required** so BSI runs produce Gen AI summaries per product design.
4. **Git** (to clone the repository).

---

## Run locally (step-by-step)

### Step 1 — Clone and enter the repo

```bash
git clone <your-repo-url>
cd et_banklens
```

### Step 2 — Backend: virtual environment and dependencies

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Step 3 — Backend: environment file

```bash
cp .env.example .env
```

Edit **`backend/.env`** and set at least:

| Variable | Purpose |
|----------|---------|
| `SECRET_KEY` | **Required.** At least 32 characters. |
| `OPENAI_API_KEY` | **Required.** Enables mandatory Gen AI summaries after each BSI run. |
| `GEN_AI_AFTER_BSI` | Keep **`true`** (default). Do not disable for hackathon/demo alignment. |
| `OPENAI_MODEL` | e.g. `gpt-4o-mini` (default) or your provider’s model id. |
| `OPENAI_BASE_URL` | Optional; set if you use Azure OpenAI or another OpenAI-compatible API. |
| `SEED_DEMO_USER` | Set to **`true`** for a quick login user. |
| `DEMO_USER_EMAIL` | Login email (e.g. `demo@example.com`). |
| `DEMO_USER_PASSWORD` | Strong password for that user. |
| `CORS_ORIGINS` | Must include the frontend origin, e.g. `http://127.0.0.1:3000,http://localhost:3000`. |

Leave `SEED_BANKLENS_DEMO=true` (default) if you want seeded borrowers for BSI/signals.

### Step 4 — Start the API server

From `backend/` with the venv activated:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Keep this terminal open.

### Step 5 — Verify the backend

- Health: `http://127.0.0.1:8000/api/v1/health` (expect `{"status":"ok"}`).
- Service root: `http://127.0.0.1:8000/`
- API docs (development): `http://127.0.0.1:8000/docs`

### Step 6 — Frontend: install and dev server

Open a **second** terminal:

```bash
cd frontend
npm install
npm run dev
```

The app is served at **`http://localhost:3000`** (see Vite output if the port differs). The dev server **proxies** `/api` to `http://127.0.0.1:8000`, so the browser talks to one origin.

### Step 7 — Sign in and exercise Gen AI

1. Open **`http://localhost:3000`**.
2. Sign in with `DEMO_USER_EMAIL` / `DEMO_USER_PASSWORD` (or another user in your DB).
3. Open **Customers**, pick a customer, use **Sync → Run BSI monitoring** (or trigger BSI via `POST /api/v1/bsi/customers/{id}/runs` in `/docs`).
4. Confirm the run response or run detail includes **`gen_ai_summary`** / model fields — that confirms **mandatory Gen AI** executed after the rules engine.

### Step 8 — Production-style frontend build (optional)

```bash
cd frontend
npm run build
npm run preview
```

For a remote API (no dev proxy), create `frontend/.env` with:

```bash
VITE_API_BASE=http://127.0.0.1:8000
```

---

## API surface (high level)

All JSON routes are under `/api/v1` unless noted.

| Area | Examples |
|------|-----------|
| Auth | `POST /auth/login` |
| Dashboard | `GET /dashboard/dashboard_info`, `GET /dashboard/me` |
| Customers | `GET /customers/monitored`, `GET /customers/{id}`, `POST /customers`, `PATCH /customers/{id}/consent` |
| BSI | `POST /bsi/customers/{id}/runs`, `GET /bsi/runs/{run_id}` |
| Signals | `GET /signals/latest`, `GET /signals/customers/{id}` |
| Omnichannel | `POST /omnichannel/messages`, `GET /omnichannel/messages` |
| Audit | `GET /audit/events` (compliance permission) |
| Health | `GET /health` |

BSI responses include Gen AI fields when the generative step completes. Responses use a success envelope with a `result` payload (`APISuccessResponse` style).

---

## Exclusions (not present in this mini version)

- ML Engine for Transaction Categorization
- Complex Kafka framework and Snowflake data store
- Pinecone implementation
- PII Masking framework for OpenAI invocations
- Omnichannel - Calls and others

The full version is present at `banklens.crawfieldanddutton.com` !
