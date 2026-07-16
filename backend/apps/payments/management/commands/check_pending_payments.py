"""
CLI wrapper: python manage.py check_pending_payments

Core logic lives in PaymentService.run_pending_payment_check() so the HTTP
cron endpoint and this command stay in sync.
"""

from django.core.management.base import BaseCommand

from apps.payments.services import PaymentService


class Command(BaseCommand):
    help = (
        "Polls PENDING_AUTHORIZATION payments older than 5 minutes and "
        "verifies them against the payment provider."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--minutes",
            type=int,
            default=5,
            help="Only payments older than this many minutes (default 5).",
        )

    def handle(self, *args, **options):
        minutes = options["minutes"]
        summary = PaymentService().run_pending_payment_check(older_than_minutes=minutes)

        self.stdout.write(
            self.style.NOTICE(
                f"Checked {summary['checked']} pending payment(s) "
                f"(older than {summary['older_than_minutes']} min)."
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"resolved_success={summary['resolved_success']} "
                f"resolved_failed={summary['resolved_failed']} "
                f"still_pending={summary['still_pending']} "
                f"skipped_no_reference={summary['skipped_no_reference']}"
            )
        )
