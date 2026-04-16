# Digital Taxation & Revenue Tracking System

# Phase Plan — Ghana District Assembly Revenue Unit

> **System:** Multi-channel tax registration & monitoring platform
> **Stack:** React + TypeScript + TailwindCSS | Python 3.10 + Django REST Framework | MongoDB | JWT | Africa's Talking USSD
> **Architecture:** Monorepo — `/backend`, `/frontend`, `/infra`
> **Design:** Central University red/white portal style (`--cu-red: #8A1020`)
>
> Each phase is **independently executable by a separate agent**.
> After completing any phase, the agent MUST update `LOG.md` with all files created/modified.
> Before starting any phase, the agent MUST read `LOG.md` to understand current state.

---

## MONOREPO STRUCTURE (TARGET — all phases build toward this)

```
ghana-tax-system/
├── PHASES.md                        ← This file
├── LOG.md                           ← Change log (updated every phase)
├── README.md                        ← Setup & docs (Phase 1)
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── core/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   └── audit_middleware.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── mongo.py             ← PyMongo connection singleton
│   │       ├── response.py          ← Standard API response helpers
│   │       └── pagination.py
│   ├── apps/
│   │   ├── auth_app/
│   │   │   ├── __init__.py
│   │   │   ├── urls.py
│   │   │   ├── views.py
│   │   │   ├── serializers.py
│   │   │   ├── services.py          ← Auth business logic
│   │   │   └── repository.py        ← MongoDB read/write for admins
│   │   ├── registration/
│   │   │   ├── __init__.py
│   │   │   ├── urls.py
│   │   │   ├── views.py
│   │   │   ├── serializers.py
│   │   │   ├── services.py          ← Registration business logic
│   │   │   └── repository.py        ← MongoDB read/write for traders
│   │   ├── tin/
│   │   │   ├── __init__.py
│   │   │   ├── urls.py
│   │   │   ├── views.py
│   │   │   ├── serializers.py
│   │   │   ├── services.py          ← TIN generation algorithm
│   │   │   └── repository.py
│   │   ├── reports/
│   │   │   ├── __init__.py
│   │   │   ├── urls.py
│   │   │   ├── views.py
│   │   │   ├── serializers.py
│   │   │   ├── services.py          ← Aggregation pipelines
│   │   │   └── repository.py
│   │   ├── audit/
│   │   │   ├── __init__.py
│   │   │   ├── urls.py
│   │   │   ├── views.py
│   │   │   └── repository.py        ← Audit log writes/reads
│   │   ├── ussd/
│   │   │   ├── __init__.py
│   │   │   ├── urls.py
│   │   │   ├── views.py             ← Webhook receiver
│   │   │   ├── state_machine.py     ← USSD flow logic
│   │   │   └── session_store.py     ← Redis/Mongo session persistence
│   │   └── notifications/
│   │       ├── __init__.py
│   │       ├── services.py          ← SMS stub + provider abstraction
│   │       └── providers/
│   │           ├── __init__.py
│   │           ├── base.py
│   │           └── africas_talking.py
│   ├── management/
│   │   └── commands/
│   │       └── seed_demo_data.py    ← python manage.py seed_demo_data
│   └── tests/
│       ├── test_tin.py
│       ├── test_registration.py
│       ├── test_ussd.py
│       ├── test_auth.py
│       └── test_reports.py
├── frontend/
│   ├── index.html
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── package.json
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── router.tsx               ← React Router config
│       ├── styles/
│       │   ├── globals.css          ← CSS variables (CU theme)
│       │   └── theme.ts             ← Tailwind theme tokens
│       ├── lib/
│       │   ├── api.ts               ← Axios instance + interceptors
│       │   ├── auth.ts              ← JWT helpers
│       │   └── utils.ts
│       ├── components/
│       │   ├── ui/
│       │   │   ├── Button.tsx
│       │   │   ├── Input.tsx
│       │   │   ├── Card.tsx
│       │   │   ├── Table.tsx
│       │   │   ├── Badge.tsx
│       │   │   ├── Modal.tsx
│       │   │   ├── Spinner.tsx
│       │   │   └── Alert.tsx
│       │   ├── layout/
│       │   │   ├── PublicLayout.tsx
│       │   │   ├── AdminLayout.tsx
│       │   │   ├── Header.tsx       ← "DISTRICT ASSEMBLY – REVENUE UNIT" strip
│       │   │   ├── Sidebar.tsx
│       │   │   └── Footer.tsx
│       │   └── charts/
│       │       ├── BarChart.tsx
│       │       ├── LineChart.tsx
│       │       └── DonutChart.tsx
│       ├── features/
│       │   ├── trader/
│       │   │   ├── pages/
│       │   │   │   ├── LandingPage.tsx
│       │   │   │   ├── RegisterPage.tsx
│       │   │   │   ├── RegistrationSuccessPage.tsx
│       │   │   │   ├── CheckTinPage.tsx
│       │   │   │   └── HelpPage.tsx
│       │   │   ├── components/
│       │   │   │   ├── RegistrationForm.tsx
│       │   │   │   └── TinDisplay.tsx
│       │   │   └── hooks/
│       │   │       └── useRegistration.ts
│       │   └── admin/
│       │       ├── pages/
│       │       │   ├── LoginPage.tsx
│       │       │   ├── DashboardPage.tsx
│       │       │   ├── TradersPage.tsx
│       │       │   ├── TraderDetailPage.tsx
│       │       │   ├── ReportsPage.tsx
│       │       │   └── AuditLogsPage.tsx
│       │       ├── components/
│       │       │   ├── StatsCard.tsx
│       │       │   ├── TraderTable.tsx
│       │       │   ├── FilterBar.tsx
│       │       │   ├── ReportSummary.tsx
│       │       │   └── AuditTable.tsx
│       │       └── hooks/
│       │           ├── useAdminAuth.ts
│       │           ├── useTraders.ts
│       │           └── useReports.ts
│       └── store/
│           ├── authStore.ts         ← Zustand or Context
│           └── uiStore.ts
└── infra/
    ├── docker-compose.yml
    ├── docker-compose.dev.yml
    ├── .env.example
    ├── nginx/
    │   └── nginx.conf
    └── mongo-init/
        └── init.js                  ← MongoDB index creation script
```

---

## PHASE OVERVIEW TABLE

| Phase | Title                                   | Depends On | Complexity |
| ----- | --------------------------------------- | ---------- | ---------- |
| 1     | Project Scaffold & Infra                | —          | Low        |
| 2     | MongoDB Data Layer & Seed               | 1          | Medium     |
| 3     | Backend: Auth Module (JWT + RBAC)       | 2          | Medium     |
| 4     | Backend: Registration + TIN Module      | 3          | High       |
| 5     | Backend: USSD Gateway Module            | 4          | High       |
| 6     | Backend: Reports, Audit & Admin APIs    | 3, 4       | Medium     |
| 7     | Backend: Notifications Module + Tests   | 4, 5, 6    | Medium     |
| 8     | Frontend: Design System + Shared Layout | 1          | Medium     |
| 9     | Frontend: Trader Portal (5 pages)       | 8          | Medium     |
| 10    | Frontend: Admin Portal (6 pages)        | 8, 3, 6    | High       |
| 11    | Integration & End-to-End Wiring         | All        | High       |
| 12    | Testing Suite                           | All        | Medium     |

---

---

## PHASE 1 — Project Scaffold & Infrastructure

**Agent Instructions:** Read LOG.md first. Create the full monorepo skeleton with all config files. Do NOT implement logic yet — only structure, configuration, and tooling.

**Depends On:** Nothing

### 1.1 — Monorepo Root & Infra

