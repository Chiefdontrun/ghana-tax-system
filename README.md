# Digital Taxation & Revenue Tracking System

**Ghana District Assembly — Revenue Unit**

A District Assembly digital tax platform for **informal-sector traders**. It covers business registration, Tax Identification Number (TIN) issuance, Business Operating Permit (BOP) assessment, and mobile-money payment over **two channels**: a web portal (traders + revenue officers) and **USSD** (`*928*309#` via Arkesel) for feature phones. Money is stored as integer **pesewas**; amounts shown to users as GHS where appropriate.

> **Docs roles:** this **README** is the project overview for setup, features, and limitations (final-year submission). **`LOG.md`** is the chronological build history. **`HANDOFF.md`** is a dense context dump for continuing development sessions—not a second user README. Prefer this file for “what the system is”; use `LOG.md` for “what changed when.”

---

## Core features (as shipped)

| Area | What works |
|------|------------|
| **Web registration** | Multi-step form: personal info → business type (**Hawker first**) → **monthly income bracket** → location → TIN + optional SMS |
| **USSD registration** | `*928*309#`: name → business type (Hawker = option 1) → income bracket → region → market → confirm → TIN |
| **TIN lookup** | Web + USSD by phone number |
| **BOP tax engine** | Assembly-wide rate schedules (`FIXED` / `PERCENTAGE_TURNOVER`); post-registration auto-assessment; district override support; exception queue for `NEEDS_TURNOVER` / `MISSING_SCHEDULE` |
| **Income brackets** | `BRACKET_1`…`BRACKET_4` on the **business** record; representative annual income used as turnover for % schedules; **25% affordability cap** on amount due when a bracket is set |
| **Trader portal** | Phone OTP login (Arkesel SMS when configured), dashboard, MoMo payment via Paystack (sandbox), receipt view |
| **USSD pay** | Outstanding assessment select → network → charge; OTP path **ends** with SMS-confirmation guidance (no long in-USSD OTP wait) |
| **Admin portal** | Email+password + OTP (Resend), traders, tax rate schedules, assessments/payments, assessment exceptions, reports KPIs + CSV export, audit logs |
| **Seed data** | `python manage.py seed_demo_data` — locations, admins, traders, schedules (incl. hawker + cap demo), assessments via `TaxService`, sample payments |
| **Cron safety net** | `POST /api/tax/payments/run-pending-check/` with `X-Cron-Secret` for PENDING payment reconciliation |

---

## Tech stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, TypeScript, Vite, TailwindCSS, Zustand, React Hook Form + Zod, Recharts, Axios |
| Backend | **Python 3.12** (pinned in `backend/runtime.txt` for Vercel) · Django 4.2 · DRF 3.14 · PyMongo 4.6 |
| Why 3.12 | Django 4.2 + Python **3.14** can break template error rendering (`BaseContext` / `dicts`). Do **not** “upgrade” Vercel to 3.14 without re-validating. Local 3.14 may still run tests with a conftest safety patch. |
| Data | MongoDB (app data) · SQLite only so Django management commands work · Redis optional (cache/rate-limit; LocMem fallback) |
| Auth | Custom JWT (PyJWT) + bcrypt · Admin OTP email via **Resend** · Trader OTP SMS via **Arkesel** (or Stub) |
| USSD | **Arkesel** shortcode `*928*309#` → `POST /ussd/callback/` (JSON). Legacy Africa’s Talking form-encoded shape still accepted for unit tests only. |
| SMS | **Active:** Arkesel when `ARKESEL_SMS_API_KEY` is set · **Not selected:** Brevo, Africa’s Talking (classes remain on disk) |
| Payments | **Paystack** MoMo when `PAYSTACK_SECRET_KEY` is set · else Stub · **Sandbox/test keys only** in this project |
| Deploy | Vercel (backend serverless + frontend) · Docker Compose under `infra/` for local stacks |

---

## Architecture overview

**registration** — Web/USSD trader onboarding, locations, businesses (`business_type`, `income_bracket`), hooks into TIN + tax assessment.

**tin** — Unique `GH-TIN-…` generation and public phone lookup.

**tax** — Rate schedules, assessment calculation (`FIXED` / `PERCENTAGE_TURNOVER` + min/max + **affordability cap**), generation, batch, exception queue APIs.

