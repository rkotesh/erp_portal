from apps.audit.models import AuditLog
import json


def log_action(actor, target, action: str, request=None) -> None:
    """
    Record an immutable audit event.
    Called from services after every write operation.
    """
    AuditLog.objects.create(
        actor=actor,
        action=action,
        model_name=target.__class__.__name__,
        object_id=str(target.pk),
        changes_json={},  # In a full implementation, pass before/after diff
        ip_address=getattr(request, 'META', {}).get('REMOTE_ADDR', '') if request else '',
    )
