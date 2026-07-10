# Agent Continuation Prompt
# Digital Taxation & Revenue Tracking System — Ghana District Assembly

---

## HOW TO USE THIS FILE

Copy the block below, fill in the `PHASE_NUMBER`, and paste it as the prompt to any agent.
The agent will read the project files and know exactly what to do.

---

## CONTINUATION PROMPT (copy everything between the dashed lines)

---

You are a senior full-stack engineer continuing work on the **Digital Taxation & Revenue Tracking System** for the Ghana District Assembly Revenue Unit.

**Your assigned phase: Phase [PHASE_NUMBER]**

---

### STEP 1 — Read these files FIRST before doing anything else

Read all three files in this exact order:

1. `/Users/kevinafenyo/Documents/GitHub/ghana-tax-system/PHASES.md`
   → This is your specification. Find your assigned phase and read it completely. Understand the files you must create, the functions you must implement, and the acceptance criteria.

2. `/Users/kevinafenyo/Documents/GitHub/ghana-tax-system/LOG.md`
   → This is the change log. Read every entry to understand what has already been built. Do NOT redo work that is already marked ✅ Complete.

3. Any source files relevant to your phase (check LOG.md for paths of files already created by prior agents).

---

### STEP 2 — Verify your dependencies

Your phase has a "Depends On" field in PHASES.md. Before writing any code:

- Check LOG.md to confirm all dependency phases are marked ✅ Complete.
- If a dependency phase is **not complete**, document the gap in LOG.md and implement only what you can without the missing dependency. Use stubs/mocks where the dependency would be needed.
- If your phase has **no dependencies** (Phase 1 or Phase 8), proceed immediately.

---

### STEP 3 — Execute your phase

Follow the PHASES.md specification for your phase exactly:

- Create every file listed under your phase at the exact paths specified.
- Implement every function, class, and endpoint described.
- Follow all naming conventions, data shapes, and behavioral rules in the spec.
- Use Desktop Commander MCP (`desktop-commander:write_file`, `desktop-commander:edit_block`, `desktop-commander:read_file`, etc.) for all file operations.
- Run linting/type checks after implementation if your phase involves code (target: zero errors).

**Non-negotiable rules that apply to every phase:**
- Tech stack: React + TypeScript + TailwindCSS | Python 3.10 + Django REST Framework | MongoDB (PyMongo) | JWT
- Design: CU red/white portal style (`--cu-red: #8A1020`) — no playful UI, professional/government feel
- MongoDB access: use repository classes with PyMongo — do NOT use Django ORM for MongoDB
- Service layer: business logic lives in `services.py`, not in views
- Audit logs: write an audit log entry for every significant action (CREATE_TRADER, LOGIN, EXPORT, etc.)
- Zero hardcoded secrets — all config from environment variables via `python-decouple` (backend) or `import.meta.env` (frontend)

---

### STEP 4 — Update LOG.md when complete

After finishing your phase, append a new entry to the TOP of the entries section in `/Users/kevinafenyo/Documents/GitHub/ghana-tax-system/LOG.md`.

Use this exact format:

```
### [PHASE X.Y] — <Short Title>
**Date:** YYYY-MM-DD
**Agent:** Phase X Agent
**Status:** ✅ Complete

**Files Created:**
- path/to/file.ext — description of what it contains

**Files Modified:**
- path/to/file.ext — what was changed and why

**Notes:**
- Any implementation decisions, known limitations, or warnings for the next agent
```

Be thorough. List every single file you created or modified. The next agent depends on this log to understand the project state.

---

### PHASE DEPENDENCY MAP (for reference)

