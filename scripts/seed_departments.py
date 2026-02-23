import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from apps.academics.models import Department

def seed_departments():
    departments = [
        {'code': 'CSE', 'name': 'Computer Science and Engineering'},
        {'code': 'ECE', 'name': 'Electronics and Communication Engineering'},
        {'code': 'AI', 'name': 'Artificial Intelligence'},
        {'code': 'AIML', 'name': 'Artificial Intelligence and Machine Learning'},
        {'code': 'EEE', 'name': 'Electrical and Electronics Engineering'},
        {'code': 'DS', 'name': 'Data Science'},
        {'code': 'IT', 'name': 'Information Technology'},
        {'code': 'CYBER', 'name': 'Cyber Security'},
        {'code': 'CIVIL', 'name': 'Civil Engineering'},
    ]

    for dept_data in departments:
        dept, created = Department.objects.get_or_create(
            code=dept_data['code'],
            defaults={'name': dept_data['name']}
        )
        if created:
            print(f"Created department: {dept.name} ({dept.code})")
        else:
            print(f"Department already exists: {dept.name} ({dept.code})")

if __name__ == '__main__':
    seed_departments()
