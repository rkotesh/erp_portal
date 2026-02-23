"""
Bulk CSV upload for Users and Students.
Admin-only views that allow importing users from CSV files.
"""
import csv
import io
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db import transaction
from apps.accounts.models import User
from apps.academics.models import Department
from apps.students.models import StudentProfile


VALID_ROLES = [r[0] for r in User.Role.choices]


@csrf_exempt
@staff_member_required
def bulk_upload_view(request):
    """Main CSV upload page with tabs for Users and Students."""
    context = {
        'title': 'Bulk CSV Upload',
        'valid_roles': VALID_ROLES,
        'departments': Department.objects.all().order_by('code'),
    }

    if request.method == 'POST':
        upload_type = request.POST.get('upload_type', '')
        csv_file = request.FILES.get('csv_file')

        if not csv_file:
            messages.error(request, 'Please select a CSV file.')
            return render(request, 'admin/bulk_upload.html', context)

        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Only .csv files are accepted.')
            return render(request, 'admin/bulk_upload.html', context)

        try:
            decoded = csv_file.read().decode('utf-8-sig')  # Handle BOM
            reader = csv.DictReader(io.StringIO(decoded))
            rows = list(reader)
        except Exception as e:
            messages.error(request, f'Error reading CSV: {e}')
            return render(request, 'admin/bulk_upload.html', context)

        if not rows:
            messages.error(request, 'CSV file is empty.')
            return render(request, 'admin/bulk_upload.html', context)

        if upload_type == 'users':
            result = _import_users(rows)
        elif upload_type == 'students':
            result = _import_students(rows)
        else:
            messages.error(request, 'Invalid upload type.')
            return render(request, 'admin/bulk_upload.html', context)

        # Report results
        if result['created']:
            messages.success(request, f"✅ Successfully created {result['created']} records.")
        if result['skipped']:
            messages.warning(request, f"⚠️ Skipped {result['skipped']} rows (duplicates or errors).")
        if result['errors']:
            for err in result['errors'][:20]:  # Show max 20 errors
                messages.error(request, err)
            if len(result['errors']) > 20:
                messages.error(request, f"... and {len(result['errors']) - 20} more errors.")

        return render(request, 'admin/bulk_upload.html', context)

    return render(request, 'admin/bulk_upload.html', context)


def _import_users(rows):
    """
    Import generic users (Faculty, HOD, Mentor, HR, Placement, Parent, etc.)
    Expected CSV columns: full_name, email, phone, role, department_code, password
    """
    result = {'created': 0, 'skipped': 0, 'errors': []}
    required = {'full_name', 'email', 'role', 'password'}

    headers = set(rows[0].keys()) if rows else set()
    missing = required - headers
    if missing:
        result['errors'].append(f"Missing required columns: {', '.join(missing)}")
        return result

    for i, row in enumerate(rows, start=2):  # Row 2 = first data row
        email = row.get('email', '').strip().lower()
        full_name = row.get('full_name', '').strip()
        role = row.get('role', '').strip()
        phone = row.get('phone', '').strip()
        password = row.get('password', '').strip()
        dept_code = row.get('department_code', '').strip().upper()

        if not email or not role or not password:
            result['errors'].append(f"Row {i}: Missing email, role, or password.")
            result['skipped'] += 1
            continue

        if role not in VALID_ROLES:
            result['errors'].append(f"Row {i}: Invalid role '{role}'. Valid: {', '.join(VALID_ROLES)}")
            result['skipped'] += 1
            continue

        if User.objects.filter(email__iexact=email).exists():
            result['errors'].append(f"Row {i}: Email '{email}' already exists — skipped.")
            result['skipped'] += 1
            continue

        department = None
        if dept_code:
            try:
                department = Department.objects.get(code__iexact=dept_code)
            except Department.DoesNotExist:
                result['errors'].append(f"Row {i}: Department code '{dept_code}' not found — skipped.")
                result['skipped'] += 1
                continue

        try:
            User.objects.create_user(
                email=email,
                password=password,
                full_name=full_name,
                role=role,
                phone=phone,
                department=department,
                is_active=True,
                is_staff=(role in ['Chairman', 'Director', 'Principal']),
            )
            result['created'] += 1
        except Exception as e:
            result['errors'].append(f"Row {i}: {str(e)}")
            result['skipped'] += 1

    return result


