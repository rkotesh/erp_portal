from django.db.models import QuerySet
from apps.accounts.models import User


def get_all_users() -> QuerySet:
    """Return all active users."""
    return User.objects.filter(is_active=True)


def get_user_by_email(email: str) -> User:
    """Return user by email."""
    return User.objects.get(email=email)