**payments** — Initiate MoMo charge, status, optional OTP submit, Paystack webhook, pending-payment cron (`CRON_SECRET`).

**notifications** — `NotificationService` selects **Arkesel → Stub** only (TIN SMS, trader OTP, payment receipts).

**ussd** — State machine + Arkesel adapter (`newSession` + single-step `userData`); registration, TIN check, pay assessment; optional capture endpoint for debugging.

**trader_auth** — Trader phone OTP request/verify + JWT for trader portal.

**auth_app** — Admin login, email OTP, refresh, RBAC (`SYS_ADMIN` / `TAX_ADMIN`), admin user management.

**reports** — Registration + tax KPI summary (cached), trader list/detail, CSV export (`traders` / `tax` / `payments`).

**audit** — Immutable audit log API and writers across registration, tax, USSD, payments.

### MongoDB collections (`core/utils/mongo.py`)

| Collection | Stores |
|------------|--------|
| `traders` | Registered traders (name, phone, TIN, channel, region/district, …) |
| `businesses` | Businesses (`business_type`, **`income_bracket`**, owner, TIN, location) |
| `locations` | Markets / regions / districts |
| `admins` | Admin accounts + roles |
| `audit_logs` | Immutable audit trail (incl. `ASSESSMENT_CAPPED_AFFORDABILITY`) |
| `ussd_sessions` | In-progress USSD session state |
| `otp_verifications` | Admin email OTPs |
| `trader_otp_verifications` | Trader SMS OTP hashes |
| `tax_rate_schedules` | BOP (etc.) FIXED / PERCENTAGE_TURNOVER rates |
| `tax_assessments` | Amount due/paid, status, period, schedule link |
| `tax_payments` | Payment attempts (Paystack refs, channel, status) |
| `tax_assessment_exceptions` | Open/resolved `NEEDS_TURNOVER` / `MISSING_SCHEDULE` |

### Business types (display / whitelist order)

From `apps/registration/validators.py` — **Hawker first**:

`hawker`, `food_vendor`, `clothing`, `electronics`, `services`, `agriculture`, `wholesale`, `retail`, `artisan`, `other`

### Income brackets & affordability cap

From `apps/tax/constants.py` (`AFFORDABILITY_CAP_FRACTION = 0.25`):

| Code | Monthly display | Representative annual income | Cap (25%) |
|------|-----------------|-----------------------------:|----------:|
| `BRACKET_1` | GHC 100 – 400 | 300 000 pesewas (GHC 3 000) | 75 000 (GHC 750) |
| `BRACKET_2` | GHC 401 – 1 000 | 840 000 (GHC 8 400) | 210 000 |
| `BRACKET_3` | GHC 1 001 – 3 000 | 2 400 000 (GHC 24 000) | 600 000 |
| `BRACKET_4` | GHC 3 001+ | 4 800 000 (GHC 48 000) | 1 200 000 |

Businesses **without** `income_bracket` (legacy) skip the cap. Seed demo uses hawker FIXED **GHC 2 000** so BRACKET_1 bills clamp to **GHC 750**.

---

## Production URLs (reference)

| Surface | URL |
|---------|-----|
| API / USSD callback | `https://ghana-tax-system-hh6f.vercel.app` · `POST /ussd/callback/` |
| Arkesel shortcode | `*928*309#` (dashboard callback must point at production `/ussd/callback/`) |
| Frontend | Deployed separately on Vercel (set `VITE_API_BASE_URL` to the API host) |

After **any** USSD code change, probe Production before trusting the shortcode (stale Production deploy has already caused missing screens).

---

## Setup

### Prerequisites

- Python **3.12** recommended (3.14 may work for tests with project conftest patch)
- Node.js 20+
- MongoDB 7 (local or Atlas)
- Redis optional (set `USE_REDIS_CACHE=False` for LocMem)
- Docker Compose optional (`infra/`)

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Fill secrets — see Environment variables below. Minimum for local API:
#   MONGO_URI, MONGO_DB_NAME, JWT_SECRET_KEY, DJANGO_SECRET_KEY