def _import_students(rows):
    """
    Import students — creates User + StudentProfile in one go.
    Expected CSV columns: full_name, email, phone, roll_no, batch, department_code, password
    """
    result = {'created': 0, 'skipped': 0, 'errors': []}
    required = {'full_name', 'email', 'roll_no', 'batch', 'department_code', 'password'}

    headers = set(rows[0].keys()) if rows else set()
    missing = required - headers
    if missing:
        result['errors'].append(f"Missing required columns: {', '.join(missing)}")
        return result

    for i, row in enumerate(rows, start=2):
        email = row.get('email', '').strip().lower()
        full_name = row.get('full_name', '').strip()
        phone = row.get('phone', '').strip()
        roll_no = row.get('roll_no', '').strip().upper()
        batch = row.get('batch', '').strip()
        dept_code = row.get('department_code', '').strip().upper()
        password = row.get('password', '').strip()

        if not email or not roll_no or not batch or not dept_code or not password:
            result['errors'].append(f"Row {i}: Missing required field(s).")
            result['skipped'] += 1
            continue

        if User.objects.filter(email__iexact=email).exists():
            result['errors'].append(f"Row {i}: Email '{email}' already exists — skipped.")
            result['skipped'] += 1
            continue

        if StudentProfile.objects.filter(roll_no__iexact=roll_no).exists():
            result['errors'].append(f"Row {i}: Roll No '{roll_no}' already exists — skipped.")
            result['skipped'] += 1
            continue

        try:
            department = Department.objects.get(code__iexact=dept_code)
        except Department.DoesNotExist:
            result['errors'].append(f"Row {i}: Department '{dept_code}' not found — skipped.")
            result['skipped'] += 1
            continue

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    email=email,
                    password=password,
                    full_name=full_name,
                    role='Student',
                    phone=phone,
                    department=department,
                    is_active=True,
                )
                StudentProfile.objects.create(
                    user=user,
                    roll_no=roll_no,
                    batch=batch,
                    department=department,
                )
            result['created'] += 1
        except Exception as e:
            result['errors'].append(f"Row {i}: {str(e)}")
            result['skipped'] += 1

    return result


@staff_member_required
def download_sample_csv(request):
    """Download a sample CSV template for the selected upload type."""
    upload_type = request.GET.get('type', 'users')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="sample_{upload_type}.csv"'
    writer = csv.writer(response)

    if upload_type == 'students':
        writer.writerow(['full_name', 'email', 'phone', 'roll_no', 'batch', 'department_code', 'password'])
        writer.writerow(['Ravi Kumar', 'ravi@ciet.edu.in', '9876543210', '22B01A0501', '2022-2026', 'CSE', 'Welcome@123'])
        writer.writerow(['Priya Sharma', 'priya@ciet.edu.in', '9876543211', '22B01A0502', '2022-2026', 'CSE', 'Welcome@123'])
        writer.writerow(['Kiran Reddy', 'kiran@ciet.edu.in', '9876543212', '22B01A0301', '2022-2026', 'ECE', 'Welcome@123'])
    else:
        writer.writerow(['full_name', 'email', 'phone', 'role', 'department_code', 'password'])
        writer.writerow(['Dr. Ramesh', 'ramesh@ciet.edu.in', '9876543213', 'Faculty', 'CSE', 'Faculty@123'])
        writer.writerow(['Prof. Suresh', 'suresh@ciet.edu.in', '9876543214', 'HOD', 'ECE', 'Hod@12345'])
        writer.writerow(['Anitha HR', 'anitha@ciet.edu.in', '9876543215', 'HR', '', 'Hr@123456'])

    return response
