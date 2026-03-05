# Digital Taxation & Revenue Tracking System — Change Log
# Ghana District Assembly | Revenue Unit

> This file is updated by every agent after completing any phase or sub-task.
> Format: newest entries at the TOP. Every entry must list files created/modified.

---

## LOG FORMAT TEMPLATE (copy for each entry)

```
### [PHASE X.Y] — <Short Title>
**Date:** YYYY-MM-DD
**Agent:** Phase X Agent
**Status:** ✅ Complete | 🔄 In Progress | ❌ Failed

**Files Created:**
- path/to/file.ext — description

**Files Modified:**
- path/to/file.ext — what changed

**Notes:**
- Any relevant implementation notes
```

---

## ENTRIES

---

### [PHASE 8] — Frontend: Design System + Shared Layout Components
**Date:** 2026-03-05
**Agent:** Phase 8 Agent
**Status:** ✅ Complete

**Files Created:**
- `frontend/src/vite-env.d.ts` — Vite env type declarations (`VITE_API_BASE_URL`); fixes `import.meta.env` TypeScript error

**Files Modified (stub → full implementation):**
- `frontend/src/components/ui/Button.tsx` — Full implementation: `primary/secondary/ghost/danger` variants, `sm/md/lg` sizes, `isLoading` spinner, `leftIcon/rightIcon`, `fullWidth` prop, `forwardRef`, disabled states
- `frontend/src/components/ui/Spinner.tsx` — Full implementation: SVG spinner with `sm/md/lg` sizes and `red/white/gray` color props; used by Button and Table
- `frontend/src/components/ui/Input.tsx` — Full implementation: `label`, `error`, `helperText`, `leftAddon/rightAddon`, `forwardRef`, ARIA attributes (`aria-invalid`, `aria-describedby`), validation styling
- `frontend/src/components/ui/Select.tsx` — Full implementation: same API shape as Input; `options: SelectOption[]`, `placeholder` (disabled first option), ARIA, validation styling, `forwardRef`
- `frontend/src/components/ui/Card.tsx` — Full implementation: `headerTitle` strip, `headerRight` slot, `noPadding` flag, `shadow-card` Tailwind token
- `frontend/src/components/ui/Badge.tsx` — Full implementation: `active` (green), `inactive` (gray), `pending` (yellow), `web` (blue), `ussd` (purple), `sys_admin` (cu-red), `tax_admin` (orange), `default` variants
- `frontend/src/components/ui/Alert.tsx` — Full implementation: `info/success/warning/error` variants with SVG icons, optional `title`, `onClose` dismiss button, ARIA `role="alert"`
- `frontend/src/components/ui/Table.tsx` — Full implementation: generic `<T>` typed columns, loading skeleton (Spinner), empty state message, `onRowClick` callback, overflow-x scroll wrapper
- `frontend/src/components/ui/Modal.tsx` — Full implementation: backdrop click/Esc to close, keyboard trap, ARIA `role="dialog"`, sizes `sm/md/lg/xl`, optional `footer` slot, `disableClose` flag; `ModalCloseButton` convenience export; body overflow lock
- `frontend/src/components/ui/index.ts` — Full barrel export for all 9 UI primitives with named type exports
- `frontend/src/components/layout/Header.tsx` — Full implementation: Ghana coat-of-arms SVG placeholder, "DISTRICT ASSEMBLY – REVENUE UNIT" identity strip, responsive nav with hamburger menu (mobile), active NavLink highlighting, cu-red background
- `frontend/src/components/layout/Footer.tsx` — Full implementation: copyright line, Help link, responsive flex layout
- `frontend/src/components/layout/PublicLayout.tsx` — Full implementation: wraps `<Outlet />` with `<Header />` + `<Footer />`; `min-h-screen flex-col` layout
- `frontend/src/components/layout/AdminLayout.tsx` — Full implementation: `<Sidebar />` + top bar + `<Outlet />` in flex layout; sticky sidebar
- `frontend/src/components/layout/Sidebar.tsx` — Full implementation: cu-red branding strip with star emblem, nav items (Dashboard/Traders/Reports/Audit Logs), SYS_ADMIN-only gating on Audit Logs, active state with cu-red left border, user email/role display, Sign Out button with `clearAuth()` + navigate to /admin/login
- `frontend/src/components/layout/ProtectedRoute.tsx` — Full implementation: checks `isAuthenticated()`, `requiredRole` guard (SYS_ADMIN gating strict; TAX_ADMIN routes also accessible to SYS_ADMIN), redirects to login or dashboard
- `frontend/src/components/charts/BarChart.tsx` — Full implementation: recharts `ResponsiveContainer` + `BarChart`, multi-bar support, cu-red default color, loading state spinner, customised axis/grid/tooltip styles
- `frontend/src/components/charts/LineChart.tsx` — Full implementation: recharts `LineChart`, multi-line support, cu-red default, dot/activeDot styling, loading state
- `frontend/src/components/charts/DonutChart.tsx` — Full implementation: recharts `PieChart` with inner/outer radius props, multi-segment with default color palette (cu-red as first), loading state, formatted tooltip
- `frontend/src/router.tsx` — Removed unused `useAuthStore` import (was causing TS6133 error)