**Files to Create:**

```
/ghana-tax-system/README.md
/ghana-tax-system/.gitignore
/ghana-tax-system/infra/docker-compose.yml
/ghana-tax-system/infra/docker-compose.dev.yml
/ghana-tax-system/infra/.env.example
/ghana-tax-system/infra/nginx/nginx.conf
/ghana-tax-system/infra/mongo-init/init.js
```

**docker-compose.yml must include services:**

- `mongodb` — mongo:7 community, port 27017, volume persisted
- `redis` — redis:7-alpine, port 6379
- `backend` — Python 3.10, build from ./backend, port 8000
- `frontend` — Node 20, build from ./frontend, port 5173 (dev) / 80 (prod)

**infra/.env.example must define:**

```
MONGO_URI=mongodb://mongodb:27017/ghana_tax_db
MONGO_DB_NAME=ghana_tax_db
REDIS_URL=redis://redis:6379/0
JWT_SECRET_KEY=changeme
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
DJANGO_SECRET_KEY=changeme
DJANGO_DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173
AT_API_KEY=                     # Africa's Talking API key
AT_USERNAME=                    # Africa's Talking username
AT_SENDER_ID=GH-REVENUE
SEED_ADMIN_EMAIL=sysadmin@demo.gov.gh
SEED_ADMIN_PASSWORD=DemoPass123!
```

**mongo-init/init.js must create all indexes:**

```javascript
// traders collection
db.traders.createIndex({ tin_number: 1 }, { unique: true });
db.traders.createIndex({ phone_number: 1 });
db.traders.createIndex({ created_at: -1 });
db.traders.createIndex({ channel: 1 });
// admins collection
db.admins.createIndex({ email: 1 }, { unique: true });
// audit_logs collection
db.audit_logs.createIndex({ created_at: -1 });
db.audit_logs.createIndex({ actor_id: 1 });
db.audit_logs.createIndex({ action: 1 });
// ussd_sessions
db.ussd_sessions.createIndex({ session_id: 1 }, { unique: true });
db.ussd_sessions.createIndex(
  { last_activity_at: 1 },
  { expireAfterSeconds: 1800 },
);
```

### 1.2 — Backend Scaffold

**Files to Create:**

```
/ghana-tax-system/backend/manage.py
/ghana-tax-system/backend/requirements.txt
/ghana-tax-system/backend/.env.example           ← copy from infra
/ghana-tax-system/backend/Dockerfile
/ghana-tax-system/backend/core/__init__.py
/ghana-tax-system/backend/core/settings.py
/ghana-tax-system/backend/core/urls.py
/ghana-tax-system/backend/core/wsgi.py
/ghana-tax-system/backend/core/middleware/__init__.py
/ghana-tax-system/backend/core/middleware/audit_middleware.py  ← stub
/ghana-tax-system/backend/core/utils/__init__.py
/ghana-tax-system/backend/core/utils/mongo.py    ← PyMongo singleton stub
/ghana-tax-system/backend/core/utils/response.py ← API response helpers stub
/ghana-tax-system/backend/core/utils/pagination.py ← stub
/ghana-tax-system/backend/apps/auth_app/__init__.py
/ghana-tax-system/backend/apps/registration/__init__.py
/ghana-tax-system/backend/apps/tin/__init__.py
/ghana-tax-system/backend/apps/reports/__init__.py
/ghana-tax-system/backend/apps/audit/__init__.py
/ghana-tax-system/backend/apps/ussd/__init__.py
/ghana-tax-system/backend/apps/notifications/__init__.py
/ghana-tax-system/backend/management/__init__.py
/ghana-tax-system/backend/management/commands/__init__.py
/ghana-tax-system/backend/management/commands/seed_demo_data.py ← stub
```

**requirements.txt must include:**

```
Django==4.2.*
djangorestframework==3.14.*
pymongo==4.6.*
redis==5.0.*
PyJWT==2.8.*
bcrypt==4.1.*
python-decouple==3.8
django-ratelimit==4.1.*
django-cors-headers==4.3.*
pytest==7.4.*
pytest-django==4.7.*
factory-boy==3.3.*
```

**settings.py must:**

- Use `python-decouple` for all env vars
- Configure DRF with JWT authentication class (custom)
- Configure CORS from env
- NOT use Django ORM for any primary data (no databases block needed for Mongo)
- Include all apps in INSTALLED_APPS

### 1.3 — Frontend Scaffold

**Files to Create:**

```
/ghana-tax-system/frontend/package.json
/ghana-tax-system/frontend/vite.config.ts
/ghana-tax-system/frontend/tsconfig.json
/ghana-tax-system/frontend/tsconfig.node.json
/ghana-tax-system/frontend/tailwind.config.ts
/ghana-tax-system/frontend/postcss.config.js
/ghana-tax-system/frontend/index.html
/ghana-tax-system/frontend/Dockerfile
/ghana-tax-system/frontend/src/main.tsx
/ghana-tax-system/frontend/src/App.tsx
/ghana-tax-system/frontend/src/router.tsx
/ghana-tax-system/frontend/src/styles/globals.css
/ghana-tax-system/frontend/src/styles/theme.ts
/ghana-tax-system/frontend/src/lib/api.ts
/ghana-tax-system/frontend/src/lib/auth.ts
/ghana-tax-system/frontend/src/lib/utils.ts
/ghana-tax-system/frontend/src/store/authStore.ts
/ghana-tax-system/frontend/src/store/uiStore.ts
```

**package.json dependencies must include:**

```json
{
  "dependencies": {
    "react": "^18",
    "react-dom": "^18",
    "react-router-dom": "^6",
    "axios": "^1",
    "zustand": "^4",
    "react-hook-form": "^7",
    "zod": "^3",
    "@hookform/resolvers": "^3",
    "recharts": "^2",
    "date-fns": "^3",
    "clsx": "^2"
  },
  "devDependencies": {
    "typescript": "^5",
    "vite": "^5",
    "@vitejs/plugin-react": "^4",
    "tailwindcss": "^3",
    "autoprefixer": "^10",
    "postcss": "^8"
  }
}
```

**globals.css must define CSS variables:**

```css
:root {
  --cu-red: #8a1020;
  --cu-red-dark: #640b15;
  --cu-red-light: #b91c35;
  --cu-white: #ffffff;
  --cu-bg: #f5f6f8;
  --cu-border: #e5e7eb;
  --cu-text: #111827;
  --cu-text-muted: #6b7280;
  --cu-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}
```

**tailwind.config.ts must extend theme with CU color tokens.**

**router.tsx must define all routes (pages can be empty stubs):**

- `/` → LandingPage
- `/register` → RegisterPage
- `/register/success` → RegistrationSuccessPage
- `/check-tin` → CheckTinPage
- `/help` → HelpPage
- `/admin/login` → LoginPage
- `/admin/dashboard` → DashboardPage (protected)
- `/admin/traders` → TradersPage (protected)
- `/admin/traders/:id` → TraderDetailPage (protected)
- `/admin/reports` → ReportsPage (protected)
- `/admin/audit-logs` → AuditLogsPage (protected, SYS_ADMIN only)

**After completing Phase 1, update LOG.md.**

---

## PHASE 2 — MongoDB Data Layer & Seed Script

**Agent Instructions:** Read LOG.md first. Verify Phase 1 is complete. Implement the MongoDB connection singleton, all repository base classes, collection schema constants, and the full seed script with dummy data.

**Depends On:** Phase 1

### 2.1 — MongoDB Connection & Core Utils

**Files to Create/Implement:**

