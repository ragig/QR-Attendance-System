from django.contrib.auth.models import User
from uuid import uuid4
from rest_framework import serializers

from .models import AttendanceRecord, AttendanceSession, Course, Department, UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'display_name', 'role', 'department', 'employee_id', 'phone', 'qr_token']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=[('admin', 'Admin'), ('manager', 'Manager'), ('employee', 'Employee')])
    display_name = serializers.CharField(required=True)
    username = serializers.CharField(required=False, allow_blank=True)
    department = serializers.CharField(required=False, allow_blank=True)
    employee_id = serializers.CharField(required=True)
    phone = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role', 'display_name', 'department', 'employee_id', 'phone']

    def validate_employee_id(self, value):
        employee_id = value.strip()
        if UserProfile.objects.filter(employee_id=employee_id).exists():
            raise serializers.ValidationError('This employee ID is already registered.')
        return employee_id

    def create(self, validated_data):
        role = validated_data.pop('role')
        display_name = validated_data.pop('display_name', '')
        username_candidate = validated_data.pop('username', '') or display_name
        department = validated_data.pop('department', '')
        employee_id = validated_data.pop('employee_id', '')
        phone = validated_data.pop('phone', '')

        # Prefer using employee_id as username when available to ensure uniqueness.
        # Fall back to the provided username/display name, and ultimately a short uuid.
        if employee_id and employee_id.strip():
            base_username = employee_id.strip()
        else:
            base_username = username_candidate.strip() or display_name.strip() or f'user_{uuid4().hex[:8]}'

        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f'{base_username}_{counter}'
            counter += 1

        user = User.objects.create_user(
            username=username,
            email=validated_data.get('email', ''),
            password=validated_data['password'],
        )
        UserProfile.objects.create(
            user=user,
            role=role,
            display_name=display_name,
            department=department,
            employee_id=employee_id,
            phone=phone,
        )
        return user


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'description']


class CourseSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'name', 'department', 'department_name', 'description']


class AttendanceSessionSerializer(serializers.ModelSerializer):
    faculty_name = serializers.CharField(source='faculty.username', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    qr_code_value = serializers.CharField(source='qr_code', read_only=True)
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all(), required=False, allow_null=True)

    class Meta:
        model = AttendanceSession
        fields = ['id', 'title', 'course', 'course_name', 'faculty', 'faculty_name', 'qr_code_value', 'expires_at', 'active', 'created_at']
        read_only_fields = ['faculty', 'qr_code', 'created_at']


class AttendanceRecordSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    session_title = serializers.CharField(source='session.title', read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = ['id', 'employee', 'employee_name', 'session', 'session_title', 'check_in', 'check_out', 'status']

    def get_employee_name(self, obj):
        profile = getattr(obj.employee, 'profile', None)
        if profile and profile.display_name:
            return profile.display_name
        return obj.employee.username