python manage.py seed_demo_data   # optional demo data
python manage.py runserver        # http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
echo "VITE_API_BASE_URL=http://localhost:8000" > .env.local   # Windows: set file contents manually
npm run dev   # http://localhost:5173
```

### Docker Compose

```bash
cd infra
cp .env.example .env   # if present; otherwise configure backend/.env and compose env
docker compose up --build
# Then: docker compose exec backend python manage.py seed_demo_data
```

### Seed demo accounts

Defaults (override with `SEED_ADMIN_*`):

| Role | Email | Password |
|------|-------|----------|
| SYS_ADMIN | sysadmin@demo.gov.gh | DemoPass123! |
| TAX_ADMIN | taxadmin1@demo.gov.gh | DemoPass123! |
| TAX_ADMIN | taxadmin2@demo.gov.gh | DemoPass123! |

Seed also creates traders, BOP schedules (including **hawker**), assessments via `TaxService`, exceptions, and sample payments for reports demos.

---

## Environment variables

**Source of truth:** `backend/.env.example` (keep Vercel Production in parity). Summary:

| Variable | Status | Purpose |
|----------|--------|---------|
| `MONGO_URI` / `MONGODB_URI` | **Active** | MongoDB connection (Atlas alias supported) |
| `MONGO_DB_NAME` | **Active** | Database name |
| `REDIS_URL` | **Active** | Redis for cache / sessions when used |
| `USE_REDIS_CACHE` | **Active** | `False` → LocMem fallback (typical local) |
| `REPORTS_CACHE_TTL` | **Active** | Reports summary cache TTL (seconds) |
| `JWT_SECRET_KEY` | **Active** | Sign JWTs (must match across deploys) |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` / `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | **Active** | Token lifetimes |
| `DJANGO_SECRET_KEY` / `DJANGO_DEBUG` | **Active** | Django core |
| `ALLOWED_HOSTS` / `CORS_ALLOWED_ORIGINS` | **Active** | Host + CORS |
| `CORS_ALLOWED_ORIGIN_REGEXES` | **Active** (optional) | e.g. Vercel preview hosts |
| `RESEND_API_KEY` / `DEFAULT_FROM_EMAIL` | **Active** | Admin login OTP email |
| `EMAIL_*` | Optional | Only if using SMTP backend |
| `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` | **Active** (seed) | Demo SYS_ADMIN |
| `PAYSTACK_SECRET_KEY` / `PAYSTACK_PUBLIC_KEY` / `PAYSTACK_BASE_URL` | **Active** when set | MoMo charges — **use `sk_test_` only** |
| `ARKESEL_SMS_API_KEY` | **Active** when set | SMS (else Stub) |
| `ARKESEL_SENDER_ID` | **Active** / **pending external approval** | e.g. `GHREVENUE` — must be approved in Arkesel for reliable handset delivery |
| `BREVO_API_KEY` / `BREVO_SMS_*` | **Legacy / unused** | Class kept; **not** selected by `NotificationService` |
| `AT_API_KEY` / `AT_USERNAME` / `AT_SENDER_ID` | **Legacy / unused** | SMS provider not selected; USSD is Arkesel |
| `CRON_SECRET` | **Active** when set | Auth for pending-payment poller |
| `VERCEL_URL` | Platform | Appended to `ALLOWED_HOSTS` on Vercel |

USSD shortcode and callback URL are configured in the **Arkesel dashboard**, not via a dedicated env var.

---

## Main API surface

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| POST | `/api/auth/login/` | Public | Admin → may return pending OTP token |
| POST | `/api/auth/verify-otp/` | Public | Complete admin login |
| POST | `/api/auth/refresh/` | Public | Refresh JWT |
| GET | `/api/auth/me/` | Admin JWT | Current admin |
| POST | `/api/register/` | Public | Web registration (**requires `income_bracket`**) |
| GET | `/api/my-businesses/` | Trader JWT | Trader’s businesses |
| POST | `/api/tin/lookup/` | Public | TIN by phone |
| POST | `/api/trader-auth/request-otp/` | Public | Trader SMS OTP |
| POST | `/api/trader-auth/verify-otp/` | Public | Body: `phone_number` + `code` |
| POST | `/ussd/callback/` | Public | Arkesel USSD webhook |
| GET | `/api/traders/` | TAX_ADMIN+ | List / filter traders |
| GET | `/api/reports/summary/` | TAX_ADMIN+ | Registration + nested tax KPIs |
| GET | `/api/reports/export/` | TAX_ADMIN+ | CSV (`type=traders\|tax\|payments`) |
| GET | `/api/audit-logs/` | SYS_ADMIN | Audit trail |
| * | `/api/tax/rate-schedules/` | Admin | CRUD-style list/create (SYS_ADMIN create) |
| * | `/api/tax/assessments/` | Admin | List / detail / batch generate |
| * | `/api/tax/assessment-exceptions/` | Admin | List + resolve-turnover / retry |
| POST | `/api/tax/payments/initiate/` | Trader JWT | Start MoMo payment |
| GET | `/api/tax/payments/<id>/status/` | Trader JWT | Payment status |
| POST | `/api/tax/payments/run-pending-check/` | `X-Cron-Secret` | Pending payment poller |
| GET/POST | `/api/cron/check-pending-payments/` | `X-Cron-Secret` | Alternate cron path |

Trailing slashes matter (`APPEND_SLASH`); prefer always including `/`.

### USSD probe (Arkesel JSON — production-shaped)

```bash
# newSession=true, userData=shortcode → main menu
# newSession=false, userData=1 → register → name → Hawker menu → Monthly income → …
curl -X POST https://ghana-tax-system-hh6f.vercel.app/ussd/callback/ \
  -H "Content-Type: application/json" \
  -d "{\"sessionID\":\"demo1\",\"userID\":\"x\",\"newSession\":true,\"msisdn\":\"233201234567\",\"userData\":\"*928*309#\",\"network\":\"MTN\"}"