**Notes:**
- `npm run lint` (tsc --noEmit) passes with **zero errors** after fixes.
- Four issues encountered and resolved: (1) unused `Link` import in Header, (2) unused `centerLabel` prop in DonutChart (renamed to `_centerLabel`), (3) missing `vite-env.d.ts` causing `import.meta.env` error, (4) unused `useAuthStore` import in router.tsx.
- All components use CU red (`#8A1020`) as primary brand color and inherit from `tailwind.config.ts` tokens.
- `noUnusedLocals: true` and `noUnusedParameters: true` are active in tsconfig — all props are intentionally destructured or prefixed with `_` where unused.
- Stub page files for Phases 9 & 10 remain as single-line stubs — they are not part of Phase 8's scope. Phase 9 and 10 agents will implement them.
- `PublicLayout` now uses the full `Header` and `Footer`; `AdminLayout` uses the full `Sidebar`. The router continues to work as-is.

---

### [PHASE 7] — Backend: Notifications Module + Full Test Suite
**Date:** 2026-03-05
**Agent:** Phase 7 Agent
**Status:** ✅ Complete

**Files Created:**

- `backend/apps/notifications/providers/base.py` — `SMSProvider` abstract base class; declares `send_sms(phone, message) -> dict` returning `{success, message_id, error}`
- `backend/apps/notifications/providers/stub.py` — `StubSMSProvider`: logs intent to `apps.notifications.providers.stub` logger, returns `stub-{uuid}` message IDs, no network calls; used in all environments without AT credentials
- `backend/apps/notifications/providers/africas_talking.py` — `AfricasTalkingProvider`: sends via Africa's Talking REST API using `urllib.request` (no external HTTP deps); accepts AT_API_KEY + AT_USERNAME + optional AT_SENDER_ID from settings; HTTP 101 = success; auto-falls-back to `StubSMSProvider` if credentials are absent
- `backend/apps/notifications/services.py` — `NotificationService`: `_build_provider()` selects `AfricasTalkingProvider` when `AT_API_KEY` is set, else `StubSMSProvider`; `send_tin_sms(phone, tin, name)` builds the registration confirmation message and delegates to provider; returns `{success, message_id}` or `{success: False, error}`
- `backend/tests/__init__.py` — empty package marker
- `backend/tests/conftest.py` — shared pytest fixtures: `test_db_name` (unique session UUID), `mongo_client` (session-scoped PyMongo client), `test_db` (autouse per-test — resets PyMongo singleton to test DB, clears all collections, flushes Redis DB 0 for session isolation), `sys_admin_doc` / `tax_admin_doc` (seeded admin documents), `sys_admin_token` / `tax_admin_token` (valid JWT access tokens), `sample_trader` (factory fixture), `client` (anonymous Django test client), `auth_client_tax` / `auth_client_sys` (pre-authenticated test clients)
- `backend/tests/test_tin.py` — 11 tests: format validation (GH-TIN-[0-9A-F]{6}), uniqueness (100k draws, ≥99,500 distinct — birthday-problem aware), speed (1k TINs <5s), retry on collision, `TINGenerationError` after `MAX_RETRIES`, audit log on exhaustion, lookup found/not-found/name-masking
- `backend/tests/test_registration.py` — 13 tests: service layer (web registration happy path + audit log + USSD channel tag + idempotent duplicate), endpoint layer (POST /api/register 201, validation 422 for invalid phone/missing name/missing location/invalid business_type, duplicate returns 200 with same TIN), TIN lookup endpoint (found, not-found 404, invalid phone 422)
- `backend/tests/test_auth.py` — 15 tests: login success + wrong password 401 + unknown email 401 + inactive account 401; audit logs (LOGIN_SUCCESS / LOGIN_FAIL); token refresh; access token rejected as refresh; protected routes 401 without token; RBAC (TAX_ADMIN 403 on SYS_ADMIN endpoints, SYS_ADMIN can access audit logs); `/api/me` returns correct payload
- `backend/tests/test_ussd.py` — 15 tests: unit tests (7 — mock `_session_store` via `patch` context manager so module state is always restored): initial main menu, option 1 → REG_NAME, invalid option, name too short, valid name → business type, invalid business type, help → END; endpoint tests (8 — real Redis, real MongoDB): initial menu, full 5-step registration flow creates trader, check TIN found, check TIN not found, session persists across requests (mid-flow state preserved), USSD registration appears in traders list, missing session_id 400, invalid input no crash
- `backend/tests/test_reports.py` — 20 tests: summary totals/by_channel/by_business_type, traders list pagination/channel filter, trader detail found/not-found, CSV export (correct columns, row count, audit log written, channel filter applied), all report endpoints require auth, performance test (10k records <3s — skipped unless `RUN_PERF_TESTS=1`)

