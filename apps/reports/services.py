import os
from django.conf import settings
from django.core.files.base import ContentFile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from openpyxl import Workbook
import io
from apps.reports.models import GeneratedReport
from apps.placements.selectors import get_placement_analytics
from apps.students.models import StudentProfile


def generate_placement_report_pdf(user=None) -> GeneratedReport:
    """Generates a PDF placement report."""
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    stats = get_placement_analytics()
    
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 750, "College ERP - Placement Report")
    
    p.setFont("Helvetica", 12)
    p.drawString(100, 700, f"Total Students Placed: {stats['total_placed']}")
    p.drawString(100, 680, f"Highest Package (LPA): {stats['highest_package']}")
    p.drawString(100, 660, f"Average Package (LPA): {stats.get('avg_package', 0)}")
    p.drawString(100, 640, f"Total Companies: {stats['total_companies']}")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    report = GeneratedReport.objects.create(
        report_type='Placement',
        format='PDF',
        created_by=user
    )
    report.file.save(f"placement_report_{report.id}.pdf", ContentFile(buffer.read()))
    return report


def generate_placement_report_excel(user=None) -> GeneratedReport:
    """Generates an Excel placement report."""
    output = io.BytesIO()
    wb = Workbook()
    ws = wb.active
    ws.title = "Placement Report"
    
    stats = get_placement_analytics()
    
    ws.append(["Metric", "Value"])
    ws.append(["Total Students Placed", stats['total_placed']])
    ws.append(["Highest Package (LPA)", stats['highest_package']])
    ws.append(["Average Package (LPA)", stats.get('avg_package', 0)])
    ws.append(["Total Companies", stats['total_companies']])
    
    wb.save(output)
    output.seek(0)
    
    report = GeneratedReport.objects.create(
        report_type='Placement',
        format='Excel',
        created_by=user
    )
    report.file.save(f"placement_report_{report.id}.xlsx", ContentFile(output.read()))
    return report


def generate_student_academic_report_pdf(student_id, user=None) -> GeneratedReport:
    """Generates a PDF academic report for a specific student."""
    student = StudentProfile.objects.get(id=student_id)
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 750, f"Academic Report: {student.user.email}")
    
    p.setFont("Helvetica", 12)
    p.drawString(100, 700, f"Roll No: {student.roll_no}")
    p.drawString(100, 680, f"Batch: {student.batch}")
    p.drawString(100, 660, f"Department: {student.department.name}")
    p.drawString(100, 640, f"CGPA: {student.cgpa}")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    report = GeneratedReport.objects.create(
        report_type='Student',
        format='PDF',
        created_by=user
    )
    report.file.save(f"student_report_{student.roll_no}_{report.id}.pdf", ContentFile(buffer.read()))
    return report
