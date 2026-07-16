"""
seed_demo_data management command.
Creates demo admins, locations, traders, businesses, audit logs,
BOP rate schedules (incl. hawker), income_bracket spread, assessments via
TaxService (affordability cap + bracket turnover), exceptions, and sample payments.
Idempotent — skips or upgrades records as needed for a realistic demo DB.

Usage:
    python manage.py seed_demo_data
"""

import logging
import random
import secrets
import uuid
from datetime import datetime, timezone, timedelta

import bcrypt
from django.core.management.base import BaseCommand
from django.conf import settings

from core.utils.mongo import (
    get_collection,
    ADMINS,
    TRADERS,
    BUSINESSES,
    LOCATIONS,
    AUDIT_LOGS,
    TAX_RATE_SCHEDULES,
    TAX_ASSESSMENTS,
    TAX_PAYMENTS,
    TAX_ASSESSMENT_EXCEPTIONS,
)

logger = logging.getLogger(__name__)

# Tax seed year
TAX_SEED_YEAR = 2026
# Skip Assembly-wide schedule for this type → MISSING_SCHEDULE exceptions
MISSING_SCHEDULE_BUSINESS_TYPE = "artisan"
# FIXED rate types (3–4). Hawker fee is deliberately above BRACKET_1 25% cap
# (cap = GHC 750 = 75000 pesewas) so the affordability clamp is visible in demos.
# Spec example said "GHC 200"; we use GHC 2,000 because only amounts > GHC 750 clamp.
FIXED_FEES_PESEWAS = {
    "hawker": 200_000,      # GHC 2,000 — exceeds BRACKET_1 cap → ASSESSMENT_CAPPED_AFFORDABILITY
    "food_vendor": 15_000,  # GHC 150
    "services": 22_000,     # GHC 220
    "agriculture": 10_000,  # GHC 100
}
# Remaining scheduled types use PERCENTAGE_TURNOVER (3%, min GHC 50, max GHC 2,000)
PERCENTAGE_BUSINESS_TYPES = {"clothing", "electronics", "wholesale", "retail"}
INCOME_BRACKET_CODES = ("BRACKET_1", "BRACKET_2", "BRACKET_3", "BRACKET_4")

# ── Constants ─────────────────────────────────────────────────────────────────

# Hawker first (matches registration menu presentation order).
BUSINESS_TYPES = [
    "hawker", "food_vendor", "clothing", "electronics", "services",
    "agriculture", "wholesale", "retail", "artisan",
]

DEMO_LOCATIONS = [
    {"region": "Greater Accra", "district": "Accra Metropolitan", "market_name": "Accra Central Market"},
    {"region": "Greater Accra", "district": "Accra Metropolitan", "market_name": "Kaneshie Market"},
    {"region": "Greater Accra", "district": "Ga South", "market_name": "Makola Market"},
    {"region": "Ashanti",       "district": "Kumasi Metropolitan", "market_name": "Kumasi Central Market"},
    {"region": "Ashanti",       "district": "Kumasi Metropolitan", "market_name": "Asafo Market"},
    {"region": "Western",       "district": "Sekondi-Takoradi",    "market_name": "Takoradi Market"},
    {"region": "Western",       "district": "Sekondi-Takoradi",    "market_name": "Sekondi Market"},
    {"region": "Northern",      "district": "Tamale Metropolitan", "market_name": "Tamale Central Market"},
    {"region": "Eastern",       "district": "New Juaben",          "market_name": "Koforidua Market"},
    {"region": "Volta",         "district": "Ho Municipal",        "market_name": "Ho Central Market"},
]

GHANAIAN_FIRST_NAMES = [
    "Kwame", "Ama", "Kofi", "Abena", "Yaw", "Akua", "Kwesi", "Adwoa",
    "Kwabena", "Afia", "Kojo", "Efua", "Kweku", "Esi", "Kwadwo", "Araba",
    "Fiifi", "Maame", "Nii", "Adaeze", "Selasi", "Elinam", "Dela", "Kafui",
    "Mawuli", "Sena", "Kekeli", "Yayra", "Setor", "Edem",
]