**Files Modified:**

- `backend/apps/registration/services.py` — replaced inline SMS stub with `NotificationService().send_tin_sms()`; added `normalise_phone` call (via `apps.ussd.validators`) so phone is always stored as `+233XXXXXXXXX` in both `register_trader_web` and `register_trader_ussd`; idempotency check in `register_trader_ussd` also normalises phone before lookup
- `backend/apps/registration/views.py` — moved `@ratelimit` from method decorator to `@method_decorator(..., name="post")` on the class to fix DRF `Request` vs Django `HttpRequest` compatibility (ratelimit requires the Django WSGI request, not the DRF wrapper)
- `backend/apps/tin/views.py` — same ratelimit fix: `@method_decorator(ratelimit(...), name="post")` on `TINLookupView`
- `backend/apps/auth_app/repository.py` — added `{"_id": 0}` projection to `find_by_email` and `find_by_id` to prevent `ObjectId` JSON serialisation errors in `/api/auth/me`
- `backend/core/settings.py` — added `django.contrib.auth` to `INSTALLED_APPS`; `django_ratelimit` introspects the `Permission` model at startup and requires the auth app to be installed
- `backend/tests/test_ussd.py` — refactored `TestUSSDStateMachineUnit._make_sm_with_mock_store()` to use `unittest.mock.patch` context manager so `apps.ussd.state_machine._session_store` is always restored after each unit test (previously the mock leaked into endpoint tests, causing sessions to silently vanish mid-test)

**Notes:**