```
/ghana-tax-system/backend/core/utils/mongo.py
/ghana-tax-system/backend/core/utils/response.py
/ghana-tax-system/backend/core/utils/pagination.py
```

**mongo.py must:**

- Create a singleton `MongoClient` using `MONGO_URI` from env
- Expose `get_db()` function returning the database instance
- Handle connection errors gracefully with retry logic
- Expose collection name constants:
  ```python
  TRADERS = "traders"
  BUSINESSES = "businesses"
  LOCATIONS = "locations"
  ADMINS = "admins"
  AUDIT_LOGS = "audit_logs"
  USSD_SESSIONS = "ussd_sessions"
  ```

**response.py must provide:**

```python
def success_response(data, message="", status=200): ...
def error_response(message, errors=None, status=400): ...
def paginated_response(data, total, page, page_size): ...
```

**pagination.py must provide:**

```python
def get_pagination_params(request) -> dict:  # returns {skip, limit, page, page_size}
def apply_pagination(queryset, skip, limit): ...
```

### 2.2 — Repository Base Classes

**Files to Create:**

```
/ghana-tax-system/backend/apps/auth_app/repository.py
/ghana-tax-system/backend/apps/registration/repository.py
/ghana-tax-system/backend/apps/tin/repository.py
/ghana-tax-system/backend/apps/reports/repository.py
/ghana-tax-system/backend/apps/audit/repository.py
/ghana-tax-system/backend/apps/ussd/session_store.py
```

**auth_app/repository.py — AdminRepository:**

```python
class AdminRepository:
    def find_by_email(self, email: str) -> dict | None
    def find_by_id(self, admin_id: str) -> dict | None
    def create(self, admin_data: dict) -> dict
    def update(self, admin_id: str, updates: dict) -> dict
    def list_all(self) -> list[dict]
    def update_last_login(self, admin_id: str) -> None
```

**registration/repository.py — TraderRepository + BusinessRepository + LocationRepository:**

```python
class TraderRepository:
    def create(self, trader_data: dict) -> dict
    def find_by_phone(self, phone: str) -> dict | None
    def find_by_tin(self, tin: str) -> dict | None
    def find_by_id(self, trader_id: str) -> dict | None
    def list_with_filters(self, filters: dict, skip: int, limit: int) -> tuple[list, int]
    def count_by_channel(self) -> dict
    def count_by_date_range(self, start, end) -> int

class BusinessRepository:
    def create(self, business_data: dict) -> dict
    def find_by_owner(self, trader_id: str) -> dict | None

class LocationRepository:
    def create(self, location_data: dict) -> dict
    def find_by_id(self, location_id: str) -> dict | None
    def list_districts(self) -> list[str]
    def list_regions(self) -> list[str]
```

**tin/repository.py — TINRepository:**

```python
class TINRepository:
    def exists(self, tin_number: str) -> bool
    def reserve(self, tin_number: str, trader_id: str) -> bool  # atomic upsert
```

**reports/repository.py — ReportsRepository:**

```python
class ReportsRepository:
    def summary_by_channel(self, date_filter: dict) -> list[dict]   # aggregation
    def summary_by_location(self, date_filter: dict) -> list[dict]  # aggregation
    def summary_by_business_type(self, date_filter: dict) -> list[dict]
    def daily_registrations(self, days: int) -> list[dict]
    def export_traders_csv(self, filters: dict) -> list[dict]
    def kpi_totals(self) -> dict
```

**audit/repository.py — AuditRepository:**

```python
class AuditRepository:
    def log(self, event_data: dict) -> None
    def list_with_filters(self, filters: dict, skip: int, limit: int) -> tuple[list, int]
```

**ussd/session_store.py — USSDSessionStore:**

```python
class USSDSessionStore:
    # Tries Redis first, falls back to MongoDB ussd_sessions
    def get(self, session_id: str) -> dict | None
    def set(self, session_id: str, data: dict, ttl: int = 1800) -> None
    def delete(self, session_id: str) -> None
```

### 2.3 — Seed Script

**File to Implement:**

```
/ghana-tax-system/backend/management/commands/seed_demo_data.py
```

**Must create (idempotent — skip if data exists):**

**Admins (3 total):**

- `sysadmin@demo.gov.gh` / `DemoPass123!` — role: `SYS_ADMIN`
- `taxadmin1@demo.gov.gh` / `DemoPass123!` — role: `TAX_ADMIN`
- `taxadmin2@demo.gov.gh` / `DemoPass123!` — role: `TAX_ADMIN`

**Locations (10 — spread across Ghana regions):**

- Greater Accra: Accra Central Market, Kaneshie Market, Makola Market
- Ashanti: Kumasi Central Market, Asafo Market
- Western: Takoradi Market, Sekondi Market
- Northern: Tamale Central Market
- Eastern: Koforidua Market
- Volta: Ho Central Market

**Traders (100 total):**

- Spread across all 10 locations
- Business types distributed: `food_vendor`, `clothing`, `electronics`, `services`, `agriculture`, `wholesale`, `retail`, `artisan`
- Channel mix: ~60 web, ~40 ussd
- Created_at spread over last 90 days
- Each trader linked to 1 business record + 1 location

**Audit Logs (200+ entries):**

- LOGIN_SUCCESS / LOGIN_FAIL events for admins
- CREATE_TRADER events for all seeded traders
- EXPORT_REPORT events (a few)
- Mixed actor_ids, channels, timestamps

**After completing Phase 2, update LOG.md.**

---

## PHASE 3 — Backend: Auth Module (JWT + RBAC)

**Agent Instructions:** Read LOG.md first. Verify Phase 2 is complete. Implement full authentication and role-based access control system.

**Depends On:** Phase 2

### 3.1 — JWT Utilities

**Files to Create/Implement:**

```
/ghana-tax-system/backend/apps/auth_app/jwt_utils.py
/ghana-tax-system/backend/apps/auth_app/permissions.py
/ghana-tax-system/backend/core/middleware/audit_middleware.py
```

**jwt_utils.py must implement:**

```python
def generate_access_token(admin_id: str, role: str) -> str:
    # Uses PyJWT, expires in JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    # Payload: {sub: admin_id, role: role, type: "access", iat, exp}

def generate_refresh_token(admin_id: str) -> str:
    # Expires in JWT_REFRESH_TOKEN_EXPIRE_DAYS
    # Payload: {sub: admin_id, type: "refresh", iat, exp}

def verify_token(token: str) -> dict:
    # Raises AuthenticationError on invalid/expired

def get_token_from_request(request) -> str:
    # Extracts Bearer token from Authorization header
```

**permissions.py must define DRF permission classes:**

```python
class IsAdminAuthenticated(BasePermission):
    # Verifies JWT access token, attaches admin to request.admin

class IsTaxAdmin(IsAdminAuthenticated):
    # role must be TAX_ADMIN or SYS_ADMIN

class IsSysAdmin(IsAdminAuthenticated):
    # role must be SYS_ADMIN only
```

### 3.2 — Auth Views & Serializers

**Files to Create/Implement:**

```
/ghana-tax-system/backend/apps/auth_app/serializers.py
/ghana-tax-system/backend/apps/auth_app/services.py
/ghana-tax-system/backend/apps/auth_app/views.py
/ghana-tax-system/backend/apps/auth_app/urls.py
```

**Endpoints to implement:**

**POST /api/auth/login**

- Request: `{email, password}`
- Validate email + password against admins collection (bcrypt verify)
- On success: return `{access, refresh, role, admin_id, name}`
- On fail: return 401
- Write audit log: `LOGIN_SUCCESS` or `LOGIN_FAIL`
- Rate limit: 10 requests/minute per IP

**POST /api/auth/refresh**

