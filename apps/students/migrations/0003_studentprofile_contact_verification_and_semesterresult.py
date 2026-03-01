from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("students", "0002_remove_certification_verified_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="studentprofile",
            name="personal_email_verified",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="studentprofile",
            name="personal_phone_verified",
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name="SemesterResult",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(default=False)),
                ("semester", models.PositiveSmallIntegerField()),
                ("exam_name", models.CharField(default="Semester Exam", max_length=100)),
                ("subject_code", models.CharField(blank=True, default="", max_length=20)),
                ("subject_name", models.CharField(max_length=200)),
                ("score", models.DecimalField(decimal_places=2, max_digits=6)),
                ("max_score", models.DecimalField(decimal_places=2, default=100.0, max_digits=6)),
                ("grade", models.CharField(blank=True, default="", max_length=5)),
                ("proof", models.FileField(blank=True, null=True, upload_to="semester_results/")),
                ("is_verified", models.BooleanField(default=False)),
                ("verified_at", models.DateTimeField(blank=True, null=True)),
                ("rejection_reason", models.TextField(blank=True, default="")),
                (
                    "student",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="semester_results",
                        to="students.studentprofile",
                    ),
                ),
                (
                    "verified_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="semester_result_verifications",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
                "unique_together": {("student", "semester", "exam_name", "subject_code", "subject_name")},
            },
        ),
    ]
