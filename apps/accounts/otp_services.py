import random
import string
from django.utils import timezone
from datetime import timedelta
from apps.accounts.models import OTPRecord, User
from django.core.mail import send_mail
from django.conf import settings
import json
import urllib.request
import urllib.parse
import base64
import logging

logger = logging.getLogger(__name__)

def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

def send_otp_email(user, otp, purpose, destination_email=None):
    subject = f'Your ERP {purpose.capitalize()} OTP'
    message = f'Your OTP code is {otp}. It will expire in 10 minutes.'
    email_from = settings.DEFAULT_FROM_EMAIL
    recipient_list = [destination_email or user.email]
    try:
        send_mail(subject, message, email_from, recipient_list, fail_silently=False)
        logger.info(f"OTP email sent to {recipient_list[0]}")
        return True, f"OTP email sent to {recipient_list[0]}"
    except Exception as exc:
        logger.exception("OTP email send failed")
        return False, str(exc)


def _send_sms_via_twilio(to_phone, message):
    """
    Realtime SMS via Twilio REST API if credentials are configured.
    Required env/settings:
      TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER
    """
    account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '') or ''
    auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '') or ''
    from_number = getattr(settings, 'TWILIO_FROM_NUMBER', '') or ''
    if not (account_sid and auth_token and from_number):
        return False, 'Twilio credentials not configured'

    url = f'https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json'
    payload = urllib.parse.urlencode({
        'From': from_number,
        'To': to_phone,
        'Body': message,
    }).encode('utf-8')
    request = urllib.request.Request(url, data=payload)
    auth = base64.b64encode(f'{account_sid}:{auth_token}'.encode('utf-8')).decode('utf-8')
    request.add_header('Authorization', f'Basic {auth}')
    request.add_header('Content-Type', 'application/x-www-form-urlencoded')
    try:
        with urllib.request.urlopen(request, timeout=10) as resp:
            if resp.status in (200, 201):
                return True, 'SMS sent via Twilio'
            return False, f'Twilio response status {resp.status}'
    except Exception as exc:
        return False, str(exc)


def _send_sms_via_generic_api(to_phone, message):
    """
    Realtime SMS via generic HTTP API if configured.
    Required env/settings:
      SMS_API_URL
    Optional:
      SMS_API_TOKEN, SMS_API_PHONE_FIELD, SMS_API_MESSAGE_FIELD
    """
    api_url = getattr(settings, 'SMS_API_URL', '') or ''
    if not api_url:
        return False, 'Generic SMS API not configured'

    token = getattr(settings, 'SMS_API_TOKEN', '') or ''
    phone_field = getattr(settings, 'SMS_API_PHONE_FIELD', 'phone')
    message_field = getattr(settings, 'SMS_API_MESSAGE_FIELD', 'message')
    body = {phone_field: to_phone, message_field: message}
    payload = json.dumps(body).encode('utf-8')
    request = urllib.request.Request(api_url, data=payload, method='POST')
    request.add_header('Content-Type', 'application/json')
    if token:
        request.add_header('Authorization', f'Bearer {token}')

    try:
        with urllib.request.urlopen(request, timeout=10) as resp:
            if 200 <= resp.status < 300:
                return True, 'SMS sent via generic API'
            return False, f'SMS API response status {resp.status}'
    except Exception as exc:
        return False, str(exc)


def send_otp_sms(user, otp, purpose):
    """Realtime SMS send with provider fallbacks."""
    return send_otp_sms_to_phone(user.phone, otp, purpose, user_email=user.email)


def send_otp_sms_to_phone(to_phone, otp, purpose, user_email=''):
    """Realtime SMS send to an explicit destination phone."""
    if not to_phone:
        logger.warning(f"OTP SMS skipped: no phone. user={user_email}")
        return False, 'Phone number missing'

    message = f'Your ERP {purpose.capitalize()} OTP is {otp}. It expires in 10 minutes.'
    ok, info = _send_sms_via_twilio(to_phone, message)
    if ok:
        logger.info(info)
        return True, info

    ok, info2 = _send_sms_via_generic_api(to_phone, message)
    if ok:
        logger.info(info2)
        return True, info2

    # Development fallback
    logger.info(f"SMS fallback (no provider): OTP for {to_phone} is {otp}. Twilio: {info}. Generic: {info2}")
    print(f"DEBUG: OTP SMS for {to_phone} is {otp}")
    return False, f"No SMS provider configured. OTP printed in server log for {to_phone}"

def create_and_send_otp(user, purpose):
    # Expire old unused OTPs
    OTPRecord.objects.filter(user=user, purpose=purpose, is_used=False).update(is_used=True)
    
    otp = generate_otp()
    expires_at = timezone.now() + timedelta(minutes=10)
    
    OTPRecord.objects.create(
        user=user,
        otp_code=otp,
        purpose=purpose,
        expires_at=expires_at
    )
    
    # Realtime multi-channel delivery
    send_otp_email(user, otp, purpose)
    send_otp_sms(user, otp, purpose)
    return True

def verify_otp(user, otp_code, purpose):
    record = OTPRecord.objects.filter(
        user=user,
        otp_code=otp_code,
        purpose=purpose,
        is_used=False,
        expires_at__gt=timezone.now()
    ).first()
    
    if record:
        record.is_used = True
        record.save()
        return True
    return False