- Request: `{refresh}` token
- Validate refresh token
- Return new `{access}` token
- Rate limit: 20 requests/minute per IP

**GET /api/me**

- Protected (IsAdminAuthenticated)
- Return: `{admin_id, email, role, name, last_login_at}`

**POST /api/admin/users** (SYS_ADMIN only)

- Create a new admin
- Hash password with bcrypt
- Write audit log: `CREATE_ADMIN`

**PATCH /api/admin/users/{admin_id}** (SYS_ADMIN only)

- Update role or is_active
- Write audit log: `ROLE_CHANGE` or `STATUS_CHANGE`
- Cannot modify own account role

**GET /api/admin/users** (SYS_ADMIN only)

- List all admins
- Return: `[{admin_id, email, role, is_active, created_at, last_login_at}]`

**services.py must contain AuthService class with all business logic (not in views).**

**After completing Phase 3, update LOG.md.**

---

## PHASE 4 — Backend: Registration + TIN Module

**Agent Instructions:** Read LOG.md first. Verify Phase 3 is complete. Implement the full registration pipeline (web channel) and TIN generation engine.

**Depends On:** Phase 3

### 4.1 — TIN Generation Service

**Files to Create/Implement:**

```
/ghana-tax-system/backend/apps/tin/services.py
/ghana-tax-system/backend/apps/tin/views.py
/ghana-tax-system/backend/apps/tin/serializers.py
/ghana-tax-system/backend/apps/tin/urls.py
```

**TIN generation algorithm (tin/services.py):**

```python
class TINService:
    TIN_PREFIX = "GH-TIN-"
    MAX_RETRIES = 10

    def generate_unique_tin(self) -> str:
        """
        1. Use secrets.token_hex(3).upper() for 6 chars of crypto-random hex
        2. Format: GH-TIN-XXXXXX (e.g., GH-TIN-3A7F2C)
        3. Check uniqueness via TINRepository.exists()
        4. Retry up to MAX_RETRIES times
        5. On MAX_RETRIES exhaustion: write audit log TIN_GENERATION_FAILED
           and raise TINGenerationError
        6. Return the unique TIN
        """

    def lookup_tin(self, phone_number: str) -> dict | None:
        """
        Find trader by phone_number.
        Return {tin_number, name_masked, status} or None.
        Mask name: first 2 chars + *** + last char (e.g., "Jo***e")
        """
```

**POST /api/tin/lookup endpoint:**

- Request: `{phone_number}`
- Validate phone format (Ghana: +233XXXXXXXXX or 0XXXXXXXXX)
- Return masked result or 404
- Rate limit: 5 requests/minute per IP

### 4.2 — Registration Service

**Files to Create/Implement:**

```
/ghana-tax-system/backend/apps/registration/services.py
/ghana-tax-system/backend/apps/registration/serializers.py
/ghana-tax-system/backend/apps/registration/views.py
/ghana-tax-system/backend/apps/registration/urls.py
/ghana-tax-system/backend/apps/registration/validators.py
```

**validators.py must implement:**

```python
def validate_ghana_phone(phone: str) -> str:
    # Accepts: +233XXXXXXXXX, 0XXXXXXXXX, 233XXXXXXXXX
    # Normalizes to +233XXXXXXXXX
    # Raises ValidationError if invalid

VALID_BUSINESS_TYPES = [
    "food_vendor", "clothing", "electronics", "services",
    "agriculture", "wholesale", "retail", "artisan", "other"
]
```

**RegistrationService:**

```python
class RegistrationService:
    def register_trader_web(self, validated_data: dict, ip_address: str) -> dict:
        """
        1. Validate phone not already registered (TraderRepository.find_by_phone)
           → If exists, return existing TIN (idempotent)
        2. Create/find location (LocationRepository)
        3. Generate TIN (TINService.generate_unique_tin)
        4. Create trader document (TraderRepository.create)
        5. Create business document (BusinessRepository.create)
        6. Write audit log: CREATE_TRADER, channel=web
        7. Trigger SMS notification (NotificationService.send_tin_sms — stub)
        8. Return {tin_number, trader_id, name}
        """
```

**POST /api/register endpoint:**

- Request body:
  ```json
  {
    "name": "string",
    "phone_number": "string",
    "business_type": "food_vendor|clothing|...",
    "location": {
      "region": "string",
      "district": "string",
      "market_name": "string"
    }
  }
  ```
- Response (201):
  ```json
  {
    "tin_number": "GH-TIN-3A7F2C",
    "trader_id": "uuid",
    "name": "string",
    "sms_status": "queued"
  }
  ```
- Rate limit: 20 registrations/minute per IP

**After completing Phase 4, update LOG.md.**

---

## PHASE 5 — Backend: USSD Gateway Module

**Agent Instructions:** Read LOG.md first. Verify Phase 4 is complete. Implement the full USSD state machine, webhook receiver, and session management.

**Depends On:** Phase 4

### 5.1 — USSD State Machine

**Files to Create/Implement:**

```
/ghana-tax-system/backend/apps/ussd/state_machine.py
/ghana-tax-system/backend/apps/ussd/session_store.py  (implement fully)
/ghana-tax-system/backend/apps/ussd/views.py
/ghana-tax-system/backend/apps/ussd/urls.py
/ghana-tax-system/backend/apps/ussd/validators.py
```

**state_machine.py — USSDStateMachine:**

States (use string constants):

```python
STATE_MAIN_MENU = "MAIN_MENU"
STATE_REG_NAME = "REG_NAME"
STATE_REG_BUSINESS_TYPE = "REG_BUSINESS_TYPE"
STATE_REG_REGION = "REG_REGION"
STATE_REG_DISTRICT = "REG_DISTRICT"
STATE_REG_MARKET = "REG_MARKET"
STATE_REG_CONFIRM = "REG_CONFIRM"
STATE_CHECK_TIN = "CHECK_TIN"
STATE_HELP = "HELP"
STATE_COMPLETE = "COMPLETE"
```

