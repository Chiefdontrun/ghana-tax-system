# Ghana Tax System — Development Handoff & Context Document

> **Generated:** 2026-07-15  
> **Purpose:** Full project context for a new AI-assisted development session.  
> **Paste this entire file as the foundation for a continuation prompt.**

---

## 1. Project Identity

| Field | Value |
|---|---|
| **Name** | Digital Taxation & Revenue Tracking System |
| **Short name** | Ghana Tax System |
| **Organisation** | Ghana District Assembly — Revenue Unit |
| **Purpose** | Multi-channel (web + USSD) platform for registering informal market traders, generating Tax Identification Numbers (TINs), and giving revenue officers a dashboard with KPI reporting, CSV export, and an immutable audit trail |
| **Intended users** | Two user groups: (1) Traders — register via web form or USSD; (2) Revenue officers — manage registrations via a secure admin portal |
| **Current stage** | **All 12 planned phases are complete.** The system is deployed and running in production on Vercel (frontend + backend serverless). The MongoDB Atlas connection credentials on the live deployment are currently broken (auth failure). Local development is fully functional. |
| **Design language** | Professional/government — Central University red/white portal style (`--cu-red: #8A1020`). TailwindCSS used throughout the frontend. |

---

## 2. Tech Stack

### Backend
| Layer | Technology |
|---|---|
| Framework | Django 4.2 + Django REST Framework 3.14 |
| Language | Python 3.12 |
| Primary database | MongoDB (via PyMongo 4.6 — **Django ORM is not used for app data**) |
| Auxiliary database | SQLite (minimal, only so Django management commands don't break — no app data stored here) |
| Cache / rate-limit backing | Redis 5 — falls back to `LocMemCache` if unavailable |
| Auth | Custom JWT (PyJWT 2.8) — access token + refresh token + OTP-pending token |
| Password hashing | bcrypt 4.1 |
| Email (OTP delivery) | Resend Python SDK 2.32.2 (`resend` package) |
| SMS (TIN notification) | Africa's Talking SDK — falls back to a `StubSMSProvider` when `AT_API_KEY` is not set |
| Config management | `python-decouple` — all secrets via `.env` / environment variables |
| Rate limiting | `django-ratelimit` 4.1 |
| CORS | `django-cors-headers` 4.3 |
| Deployment | Vercel serverless (backend `vercel.json` present) |

### Frontend
| Layer | Technology |
|---|---|
| Framework | React 18 + TypeScript 5.6 |
| Build tool | Vite 5.4 |
| Routing | React Router DOM 6.26 |
| State management | Zustand 4.5 (persisted to `sessionStorage`) |
| HTTP client | Axios 1.7 with automatic JWT refresh interceptor |
| Forms | React Hook Form 7.53 + Zod 3.23 + `@hookform/resolvers` |
| Charts | Recharts 2.12 |
| Styling | TailwindCSS 3.4 |
| Dates | date-fns 3.6 |
| Deployment | Vercel (frontend `vercel.json` present) |

### Infrastructure
| Layer | Technology |
|---|---|
| Containerisation | Docker + Docker Compose (`infra/` directory) |
| MongoDB indexes | `infra/mongo-init/init.js` — creates all production indexes |
| USSD gateway | Africa's Talking USSD webhook |

---

## 3. Repo Structure

```
ghana-tax-system-1/
├── PHASES.md              ← Original phase-by-phase build specification
├── LOG.md                 ← Chronological change log (newest first)
├── README.md              ← Setup docs
├── CONTINUE_PROMPT.md     ← Template for launching new phase agents
├── HANDOFF.md             ← This file
├── api-tests/
│   └── ghana-tax-system.http  ← VS Code REST Client tests (53 cases)
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env               ← Local secrets (not committed)
│   ├── .env.example
│   ├── vercel.json
│   ├── core/
│   │   ├── settings.py         ← Central Django config + all env vars
│   │   ├── urls.py             ← Root URL router
│   │   ├── middleware/
│   │   │   └── audit_middleware.py
│   │   └── utils/
│   │       ├── mongo.py        ← PyMongo singleton + collection constants
│   │       └── response.py     ← Standardised API response helpers
│   ├── apps/
│   │   ├── auth_app/           ← JWT login, OTP, admin user management
│   │   ├── registration/       ← Trader registration (web + USSD shared)
│   │   ├── tin/                ← TIN generation + public lookup
│   │   ├── reports/            ← Aggregation reports, CSV export, trader list
│   │   ├── audit/              ← Immutable audit log
│   │   ├── ussd/               ← USSD webhook + 5-step state machine
│   │   └── notifications/      ← SMS abstraction (AT + stub providers)
│   ├── management/
│   │   └── commands/
│   │       └── seed_demo_data.py  ← `python manage.py seed_demo_data`
│   └── tests/                 ← pytest test suite (73 passing tests)
└── frontend/
    ├── index.html
    ├── vite.config.ts
    ├── package.json
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── router.tsx          ← All routes defined here
        ├── store/
        │   ├── authStore.ts    ← Zustand: JWT tokens, role, admin identity
        │   └── uiStore.ts
        ├── lib/
        │   ├── api.ts          ← Axios instance with refresh interceptor
        │   └── auth.ts
        ├── components/         ← Shared UI primitives + layouts
        └── features/
            ├── admin/          ← Admin portal pages, hooks, components
            └── trader/         ← Trader portal pages (public)
```

---

## 4. Data Models

All collections live in MongoDB. There is no Django ORM model — data shapes are defined by the repository classes.

### `admins` collection
| Field | Type | Notes |
|---|---|---|
| `admin_id` | string (UUID) | Primary key |
| `email` | string | Unique, case-insensitive |
| `name` | string | Display name |
| `role` | string | `"SYS_ADMIN"` or `"TAX_ADMIN"` |
| `password_hash` | string | bcrypt hash — never returned in API responses |
| `is_active` | boolean | Soft-disable without deletion |
| `created_at` | datetime (UTC) | |
| `updated_at` | datetime (UTC) | |
| `last_login_at` | datetime / null | Stamped on every successful OTP verification |

### `otp_verifications` collection
| Field | Type | Notes |
|---|---|---|
| `otp_id` | string (UUID) | Unique |
| `admin_id` | string | Foreign key → admins |
| `otp_hash` | string | bcrypt hash of the 6-digit code |
| `expires_at` | datetime | 5 minutes from creation; MongoDB TTL index auto-deletes |
| `attempts` | int | Incremented on wrong code; max 5 before invalidation |
| `resend_count` | int | Max 3 resends allowed |
| `created_at` | datetime | Used for resend cooldown (60s) |
| `used_at` | datetime / null | Stamped when OTP is consumed |
| `invalidated_at` | datetime / null | Stamped when invalidated early |

### `traders` collection
| Field | Type | Notes |
|---|---|---|
| `trader_id` | string (UUID) | Primary key |
| `tin_number` | string | Format: `GH-TIN-XXXXXX`, unique |
| `name` | string | Trader's full name |
| `phone_number` | string | Normalised to `+233XXXXXXXXX`; unique (used for idempotency) |
| `business_type` | string | `food_vendor`, `clothing`, `electronics`, `services`, `agriculture`, `other` |
| `region` | string | Ghana region |
| `district` | string | |
| `market_name` | string | |
| `location_id` | string | Foreign key → locations |
| `channel` | string | `"web"` or `"ussd"` |
| `status` | string | `"active"` (only value currently written) |
| `ip_address` | string | Web channel only |
| `created_at` | datetime | |
| `updated_at` | datetime | |

### `businesses` collection
| Field | Type | Notes |
|---|---|---|
| `business_id` | string (UUID) | Primary key |
| `owner_trader_id` | string | Foreign key → traders |
| `business_type` | string | Mirrors trader's business_type |
| `tin_number` | string | Mirrors trader's TIN |
| `location_id` | string | Foreign key → locations |
| `created_at` | datetime | |

### `locations` collection
| Field | Type | Notes |
|---|---|---|
| `location_id` | string (UUID) | Primary key |
| `region` | string | |
| `district` | string | |
| `market_name` | string | |
| `created_at` | datetime | `find_or_create` logic — de-duplicated by (region, district, market_name) |

### `audit_logs` collection
| Field | Type | Notes |
|---|---|---|
| `event_id` | string (UUID) | |
| `actor_id` | string | Admin UUID or `"anonymous"` or `"system"` |
| `actor_role` | string | Admin role or `"anonymous"` / `"system"` |
| `action` | string | See actions below |
| `entity_type` | string | `"trader"`, `"admin"`, `"session"`, `"otp_verification"`, `"report"` |
| `entity_id` | string | ID of the entity acted upon |
| `channel` | string | `"admin"`, `"web"`, `"ussd"` |
| `ip_address` | string | |
| `user_agent` | string | |
| `before` / `after` | dict / null | State snapshot for change-diff |
| `details` | dict | Extra context (varies by action) |
| `created_at` | datetime | |

**Known audit actions:** `LOGIN_SUCCESS`, `LOGIN_FAIL`, `OTP_GENERATED`, `OTP_VERIFIED`, `OTP_FAILED`, `OTP_EXPIRED`, `OTP_RESENT`, `OTP_EMAIL_FAILED`, `CREATE_TRADER`, `DUPLICATE_REGISTRATION_ATTEMPT`, `CREATE_ADMIN`, `ROLE_CHANGE`, `STATUS_CHANGE`, `EXPORT_CSV`

### `ussd_sessions` collection
Managed by `USSDSessionStore`. Holds the multi-step USSD flow state (current state name + collected field values) keyed by Africa's Talking `sessionId`. Has a MongoDB TTL index for automatic expiry.

---

## 5. API Surface

All endpoints are prefixed relative to the Django server root (`http://localhost:8000` locally). Auth column: `Public` = no token required, `OTP` = OTP-pending JWT, `Any Admin` = any valid admin JWT, `TAX_ADMIN+` = TAX_ADMIN or SYS_ADMIN, `SYS_ADMIN` = SYS_ADMIN only.

### Auth — `/api/auth/`
| Method | Path | Auth | Rate limit | Description |
|---|---|---|---|---|
| POST | `/api/auth/login/` | Public | 10/min/IP | Validate email+password, send OTP email, return pending token |
| POST | `/api/auth/verify-otp/` | OTP | 10/min/IP | Verify 6-digit code, return access + refresh tokens |
| POST | `/api/auth/resend-otp/` | OTP | 5/min/IP | Resend OTP (60s cooldown, max 3 resends) |
| POST | `/api/auth/refresh/` | Public | 20/min/IP | Exchange refresh token for new access token |
| GET | `/api/auth/me/` | Any Admin | — | Return current admin profile |

### Admin User Management — `/api/admin/`
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/admin/users/` | SYS_ADMIN | List all admin accounts |
| POST | `/api/admin/users/` | SYS_ADMIN | Create a new admin account |
| PATCH | `/api/admin/users/<admin_id>/` | SYS_ADMIN | Update role or is_active |

### Trader Registration — `/api/`
| Method | Path | Auth | Rate limit | Description |
|---|---|---|---|---|
| POST | `/api/register/` | Public | 20/min/IP | Register a new trader, returns TIN. Idempotent on phone number. |

### TIN Lookup — `/api/tin/`
| Method | Path | Auth | Rate limit | Description |
|---|---|---|---|---|
| POST | `/api/tin/lookup/` | Public | 5/min/IP | Look up TIN by phone number |

### Traders — `/api/traders/`
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/traders/` | TAX_ADMIN+ | Paginated + filtered trader list (`?search=&channel=&business_type=&region=&district=&date_from=&date_to=&page=&page_size=`) |
| GET | `/api/traders/<trader_id>/` | TAX_ADMIN+ | Full trader profile |

### Reports — `/api/reports/`
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/reports/summary/` | TAX_ADMIN+ | Aggregated KPIs (`?period=7d\|30d\|all`). Redis-cached (45s TTL). |
| GET | `/api/reports/export/` | TAX_ADMIN+ | CSV download (`?channel=&business_type=&region=&district=&date_from=&date_to=`) |

### Audit Logs — `/api/audit-logs/`
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/audit-logs/` | SYS_ADMIN | Paginated audit log (`?action=&actor_id=&date_from=&date_to=&page=&page_size=`) |

### USSD — `/ussd/`
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/ussd/callback/` | Public (webhook) | Africa's Talking USSD webhook. Returns `CON` or `END` plain text. |

### Standard API Response Shape
```json
{
  "success": true,
  "message": "Human-readable message",
  "data": {}
}
```
Pagination adds `total`, `page`, `page_size` alongside `data`.

---

## 6. Roles & Permissions

| Role | What they can do |
|---|---|
| **Anonymous / Public** | Register as a trader, look up TIN by phone number, use USSD |
| **TAX_ADMIN** | Login → Dashboard KPIs → View trader list → View trader detail → Download CSV reports |
| **SYS_ADMIN** | Everything TAX_ADMIN can do, PLUS: view audit logs, create/update/deactivate admin accounts. Cannot change their own role (lockout prevention). |

Permission is enforced at two layers:
1. **View layer** — `IsAdminAuthenticated`, `IsTaxAdmin`, `IsSysAdmin` DRF permission classes in `apps/auth_app/permissions.py`
2. **Service layer** — RBAC assertions in `ReportsService` and `AuthService.list_admins()` as defence-in-depth

---

## 7. Current State

### Fully Working (locally)
- Complete admin authentication flow: login → OTP email → verify → JWT session
- OTP resend with cooldown (60s), max-resend limit (3), bcrypt-hashed codes
- Trader registration via web form with idempotency
- TIN generation (format: `GH-TIN-XXXXXX`, cryptographically random, guaranteed unique)
- Public TIN lookup by phone number
- Full admin portal: Dashboard KPIs, trader list with filters, trader detail, CSV export
- Audit log page (SYS_ADMIN only)
- USSD flow: 5-step registration + TIN lookup (via Africa's Talking webhook)
- Redis caching for reports summary (45s TTL, auto-invalidated on new registrations)
- JWT access token silent refresh (Axios interceptor)
- Rate limiting on all endpoints
- Seed data command: `python manage.py seed_demo_data`

### Partially Working / Caveats
- **Resend OTP email in production:** Requires a verified sender domain in Resend. Currently using `onboarding@resend.dev` (Resend's test address), which only delivers to the email address registered with the Resend account. OTP emails sent to `taxadmin1@demo.gov.gh` / `taxadmin2@demo.gov.gh` are silently redirected to `SEED_ADMIN_EMAIL` when `DJANGO_DEBUG=True`.
- **SMS notifications:** Falls back to `StubSMSProvider` (logs only) unless `AT_API_KEY` and `AT_USERNAME` are set. No real SMS is sent in default setup.
- **Rate limiting warning:** `django_ratelimit.W001` — the Redis-backed cache is not officially supported by `django-ratelimit`. Functionally works but shows a system check warning.

### Known Broken (production)
- **MongoDB Atlas auth failure on live Vercel deployment.** The `MONGODB_URI` environment variable on Vercel has incorrect credentials (wrong username/password for the Atlas database user). Fix: update the `MONGODB_URI` env var in Vercel project settings with the correct Atlas credentials and redeploy.

---

## 8. Recent Work (as of 2026-07-15)

The last debugging session focused on the Resend OTP email delivery:

1. **Fixed a critical bug in `email_service.py`** — The Resend Python SDK v2.32.2 returns a `TypedDict` (dict), not an object, from `Emails.send()`. The old code used `getattr(response, "id", None)` which always returned `None` on a dict, causing every successful email send to raise `EmailDeliveryError`. Fixed to check `response.get("id")` when response is a dict.

2. **Added local dev bypass** — When `DJANGO_DEBUG=True` and `RESEND_API_KEY` is empty, OTP emails are intercepted and the code is printed to the Django server console log instead. Allows full local testing without an email provider.

3. **Added test-mode email redirect** — When `DJANGO_DEBUG=True` and a `RESEND_API_KEY` is present, all OTP emails that would go to a non-owner email (e.g. `taxadmin1@demo.gov.gh`) are transparently redirected to `SEED_ADMIN_EMAIL`. This is required because Resend's free test sender (`onboarding@resend.dev`) can only deliver to the account owner's email.

4. **Diagnosed production MongoDB auth failure** — Identified as wrong Atlas credentials in Vercel env vars (not a code issue).

**File last modified:** `backend/apps/auth_app/email_service.py`

---

## 9. Open Issues & Tech Debt

| # | Severity | Area | Description |
|---|---|---|---|
| 1 | CRITICAL | Production | MongoDB Atlas authentication fails on Vercel. Fix: update `MONGODB_URI` in Vercel environment variables with correct Atlas DB user credentials. |
| 2 | Medium | Email | Resend sender domain not configured. Currently using `onboarding@resend.dev` which only delivers to the Resend account owner. Production deployment needs a verified custom domain in Resend and the `DEFAULT_FROM_EMAIL` env var updated. |
| 3 | Medium | Email | The `DEBUG`-mode email redirect (`SEED_ADMIN_EMAIL`) is a development workaround, not a production pattern. Should be removed or guarded strictly before going live. |
| 4 | Medium | SMS | `AT_API_KEY` and `AT_USERNAME` are not set. All SMS falls back to `StubSMSProvider` — no actual SMS is sent after trader registration. |
| 5 | Low | Rate limiting | `django_ratelimit.W001` warning about Redis cache not being officially supported. Low impact — functionally works. |
| 6 | Low | Settings | When Redis is unreachable, the fallback `CACHES` config still tries to use `RedisCache` (not `LocMemCache`). This is a copy-paste bug in the fallback branch of `settings.py` (lines 110-117). The `RATELIMIT_ENABLE = False` guard prevents crashes but cache won't actually work. |
| 7 | Low | Frontend | No logout button / session expiry UI feedback beyond redirect to `/admin/login`. |
| 8 | Low | Frontend | `TradersPage.tsx` is a minimal stub — it delegates to `TraderTable` but may not have full filter UI wired. |
| 9 | Low | Backend | `apps/notifications/repository.py`, `services.py`, `views.py` are essentially empty stubs. |
| 10 | Low | Migrations | 14 unapplied Django migrations on first run (for `auth` and `contenttypes` built-in apps). Run `python manage.py migrate` after first setup. These are Django built-in migrations unrelated to app data. |

---

## 10. File Location Reference

### Backend — Key Files

| Purpose | Path |
|---|---|
| Django settings (all config) | `backend/core/settings.py` |
| Root URL router | `backend/core/urls.py` |
| MongoDB singleton + collection names | `backend/core/utils/mongo.py` |
| Standard response helpers | `backend/core/utils/response.py` |
| Auth service (login, OTP, token refresh, admin CRUD) | `backend/apps/auth_app/services.py` |
| Auth views | `backend/apps/auth_app/views.py` |
| Auth URLs | `backend/apps/auth_app/urls.py` |
| Admin management URLs | `backend/apps/auth_app/admin_urls.py` |
| Admin repository (MongoDB) | `backend/apps/auth_app/repository.py` |
| OTP repository (MongoDB) | `backend/apps/auth_app/otp_repository.py` |
| JWT utilities | `backend/apps/auth_app/jwt_utils.py` |
| DRF permission classes | `backend/apps/auth_app/permissions.py` |
| JWT authentication backend | `backend/apps/auth_app/authentication.py` |
| Email service (Resend integration) | `backend/apps/auth_app/email_service.py` |
| Trader registration service | `backend/apps/registration/services.py` |
| Trader/Business/Location repositories | `backend/apps/registration/repository.py` |
| Registration views | `backend/apps/registration/views.py` |
| TIN generation service | `backend/apps/tin/services.py` |
| Reports aggregation service | `backend/apps/reports/services.py` |
| Reports views (summary, export, trader list/detail) | `backend/apps/reports/views.py` |
| Audit repository | `backend/apps/audit/repository.py` |
| Audit log list view | `backend/apps/audit/views.py` |
| USSD state machine | `backend/apps/ussd/state_machine.py` |
| USSD session store (Redis/Mongo) | `backend/apps/ussd/session_store.py` |
| USSD webhook view | `backend/apps/ussd/views.py` |
| SMS notification service | `backend/apps/notifications/services.py` |
| Seed data command | `backend/management/commands/seed_demo_data.py` |
| Test suite | `backend/tests/` |
| Backend env vars | `backend/.env` |

### Frontend — Key Files

| Purpose | Path |
|---|---|
| App entry point | `frontend/src/main.tsx` |
| Route definitions (all routes) | `frontend/src/router.tsx` |
| Auth store (Zustand — JWT, role, admin ID) | `frontend/src/store/authStore.ts` |
| Axios instance + refresh interceptor | `frontend/src/lib/api.ts` |
| Admin auth hook (login, verifyOtp, resendOtp) | `frontend/src/features/admin/hooks/useAdminAuth.ts` |
| Reports + traders data hooks | `frontend/src/features/admin/hooks/useReports.ts` and `useTraders.ts` |
| Admin — Login page | `frontend/src/features/admin/pages/LoginPage.tsx` |
| Admin — OTP verification page | `frontend/src/features/admin/pages/VerifyOtpPage.tsx` |
| Admin — Dashboard (KPIs + charts) | `frontend/src/features/admin/pages/DashboardPage.tsx` |
| Admin — Traders list | `frontend/src/features/admin/pages/TradersPage.tsx` |
| Admin — Trader detail | `frontend/src/features/admin/pages/TraderDetailPage.tsx` |
| Admin — Reports (CSV export) | `frontend/src/features/admin/pages/ReportsPage.tsx` |
| Admin — Audit logs | `frontend/src/features/admin/pages/AuditLogsPage.tsx` |
| Trader — Landing page | `frontend/src/features/trader/pages/LandingPage.tsx` |
| Trader — Registration form | `frontend/src/features/trader/pages/RegisterPage.tsx` |
| Trader — Registration success | `frontend/src/features/trader/pages/RegistrationSuccessPage.tsx` |
| Trader — Check TIN | `frontend/src/features/trader/pages/CheckTinPage.tsx` |
| Trader — Help / FAQ | `frontend/src/features/trader/pages/HelpPage.tsx` |
| Protected route guard | `frontend/src/components/layout/ProtectedRoute.tsx` |
| Admin layout (sidebar nav) | `frontend/src/components/layout/AdminLayout.tsx` |

---

## 11. Local Development Setup

### Prerequisites
- Python 3.12
- Node.js 20+
- MongoDB (local) OR a MongoDB Atlas URI
- Redis (optional — falls back gracefully)

### Backend
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in values
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver
# Server runs at http://localhost:8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# App runs at http://localhost:5173
```

### Key `.env` values (backend)
```env
MONGO_URI=mongodb://localhost:27017/ghana_tax_db
REDIS_URL=redis://localhost:6379/0
USE_REDIS_CACHE=false
DJANGO_SECRET_KEY=<any-long-random-string>
JWT_SECRET_KEY=<any-long-random-string>
DJANGO_DEBUG=True
SEED_ADMIN_EMAIL=<your-email>
SEED_ADMIN_PASSWORD=DemoPass123!
RESEND_API_KEY=
DEFAULT_FROM_EMAIL=onboarding@resend.dev
```

### Demo Accounts (seeded by `seed_demo_data`)
| Role | Email | Password |
|---|---|---|
| SYS_ADMIN | sysadmin@demo.gov.gh | DemoPass123! |
| TAX_ADMIN | taxadmin1@demo.gov.gh | DemoPass123! |
| TAX_ADMIN | taxadmin2@demo.gov.gh | DemoPass123! |

> OTP note (local dev): With `RESEND_API_KEY` left empty, OTP codes are printed to the Django server console. With a Resend API key set, codes for non-owner accounts are redirected to `SEED_ADMIN_EMAIL`.

---

## 12. Deployment (Vercel)

Both the frontend and backend are deployed to Vercel.

- **Frontend:** `frontend/vercel.json` — static build, all routes rewrite to `index.html`
- **Backend:** `backend/vercel.json` — serverless Django

### Required Vercel Environment Variables
```
MONGODB_URI          <- Atlas connection string with correct user credentials <- CURRENTLY BROKEN
MONGO_DB_NAME=ghana_tax_db
REDIS_URL            <- Upstash or similar serverless Redis
USE_REDIS_CACHE=true
DJANGO_SECRET_KEY
JWT_SECRET_KEY
DJANGO_DEBUG=False
ALLOWED_HOSTS=<your-vercel-domain>,<custom-domain>
CORS_ALLOWED_ORIGINS=https://<your-frontend-domain>
DEFAULT_FROM_EMAIL=Ghana Tax System <no-reply@yourdomain.com>
RESEND_API_KEY       <- From resend.com dashboard
SEED_ADMIN_EMAIL     <- Developer's real email (owner of Resend account)
SEED_ADMIN_PASSWORD
AT_API_KEY           <- Africa's Talking (optional)
AT_USERNAME          <- Africa's Talking (optional)
```

---

## 13. [Phase A / Step A2] Assessment calculation & generation service — 2026-07-15

**Status:** Complete

**What was built:**
- `TaxService` calculating exact assessment amounts based on `FIXED` and `PERCENTAGE_TURNOVER` rules.
- Precedence logic (district > region > assembly-wide) for active tax schedules matching the trader context.
- Hooks automatically generating assessments post-registration in both Web and USSD pathways.
- Idempotent API structures enforcing "one generation per year per tax category".
- Batch assessment generator aggregating `needs_turnover` and `missing_schedule` events instead of crashing.
- Custom exceptions `TurnoverRequiredError` and `RateScheduleNotFoundError` for precise error catching.

**Files created/modified:**
- `backend/apps/tax/exceptions.py` (New)
- `backend/apps/tax/services.py` (Modified heavily)
- `backend/apps/registration/services.py` (Modified hooks)
- `backend/tests/test_tax.py` (Tests added)

**Deviations from spec:**
- Handled floating-point rounding accurately using `Decimal` quantization rather than standard `round()` to guarantee reproducible currency figures. 

**New facts for the next step (exact function signatures, exception names, rounding behavior chosen, due_date convention used, etc.):**
- Rounding behavior is `ROUND_HALF_UP` out of `Decimal` quantized to `.quantize(Decimal("1"))` resulting in the nearest integer pesewa.
- Due date logic is Dec 31st of the evaluation year specifically for `"BOP"` schedules.
- `TurnoverRequiredError` raises when `% turnover` calculation triggers without turnover data.
- `RateScheduleNotFoundError` raises when no exact-region/district or global fallback match can be established.
- Idempotency evaluates matches on `(business_id, tax_category, period_label)`.

**Open questions / things that need a decision:**
- How should un-collected `PERCENTAGE_TURNOVER` instances be targeted by admin staff if `admin_batch` skips them?

**Tests:** 
- `backend/tests/test_tax.py`: 9 out of 9 tests pass. Success verifying bounds capping, exception handling, batch accumulation, exact value mapping, and DB idempotency constraints.
