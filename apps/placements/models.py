from apps.core.models import BaseModel
from django.db import models
from django.core.validators import MinValueValidator


class Company(BaseModel):
    name = models.CharField(max_length=255)
    website = models.URLField(blank=True, default='')
    industry = models.CharField(max_length=100, blank=True, default='')
    description = models.TextField(blank=True, default='')

    class Meta:
        verbose_name_plural = "Companies"

    def __str__(self):
        return self.name


class PlacementDrive(BaseModel):
    class DriveStatus(models.TextChoices):
        UPCOMING = 'Upcoming', 'Upcoming'
        ONGOING = 'Ongoing', 'Ongoing'
        COMPLETED = 'Completed', 'Completed'

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='drives')
    job_title = models.CharField(max_length=200)
    job_description = models.TextField()
    eligibility_cgpa = models.DecimalField(max_digits=4, decimal_places=2, default=0.0)
    eligibility_depts = models.ManyToManyField('academics.Department', related_name='drives')
    deadline = models.DateTimeField()
    status = models.CharField(max_length=20, choices=DriveStatus.choices, default=DriveStatus.UPCOMING)
    ctc_package = models.DecimalField(max_digits=10, decimal_places=2, help_text="In LPA", default=0.0)

    def __str__(self):
        return f"{self.company.name} - {self.job_title}"


class StudentApplication(BaseModel):
    class AppStatus(models.TextChoices):
        APPLIED = 'Applied', 'Applied'
        SHORTLISTED = 'Shortlisted', 'Shortlisted'
        INTERVIEWED = 'Interviewed', 'Interviewed'
        SELECTED = 'Selected', 'Selected'
        REJECTED = 'Rejected', 'Rejected'

    drive = models.ForeignKey(PlacementDrive, on_delete=models.CASCADE, related_name='applications')
    student = models.ForeignKey('students.StudentProfile', on_delete=models.CASCADE, related_name='placements')
    status = models.CharField(max_length=20, choices=AppStatus.choices, default=AppStatus.APPLIED)
    offered_package = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="In LPA")
    remarks = models.TextField(blank=True, default='')

    class Meta:
        unique_together = ('drive', 'student')

    def __str__(self):
        return f"{self.student.roll_no} - {self.drive}"
