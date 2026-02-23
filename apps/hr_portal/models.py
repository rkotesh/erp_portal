from apps.core.models import BaseModel
from django.db import models
import uuid


class HRLink(BaseModel):
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    expires_at = models.DateTimeField()
    students = models.ManyToManyField('students.StudentProfile', related_name='hr_links+')

    def __str__(self):
        return f"HR Link by {self.created_by.email} (Expires: {self.expires_at})"


class HRSharedStudent(BaseModel):
    hr_user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, limit_choices_to={'role': 'HR'}, related_name='shared_students')
    student = models.ForeignKey('students.StudentProfile', on_delete=models.CASCADE, related_name='hr_shared_entries')
    shared_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='shared_students_by_admin')

    class Meta:
        unique_together = ('hr_user', 'student')

    def __str__(self):
        return f"{self.student.user.full_name} shared with {self.hr_user.email}"