- **Test isolation strategy:** `test_db` autouse fixture uses a per-session unique DB name (`ghana_tax_test_{uuid4().hex[:8]}`), resets the PyMongo `_client`/`_db` singletons, clears all collections, and calls `r.flushdb()` on Redis DB 0 — ensuring USSD session keys never leak across tests.
- **Phone normalisation:** registrations via both web and USSD now always store `+233XXXXXXXXX` in MongoDB regardless of input format. Callers may pass `0244...`, `233244...`, or `+233244...`; the service normalises before write.
- **ratelimit + DRF:** `django_ratelimit.decorators.ratelimit` must be applied via `@method_decorator(..., name="dispatch|post")` on the class, not directly on the method, when using DRF `APIView`. Direct method decoration receives the DRF `Request` wrapper which lacks `.method` on the view class itself.
- **_session_store mock leakage fix:** the root cause of 3 flaky USSD endpoint tests in the full suite was that `TestUSSDStateMachineUnit` mutated the module-level `apps.ussd.state_machine._session_store` and never restored it. Switching all 7 unit tests to `with patch("apps.ussd.state_machine._session_store") as mock_store:` ensures automatic teardown via `unittest.mock`'s context manager protocol.
- **Test count:** 73 tests pass, 1 skipped (`test_reports_performance_10k` — requires `RUN_PERF_TESTS=1`), 0 failures. Suite is stable across ≥3 consecutive full runs.
- **Git commits (8):** notifications base/stub/AT providers, NotificationService, registration service SMS + phone normalisation, ratelimit view fix, auth repository _id projection fix, settings django.contrib.auth, conftest, full test suite.

---

### [PHASE 6] — Backend: Reports, Audit & Admin APIs
**Date:** 2026-03-05
**Agent:** Phase 6 Agent
**Status:** ✅ Complete

**Files Created:**
- `backend/apps/reports/serializers.py` — ReportsSummaryQuerySerializer (period choice), ReportsExportQuerySerializer (all filter params), TradersListQuerySerializer (channel/business_type/region/district/date_from/date_to/search/page/page_size)
- `backend/apps/reports/services.py` — ReportsService: get_summary (all aggregations, period→date_filter, KPI totals, channel/business-type/region breakdowns, daily trend), get_traders_list (paginated with filters), get_trader_detail (with business join), export_csv (CSV string via io.StringIO, writes EXPORT_REPORT audit log); helpers _period_to_date_filter, _build_filter_dict, CSV_COLUMNS constant
- `backend/apps/reports/views.py` — ReportsSummaryView (GET /api/reports/summary, IsTaxAdmin), ReportsExportView (GET /api/reports/export, returns HttpResponse CSV attachment), TradersListView (GET /api/traders, paginated_response), TraderDetailView (GET /api/traders/<trader_id>)
- `backend/apps/reports/urls.py` — reports_urlpatterns (/summary, /export) + traders_urlpatterns (/, /<trader_id>) exported separately so core/urls.py can mount each at the correct prefix
- `backend/apps/audit/serializers.py` — AuditLogQuerySerializer (action/actor_id/date_from/date_to/page/page_size)
- `backend/apps/audit/views.py` — AuditLogListView (GET /api/audit-logs, IsSysAdmin, paginated, datetime serialised to ISO string)
- `backend/apps/audit/urls.py` — URL routing for GET /api/audit-logs

**Files Modified:**
- `backend/core/urls.py` — added `path("api/traders/", include((traders_urlpatterns, "traders")))` so GET /api/traders and GET /api/traders/<id> resolve correctly; import added for traders_urlpatterns

**Notes:**
- All 8 files pass py_compile and full Django import check with zero errors.
- ReportsService uses only ReportsRepository aggregation pipelines — no Python-level loops over result sets.
- _period_to_date_filter: '7d'→$gte now-7d, '30d'→$gte now-30d, 'all'→None (no date filter added to query).
- Export CSV uses io.StringIO + csv.writer; datetime fields formatted as "YYYY-MM-DD HH:MM:SS"; Content-Disposition triggers browser download.
- traders_urlpatterns exported as a named module-level list so core/urls.py can include them at /api/traders/ without a second urls.py file.
- Audit log datetime fields coerced to ISO string in the view before returning (MongoDB stores as datetime objects).
- EXPORT_REPORT audit log includes filter dict and row_count for traceability.

---

### [PHASE 5] — Backend: USSD Gateway Module
**Date:** 2026-03-05
**Agent:** Phase 5 Agent
**Status:** ✅ Complete

