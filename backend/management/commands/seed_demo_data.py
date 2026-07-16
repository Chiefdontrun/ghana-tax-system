"""
seed_demo_data management command.
Creates demo admins, locations, traders, businesses, and audit logs.
Idempotent — skips any record that already exists.

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
# Percentage-of-turnover types (others with schedules use FIXED)
PERCENTAGE_BUSINESS_TYPES = {"electronics", "clothing"}
FIXED_FEES_PESEWAS = {
    "food_vendor": 15000,   # GHS 150
    "services": 22000,      # GHS 220
    "agriculture": 10000,   # GHS 100
    "wholesale": 30000,     # GHS 300
    "retail": 18000,        # GHS 180
}

# ── Constants ─────────────────────────────────────────────────────────────────

BUSINESS_TYPES = [
    "food_vendor", "clothing", "electronics", "services",
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
            btype = random.choice(BUSINESS_TYPES)
            channel = channels[i % len(channels)]
            created_at = _random_past(90)

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

    # ── Tax schedules, assessments, payments, exceptions ─────────────────────

    def _seed_tax_data(self, admins: list[dict]) -> None:
        """
        Seed BOP rate schedules + generate assessments via TaxService,
        open exceptions for demo, and a few SUCCESS payments for KPI demo.
        Idempotent on schedules (unique by type/scope/year) and assessments
        (TaxService already idempotent per business/period).
        """
        from apps.tax.services import TaxService
        from apps.tax.exceptions import TurnoverRequiredError, RateScheduleNotFoundError

        admin_id = (admins[0].get("admin_id") if admins else None) or "seed-system"
        schedule_col = get_collection(TAX_RATE_SCHEDULES)
        business_col = get_collection(BUSINESSES)

        # Distinct business types from live data (fallback to constants)
        types_in_db = business_col.distinct("business_type")
        business_types = sorted(set(types_in_db) or set(BUSINESS_TYPES))

        # ── 1. Rate schedules ───────────────────────────────────────────────
        schedules_created = 0
        for btype in business_types:
            if btype == MISSING_SCHEDULE_BUSINESS_TYPE:
                # Deliberately no Assembly-wide schedule → MISSING_SCHEDULE queue
                continue

            existing = schedule_col.find_one({
                "tax_category": "BOP",
                "business_type": btype,
                "effective_year": TAX_SEED_YEAR,
                "region": None,
                "district": None,
            }, {"_id": 0})
            if existing:
                continue

            if btype in PERCENTAGE_BUSINESS_TYPES:
                doc = {
                    "schedule_id": str(uuid.uuid4()),
                    "tax_category": "BOP",
                    "business_type": btype,
                    "region": None,
                    "district": None,
                    "rate_type": "PERCENTAGE_TURNOVER",
                    "fixed_amount": None,
                    "percentage_rate": 3.0,
                    "min_amount": 5000,
                    "max_amount": 200000,
                    "period": "ANNUAL",
                    "effective_year": TAX_SEED_YEAR,
                    "is_active": True,
                    "created_by": admin_id,
                    "created_at": _now(),
                    "updated_at": _now(),
                }
            else:
                fee = FIXED_FEES_PESEWAS.get(btype, 15000)
                doc = {
                    "schedule_id": str(uuid.uuid4()),
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
                    "created_at": _now(),
                    "updated_at": _now(),
                }
            schedule_col.insert_one(doc)
            schedules_created += 1

        # District override: Accra Metropolitan food_vendor (higher fee) if that district exists
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
                    "fixed_amount": 28000,  # GHS 280 — district > assembly
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
            f"  Tax sched: {schedules_created} assembly-wide + {district_override_created} district override "
            f"(skipped type={MISSING_SCHEDULE_BUSINESS_TYPE!r} for MISSING_SCHEDULE demo)"
        )

        # ── 2. Assessments via real TaxService ─────────────────────────────
        tax = TaxService()
        period = str(TAX_SEED_YEAR)
        created = 0
        skipped = 0
        needs_turnover_n = 0
        missing_schedule_n = 0
        # Leave first few percentage businesses without turnover for NEEDS_TURNOVER
        pct_left_for_exception = 2

        businesses = list(business_col.find({}, {"_id": 0}))
        for business in businesses:
            btype = business.get("business_type")
            bid = business["business_id"]

            existing = get_collection(TAX_ASSESSMENTS).find_one({
                "business_id": bid,
                "tax_category": "BOP",
                "period_label": period,
            })
            if existing:
                skipped += 1
                continue

            turnover = None
            if btype in PERCENTAGE_BUSINESS_TYPES:
                if pct_left_for_exception > 0:
                    pct_left_for_exception -= 1
                    turnover = None  # force NEEDS_TURNOVER
                else:
                    turnover = random.randint(1_500_000, 4_000_000)  # GHS 15k–40k

            try:
                tax.generate_assessment(
                    business_id=bid,
                    tax_category="BOP",
                    period_label=period,
                    channel_generated="seed_demo",
                    declared_turnover_pesewas=turnover,
                    audit_log=False,
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

        self.stdout.write(
            f"  Tax assess: {created} generated via TaxService, {skipped} already existed, "
            f"NEEDS_TURNOVER={needs_turnover_n}, MISSING_SCHEDULE={missing_schedule_n}"
        )

        # ── 3. Sample SUCCESS payments for KPI demo ────────────────────────
        pay_col = get_collection(TAX_PAYMENTS)
        assess_col = get_collection(TAX_ASSESSMENTS)
        pending = list(
            assess_col.find({"status": "PENDING", "period_label": period}, {"_id": 0})
            .limit(5)
        )
        payments_created = 0
        channels = ["web", "ussd"]
        for i, assessment in enumerate(pending[:3]):
            # Avoid re-seeding if this assessment already has a SUCCESS payment
            if pay_col.find_one({"assessment_id": assessment["assessment_id"], "status": "SUCCESS"}):
                continue
            due = int(assessment.get("amount_due") or 0)
            if due <= 0:
                continue
            # First: full PAID; second: PARTIAL (~50%); third: full PAID
            if i == 1:
                amount = max(1, due // 2)
                new_status = "PARTIAL"
            else:
                amount = due
                new_status = "PAID"
            payment_id = str(uuid.uuid4())
            pay_col.insert_one({
                "payment_id": payment_id,
                "assessment_id": assessment["assessment_id"],
                "trader_id": assessment.get("trader_id"),
                "amount_pesewas": amount,
                "status": "SUCCESS",
                "channel": channels[i % 2],
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

        self.stdout.write(f"  Tax pays : {payments_created} SUCCESS seed payment(s) applied")

        # Summary counts for log
        self.stdout.write(
            f"  Tax totals now: schedules={schedule_col.count_documents({})}, "
            f"assessments={assess_col.count_documents({})}, "
            f"payments={pay_col.count_documents({})}, "
            f"exceptions_open={get_collection(TAX_ASSESSMENT_EXCEPTIONS).count_documents({'status': 'OPEN'})}"
        )
