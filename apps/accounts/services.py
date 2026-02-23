from django.utils import timezone
from datetime import timedelta
import random
from apps.accounts.models import OTPRecord, User
from apps.notifications.tasks import send_otp_sms


def generate_and_send_otp(user: User, purpose: str) -> None:
    """Generate OTP and dispatch async SMS."""
    otp_code = f"{random.randint(100000, 999999)}"
    OTPRecord.objects.create(
        user=user,
        otp_code=otp_code,
        purpose=purpose,
        expires_at=timezone.now() + timedelta(minutes=10)
    )
    # Dispatch Celery task
    send_otp_sms.delay(str(user.id), otp_code)


def verify_otp(user: User, otp_code: str, purpose: str) -> bool:
    """
    Verify OTP. Locks account after 3 failed attempts.
    Returns True on success, False on failure.
    """
    try:
        record = OTPRecord.objects.filter(
            user=user,
            purpose=purpose,
            is_used=False,
            expires_at__gt=timezone.now()
        ).latest('created_at')
    except OTPRecord.DoesNotExist:
        return False

    if record.otp_code != otp_code:
        record.attempt_count += 1
        record.save(update_fields=['attempt_count'])
        if record.attempt_count >= 3:
            user.is_active = False
            user.save(update_fields=['is_active'])
        return False

    record.is_used = True
    record.save(update_fields=['is_used'])
    return True