**Files Created:**
- `backend/apps/ussd/validators.py` — validate_ussd_name (3–60 chars), validate_ussd_market (≤80 chars), validate_ussd_phone (Ghana regex), normalise_phone (+233XXXXXXXXX normalisation)
- `backend/apps/ussd/state_machine.py` — USSDStateMachine: full 9-state flow (MAIN_MENU → REG_NAME → REG_BUSINESS_TYPE → REG_REGION → REG_DISTRICT → REG_CONFIRM → COMPLETE; CHECK_TIN; HELP); parses AT *-delimited text history; restores session from USSDSessionStore; writes USSD_SESSION_STEP + USSD_REG_COMPLETE audit logs; calls RegistrationService.register_trader_ussd on confirm
- `backend/apps/ussd/views.py` — USSDCallbackView: csrf_exempt, rate-limited 100/min per IP, AT webhook payload parsing (sessionId/serviceCode/phoneNumber/text), plain-text Content-Type response
- `backend/apps/ussd/urls.py` — URL routing for /ussd/callback

**Files Modified:**
- `backend/apps/ussd/session_store.py` — already fully implemented by Phase 2 agent; no changes needed

**Notes:**
- All 4 new files pass py_compile with zero errors.
- Full Django import + assertion check passes (validators, state machine instantiation, all state constants, USSDCallbackView).
- State machine parses AT `text` field as `*`-delimited history; always takes last segment as current input.
- Session is created on first dial (text=""), restored from Redis/Mongo on subsequent steps.
- On invalid input, steps re-display their own prompt — no session reset.
- "2. Start Over" on confirm screen resets collected data to MAIN_MENU without deleting the session.
- CHECK_TIN: "0" uses caller's own MSISDN; any other input is validated as Ghana phone and normalised.
- HELP goes straight to END (no session persisted).
- register_trader_ussd called with channel="ussd"; idempotent — re-uses existing TIN if msisdn already registered.
- TINGenerationError maps to graceful END response so user isn't left in a broken session.

---

### [PHASE 4] — Backend: Registration + TIN Module
**Date:** 2026-03-05
**Agent:** Phase 4 Agent
**Status:** ✅ Complete

**Files Created:**
- `backend/apps/tin/services.py` — TINService: generate_unique_tin (crypto-random, GH-TIN-XXXXXX format, MAX_RETRIES=10, writes TIN_GENERATION_FAILED audit on exhaustion), lookup_tin (find by phone, masked name response)
- `backend/apps/tin/serializers.py` — TINLookupRequestSerializer, TINLookupResponseSerializer
- `backend/apps/tin/views.py` — TINLookupView: POST /api/tin/lookup, AllowAny, rate-limited 5/min per IP
- `backend/apps/tin/urls.py` — URL routing for /api/tin/lookup
- `backend/apps/registration/validators.py` — validate_ghana_phone (normalises to +233XXXXXXXXX, accepts +233/0/233 prefixes), validate_business_type, VALID_BUSINESS_TYPES constant
- `backend/apps/registration/serializers.py` — TraderRegistrationSerializer (with phone_number validation), LocationInputSerializer, RegistrationResponseSerializer
- `backend/apps/registration/services.py` — RegistrationService: register_trader_web (idempotency, find_or_create location, TIN generation, trader+business create, audit log, SMS stub), register_trader_ussd (for Phase 5 state machine), _send_tin_sms_stub (Phase 7 hook)
- `backend/apps/registration/views.py` — RegisterTraderView: POST /api/register, AllowAny, rate-limited 20/min per IP, XFF-aware IP extraction
- `backend/apps/registration/urls.py` — URL routing for /api/register

**Files Modified:**
- None — all Phase 1 stubs replaced with full implementations; core/urls.py already wired these correctly

