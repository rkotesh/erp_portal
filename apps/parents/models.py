from django.db import models
from apps.core.models import BaseModel

class ParentProfile(BaseModel):
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='parent_profile')
    students = models.ManyToManyField('students.StudentProfile', related_name='parents')

    class Meta:
        verbose_name = 'Parent Profile'

    def __str__(self):
        return f"Parent: {self.user.email}"
