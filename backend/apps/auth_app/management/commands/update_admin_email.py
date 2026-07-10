"""
Management command to update an admin's email address and send OTP to the new email.
Usage:
  python manage.py update_admin_email <old_email> <new_email>
  
Example:
  python manage.py update_admin_email "admin@example.com" "marteytheoplius2004@gmail.com"
"""

import logging
from django.core.management.base import BaseCommand, CommandError
from apps.auth_app.repository import AdminRepository
from apps.auth_app.otp_repository import OtpVerificationRepository
from apps.auth_app.email_service import AdminAuthEmailService, EmailDeliveryError
from apps.auth_app.services import AuthService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Update admin email and send OTP verification to the new email address"

    def add_arguments(self, parser):
        parser.add_argument(
            'old_email',
            type=str,
            help='Current email address of the admin to update'
        )
        parser.add_argument(
            'new_email',
            type=str,
            help='New email address (e.g., marteytheoplius2004@gmail.com)'
        )

    def handle(self, *args, **options):
        old_email = options['old_email'].strip()
        new_email = options['new_email'].strip()

        self.stdout.write(self.style.WARNING(f'🔄 Updating admin email from {old_email} to {new_email}...'))

        admin_repo = AdminRepository()
        otp_repo = OtpVerificationRepository()
        email_service = AdminAuthEmailService()
        auth_service = AuthService()

        # Step 1: Find admin by old email
        admin = admin_repo.find_by_email(old_email)
        if not admin:
            raise CommandError(f'❌ Admin not found with email: {old_email}')

        admin_id = admin['admin_id']
        self.stdout.write(f'✓ Found admin: {admin["name"]} (ID: {admin_id})')

        # Step 2: Update email (keeping password and other fields)
        try:
            updated_admin = admin_repo.update(admin_id, {'email': new_email})
            self.stdout.write(self.style.SUCCESS(f'✓ Email updated to: {new_email}'))
        except Exception as e:
            raise CommandError(f'❌ Failed to update email: {str(e)}')

        # Step 3: Invalidate any active OTP codes
        try:
            otp_repo.invalidate_active_for_admin(admin_id)
            self.stdout.write('✓ Invalidated previous OTP codes')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠ Could not clear previous OTPs: {str(e)}'))

        # Step 4: Generate new OTP and send to new email
        try:
            otp_record, plain_code = auth_service._create_otp_record(admin_id)
            self.stdout.write(f'✓ Generated OTP code: {plain_code}')
        except Exception as e:
            raise CommandError(f'❌ Failed to create OTP record: {str(e)}')

        # Step 5: Send OTP to new email
        try:
            email_service.send_otp(new_email, plain_code)
            self.stdout.write(self.style.SUCCESS(f'✓ OTP verification email sent to: {new_email}'))
        except EmailDeliveryError as e:
            otp_repo.invalidate(otp_record['otp_id'])
            raise CommandError(f'❌ Failed to send OTP email: {str(e)}')
        except Exception as e:
            raise CommandError(f'❌ Unexpected error sending OTP: {str(e)}')

        # Step 6: Log the OTP generation event
        try:
            auth_service._log_otp_event(
                admin=updated_admin,
                action='OTP_GENERATED_VIA_EMAIL_UPDATE',
                ip_address='system',
                user_agent='management-command',
                otp_id=otp_record['otp_id'],
            )
            self.stdout.write('✓ Audit log recorded')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠ Could not log audit event: {str(e)}'))

        # Final summary
        self.stdout.write(self.style.SUCCESS('\n✅ Admin email updated successfully!\n'))
        self.stdout.write(self.style.SUCCESS('Summary:'))
        self.stdout.write(f'  • Admin: {updated_admin.get("name")}')
        self.stdout.write(f'  • Old Email: {old_email}')
        self.stdout.write(f'  • New Email: {new_email}')
        self.stdout.write(f'  • Password: Unchanged')
        self.stdout.write(f'  • OTP Code: {plain_code} (expires in 5 minutes)')
        self.stdout.write(f'  • OTP sent to: {new_email}\n')