**Notes:**
- All 9 new files pass `python3 -m py_compile` with zero errors.
- Full Django import check passes (django.setup() + all class/function imports) — confirmed with live test run.
- Phone validator accepts +233XXXXXXXXX, 0XXXXXXXXX, 233XXXXXXXXX; all normalise to +233XXXXXXXXX.
- register_trader_web is idempotent: repeated calls with same phone return existing TIN (sms_status="skipped").
- register_trader_ussd is a separate method (channel="ussd") used by Phase 5 state machine — same idempotency guarantee.
- SMS sending is a stub (logs intent, returns "queued") — Phase 7 wires the real NotificationService.
- TINGenerationError raised after 10 retries and returns HTTP 503 to client.
- VALID_BUSINESS_TYPES list is the single source of truth shared across validators and serializers.

---

### [PHASE 3] — Backend: Auth Module (JWT + RBAC)
**Date:** 2026-03-05
**Agent:** Phase 3 Agent
**Status:** ✅ Complete

**Files Created:**
- `backend/apps/auth_app/jwt_utils.py` — generate_access_token, generate_refresh_token, verify_token (with expected_type guard), get_token_from_request; custom TokenExpiredError and TokenInvalidError exceptions
- `backend/apps/auth_app/permissions.py` — IsAdminAuthenticated, IsTaxAdmin, IsSysAdmin DRF permission classes; SYS_ADMIN is superset of TAX_ADMIN
- `backend/apps/auth_app/serializers.py` — LoginSerializer, RefreshSerializer, CreateAdminSerializer, UpdateAdminSerializer
- `backend/apps/auth_app/services.py` — AuthService: login (bcrypt verify + timing-attack safe), refresh_access_token, create_admin, update_admin (own-role guard), list_admins, get_me; all write audit logs

**Files Modified:**
- `backend/apps/auth_app/authentication.py` — Full JWTAuthentication DRF backend (replaces Phase 1 stub): verifies Bearer token, loads admin from DB, checks is_active, attaches request.admin
- `backend/apps/auth_app/views.py` — LoginView (rate 10/m), RefreshView (rate 20/m), MeView, AdminUserListCreateView (GET+POST), AdminUserDetailView (PATCH)
- `backend/apps/auth_app/urls.py` — /api/auth/login, /api/auth/refresh, /api/auth/me
- `backend/apps/auth_app/admin_urls.py` — /api/admin/users, /api/admin/users/<admin_id>
- `backend/core/middleware/audit_middleware.py` — Full implementation: X-Forwarded-For aware IP extraction, user_agent truncated to 512 chars, attached to every request
- `backend/core/settings.py` — Fixed INSTALLED_APPS: 'ratelimit' → 'django_ratelimit'

**Git Commits:**
- feat(auth): implement JWT utilities, JWTAuthentication backend, and RBAC permission classes
- feat(auth): implement AuthService, serializers, views and URL config for all auth endpoints
- fix(settings): correct INSTALLED_APPS entry from 'ratelimit' to 'django_ratelimit'

**Notes:**
- 15/15 unit assertions pass (Django setup, JWT round-trips, serializer validation, permission class logic).
- login() always runs bcrypt.checkpw even on unknown email to prevent timing-based user enumeration.
- verify_token() accepts optional expected_type — prevents refresh tokens being used as access tokens.
- JWTAuthentication returns None (not raises) when no Authorization header present, allowing AllowAny endpoints to work.
- Views import `created_response` from core.utils.response — confirmed present from Phase 1.


---

### [PHASE 2] — MongoDB Data Layer & Seed Script
**Date:** 2026-03-05
**Agent:** Phase 2 Agent
**Status:** ✅ Complete

**Files Modified:**
- `backend/core/utils/mongo.py` — Full implementation: singleton MongoClient with 5-retry logic, ping health-check, get_db(), get_collection(), close_client(), collection name constants

**Files Created:**
- `backend/apps/auth_app/repository.py` — AdminRepository: find_by_email, find_by_id, list_all, create, update, update_last_login
- `backend/apps/registration/repository.py` — TraderRepository, BusinessRepository, LocationRepository with full filter query builders
- `backend/apps/tin/repository.py` — TINRepository: exists(), reserve() using atomic upsert
- `backend/apps/reports/repository.py` — ReportsRepository: kpi_totals, summary_by_channel/location/business_type, daily_registrations, export_traders_csv (all aggregation pipelines)
- `backend/apps/audit/repository.py` — AuditRepository: log() (fire-and-forget), list_with_filters
- `backend/apps/ussd/session_store.py` — USSDSessionStore: Redis-first with automatic MongoDB fallback, TTL-aware
- `backend/management/commands/seed_demo_data.py` — Full idempotent seed: 3 admins, 10 locations, 100 traders, 200+ audit logs