```

Legacy form-encoded Africa’s Talking-style posts still work for local unit tests (accumulating `text` with `*`).

---

## Testing

```bash
cd backend
# Prefer project venv with requirements installed
pytest tests/ -q
```

- Tests live under `backend/tests/` (pytest + pytest-django; real Mongo via `conftest` — local or Atlas from `MONGO_URI`).
- As of **2026-07-17**, collection size is on the order of **~170+** test functions; run the full suite for a single pass/fail count. Phase G’s formal full-suite number should be recorded in `LOG.md` when that pass finishes.
- Recent green subsets (see `LOG.md`): registration + USSD + tax packages, Arkesel adapter tests, payment provider unit tests, pending-payment check, tax reports KPIs.

Scratch/debug test files (e.g. root `test_pay_debug.py`) must not ship—remove if reintroduced.

---

## Known limitations & external dependencies

State these plainly for academic integrity:

| Item | Status |
|------|--------|
| **Arkesel SMS sender ID** (`GHREVENUE` / dashboard config) | API may return success while **handset delivery** waits on Arkesel approval / credits / network |
| **MTN shortcode / network provisioning** | Historical live quirks with Arkesel; prefer a network confirmed working for handset dial-throughs |
| **Paystack** | **Sandbox / test keys only** — not production MoMo settlement |
| **AirtelTigo MoMo** | Offered in USSD/network menus; **never live-verified** against real Paystack |
| **Overpayment / refund** | No automated refund workflow; excess handling is manual/ops |
| **Brevo SMS** | Code retained, **not** on the active selection path (Arkesel → Stub only) |
| **Africa’s Talking** | **Not** the live USSD or SMS provider; legacy SMS class + form-encoded test adapter only |
| **External 5‑minute payment cron** | Endpoint exists; operator must set `CRON_SECRET` and a real scheduler (Vercel Hobby cron is daily only) |
| **Physical handset** | Some “live” verifications use production HTTP Arkesel payloads when no phone is available—confirm shortcode on device after deploys |
| **Vercel Production lag** | Git `main` can be ahead of Production; always re-probe USSD after deploy |

---

## Project layout (high level)

```
├── README.md              ← this file
├── LOG.md                 ← chronological change log (newest first)
├── HANDOFF.md             ← dense AI/session handoff context
├── PHASES.md              ← original build plan (historical)
├── api-tests/             ← VS Code REST Client .http samples
├── backend/               ← Django API, apps/, tests/, runtime.txt, vercel.json
├── frontend/              ← React trader + admin UI
└── infra/                 ← Docker Compose, mongo-init indexes, nginx
```

---

## License / academic use

Final-year project software for District Assembly informal-sector revenue collection demonstration. Configure secrets and third-party accounts (Arkesel, Paystack, Resend, MongoDB Atlas) for your own environment; do not commit real API keys.
