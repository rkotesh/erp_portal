from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_otp_sms(self, user_id: str, otp_code: str):
    """
    Send OTP via SMS. Retries up to 3 times on failure.
    In development, we just log the OTP.
    """
    try:
        from apps.accounts.models import User
        user = User.objects.get(id=user_id)
        
        # In production, call Twilio / MSG91 API here:
        # sms_client.send(to=user.phone, body=f'Your ERP OTP: {otp_code}. Valid for 10 minutes.')
        
        message = f'Your ERP OTP: {otp_code}. Valid for 10 minutes.'
        logger.info(f"SMS to {user.phone}: {message}")
        print(f"DEBUG: SMS to {user.phone}: {message}") # Visible in celery logs
        
        return True
    except Exception as exc:
        logger.error(f"OTP send failed for {user_id}: {exc}")
        raise self.retry(exc=exc)