**Git Commits:**
- feat(mongo): implement PyMongo singleton with retry logic and collection name constants
- feat(repository): implement AdminRepository, TraderRepository, BusinessRepository, LocationRepository
- feat(repository): implement TINRepository, ReportsRepository, AuditRepository, USSDSessionStore
- feat(seed): implement seed_demo_data command — 3 admins, 10 locations, 100 traders, 200+ audit logs

**Notes:**
- All 71 Python files verified to compile cleanly.
- AuditRepository.log() swallows exceptions so audit failures never interrupt primary flows.
- USSDSessionStore tries Redis first; falls back to MongoDB ussd_sessions silently.
- ReportsRepository uses only aggregation pipelines — no Python-level loops.
- Seed is fully idempotent — safe to run multiple times.


---

### [PHASE 1] — Project Scaffold & Infrastructure
**Date:** 2026-03-05
**Agent:** Phase 1 Agent
**Status:** ✅ Complete

**Files Created:**

*Root:*
- `.gitignore` — Python, Node, Django, Docker, .env patterns
- `README.md` — Full project docs: setup, architecture diagram, API table, USSD curl examples

*Infra (`infra/`):*
- `infra/docker-compose.yml` — Production compose: mongodb, redis, backend, frontend services
- `infra/docker-compose.dev.yml` — Dev compose: hot-reload volumes, frontend on port 5173
- `infra/.env.example` — All required env vars with comments
- `infra/nginx/nginx.conf` — Nginx config: SPA routing, API proxy, USSD proxy, asset caching
- `infra/mongo-init/init.js` — MongoDB init script: all collections, all indexes (unique, TTL)

*Backend (`backend/`):*
- `backend/Dockerfile` — Multi-stage: development + production (gunicorn) targets
- `backend/manage.py` — Django management entry point
- `backend/requirements.txt` — All dependencies pinned with minor-version wildcards
- `backend/.env.example` — Backend-scoped env example (localhost URLs for local dev)
- `backend/pytest.ini` — Pytest config pointing at core.settings
- `backend/core/settings.py` — Full Django settings: decouple, DRF config, CORS, JWT, logging, no-ORM Mongo setup
- `backend/core/urls.py` — Root URL config wiring all app routers
- `backend/core/wsgi.py` — WSGI entry point
- `backend/core/middleware/audit_middleware.py` — Attaches client_ip and user_agent to all requests
- `backend/core/utils/mongo.py` — PyMongo singleton stub with collection name constants
- `backend/core/utils/response.py` — Standard API response envelope helpers + custom DRF exception handler
- `backend/core/utils/pagination.py` — Page/skip/limit extraction helpers
- `backend/apps/auth_app/authentication.py` — JWTAuthentication stub (full impl Phase 3)
- `backend/apps/auth_app/{urls,admin_urls,views,serializers,services,repository}.py` — Stubs
- `backend/apps/{registration,tin,reports,audit,ussd,notifications}/{urls,views,serializers,services,repository}.py` — Stubs
- `backend/apps/ussd/state_machine.py` — Stub (Phase 5)
- `backend/apps/ussd/session_store.py` — Stub (Phase 5)
- `backend/apps/notifications/providers/{base,africas_talking,stub}.py` — Stubs (Phase 7)
- `backend/management/commands/seed_demo_data.py` — Stub (Phase 2)
- `backend/tests/{test_tin,test_registration,test_ussd,test_auth,test_reports}.py` — Stubs (Phase 7)
- All `__init__.py` files for every package