**Full USSD flow (Africa's Talking compatible):**

```
MAIN MENU (initial / text == ""):
CON Welcome to DA Revenue
    1. Register Business
    2. Check My TIN
    3. Help

→ "1": go to STATE_REG_NAME
→ "2": go to STATE_CHECK_TIN
→ "3": go to STATE_HELP
→ other: CON Invalid option.\n[show menu again]

STATE_REG_NAME:
CON Step 1 of 5
    Enter your full name:

→ validate: non-empty, min 3 chars, max 60 chars
→ store in session: collected.name
→ go to STATE_REG_BUSINESS_TYPE

STATE_REG_BUSINESS_TYPE:
CON Step 2 of 5 - Business Type
    1. Food Vendor
    2. Clothing
    3. Electronics
    4. Services
    5. Agriculture
    6. Other

→ validate: 1-6
→ store in session: collected.business_type
→ go to STATE_REG_REGION

STATE_REG_REGION:
CON Step 3 of 5 - Region
    1. Greater Accra
    2. Ashanti
    3. Western
    4. Northern
    5. Eastern
    6. Volta
    7. Other

→ validate: 1-7
→ store in session: collected.region
→ go to STATE_REG_DISTRICT

STATE_REG_DISTRICT:
CON Step 4 of 5
    Enter market or community name:

→ validate: non-empty, max 80 chars
→ store in session: collected.market_name, collected.district = market_name
→ go to STATE_REG_CONFIRM

STATE_REG_CONFIRM:
CON Step 5 of 5 - Confirm
    Name: {name}
    Business: {business_type}
    Location: {region} - {market_name}

    1. Confirm & Register
    2. Start Over

→ "1": complete registration via RegistrationService.register_trader_ussd()
       write audit: USSD_REG_COMPLETE
       delete session
       → END Registration complete!
          Your TIN: GH-TIN-XXXXXX
          An SMS will be sent shortly.
→ "2": reset session to MAIN_MENU
       CON [show main menu]

STATE_CHECK_TIN:
CON Enter phone number or press 0 to use this number:

→ "0": use msisdn from session
→ other: validate Ghana phone format
→ Look up TIN via TINService.lookup_tin()
→ If found: END Your TIN is GH-TIN-XXXXXX
→ Not found: END No registration found for that number.

STATE_HELP:
END For help registering:
    Dial *XXX# and follow steps.
    Visit your District Assembly office.
    Or register online at [web URL]
```

**USSD webhook must:**

- Accept Africa's Talking payload: `{sessionId, serviceCode, phoneNumber, text}`
- Parse `text` as `*` delimited history string (e.g., `"1*John Doe*2"`)
- Restore session from Redis/Mongo
- Route to state machine based on current step
- Write audit log: `USSD_SESSION_STEP` for each step
- Return plain text response (Content-Type: text/plain)
- Response time target: ≤10 seconds

**POST /ussd/callback endpoint** (no auth required — webhook):

- Rate limit: 100 requests/minute per IP (DoS protection)
- Log every request

**After completing Phase 5, update LOG.md.**

---

## PHASE 6 — Backend: Reports, Audit & Admin APIs

**Agent Instructions:** Read LOG.md first. Verify Phase 4 is complete. Implement reports endpoints, audit log API, and traders list API with full filtering.

**Depends On:** Phase 3, Phase 4

### 6.1 — Reports Service

**Files to Create/Implement:**

```
/ghana-tax-system/backend/apps/reports/services.py
/ghana-tax-system/backend/apps/reports/serializers.py
/ghana-tax-system/backend/apps/reports/views.py
/ghana-tax-system/backend/apps/reports/urls.py
```

**GET /api/reports/summary** (TAX_ADMIN or SYS_ADMIN):

- Query params: `period=7d|30d|all`
- Response:
  ```json
  {
    "total_traders": 1250,
    "period": "30d",
    "by_channel": {"web": 750, "ussd": 500},
    "by_business_type": [{"type": "food_vendor", "count": 320}, ...],
    "by_region": [{"region": "Greater Accra", "count": 450}, ...],
    "daily_trend": [{"date": "2024-01-15", "count": 42}, ...],
    "generated_at": "ISO8601"
  }
  ```
- Must use MongoDB aggregation pipelines (NOT Python-level loops)
- Must complete in ≤3 seconds for 10,000+ records

**GET /api/reports/export** (TAX_ADMIN or SYS_ADMIN):

- Query params: same filters as /api/traders + `format=csv`
- Returns CSV file download
- Columns: `TIN,Name,Phone,Business Type,Region,District,Market,Channel,Registered At`
- Write audit log: `EXPORT_REPORT`

**GET /api/traders** (TAX_ADMIN or SYS_ADMIN):

- Query params:
  - `channel=web|ussd`
  - `business_type=string`
  - `region=string`
  - `district=string`
  - `date_from=YYYY-MM-DD`
  - `date_to=YYYY-MM-DD`
  - `search=string` (searches name + phone + tin)
  - `page=1`
  - `page_size=20` (max 100)
- Response: `{traders: [...], total, page, page_size, total_pages}`
- Each trader includes: `{trader_id, tin_number, name, phone_number, channel, business_type, region, district, market_name, created_at}`
- Must use MongoDB indexes for all filter fields

**GET /api/traders/{trader_id}** (TAX_ADMIN or SYS_ADMIN):

- Full trader detail including business info and location

### 6.2 — Audit Log API

**Files to Create/Implement:**

```
/ghana-tax-system/backend/apps/audit/views.py
/ghana-tax-system/backend/apps/audit/urls.py
/ghana-tax-system/backend/apps/audit/serializers.py
```

**GET /api/audit-logs** (SYS_ADMIN only):

- Query params:
  - `action=string`
  - `actor_id=string`
  - `date_from`, `date_to`
  - `page`, `page_size`
- Returns paginated audit log entries

**After completing Phase 6, update LOG.md.**

---

## PHASE 7 — Backend: Notifications Module + Full Test Suite ✅ COMPLETE

**Agent Instructions:** Read LOG.md first. Verify Phases 4-6 are complete. Implement the notification abstraction layer and all backend tests.

**Depends On:** Phase 4, 5, 6

### 7.1 — Notifications Module

**Files to Create/Implement:**

```
/ghana-tax-system/backend/apps/notifications/providers/base.py
/ghana-tax-system/backend/apps/notifications/providers/africas_talking.py
/ghana-tax-system/backend/apps/notifications/providers/stub.py
/ghana-tax-system/backend/apps/notifications/services.py
```

**base.py:**

```python
class SMSProvider(ABC):
    @abstractmethod
    def send_sms(self, phone: str, message: str) -> dict:
        """Returns {success: bool, message_id: str|None, error: str|None}"""
```

**stub.py:**

```python
class StubSMSProvider(SMSProvider):
    def send_sms(self, phone, message):
        logger.info(f"[SMS STUB] To: {phone} | Msg: {message}")
        return {"success": True, "message_id": "stub-" + uuid4().hex[:8]}
```

**africas_talking.py:**

```python
class AfricasTalkingProvider(SMSProvider):
    def send_sms(self, phone, message):
        # Real implementation using AT API
        # If AT_API_KEY not set → fall back to stub behavior
```

**services.py — NotificationService:**

```python
class NotificationService:
    def send_tin_sms(self, phone: str, tin: str, name: str) -> dict:
        message = f"Dear {name}, your TIN is {tin}. Keep this safe. - District Revenue"
        return self._provider.send_sms(phone, message)
```

### 7.2 — Backend Tests

**Files to Create:**

```
/ghana-tax-system/backend/tests/__init__.py
/ghana-tax-system/backend/tests/test_tin.py
/ghana-tax-system/backend/tests/test_registration.py
/ghana-tax-system/backend/tests/test_ussd.py
/ghana-tax-system/backend/tests/test_auth.py
/ghana-tax-system/backend/tests/test_reports.py
/ghana-tax-system/backend/tests/conftest.py
/ghana-tax-system/backend/pytest.ini
```

**test_tin.py must include:**

- `test_tin_format_is_correct()` — verify GH-TIN-XXXXXX format
- `test_tin_uniqueness_100k()` — generate 100,000 TINs, assert no duplicates
- `test_tin_generation_speed()` — 1,000 TINs in <5 seconds
- `test_tin_retry_on_collision()` — mock repository to force collision, verify retry
- `test_tin_fails_after_max_retries()` — verify TINGenerationError raised

**test_registration.py must include:**

- `test_web_registration_success()` — full happy path
- `test_web_registration_duplicate_phone_returns_existing_tin()`
- `test_web_registration_invalid_phone_returns_400()`
- `test_web_registration_missing_fields_returns_400()`
- `test_tin_lookup_found()` and `test_tin_lookup_not_found()`

**test_ussd.py must include:**

- `test_ussd_initial_shows_main_menu()`
- `test_ussd_full_registration_flow()` — simulate all 5 steps, verify trader created
- `test_ussd_invalid_input_shows_error()`
- `test_ussd_check_tin_found()`
- `test_ussd_check_tin_not_found()`
- `test_ussd_session_persists_between_requests()`
- `test_ussd_registration_appears_in_traders_list()` — integration test

**test_auth.py must include:**

- `test_login_success_returns_tokens()`
- `test_login_wrong_password_returns_401()`
- `test_access_protected_route_without_token_returns_401()`
- `test_tax_admin_cannot_access_sys_admin_endpoint()`
- `test_token_refresh_works()`

**test_reports.py must include:**

- `test_summary_returns_correct_totals()`
- `test_summary_by_channel_correct()`
- `test_export_csv_returns_correct_columns()`
- `test_summary_performance_under_3s()` — with 10k seeded records

**conftest.py must provide:**

- `test_db` fixture — isolated test MongoDB database
- `sys_admin_token` fixture
- `tax_admin_token` fixture
- `sample_trader` factory fixture

**After completing Phase 7, update LOG.md.**

---

## PHASE 8 — Frontend: Design System + Shared Layout Components

**Agent Instructions:** Read LOG.md first. Verify Phase 1 is complete. Build all reusable UI components and layout shells. No API calls yet — use mock/placeholder data.

**Depends On:** Phase 1

### 8.1 — Theme & Global Styles

**Files to Create/Implement:**

```
/ghana-tax-system/frontend/src/styles/globals.css       (implement fully)
/ghana-tax-system/frontend/src/styles/theme.ts
/ghana-tax-system/frontend/tailwind.config.ts           (implement fully)
```

**tailwind.config.ts must extend:**

```typescript
theme: {
  extend: {
    colors: {
      'cu-red': '#8A1020',
      'cu-red-dark': '#640B15',
      'cu-red-light': '#B91C35',
      'cu-bg': '#F5F6F8',
      'cu-border': '#E5E7EB',
      'cu-text': '#111827',
      'cu-muted': '#6B7280',
    },
    fontFamily: {
      sans: ['Inter', 'system-ui', 'sans-serif'],
    }
  }
}
```

### 8.2 — UI Primitive Components

**Files to Create:**

```
/ghana-tax-system/frontend/src/components/ui/Button.tsx
/ghana-tax-system/frontend/src/components/ui/Input.tsx
/ghana-tax-system/frontend/src/components/ui/Card.tsx
/ghana-tax-system/frontend/src/components/ui/Table.tsx
/ghana-tax-system/frontend/src/components/ui/Badge.tsx
/ghana-tax-system/frontend/src/components/ui/Modal.tsx
/ghana-tax-system/frontend/src/components/ui/Spinner.tsx
/ghana-tax-system/frontend/src/components/ui/Alert.tsx
/ghana-tax-system/frontend/src/components/ui/Select.tsx
/ghana-tax-system/frontend/src/components/ui/index.ts  ← barrel export
```

**Button variants:** `primary` (cu-red bg), `secondary` (white + cu-red border), `ghost`, `danger`
**Input:** label, error message, helper text support
**Badge:** `active` (green), `pending` (yellow), `web` (blue), `ussd` (purple)
**Card:** white bg, subtle border, optional header strip

### 8.3 — Layout Components

**Files to Create:**

```
/ghana-tax-system/frontend/src/components/layout/Header.tsx
/ghana-tax-system/frontend/src/components/layout/Footer.tsx
/ghana-tax-system/frontend/src/components/layout/PublicLayout.tsx
/ghana-tax-system/frontend/src/components/layout/AdminLayout.tsx
/ghana-tax-system/frontend/src/components/layout/Sidebar.tsx
/ghana-tax-system/frontend/src/components/layout/ProtectedRoute.tsx
```

**Header.tsx must include:**

- Top strip: Ghana coat of arms placeholder (SVG circle) + "DISTRICT ASSEMBLY – REVENUE UNIT" text
- Background: `cu-red`, text: white
- Navigation links (public: Home, Register, Check TIN, Help)
- Fully responsive (hamburger on mobile)

**Sidebar.tsx (admin):**

- Logo/title at top
- Nav items: Dashboard, Traders, Reports, Audit Logs (SYS_ADMIN only)
- Logout button at bottom
- Active state: cu-red left border

**ProtectedRoute.tsx:**

- Checks authStore for valid token
- Optional `requiredRole` prop for SYS_ADMIN gating
- Redirects to /admin/login if not authenticated

### 8.4 — Charts Components

**Files to Create:**

```
/ghana-tax-system/frontend/src/components/charts/BarChart.tsx
/ghana-tax-system/frontend/src/components/charts/LineChart.tsx
/ghana-tax-system/frontend/src/components/charts/DonutChart.tsx
```

Use `recharts` library. Each chart must:

- Accept generic `data` and `keys` props
- Use cu-red as primary color
- Include responsive container
- Have loading state

**After completing Phase 8, update LOG.md.**

---

## PHASE 9 — Frontend: Trader Portal (5 Pages)

**Agent Instructions:** Read LOG.md first. Verify Phase 8 is complete. Build all 5 trader-facing pages. Wire up to real API (backend must be running). Use mock data fallback if backend not yet available.

**Depends On:** Phase 8

### Pages to Build

All pages use `PublicLayout` wrapper (Header + Footer).
All pages match CU red/white portal style.

---

**Page 1: LandingPage.tsx** — `/`

```
/ghana-tax-system/frontend/src/features/trader/pages/LandingPage.tsx
```

Layout:

- Hero section: Ghana coat of arms, "Digital Taxation & Revenue System", "District Assembly Revenue Unit"
- Brief description of the system
- Two prominent CTA buttons:
  - "Register Your Business" → /register (cu-red, large)
  - "Check My TIN" → /check-tin (secondary)
- Stats row: "1,200+ Registered Traders | 10 Districts | 2 Channels"
- How it works: 3 steps with icons (1. Fill form → 2. Get TIN → 3. Stay compliant)
- USSD banner: "No internet? Dial \*XXX# to register via phone" (cu-red banner)

---

**Page 2: RegisterPage.tsx** — `/register`

```
/ghana-tax-system/frontend/src/features/trader/pages/RegisterPage.tsx
/ghana-tax-system/frontend/src/features/trader/components/RegistrationForm.tsx
/ghana-tax-system/frontend/src/features/trader/hooks/useRegistration.ts
```

Form fields (use react-hook-form + zod):

- Full Name (required, min 3 chars)
- Phone Number (required, Ghana format +233XXXXXXXXX / 0XXXXXXXXX)
- Business Type (dropdown/select — 9 options)
- Region (dropdown — 7 regions)
- District (text input)
- Market / Community Name (text input)

UX requirements:

- Step indicator (Step 1 of 2: Personal Info → Business Info)
- Client-side validation with inline error messages
- Submit button disabled while loading, shows spinner
- On success → navigate to /register/success with TIN data
- On error → show Alert component with server error message

useRegistration.ts hook:

- POST to /api/register
- Handle loading, error, success states
- Store TIN result in component state (not global store — one-time use)

---

**Page 3: RegistrationSuccessPage.tsx** — `/register/success`

```
/ghana-tax-system/frontend/src/features/trader/pages/RegistrationSuccessPage.tsx
/ghana-tax-system/frontend/src/features/trader/components/TinDisplay.tsx
```

Layout:

- Green checkmark icon
- "Registration Successful!" heading
- TIN display box (prominent, bordered, cu-red text, large font): "GH-TIN-3A7F2C"
- "Screenshot or write down your TIN number"
- SMS notice: "An SMS has been sent to +233XXXXXXXXX"
- Buttons: "Register Another Business" | "Check Your TIN"
- If user navigates here without TIN (direct URL) → redirect to /register

TinDisplay.tsx:

- Accepts `tin` prop
- Prominent display with copy-to-clipboard button
- Print-friendly styling

---

**Page 4: CheckTinPage.tsx** — `/check-tin`

```
/ghana-tax-system/frontend/src/features/trader/pages/CheckTinPage.tsx
```

Layout:

- Simple form: phone number input + "Find My TIN" button
- On success: show TIN result card (TIN number, masked name, status badge)
- On not found: show Alert "No registration found for this number"
- Rate limit message: if 429 → show "Too many attempts. Please wait."

---

**Page 5: HelpPage.tsx** — `/help`

```
/ghana-tax-system/frontend/src/features/trader/pages/HelpPage.tsx
```

Layout:

- FAQ accordion (5 questions):
  - "What is a TIN?"
  - "How do I register online?"
  - "How do I register via USSD?"
  - "What if I lose my TIN?"
  - "Who do I contact for help?"
- USSD guide: step-by-step numbered instructions with screenshot mockup
- Contact info: District Assembly Revenue Unit address/phone placeholder
- Download guide button (placeholder PDF link)

**After completing Phase 9, update LOG.md.**

---

## PHASE 10 — Frontend: Admin Portal (6 Pages)

**Agent Instructions:** Read LOG.md first. Verify Phase 8 complete. Backend Phases 3 & 6 should be complete for full wiring. Build all admin pages with full API integration.

**Depends On:** Phase 8, Phase 3, Phase 6

---

**Page 1: LoginPage.tsx** — `/admin/login`

```
/ghana-tax-system/frontend/src/features/admin/pages/LoginPage.tsx
```

Layout (mimic CU portal login):

- Centered card on cu-bg background
- Top: cu-red header strip with "DISTRICT ASSEMBLY – REVENUE UNIT" + emblem placeholder
- Form: Email + Password fields
- "Sign In" button (full width, cu-red)
- Error message below form (wrong credentials)
- No "register" link (admin accounts created by SYS_ADMIN)

Auth flow:

- POST /api/auth/login
- Store `{access, refresh, role, admin_id}` in authStore (Zustand)
- Redirect to /admin/dashboard on success
- Show error on 401

---

**Page 2: DashboardPage.tsx** — `/admin/dashboard`

```
/ghana-tax-system/frontend/src/features/admin/pages/DashboardPage.tsx
/ghana-tax-system/frontend/src/features/admin/components/StatsCard.tsx
/ghana-tax-system/frontend/src/features/admin/hooks/useReports.ts
```

Layout sections:

**KPI Row (4 StatsCards):**

- Total Traders | Today's Registrations | Web Registrations | USSD Registrations

**Charts Row:**

- Left: BarChart — registrations by business type
- Right: DonutChart — web vs USSD split

**Bottom Row:**

- LineChart — daily registrations last 30 days
- Table — top 5 districts by registration count

**Period filter:** buttons "7 Days | 30 Days | All Time" (updates all charts)

StatsCard.tsx:

- Icon + label + large number + trend indicator (+12% vs last week)
- White card, cu-red icon accent

---

**Page 3: TradersPage.tsx** — `/admin/traders`

```
/ghana-tax-system/frontend/src/features/admin/pages/TradersPage.tsx
/ghana-tax-system/frontend/src/features/admin/components/TraderTable.tsx
/ghana-tax-system/frontend/src/features/admin/components/FilterBar.tsx
/ghana-tax-system/frontend/src/features/admin/hooks/useTraders.ts
```

FilterBar component filters:

- Search (name / phone / TIN)
- Channel (All / Web / USSD)
- Business Type (dropdown)
- Region (dropdown)
- Date From / Date To

TraderTable:

- Columns: TIN | Name | Phone | Business Type | Region | Channel | Registered At | Actions
- Channel column: Badge (web=blue, ussd=purple)
- Pagination: 20 per page, page controls at bottom
- "View" button → /admin/traders/:id
- Loading skeleton while fetching

useTraders.ts hook:

- GET /api/traders with all filter params
- Debounce search input (300ms)
- Reset page on filter change

---

**Page 4: TraderDetailPage.tsx** — `/admin/traders/:id`

```
/ghana-tax-system/frontend/src/features/admin/pages/TraderDetailPage.tsx
```

Sections:

- Breadcrumb: Traders > {name}
- Profile card: TIN (prominent), Name, Phone, Status badge
- Business info card: Business Type, Location details
- Registration info: Channel, Created At, Registered via
- Back button

---

**Page 5: ReportsPage.tsx** — `/admin/reports`

```
/ghana-tax-system/frontend/src/features/admin/pages/ReportsPage.tsx
/ghana-tax-system/frontend/src/features/admin/components/ReportSummary.tsx
```

Sections:

- Filter bar: Period, Region, Channel, Business Type, Date Range
- Summary table (government style): clear headings, totals row
  - Total registrations | By channel | By top regions | By business type
- "Export CSV" button → GET /api/reports/export (triggers download)
- "Generated at: {timestamp}" footer
- Loading state while generating

---

**Page 6: AuditLogsPage.tsx** — `/admin/audit-logs` (SYS_ADMIN only)

```
/ghana-tax-system/frontend/src/features/admin/pages/AuditLogsPage.tsx
/ghana-tax-system/frontend/src/features/admin/components/AuditTable.tsx
```

- Route protected by `requiredRole="SYS_ADMIN"` on ProtectedRoute
- Filter by: Action type, Actor, Date range
- Table columns: Timestamp | Actor | Role | Action | Entity | Channel | IP Address
- Paginated (20/page)
- Row detail expand (click row to see before/after JSON if available)

**After completing Phase 10, update LOG.md.**

---

## PHASE 11 — Integration & End-to-End Wiring

**Agent Instructions:** Read LOG.md first. Verify ALL previous phases complete. Wire frontend to backend, fix any integration issues, and verify all acceptance criteria are met.

**Depends On:** All previous phases

### 11.1 — API Client & Auth Wiring

**Files to Implement/Update:**

```
/ghana-tax-system/frontend/src/lib/api.ts         (implement fully)
/ghana-tax-system/frontend/src/lib/auth.ts        (implement fully)
/ghana-tax-system/frontend/src/store/authStore.ts (implement fully)
```

**api.ts — Axios instance with:**

- Base URL from env var `VITE_API_BASE_URL`
- Request interceptor: attach `Authorization: Bearer {access_token}` from authStore
- Response interceptor:
  - On 401: attempt token refresh via POST /api/auth/refresh
  - On refresh success: retry original request
  - On refresh fail: clear authStore, redirect to /admin/login
- Error normalization: extract error message from response body

**authStore.ts — Zustand store:**

```typescript
interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  role: "SYS_ADMIN" | "TAX_ADMIN" | null;
  adminId: string | null;
  setAuth: (tokens, role, adminId) => void;
  clearAuth: () => void;
  isAuthenticated: () => boolean;
}
// Persist to sessionStorage (NOT localStorage)
```

### 11.2 — CORS & Environment Configuration

**Verify/Fix:**

- Backend CORS allows frontend origin (from `CORS_ALLOWED_ORIGINS` env)
- Frontend `VITE_API_BASE_URL` points to backend
- Docker Compose networking allows service-to-service communication
- USSD callback URL accessible for webhook testing

**Files to Update:**

```
/ghana-tax-system/infra/docker-compose.yml        ← verify networking
/ghana-tax-system/frontend/.env.example           ← VITE_API_BASE_URL
/ghana-tax-system/backend/core/settings.py        ← CORS config verify
```

### 11.3 — README & Documentation

**Files to Create/Implement:**

```
/ghana-tax-system/README.md
/ghana-tax-system/api-tests/ghana-tax-system.http  ← .http test file
```

**README.md must include:**

1. Architecture diagram (ASCII)
2. Prerequisites list
3. Quick start with Docker Compose
4. Manual setup instructions (backend + frontend)
5. Environment variables reference
6. How to seed demo data
7. USSD simulation curl examples
8. Default demo accounts table
9. API endpoint reference table
10. Running tests instructions

**ASCII Architecture Diagram:**

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT LAYER                              │
│  ┌─────────────────────┐    ┌──────────────────────────┐   │
│  │   React Web App      │    │    USSD Gateway           │   │
│  │  (Trader + Admin)    │    │  (Africa's Talking)       │   │
│  └──────────┬──────────┘    └─────────────┬────────────┘   │
└─────────────┼─────────────────────────────┼────────────────┘
              │ HTTP/REST                    │ Webhook POST
┌─────────────▼─────────────────────────────▼────────────────┐
│                  API LAYER (Django DRF)                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │   Auth   │ │  Regist. │ │   USSD   │ │   Reports    │  │
│  │  + RBAC  │ │  + TIN   │ │  Engine  │ │  + Audit     │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
   ┌─────────┐    ┌─────────┐    ┌──────────┐
   │ MongoDB │    │  Redis  │    │  Africa's│
   │ (data)  │    │(sessions│    │  Talking │
   └─────────┘    └─────────┘    │   SMS)   │
                                 └──────────┘
```

**USSD curl simulation examples:**

```bash
# Initial menu
curl -X POST http://localhost:8000/ussd/callback \
  -d "sessionId=sess_001&serviceCode=*123#&phoneNumber=%2B233201234567&text="

# Enter "1" to register
curl -X POST http://localhost:8000/ussd/callback \
  -d "sessionId=sess_001&serviceCode=*123#&phoneNumber=%2B233201234567&text=1"

# Enter name
curl -X POST http://localhost:8000/ussd/callback \
  -d "sessionId=sess_001&serviceCode=*123#&phoneNumber=%2B233201234567&text=1*Kofi%20Mensah"

# Continue through all steps
# text=1*Kofi Mensah*1*1*Kumasi Market*1
```

**ghana-tax-system.http file must include test calls for ALL endpoints.**

### 11.4 — Acceptance Verification Checklist

Agent must verify and document results for each:

```
[ ] React frontend runs at http://localhost:5173 with CU portal style
[ ] Django backend runs at http://localhost:8000
[ ] MongoDB connected and contains seeded data (100 traders, 3 admins, 200+ audit logs)
[ ] POST /ussd/callback simulation completes full registration
[ ] POST /api/register creates trader with unique TIN
[ ] Both registrations appear in GET /api/traders
[ ] Admin login returns JWT tokens
[ ] /admin/dashboard shows correct KPIs
[ ] /admin/traders shows paginated trader list with filters
[ ] Reports export returns valid CSV
[ ] RBAC: TAX_ADMIN cannot GET /api/audit-logs (403)
[ ] RBAC: TAX_ADMIN cannot POST /api/admin/users (403)
[ ] Audit logs written for: trader creation, login, export
[ ] TIN uniqueness: no duplicates in seeded data
[ ] docker-compose up starts all services
```

**After completing Phase 11, update LOG.md with full acceptance checklist results.**

---

## PHASE 12 — Security Hardening & Performance Tuning

**Agent Instructions:** Read LOG.md first. Verify Phase 11 complete. Final hardening pass.

**Depends On:** Phase 11

### Security Checks:

- Verify rate limiting active on all specified endpoints
- Verify input sanitization on all form fields
- Verify CORS headers correct in production mode
- Verify JWT expiry enforced
- Verify RBAC double-checked at service layer (not just view layer)
- Audit log all edge cases: failed TIN generation, duplicate phone

### Performance Checks:

- Run reports summary against 10k records — must be ≤3s
- Verify MongoDB indexes exist (run mongo-init script)
- Add caching for /api/reports/summary (30-60s TTL using Redis)

### Files to Update (as needed):

```
/ghana-tax-system/backend/apps/reports/services.py   ← add Redis cache
/ghana-tax-system/backend/core/settings.py           ← cache config
/ghana-tax-system/backend/apps/*/views.py            ← rate limit review
```

**After completing Phase 12, update LOG.md.**

---

## AGENT INSTRUCTIONS (READ BEFORE EVERY PHASE)

1. **Always read LOG.md first** to understand current state of the project
2. **Verify dependencies** — check LOG.md confirms prior phases completed
3. **Follow file paths exactly** as specified in this document
4. **After completing your phase:**
   - Update LOG.md with the entry format shown at the top
   - List EVERY file created or modified
   - Set status to ✅ Complete
5. **Zero analyzer errors policy** — run linting/type checks before marking complete
6. **Do not modify files outside your phase scope** unless fixing a blocker
7. **If a prior phase is incomplete** — document the gap in LOG.md and work around it

---

## QUICK REFERENCE: ALL PAGES

### Trader Portal (Public)

| Route               | Page File                     | Description                           |
| ------------------- | ----------------------------- | ------------------------------------- |
| `/`                 | `LandingPage.tsx`             | Government portal home with CTAs      |
| `/register`         | `RegisterPage.tsx`            | Multi-step business registration form |
| `/register/success` | `RegistrationSuccessPage.tsx` | TIN display + confirmation            |
| `/check-tin`        | `CheckTinPage.tsx`            | Phone number → TIN lookup             |
| `/help`             | `HelpPage.tsx`                | FAQ + USSD guide                      |

### Admin Portal (Protected)

| Route                | Page File              | Access         | Description             |
| -------------------- | ---------------------- | -------------- | ----------------------- |
| `/admin/login`       | `LoginPage.tsx`        | Public         | CU-style portal login   |
| `/admin/dashboard`   | `DashboardPage.tsx`    | TAX_ADMIN+     | KPIs + charts           |
| `/admin/traders`     | `TradersPage.tsx`      | TAX_ADMIN+     | Filterable trader table |
| `/admin/traders/:id` | `TraderDetailPage.tsx` | TAX_ADMIN+     | Full trader profile     |
| `/admin/reports`     | `ReportsPage.tsx`      | TAX_ADMIN+     | Summary + CSV export    |
| `/admin/audit-logs`  | `AuditLogsPage.tsx`    | SYS_ADMIN only | Audit trail             |

### Total: 11 Pages

---

## QUICK REFERENCE: ALL API ENDPOINTS

| Method | Endpoint               | Auth           | Description              |
| ------ | ---------------------- | -------------- | ------------------------ |
| POST   | `/api/auth/login`      | None           | Admin login              |
| POST   | `/api/auth/refresh`    | None           | Refresh access token     |
| GET    | `/api/me`              | Any Admin      | Current admin info       |
| POST   | `/api/register`        | None           | Web trader registration  |
| POST   | `/api/tin/lookup`      | None           | TIN lookup by phone      |
| POST   | `/ussd/callback`       | None (webhook) | USSD session handler     |
| GET    | `/api/traders`         | TAX_ADMIN+     | List traders (filtered)  |
| GET    | `/api/traders/:id`     | TAX_ADMIN+     | Trader detail            |
| GET    | `/api/reports/summary` | TAX_ADMIN+     | Aggregated KPIs          |
| GET    | `/api/reports/export`  | TAX_ADMIN+     | CSV download             |
| GET    | `/api/audit-logs`      | SYS_ADMIN      | Audit log entries        |
| POST   | `/api/admin/users`     | SYS_ADMIN      | Create admin             |
| PATCH  | `/api/admin/users/:id` | SYS_ADMIN      | Update admin role/status |
| GET    | `/api/admin/users`     | SYS_ADMIN      | List admins              |

---

_End of Phase Plan — ghana-tax-system_
_Version: 1.0 | Created: 2026-03-05_
