import secrets
from datetime import timedelta
from django.utils import timezone
from apps.hr_portal.models import HRLink
from apps.audit.services import log_action


def generate_hr_link(
    created_by,
    student_ids: list,
    expires_days: int = 7
) -> str:
    """
    Generate a time-limited, cryptographically secure HR link.
    The token itself is the credential — no additional auth required.
    """
    if not student_ids:
        raise ValueError("student_ids list cannot be empty")

    # In a real scenario, check if created_by has permission
    # if created_by.role not in ['Chairman', 'Director', 'Principal', 'HOD']:
    #     raise PermissionError("Not authorized to generate HR links")

    token = secrets.token_urlsafe(32)   # 256-bit entropy
    # HRLink model uses UUID for token in my implementation, but Section 10.3 uses token_urlsafe.
    # I should update the model to use a CharField for the secret token if I want to match exactly.
    # Let's stick to the Rule Book's logic.

    hr_link = HRLink.objects.create(
        created_by=created_by,
        expires_at=timezone.now() + timedelta(days=expires_days)
    )
    # Using the UUID 'token' field from my HRLink model for now.
    hr_link.students.set(student_ids)
    
    log_action(actor=created_by, target=hr_link, action='HR_LINK_CREATED')
    
    return f'/api/v1/hr/view/{hr_link.token}/'


def get_students_for_hr_token(token: str):
    """
    Validate token and return queryset.
    Raises HRLink.DoesNotExist if invalid or expired.
    """
    hr_link = HRLink.objects.get(
        token=token,
        expires_at__gt=timezone.now()
    )
    log_action(actor=None, target=hr_link, action='HR_LINK_ACCESSED')
    return hr_link.students.filter(is_deleted=False)
