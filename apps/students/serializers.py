from rest_framework import serializers
from apps.students.models import StudentProfile, Certification, Project
from apps.accounts.serializers import UserSerializer


class CertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = '__all__'


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'


class StudentProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    certifications = CertificationSerializer(many=True, read_only=True)
    projects = ProjectSerializer(many=True, read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            'id', 'user', 'roll_no', 'batch', 'department', 
            'cgpa', 'resume', 'linkedin_url', 'is_public', 
            'slug', 'certifications', 'projects'
        ]
        read_only_fields = ['id', 'slug', 'cgpa']