*Frontend (`frontend/`):*
- `frontend/Dockerfile` — Multi-stage: development (Vite dev server) + production (nginx)
- `frontend/package.json` — All deps: react 18, react-router-dom 6, axios, zustand, react-hook-form, zod, recharts, date-fns, clsx
- `frontend/vite.config.ts` — Vite config with `@` path alias and API proxy
- `frontend/tsconfig.json` + `frontend/tsconfig.node.json` — Strict TypeScript config
- `frontend/tailwind.config.ts` — CU color tokens extended into Tailwind theme
- `frontend/postcss.config.js` — Tailwind + autoprefixer
- `frontend/index.html` — HTML entry point with Inter font, meta tags
- `frontend/src/main.tsx` — React DOM entry
- `frontend/src/App.tsx` — Root component
- `frontend/src/router.tsx` — Full route tree: all 11 pages wired (public + protected admin)
- `frontend/src/styles/globals.css` — CSS variables (--cu-red, --cu-bg, etc.) + base styles + portal utilities
- `frontend/src/styles/theme.ts` — TypeScript token constants
- `frontend/src/lib/api.ts` — Axios instance with stub interceptors (Phase 11 adds refresh)
- `frontend/src/lib/auth.ts` — JWT decode + expiry helpers
- `frontend/src/lib/utils.ts` — cn(), formatDate(), formatDateTime(), maskPhone(), formatBusinessType()
- `frontend/src/store/authStore.ts` — Zustand auth store with sessionStorage persistence
- `frontend/src/store/uiStore.ts` — Zustand UI store (sidebar, toasts)
- `frontend/src/components/layout/PublicLayout.tsx` — Minimal public layout with CU red header strip
- `frontend/src/components/layout/AdminLayout.tsx` — Minimal admin layout with sidebar shell
- `frontend/src/components/layout/ProtectedRoute.tsx` — JWT guard + role guard
- `frontend/src/components/layout/{Header,Sidebar,Footer}.tsx` — Stubs (Phase 8)
- `frontend/src/components/ui/{Button,Input,Card,Table,Badge,Modal,Spinner,Alert,Select,index}.tsx` — Stubs (Phase 8)
- `frontend/src/components/charts/{BarChart,LineChart,DonutChart}.tsx` — Stubs (Phase 8)
- `frontend/src/features/trader/pages/{LandingPage,RegisterPage,RegistrationSuccessPage,CheckTinPage,HelpPage}.tsx` — Stubs (Phase 9)
- `frontend/src/features/trader/components/{RegistrationForm,TinDisplay}.tsx` — Stubs (Phase 9)
- `frontend/src/features/trader/hooks/useRegistration.ts` — Stub (Phase 9)
- `frontend/src/features/admin/pages/{LoginPage,DashboardPage,TradersPage,TraderDetailPage,ReportsPage,AuditLogsPage}.tsx` — Stubs (Phase 10)
- `frontend/src/features/admin/components/{StatsCard,TraderTable,FilterBar,ReportSummary,AuditTable}.tsx` — Stubs (Phase 10)
- `frontend/src/features/admin/hooks/{useAdminAuth,useTraders,useReports}.ts` — Stubs (Phase 10)

**Git Commits:**
- `chore(infra): add docker-compose, nginx config, mongo init, env example and gitignore`
- `feat(backend): scaffold Django project structure, settings, core utils, and app stubs`
- `feat(frontend): scaffold Vite+React+TS project, tailwind config, router, stores, all page/component stubs`
- `docs: add project README with setup instructions, architecture diagram, and API reference`

**Notes:**
- Django ORM intentionally NOT used for primary data — MongoDB via PyMongo only. A minimal SQLite db config is kept so Django management commands don't error.
- JWTAuthentication stub is in place so DRF REST_FRAMEWORK config loads cleanly; it returns `None` until Phase 3 implements the real class.
- The frontend router fully wires all 11 routes. Stub pages render a placeholder — the app is navigable immediately.
- `authStore` uses `sessionStorage` (not localStorage) — cleared on tab close for security.
- All `.env` files are `.env.example` only — actual `.env` files are gitignored.