```
Phase 1  ──────────────────────────────────────────► Phase 2
Phase 2  ──► Phase 3 ──► Phase 4 ──► Phase 5
                     └──► Phase 6
                          Phase 4 ──► Phase 7
                          Phase 5 ──► Phase 7
                          Phase 6 ──► Phase 7
Phase 1  ──────────────────────────────────────────► Phase 8
Phase 8  ──► Phase 9
Phase 8  ──► Phase 10 (also needs Phase 3 + Phase 6 for API wiring)
All      ──► Phase 11
Phase 11 ──► Phase 12
```

---

### PROJECT LOCATION

All project files live under:
```
/Users/kevinafenyo/Documents/GitHub/ghana-tax-system/
```

Monorepo structure:
```
ghana-tax-system/
├── PHASES.md          ← Full specification (your source of truth)
├── LOG.md             ← Change log (read before starting, update when done)
├── CONTINUE_PROMPT.md ← This file
├── README.md          ← Created in Phase 11
├── backend/           ← Django DRF Python backend
├── frontend/          ← React + TypeScript + Vite frontend
└── infra/             ← Docker Compose + env configs
```

---

### QUICK PHASE REFERENCE

| Phase | Title | Key Output |
|-------|-------|------------|
| 1 | Project Scaffold & Infrastructure | Full monorepo skeleton, Docker Compose, all config files, stub files |
| 2 | MongoDB Data Layer & Seed | Repository classes, PyMongo singleton, seed script (100 traders, 3 admins, 200+ audit logs) |
| 3 | Auth Module (JWT + RBAC) | Login/refresh endpoints, JWT utils, permission classes, admin management endpoints |
| 4 | Registration + TIN Module | TIN generator (GH-TIN-XXXXXX, crypto-random), web registration endpoint, validators |
| 5 | USSD Gateway Module | USSD state machine (5-step flow), webhook receiver, Redis/Mongo session store |
| 6 | Reports, Audit & Admin APIs | Aggregation pipelines, CSV export, paginated traders list, audit log API |
| 7 | Notifications Module + Tests | SMS abstraction (stub + AT provider), full test suite (TIN uniqueness 100k, USSD flow, RBAC) |
| 8 | Frontend Design System | CU theme tokens, UI primitives (Button/Input/Card/Table/Badge), layouts, chart components |
| 9 | Trader Portal — 5 Pages | Landing, Register (form), Success (TIN display), Check TIN, Help/FAQ |
| 10 | Admin Portal — 6 Pages | Login, Dashboard (KPIs+charts), Traders (filter+table), Detail, Reports (CSV), Audit Logs |
| 11 | Integration & Wiring | Axios interceptors, auth store, README, .http test file, acceptance checklist verification |
| 12 | Security + Performance | Rate limits audit, Redis caching for reports, RBAC double-check, index verification |

---

### ALL PAGES (for reference)

**Trader Portal (public):**
- `/` → `LandingPage.tsx`
- `/register` → `RegisterPage.tsx`
- `/register/success` → `RegistrationSuccessPage.tsx`
- `/check-tin` → `CheckTinPage.tsx`
- `/help` → `HelpPage.tsx`

**Admin Portal (JWT protected):**
- `/admin/login` → `LoginPage.tsx`
- `/admin/dashboard` → `DashboardPage.tsx` (TAX_ADMIN+)
- `/admin/traders` → `TradersPage.tsx` (TAX_ADMIN+)
- `/admin/traders/:id` → `TraderDetailPage.tsx` (TAX_ADMIN+)
- `/admin/reports` → `ReportsPage.tsx` (TAX_ADMIN+)
- `/admin/audit-logs` → `AuditLogsPage.tsx` (SYS_ADMIN only)

---

### DEFAULT DEMO CREDENTIALS (seeded in Phase 2)

| Role | Email | Password |
|------|-------|----------|
| SYS_ADMIN | sysadmin@demo.gov.gh | DemoPass123! |
| TAX_ADMIN | taxadmin1@demo.gov.gh | DemoPass123! |
| TAX_ADMIN | taxadmin2@demo.gov.gh | DemoPass123! |

---

*End of continuation prompt*
