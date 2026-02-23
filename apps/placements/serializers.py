from rest_framework import serializers
from apps.placements.models import Company, PlacementDrive, StudentApplication


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'


class PlacementDriveSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = PlacementDrive
        fields = '__all__'


class StudentApplicationSerializer(serializers.ModelSerializer):
    student_roll_no = serializers.CharField(source='student.roll_no', read_only=True)
    drive_title = serializers.CharField(source='drive.job_title', read_only=True)
    company_name = serializers.CharField(source='drive.company.name', read_only=True)

    class Meta:
        model = StudentApplication
        fields = '__all__'
