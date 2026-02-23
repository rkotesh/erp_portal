from celery import shared_task
from apps.reports import services
import logging

logger = logging.getLogger(__name__)


@shared_task
def generate_weekly_placement_report():
    """Scheduled task to generate weekly placement summary."""
    try:
        report = services.generate_placement_report_pdf(user=None)
        logger.info(f"Weekly placement report generated: {report.id}")
        return True
    except Exception as e:
        logger.error(f"Failed to generate weekly report: {e}")
        return False


@shared_task
def generate_async_report(report_type: str, format: str, user_id=None):
    """Background task to generate a requested report."""
    from apps.accounts.models import User
    user = User.objects.get(id=user_id) if user_id else None
    
    if report_type == 'Placement':
        if format == 'PDF':
            services.generate_placement_report_pdf(user)
        else:
            services.generate_placement_report_excel(user)
    # Add other types here
    return True
