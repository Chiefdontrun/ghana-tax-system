"""
Update an admin login email and password.

Usage:
    python manage.py set_admin_login
    python manage.py set_admin_login --email admin@example.com --password "StrongPass123!"
    python manage.py set_admin_login --current-email old@example.com --email new@example.com
"""

import uuid
from datetime import datetime, timezone

import bcrypt
from django.core.management.base import BaseCommand, CommandError

from core.utils.mongo import ADMINS, AUDIT_LOGS, get_collection


DEFAULT_EMAIL = "marteytheoplius2004@gmail.com"


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


class Command(BaseCommand):
    help = "Update an existing admin account email and password."

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            default=DEFAULT_EMAIL,
            help=f"New admin email/login. Defaults to {DEFAULT_EMAIL}.",
        )
        parser.add_argument(
            "--password",
            default=None,
            help="New admin password. Defaults to the email value if omitted.",
        )
        parser.add_argument(
            "--current-email",
            default=None,
            help="Current admin email to update. If omitted, the first SYS_ADMIN is used.",
        )
        parser.add_argument(
            "--admin-id",
            default=None,
            help="Admin ID to update. Takes priority over --current-email.",
        )

    def handle(self, *args, **options):
        email = options["email"].strip().lower()
        password = options["password"] if options["password"] is not None else email
        current_email = options["current_email"]
        admin_id = options["admin_id"]

        admins = get_collection(ADMINS)
        query = self._build_query(admin_id, current_email)
        admin = admins.find_one(query, {"_id": 0})
        if not admin:
            raise CommandError(
                "No admin found. Pass --current-email or --admin-id to choose the account to update."
            )

        existing_with_email = admins.find_one(
            {"email": email, "admin_id": {"$ne": admin["admin_id"]}},
            {"_id": 0},
        )
        if existing_with_email:
            raise CommandError(f"Another admin already uses {email}.")

        now = datetime.now(timezone.utc)
        admins.update_one(
            {"admin_id": admin["admin_id"]},
            {
                "$set": {
                    "email": email,
                    "password_hash": _hash_password(password),
                    "is_active": True,
                    "updated_at": now,
                }
            },
        )

        get_collection(AUDIT_LOGS).insert_one({
            "event_id": str(uuid.uuid4()),
            "actor_id": "system",
            "actor_role": "system",
            "action": "RESET_ADMIN_LOGIN",
            "entity_type": "admin",
            "entity_id": admin["admin_id"],
            "channel": "management_command",
            "ip_address": "local",
            "user_agent": "manage.py set_admin_login",
            "before": {"email": admin.get("email")},
            "after": {"email": email, "password_changed": True, "is_active": True},
            "created_at": now,
        })

        self.stdout.write(self.style.SUCCESS("Admin login updated successfully."))
        self.stdout.write(f"  admin_id: {admin['admin_id']}")
        self.stdout.write(f"  email   : {email}")
        if options["password"] is None:
            self.stdout.write("  password: same as email")
        else:
            self.stdout.write("  password: updated from --password")

    @staticmethod
    def _build_query(admin_id: str | None, current_email: str | None) -> dict:
        if admin_id:
            return {"admin_id": admin_id}
        if current_email:
            return {"email": current_email.strip().lower()}
        return {"role": "SYS_ADMIN"}
