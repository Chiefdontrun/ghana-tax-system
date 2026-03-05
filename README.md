# Digital Taxation & Revenue Tracking System
## Ghana District Assembly — Revenue Unit

A multi-channel tax registration and monitoring platform for small-scale enterprises. Traders register via **web form** or **USSD** (no smartphone required), receive a unique Tax Identification Number (TIN), and are tracked on a government-style administrative dashboard.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENT LAYER                            │
│  ┌──────────────────────┐    ┌──────────────────────────┐   │
│  │   React Web App       │    │    USSD Gateway           │   │
│  │  (Trader + Admin)     │    │  (Africa's Talking)       │   │
│  └──────────┬───────────┘    └────────────┬─────────────┘   │
└─────────────┼──────────────────────────────┼────────────────┘
              │ HTTP/REST                     │ Webhook POST
┌─────────────▼──────────────────────────────▼────────────────┐
│                 API LAYER (Django DRF / Python)               │
│  ┌──────────┐ ┌────────────┐ ┌──────────┐ ┌─────────────┐  │
│  │   Auth   │ │ Regist.+   │ │   USSD   │ │  Reports +  │  │
│  │  + RBAC  │ │    TIN     │ │  Engine  │ │    Audit    │  │
│  └──────────┘ └────────────┘ └──────────┘ └─────────────┘  │
└─────────────────────────┬───────────────────────────────────┘
                           │
          ┌────────────────┼───────────────┐
          ▼                ▼               ▼
     ┌─────────┐     ┌─────────┐    ┌──────────┐
     │ MongoDB │     │  Redis  │    │ Africa's │
     │  (data) │     │(sessions│    │  Talking │
     └─────────┘     └─────────┘    │   SMS)   │
                                    └──────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + TypeScript + Vite + TailwindCSS |
| Backend | Python 3.10 + Django REST Framework |
| Database | MongoDB 7 (PyMongo) |
| Cache / Sessions | Redis 7 |
| Auth | JWT (PyJWT + bcrypt) |
| USSD Gateway | Africa's Talking |
| Container | Docker + Docker Compose |

---

## Prerequisites

- Docker & Docker Compose v2+
- (For local dev without Docker) Python 3.10+, Node.js 20+, MongoDB 7, Redis 7

---

## Quick Start with Docker Compose

```bash
# 1. Clone the repo
git clone <repo-url>
cd ghana-tax-system

# 2. Copy and configure environment
cp infra/.env.example infra/.env
# Edit infra/.env — at minimum set JWT_SECRET_KEY and DJANGO_SECRET_KEY

# 3. Start all services (MongoDB, Redis, Backend, Frontend)
cd infra
docker compose up --build

# 4. The seed script runs automatically on first start.
#    Alternatively, run it manually:
docker compose exec backend python manage.py seed_demo_data

# 5. Open the app
#    Trader portal:  http://localhost
#    Admin portal:   http://localhost/admin/login
#    Backend API:    http://localhost:8000
```

---

## Manual Local Development Setup

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env with your local MongoDB URI, Redis URL, secrets

python manage.py seed_demo_data
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install

# Create .env.local
echo "VITE_API_BASE_URL=http://localhost:8000" > .env.local

npm run dev
# Opens at http://localhost:5173
```

---

## Seed Demo Data

```bash
# Via Docker
docker compose exec backend python manage.py seed_demo_data

# Or locally
cd backend && python manage.py seed_demo_data
```

Seeds: 3 admin accounts, 10 locations, 100 traders, 200+ audit logs.

---

## Default Demo Accounts

| Role | Email | Password |
|------|-------|----------|
| System Administrator | sysadmin@demo.gov.gh | DemoPass123! |
| Tax Administrator | taxadmin1@demo.gov.gh | DemoPass123! |
| Tax Administrator | taxadmin2@demo.gov.gh | DemoPass123! |

---

## Environment Variables

See `infra/.env.example` for the full list. Key variables:

| Variable | Description |
|----------|-------------|
| `MONGO_URI` | MongoDB connection string |
| `REDIS_URL` | Redis connection string |
| `JWT_SECRET_KEY` | Secret for signing JWT tokens |
| `DJANGO_SECRET_KEY` | Django secret key |
| `AT_API_KEY` | Africa's Talking API key (USSD/SMS) |
| `AT_USERNAME` | Africa's Talking username |
| `SEED_ADMIN_EMAIL` | Email for seeded SYS_ADMIN account |
| `SEED_ADMIN_PASSWORD` | Password for seeded SYS_ADMIN account |

---

## USSD Simulation (curl)

```bash
# 1. Initial menu
curl -X POST http://localhost:8000/ussd/callback \
  -d "sessionId=test_001&serviceCode=*714%23&phoneNumber=%2B233201234567&text="

# 2. Choose Register (option 1)
curl -X POST http://localhost:8000/ussd/callback \
  -d "sessionId=test_001&serviceCode=*714%23&phoneNumber=%2B233201234567&text=1"

# 3. Enter name
curl -X POST http://localhost:8000/ussd/callback \
  -d "sessionId=test_001&serviceCode=*714%23&phoneNumber=%2B233201234567&text=1*Kofi+Mensah"

# 4. Select business type (1=Food Vendor)
curl -X POST http://localhost:8000/ussd/callback \
  -d "sessionId=test_001&serviceCode=*714%23&phoneNumber=%2B233201234567&text=1*Kofi+Mensah*1"

# 5. Select region (1=Greater Accra)
curl -X POST http://localhost:8000/ussd/callback \
  -d "sessionId=test_001&serviceCode=*714%23&phoneNumber=%2B233201234567&text=1*Kofi+Mensah*1*1"

# 6. Enter market name
curl -X POST http://localhost:8000/ussd/callback \
  -d "sessionId=test_001&serviceCode=*714%23&phoneNumber=%2B233201234567&text=1*Kofi+Mensah*1*1*Makola+Market"

# 7. Confirm (1=Yes)
curl -X POST http://localhost:8000/ussd/callback \
  -d "sessionId=test_001&serviceCode=*714%23&phoneNumber=%2B233201234567&text=1*Kofi+Mensah*1*1*Makola+Market*1"
```

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/login` | None | Admin login → JWT tokens |
| POST | `/api/auth/refresh` | None | Refresh access token |
| GET | `/api/me` | Any Admin | Current admin info |
| POST | `/api/register` | None | Web trader registration |
| POST | `/api/tin/lookup` | None | TIN lookup by phone |
| POST | `/ussd/callback` | None | USSD webhook handler |
| GET | `/api/traders` | TAX_ADMIN+ | List traders (filtered, paginated) |
| GET | `/api/traders/:id` | TAX_ADMIN+ | Trader detail |
| GET | `/api/reports/summary` | TAX_ADMIN+ | KPI aggregates |
| GET | `/api/reports/export` | TAX_ADMIN+ | CSV export |
| GET | `/api/audit-logs` | SYS_ADMIN | Audit log entries |
| POST | `/api/admin/users` | SYS_ADMIN | Create admin account |
| PATCH | `/api/admin/users/:id` | SYS_ADMIN | Update admin role/status |
| GET | `/api/admin/users` | SYS_ADMIN | List all admins |

---

## Running Tests

```bash
cd backend
pip install -r requirements.txt
pytest

# Specific test file
pytest tests/test_tin.py -v

# With coverage
pytest --cov=apps --cov-report=html
```

---

## Phase Progress

See `PHASES.md` for the full build plan and `LOG.md` for completed work.

| Phase | Status |
|-------|--------|
| 1 — Project Scaffold & Infra | ✅ Complete |
| 2 — MongoDB Data Layer & Seed | ✅ Complete |
| 3 — Auth Module | ✅ Complete |
| 4 — Registration + TIN | ✅ Complete |
| 5 — USSD Gateway | ✅ Complete |
| 6 — Reports + Audit APIs | ✅ Complete |
| 7 — Notifications + Tests | ✅ Complete |
| 8 — Frontend Design System | ✅ Complete |
| 9 — Trader Portal (5 pages) | ✅ Complete |
| 10 — Admin Portal (6 pages) | ✅ Complete |
| 11 — Integration & Wiring | ✅ Complete |
| 12 — Security + Performance | ⏳ Pending |

---

## API Test File

A comprehensive `.http` test file for VS Code REST Client is available at:

```
api-tests/ghana-tax-system.http
```

Covers all 14 API endpoints across Auth, Registration, TIN Lookup, USSD, Traders, Reports, and Audit Logs.
