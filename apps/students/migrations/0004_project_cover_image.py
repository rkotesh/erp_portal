from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("students", "0003_studentprofile_contact_verification_and_semesterresult"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="cover_image",
            field=models.ImageField(blank=True, null=True, upload_to="project_covers/"),
        ),
    ]
