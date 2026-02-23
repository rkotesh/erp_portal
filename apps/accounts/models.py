from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from apps.core.models import BaseModel
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    class Role(models.TextChoices):
        CHAIRMAN  = 'Chairman',  'Chairman'
        DIRECTOR  = 'Director',  'Director'
        PRINCIPAL = 'Principal', 'Principal'
        HOD       = 'HOD',       'HOD'
        MENTOR    = 'Mentor',    'Mentor'
        FACULTY   = 'Faculty',   'Faculty'
        STUDENT   = 'Student',   'Student'
        PARENT    = 'Parent',    'Parent'
        HR        = 'HR',        'HR'
        PLACEMENT = 'Placement', 'Placement'

    full_name     = models.CharField(max_length=255, blank=True, default='')
    email         = models.EmailField(unique=True)
    phone         = models.CharField(max_length=15, blank=True, default='')
    role          = models.CharField(max_length=20, choices=Role.choices)
    department    = models.ForeignKey('academics.Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='staff')
    is_active     = models.BooleanField(default=True)
    is_staff      = models.BooleanField(default=False)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['role']

    class Meta:
        verbose_name = 'User'
        ordering     = ['-created_at']

    def __str__(self):
        return f"{self.email} ({self.role})"


class OTPRecord(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otp_records')
    otp_code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=50)  # e.g., 'login', 'reset_password'
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempt_count = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'OTP Record'
        ordering = ['-created_at']

    def __str__(self):
        return f"OTP for {self.user.email} - {self.purpose}"
