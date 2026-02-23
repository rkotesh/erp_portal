import random
import string
from django.utils import timezone
from datetime import timedelta
from apps.accounts.models import OTPRecord, User
from django.core.mail import send_mail
from django.conf import settings

def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

def send_otp_email(user, otp, purpose):
    subject = f'Your ERP {purpose.capitalize()} OTP'
    message = f'Your OTP code is {otp}. It will expire in 10 minutes.'
    email_from = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]
    send_mail(subject, message, email_from, recipient_list)
    print(f"DEBUG: OTP for {user.email} is {otp}") # Verification for dev

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
    
    send_otp_email(user, otp, purpose)
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