GHANAIAN_LAST_NAMES = [
    "Mensah", "Asante", "Boateng", "Owusu", "Appiah", "Agyeman", "Osei",
    "Amponsah", "Amoah", "Danso", "Fiagbetor", "Amegashie", "Adzaho",
    "Agbenyega", "Dodzi", "Tetteh", "Quaye", "Nortey", "Ankrah", "Laryea",
    "Afriyie", "Bonsu", "Frimpong", "Kyei", "Yeboah", "Darko", "Asiedu",
    "Baah", "Adusei", "Nkrumah",
]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _random_past(days: int = 90) -> datetime:
    """Return a random datetime within the last `days` days."""
    delta = timedelta(seconds=random.randint(0, days * 86400))
    return _now() - delta


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def _generate_tin() -> str:
    return f"GH-TIN-{secrets.token_hex(3).upper()}"


def _random_ghana_phone() -> str:
    prefixes = ["024", "025", "026", "027", "028", "020", "023", "050", "054", "055", "059"]
    return random.choice(prefixes) + "".join(str(random.randint(0, 9)) for _ in range(7))


def _normalize_phone(phone: str) -> str:
    phone = phone.strip()
    if phone.startswith("0"):
        return "+233" + phone[1:]
    return phone


class Command(BaseCommand):
    help = "Seed the database with demo data (idempotent)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=== Ghana Tax System — Demo Seed ==="))

        location_docs = self._seed_locations()
        admin_docs = self._seed_admins()
        trader_docs = self._seed_traders(location_docs)
        self._seed_audit_logs(admin_docs, trader_docs)
        # Ensure brackets / hawker demo even when traders already existed
        self._ensure_income_brackets_and_hawker_demo(location_docs)
        self._seed_tax_data(admin_docs)

        self.stdout.write(self.style.SUCCESS("\n✅ Seed complete.\n"))

    # ── Locations ──────────────────────────────────────────────────────────────

    def _seed_locations(self) -> list[dict]:
        col = get_collection(LOCATIONS)
        seeded = []
        new_count = 0

        for loc in DEMO_LOCATIONS:
            existing = col.find_one(
                {"region": loc["region"], "market_name": loc["market_name"]},
                {"_id": 0},
            )
            if existing:
                seeded.append(existing)
                continue

            doc = {
                "location_id": str(uuid.uuid4()),
                **loc,
                "created_at": _now(),
            }
            col.insert_one(doc)
            doc.pop("_id", None)
            seeded.append(doc)
            new_count += 1

        self.stdout.write(f"  Locations: {new_count} created, {len(DEMO_LOCATIONS) - new_count} already existed")
        return seeded

    # ── Admins ─────────────────────────────────────────────────────────────────

    def _seed_admins(self) -> list[dict]:
        col = get_collection(ADMINS)
        admin_defs = [
            {
                "email": settings.SEED_ADMIN_EMAIL,
                "name": "System Administrator",
                "role": "SYS_ADMIN",
                "password": settings.SEED_ADMIN_PASSWORD,
            },
            {
                "email": "taxadmin1@demo.gov.gh",
                "name": "Tax Administrator One",
                "role": "TAX_ADMIN",
                "password": settings.SEED_ADMIN_PASSWORD,
            },
            {
                "email": "taxadmin2@demo.gov.gh",
                "name": "Tax Administrator Two",
                "role": "TAX_ADMIN",
                "password": settings.SEED_ADMIN_PASSWORD,
            },
        ]
        seeded = []
        new_count = 0

        for defn in admin_defs:
            existing = col.find_one({"email": defn["email"]}, {"_id": 0})
            if existing:
                seeded.append(existing)
                continue

            now = _now()
            doc = {
                "admin_id": str(uuid.uuid4()),
                "email": defn["email"],
                "name": defn["name"],
                "role": defn["role"],
                "password_hash": _hash_password(defn["password"]),
                "is_active": True,
                "created_at": now,
                "updated_at": now,
                "last_login_at": None,
            }
            col.insert_one(doc)
            doc.pop("_id", None)
            doc.pop("password_hash", None)
            seeded.append(doc)
            new_count += 1

        self.stdout.write(f"  Admins   : {new_count} created, {len(admin_defs) - new_count} already existed")
        return seeded

    # ── Traders ────────────────────────────────────────────────────────────────

    def _seed_traders(self, locations: list[dict]) -> list[dict]:
        trader_col = get_collection(TRADERS)
        business_col = get_collection(BUSINESSES)

        existing_count = trader_col.count_documents({})
        target = 100
        to_create = max(0, target - existing_count)

        if to_create == 0:
            self.stdout.write(f"  Traders  : 0 created, {existing_count} already existed")
            return list(trader_col.find({}, {"_id": 0}).limit(target))

        channels = ["web"] * 60 + ["ussd"] * 40
        random.shuffle(channels)

        # Track used TINs and phones within this seed run
        used_tins: set[str] = set()
        used_phones: set[str] = set()

        seeded = []
        for i in range(to_create):
            first = random.choice(GHANAIAN_FIRST_NAMES)
            last = random.choice(GHANAIAN_LAST_NAMES)
            name = f"{first} {last}"

            phone_raw = _random_ghana_phone()
            phone = _normalize_phone(phone_raw)
            # Ensure uniqueness within seed run
            while phone in used_phones or trader_col.count_documents({"phone_number": phone}, limit=1) > 0:
                phone = _normalize_phone(_random_ghana_phone())
            used_phones.add(phone)

            # Generate collision-free TIN
            tin = _generate_tin()
            while tin in used_tins or trader_col.count_documents({"tin_number": tin}, limit=1) > 0:
                tin = _generate_tin()
            used_tins.add(tin)

            loc = random.choice(locations)
            # Spread types; force first new trader as hawker for menu/cap demos
            if i == 0:
                btype = "hawker"
            else:
                btype = BUSINESS_TYPES[i % len(BUSINESS_TYPES)]
            channel = channels[i % len(channels)]
            created_at = _random_past(90)

            # Spread income brackets; last new trader of this run is legacy (no bracket)
            if i == to_create - 1 and to_create > 1:
                income_bracket = None  # pre-existing / legacy simulation
            else:
                income_bracket = INCOME_BRACKET_CODES[i % len(INCOME_BRACKET_CODES)]
            # Hawker + BRACKET_1 so affordability cap can fire against excessive FIXED fee
            if btype == "hawker" and income_bracket is not None:
                income_bracket = "BRACKET_1"

            trader_id = str(uuid.uuid4())
            trader_doc = {
                "trader_id": trader_id,
                "name": name,
                "phone_number": phone,
                "tin_number": tin,
                "channel": channel,
                "status": "active",
                "business_type": btype,
                "region": loc["region"],
                "district": loc["district"],
                "market_name": loc["market_name"],
                "location_id": loc["location_id"],
                "created_at": created_at,
                "updated_at": created_at,
            }

            business_doc = {
                "business_id": str(uuid.uuid4()),
                "owner_trader_id": trader_id,
                "business_type": btype,
                "location_id": loc["location_id"],
                "created_at": created_at,
            }
            if income_bracket is not None:
                business_doc["income_bracket"] = income_bracket

            try:
                trader_col.insert_one(trader_doc)
                trader_doc.pop("_id", None)
                business_col.insert_one(business_doc)
                business_doc.pop("_id", None)
                seeded.append(trader_doc)
            except Exception as exc:
                logger.warning("Skipping trader insert (likely duplicate): %s", exc)

        self.stdout.write(f"  Traders  : {len(seeded)} created, {existing_count} already existed")
        return seeded

    # ── Audit Logs ─────────────────────────────────────────────────────────────

    def _seed_audit_logs(self, admins: list[dict], traders: list[dict]) -> None:
        col = get_collection(AUDIT_LOGS)
        existing = col.count_documents({})
        if existing >= 200:
            self.stdout.write(f"  Audit    : 0 created, {existing} already existed")
            return

        logs = []

        # LOGIN events for each admin (mix of success and fail)
        for admin in admins:
            for _ in range(random.randint(8, 15)):
                success = random.random() > 0.15
                logs.append({
                    "event_id": str(uuid.uuid4()),
                    "actor_id": admin.get("admin_id", "system"),
                    "actor_role": admin.get("role", "TAX_ADMIN"),
                    "action": "LOGIN_SUCCESS" if success else "LOGIN_FAIL",
                    "entity_type": "session",
                    "entity_id": str(uuid.uuid4()),
                    "channel": "admin",
                    "ip_address": f"41.21.{random.randint(1, 254)}.{random.randint(1, 254)}",
                    "user_agent": "Mozilla/5.0 (compatible; Demo)",
                    "before": None,
                    "after": None,
                    "created_at": _random_past(90),
                })

        # CREATE_TRADER for each seeded trader
        for trader in traders:
            actor = random.choice(admins) if admins else {"admin_id": "system", "role": "system"}
            logs.append({
                "event_id": str(uuid.uuid4()),
                "actor_id": "system",
                "actor_role": "system",
                "action": "CREATE_TRADER",
                "entity_type": "trader",
                "entity_id": trader.get("trader_id", ""),
                "channel": trader.get("channel", "web"),
                "ip_address": f"154.160.{random.randint(1, 254)}.{random.randint(1, 254)}",
                "user_agent": "Ghana-Tax-System/1.0",
                "before": None,
                "after": {
                    "tin_number": trader.get("tin_number"),
                    "name": trader.get("name"),
                    "channel": trader.get("channel"),
                },
                "created_at": trader.get("created_at", _now()),
            })

        # EXPORT_REPORT events (a handful per admin)
        for admin in admins:
            for _ in range(random.randint(2, 5)):
                logs.append({
                    "event_id": str(uuid.uuid4()),
                    "actor_id": admin.get("admin_id", "system"),
                    "actor_role": admin.get("role", "TAX_ADMIN"),
                    "action": "EXPORT_REPORT",
                    "entity_type": "report",
                    "entity_id": str(uuid.uuid4()),
                    "channel": "admin",
                    "ip_address": f"41.21.{random.randint(1, 254)}.{random.randint(1, 254)}",
                    "user_agent": "Mozilla/5.0 (compatible; Demo)",
                    "before": None,
                    "after": {"filters": {"period": "30d"}},
                    "created_at": _random_past(60),
                })

        if logs:
            col.insert_many(logs)

        self.stdout.write(f"  Audit    : {len(logs)} created, {existing} already existed")

    # ── Income brackets + dedicated hawker demo ──────────────────────────────

    def _ensure_income_brackets_and_hawker_demo(self, locations: list[dict]) -> None:
        """
        Backfill income_bracket across businesses (all four codes), leave one
        legacy business without a bracket, and guarantee a hawker + BRACKET_1
        row for the affordability-cap demo. Safe when traders already exist.
        """
        trader_col = get_collection(TRADERS)
        business_col = get_collection(BUSINESSES)

        businesses = list(business_col.find({}, {"_id": 0}))
        if not businesses:
            self.stdout.write("  Brackets : no businesses yet — skip")
            return

        # Leave the oldest business without a bracket (legacy simulation)
        legacy_id = businesses[0]["business_id"]
        updated = 0
        for i, biz in enumerate(businesses):
            bid = biz["business_id"]
            if bid == legacy_id:
                # Explicitly clear if a prior seed set a bracket
                if biz.get("income_bracket") is not None:
                    business_col.update_one(
                        {"business_id": bid},
                        {"$unset": {"income_bracket": ""}},
                    )
                    updated += 1
                continue
            if biz.get("income_bracket") in INCOME_BRACKET_CODES:
                continue
            # Hawker businesses get BRACKET_1 (cap demo); others cycle all four
            if biz.get("business_type") == "hawker":
                bracket = "BRACKET_1"
            else:
                bracket = INCOME_BRACKET_CODES[i % len(INCOME_BRACKET_CODES)]
            business_col.update_one(
                {"business_id": bid},
                {"$set": {"income_bracket": bracket}},
            )
            updated += 1

        # Dedicated hawker + BRACKET_1 if none exists
        hawker_b1 = business_col.find_one({
            "business_type": "hawker",
            "income_bracket": "BRACKET_1",
        })
        created_hawker = 0
        if not hawker_b1:
            loc = locations[0] if locations else {
                "location_id": str(uuid.uuid4()),
                "region": "Greater Accra",
                "district": "Accra Metropolitan",
                "market_name": "Accra Central Market",
            }
            trader_id = str(uuid.uuid4())
            tin = _generate_tin()
            while trader_col.count_documents({"tin_number": tin}, limit=1) > 0:
                tin = _generate_tin()
            phone = _normalize_phone(_random_ghana_phone())
            while trader_col.count_documents({"phone_number": phone}, limit=1) > 0:
                phone = _normalize_phone(_random_ghana_phone())
            created_at = _now()
            trader_col.insert_one({
                "trader_id": trader_id,
                "name": "Akua Hawker Demo",
                "phone_number": phone,
                "tin_number": tin,
                "channel": "web",
                "status": "active",
                "business_type": "hawker",
                "region": loc.get("region", "Greater Accra"),
                "district": loc.get("district", "Accra Metropolitan"),
                "market_name": loc.get("market_name", "Accra Central Market"),
                "location_id": loc.get("location_id"),
                "created_at": created_at,
                "updated_at": created_at,
            })
            business_col.insert_one({
                "business_id": str(uuid.uuid4()),
                "owner_trader_id": trader_id,
                "business_type": "hawker",
                "income_bracket": "BRACKET_1",
                "tin_number": tin,
                "location_id": loc.get("location_id"),
                "created_at": created_at,
            })
            created_hawker = 1

        # Counts for log
        with_bracket = business_col.count_documents({"income_bracket": {"$in": list(INCOME_BRACKET_CODES)}})
        without = business_col.count_documents({
            "$or": [
                {"income_bracket": {"$exists": False}},
                {"income_bracket": None},
            ]
        })
        by_bracket = {
            code: business_col.count_documents({"income_bracket": code})
            for code in INCOME_BRACKET_CODES
        }
        self.stdout.write(
            f"  Brackets : backfilled/updated={updated}, new_hawker_demo={created_hawker}, "
            f"with_bracket={with_bracket}, legacy_no_bracket={without}, spread={by_bracket}"
        )

    # ── Tax schedules, assessments, payments, exceptions ─────────────────────

    def _seed_tax_data(self, admins: list[dict]) -> None:
        """
        Seed BOP rate schedules + generate assessments via real TaxService
        (bracket representative turnover + affordability cap), open exceptions
        for demo, and a few SUCCESS payments for KPI demo.
        """
        from apps.tax.services import TaxService
        from apps.tax.exceptions import TurnoverRequiredError, RateScheduleNotFoundError
        from apps.tax.constants import (
            get_representative_annual_income_pesewas,
            affordability_cap_pesewas,
        )

        admin_id = (admins[0].get("admin_id") if admins else None) or "seed-system"
        schedule_col = get_collection(TAX_RATE_SCHEDULES)
        business_col = get_collection(BUSINESSES)
        assess_col = get_collection(TAX_ASSESSMENTS)
        pay_col = get_collection(TAX_PAYMENTS)
        exc_col = get_collection(TAX_ASSESSMENT_EXCEPTIONS)
        audit_col = get_collection(AUDIT_LOGS)

        # All seeded types + any already in DB
        types_in_db = set(business_col.distinct("business_type") or [])
        business_types = sorted(types_in_db | set(BUSINESS_TYPES))

        # ── 1. Rate schedules (assembly-wide per type except artisan) ───────
        schedules_created = 0
        schedules_updated = 0
        for btype in business_types:
            if btype == MISSING_SCHEDULE_BUSINESS_TYPE:
                continue

            existing = schedule_col.find_one({
                "tax_category": "BOP",
                "business_type": btype,
                "effective_year": TAX_SEED_YEAR,
                "region": None,
                "district": None,
            })

            # FIXED map → fixed; PERCENTAGE set → percentage; else default FIXED
            use_fixed = btype not in PERCENTAGE_BUSINESS_TYPES

            if use_fixed:
                fee = FIXED_FEES_PESEWAS.get(btype, 15_000)
                payload = {
                    "tax_category": "BOP",
                    "business_type": btype,
                    "region": None,
                    "district": None,
                    "rate_type": "FIXED",
                    "fixed_amount": fee,
                    "percentage_rate": None,
                    "min_amount": None,
                    "max_amount": None,
                    "period": "ANNUAL",
                    "effective_year": TAX_SEED_YEAR,
                    "is_active": True,
                    "created_by": admin_id,
                    "updated_at": _now(),
                }
            else:
                payload = {
                    "tax_category": "BOP",
                    "business_type": btype,
                    "region": None,
                    "district": None,
                    "rate_type": "PERCENTAGE_TURNOVER",
                    "fixed_amount": None,
                    "percentage_rate": 3.0,
                    "min_amount": 5_000,    # GHC 50
                    "max_amount": 200_000,  # GHC 2,000
                    "period": "ANNUAL",
                    "effective_year": TAX_SEED_YEAR,
                    "is_active": True,
                    "created_by": admin_id,
                    "updated_at": _now(),
                }

            if existing:
                # Keep hawker (and other FIXED) fees aligned with demo constants
                # so re-seed upgrades older amounts without duplicating rows.
                needs = (
                    existing.get("rate_type") != payload["rate_type"]
                    or existing.get("fixed_amount") != payload.get("fixed_amount")
                    or existing.get("percentage_rate") != payload.get("percentage_rate")
                    or existing.get("min_amount") != payload.get("min_amount")
                    or existing.get("max_amount") != payload.get("max_amount")
                    or not existing.get("is_active", True)
                )
                if needs:
                    schedule_col.update_one(
                        {"schedule_id": existing["schedule_id"]},
                        {"$set": payload},
                    )
                    schedules_updated += 1
                continue

            schedule_col.insert_one({
                "schedule_id": str(uuid.uuid4()),
                "created_at": _now(),
                **payload,
            })
            schedules_created += 1

        # District override: Accra Metropolitan food_vendor (higher fee)
        district_override_created = 0
        if any(t.get("district") == "Accra Metropolitan" for t in get_collection(TRADERS).find({}, {"district": 1})):
            ov = schedule_col.find_one({
                "tax_category": "BOP",
                "business_type": "food_vendor",
                "effective_year": TAX_SEED_YEAR,
                "district": "Accra Metropolitan",
            })
            if not ov:
                schedule_col.insert_one({
                    "schedule_id": str(uuid.uuid4()),
                    "tax_category": "BOP",
                    "business_type": "food_vendor",
                    "region": "Greater Accra",
                    "district": "Accra Metropolitan",
                    "rate_type": "FIXED",
                    "fixed_amount": 28_000,  # GHS 280 — district > assembly
                    "percentage_rate": None,
                    "min_amount": None,
                    "max_amount": None,
                    "period": "ANNUAL",
                    "effective_year": TAX_SEED_YEAR,
                    "is_active": True,
                    "created_by": admin_id,
                    "created_at": _now(),
                    "updated_at": _now(),
                })
                district_override_created = 1

        self.stdout.write(
            f"  Tax sched: {schedules_created} created, {schedules_updated} updated, "
            f"{district_override_created} district override "
            f"(skipped type={MISSING_SCHEDULE_BUSINESS_TYPE!r} for MISSING_SCHEDULE demo); "
            f"FIXED={sorted(FIXED_FEES_PESEWAS)}, PCT={sorted(PERCENTAGE_BUSINESS_TYPES)}"
        )

        # ── 2. Assessments via real TaxService ─────────────────────────────
        tax = TaxService()
        period = str(TAX_SEED_YEAR)
        created = 0
        skipped = 0
        regenerated = 0
        needs_turnover_n = 0
        missing_schedule_n = 0

        businesses = list(business_col.find({}, {"_id": 0}))

        # Force NEEDS_TURNOVER: first two percentage businesses with no bracket
        # (or any percentage if none lack a bracket)
        pct_force_needs: set[str] = set()
        for biz in businesses:
            if biz.get("business_type") not in PERCENTAGE_BUSINESS_TYPES:
                continue
            if biz.get("income_bracket") in INCOME_BRACKET_CODES:
                continue
            pct_force_needs.add(biz["business_id"])
            if len(pct_force_needs) >= 2:
                break
        if len(pct_force_needs) < 1:
            for biz in businesses:
                if biz.get("business_type") in PERCENTAGE_BUSINESS_TYPES:
                    pct_force_needs.add(biz["business_id"])
                    if len(pct_force_needs) >= 2:
                        break

        for business in businesses:
            btype = business.get("business_type")
            bid = business["business_id"]
            bracket = business.get("income_bracket")

            existing = assess_col.find_one({
                "business_id": bid,
                "tax_category": "BOP",
                "period_label": period,
            }, {"_id": 0})

            # Resolve intended turnover for percentage types
            turnover = None
            force_needs = bid in pct_force_needs
            if btype in PERCENTAGE_BUSINESS_TYPES and not force_needs:
                if bracket in INCOME_BRACKET_CODES:
                    turnover = get_representative_annual_income_pesewas(bracket)
                else:
                    turnover = random.randint(1_500_000, 4_000_000)

            # If assessment already exists, keep unless we need to re-apply
            # affordability cap / bracket turnover (stale pre-bracket rows).
            if existing:
                should_regen = False
                if bracket in INCOME_BRACKET_CODES:
                    cap = affordability_cap_pesewas(bracket)
                    due = int(existing.get("amount_due") or 0)
                    # Cap should have applied
                    if cap is not None and due > cap:
                        should_regen = True
                    # Hawker BRACKET_1 must show clamped GHC 750 after FIXED 2000
                    if btype == "hawker" and bracket == "BRACKET_1" and due != 75_000:
                        # 75000 only if assembly FIXED is 200000 and no higher district match
                        should_regen = True
                if force_needs:
                    # Prefer OPEN NEEDS_TURNOVER over a prior successful assessment
                    should_regen = True
                    assess_col.delete_one({"assessment_id": existing["assessment_id"]})
                    pay_col.delete_many({"assessment_id": existing["assessment_id"]})
                    existing = None
                elif should_regen:
                    assess_col.delete_one({"assessment_id": existing["assessment_id"]})
                    pay_col.delete_many({"assessment_id": existing["assessment_id"]})
                    existing = None
                    regenerated += 1
                else:
                    skipped += 1
                    continue

            try:
                tax.generate_assessment(
                    business_id=bid,
                    tax_category="BOP",
                    period_label=period,
                    channel_generated="seed_demo",
                    declared_turnover_pesewas=turnover,
                    audit_log=True,
                    actor_id=admin_id,
                )
                created += 1
            except TurnoverRequiredError:
                tax.log_assessment_exception(bid, "BOP", period, "NEEDS_TURNOVER")
                needs_turnover_n += 1
            except RateScheduleNotFoundError:
                tax.log_assessment_exception(bid, "BOP", period, "MISSING_SCHEDULE")
                missing_schedule_n += 1
            except Exception as exc:
                logger.warning("Seed assessment failed for %s: %s", bid, exc)

        capped_audit_n = audit_col.count_documents({"action": "ASSESSMENT_CAPPED_AFFORDABILITY"})
        open_needs = exc_col.count_documents({"status": "OPEN", "exception_type": "NEEDS_TURNOVER"})
        open_missing = exc_col.count_documents({"status": "OPEN", "exception_type": "MISSING_SCHEDULE"})

        self.stdout.write(
            f"  Tax assess: {created} generated via TaxService, {skipped} already ok, "
            f"stale_regenerated≈{regenerated}, "
            f"NEEDS_TURNOVER_this_run={needs_turnover_n}, MISSING_SCHEDULE_this_run={missing_schedule_n}"
        )
        self.stdout.write(
            f"  Cap audit : ASSESSMENT_CAPPED_AFFORDABILITY total={capped_audit_n} "
            f"(need ≥1 for demo)"
        )
        self.stdout.write(
            f"  Exceptions: OPEN NEEDS_TURNOVER={open_needs}, OPEN MISSING_SCHEDULE={open_missing}"
        )

        # ── 3. Sample SUCCESS payments for KPI demo ────────────────────────
        # Prefer PENDING assessments that are not the cap demo (any is fine)
        pending = list(
            assess_col.find({"status": "PENDING", "period_label": period}, {"_id": 0})
            .limit(10)
        )
        payments_created = 0
        channels = ["web", "ussd"]
        target_payments = 2  # 1 PAID + 1 PARTIAL minimum for reports
        for i, assessment in enumerate(pending):
            if payments_created >= target_payments and payments_created >= 2:
                break
            if pay_col.find_one({"assessment_id": assessment["assessment_id"], "status": "SUCCESS"}):
                continue
            due = int(assessment.get("amount_due") or 0)
            if due <= 0:
                continue
            # Alternate: full PAID then PARTIAL
            if payments_created % 2 == 1:
                amount = max(1, due // 2)
                new_status = "PARTIAL"
            else:
                amount = due
                new_status = "PAID"
            payment_id = str(uuid.uuid4())
            channel = channels[payments_created % 2]
            pay_col.insert_one({
                "payment_id": payment_id,
                "assessment_id": assessment["assessment_id"],
                "trader_id": assessment.get("trader_id"),
                "amount_pesewas": amount,
                "status": "SUCCESS",
                "channel": channel,
                "momo_network": "mtn",
                "provider": "paystack_seed",
                "provider_reference": f"seed-{payment_id[:8]}",
                "phone_number": "+233200000000",
                "created_at": _now(),
                "updated_at": _now(),
            })
            assess_col.update_one(
                {"assessment_id": assessment["assessment_id"]},
                {"$set": {"amount_paid": amount, "status": new_status, "updated_at": _now()}},
            )
            payments_created += 1

        # If DB already had payments, still report current KPI-ish totals
        paid_n = assess_col.count_documents({"status": "PAID", "period_label": period})
        partial_n = assess_col.count_documents({"status": "PARTIAL", "period_label": period})
        pending_n = assess_col.count_documents({"status": "PENDING", "period_label": period})

        self.stdout.write(
            f"  Tax pays : {payments_created} SUCCESS seed payment(s) applied this run; "
            f"status mix period={period}: PAID={paid_n}, PARTIAL={partial_n}, PENDING={pending_n}"
        )

        # KPI snapshot via real aggregator
        try:
            from apps.reports.tax_kpis import aggregate_tax_kpis
            kpis = aggregate_tax_kpis(period_label=period)
            self.stdout.write(
                f"  Tax KPIs : assessed_ghs={kpis.get('total_assessed_ghs')}, "
                f"collected_ghs={kpis.get('total_collected_ghs')}, "
                f"rate_pct={kpis.get('collection_rate_pct')}"
            )
        except Exception as exc:
            logger.warning("KPI snapshot skipped: %s", exc)
            kpis = {}

        # Capped amount sample for log
        capped_sample = assess_col.find_one(
            {"amount_due": 75_000, "period_label": period},
            {"_id": 0, "assessment_id": 1, "business_id": 1, "amount_due": 1},
        )
        self.stdout.write(
            f"  Cap sample assessment: {capped_sample or 'NONE — check hawker BRACKET_1 schedule'}"
        )

        # Summary counts for log
        sched_types = sorted(schedule_col.distinct("business_type") or [])
        self.stdout.write(
            f"  Tax totals now: schedules={schedule_col.count_documents({})}, "
            f"schedule_types={sched_types}, "
            f"assessments={assess_col.count_documents({})}, "
            f"payments={pay_col.count_documents({})}, "
            f"exceptions_open={exc_col.count_documents({'status': 'OPEN'})}, "
            f"capped_audits={capped_audit_n}"
        )
