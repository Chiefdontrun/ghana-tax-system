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

from core.utils.mongo import get_collection, ADMINS, TRADERS, BUSINESSES, LOCATIONS, AUDIT_LOGS

logger = logging.getLogger(__name__)

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
