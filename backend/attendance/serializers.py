from django.contrib.auth.models import User
import re
from uuid import uuid4
from rest_framework import serializers

from .models import AttendanceRecord, AttendanceSession, Course, Department, UserProfile, Notice


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'user_id', 'username', 'email', 'display_name', 'role', 'department', 'employee_id', 'phone', 'qr_token']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=[('admin', 'Admin'), ('manager', 'Manager'), ('employee', 'Employee')])
    display_name = serializers.CharField(required=True)
    username = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=True)
    department = serializers.CharField(required=False, allow_blank=True)
    employee_id = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role', 'display_name', 'department', 'employee_id', 'phone']

    def validate_email(self, value):
        if value is None:
            raise serializers.ValidationError('Email is required.')
        email = str(value).strip()
        gmail_pattern = r'^(?=.{1,30}@gmail\.com$)(?=[a-z0-9.]*[a-z])[a-z0-9](?!.*\.\.)[a-z0-9.]*[a-z0-9]@gmail\.com$'
        if not re.fullmatch(gmail_pattern, email):
            raise serializers.ValidationError('Enter a valid Gmail address using lowercase letters and numbers before @gmail.com.')
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError('This email is already registered.')
        return email

    def validate_employee_id(self, value):
        if not value:
            return value
        employee_id = str(value).strip()
        if employee_id and UserProfile.objects.filter(employee_id__iexact=employee_id).exists():
            raise serializers.ValidationError('This employee ID is already registered.')
        return employee_id

    def generate_employee_id(self, role):
        prefix = {'employee': 'E', 'manager': 'M', 'admin': 'A'}.get(role, 'U')
        pattern = re.compile(rf'^{prefix}(\d{{1,2}})$', re.IGNORECASE)
        existing_ids = UserProfile.objects.filter(employee_id__iregex=rf'^{prefix}\d{{1,2}}$').values_list('employee_id', flat=True)
        max_number = 0
        for existing_id in existing_ids:
            match = pattern.match(existing_id or '')
            if match:
                number = int(match.group(1))
                if number > max_number:
                    max_number = number
        next_number = max_number + 1
        next_employee_id = f'{prefix}{next_number:02d}'
        while UserProfile.objects.filter(employee_id__iexact=next_employee_id).exists():
            next_number += 1
            next_employee_id = f'{prefix}{next_number:02d}'
        return next_employee_id

    def create(self, validated_data):
        role = validated_data.pop('role')
        display_name = str(validated_data.pop('display_name', '') or '').strip()
        username_candidate = str(validated_data.pop('username', '') or '').strip() or display_name
        department = str(validated_data.pop('department', '') or '').strip()
        employee_id = str(validated_data.pop('employee_id', '') or '').strip()
        phone = str(validated_data.pop('phone', '') or '').strip()

        if not employee_id:
            employee_id = self.generate_employee_id(role)

        # Use a provided username when present; otherwise employee_id is a stable login-friendly fallback.
        base_username = username_candidate.strip() or employee_id.strip() or display_name.strip() or f'user_{uuid4().hex[:8]}'

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


class NoticeSerializer(serializers.ModelSerializer):
    sender = serializers.PrimaryKeyRelatedField(read_only=True)
    recipient = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    sender_name = serializers.SerializerMethodField()
    recipient_name = serializers.SerializerMethodField()

    class Meta:
        model = Notice
        fields = ['id', 'sender', 'sender_name', 'recipient', 'recipient_name', 'message', 'created_at']
        read_only_fields = ['sender', 'sender_name', 'recipient_name', 'created_at']

    def get_sender_name(self, obj):
        sender_profile = getattr(obj.sender, 'profile', None)
        if sender_profile and sender_profile.display_name:
            return sender_profile.display_name
        return obj.sender.username

    def get_recipient_name(self, obj):
        recipient_profile = getattr(obj.recipient, 'profile', None)
        if recipient_profile and recipient_profile.display_name:
            return recipient_profile.display_name
        return obj.recipient.username


class AttendanceRecordSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    session_title = serializers.CharField(source='session.title', read_only=True)
    hours = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceRecord
        fields = ['id', 'employee', 'employee_name', 'session', 'session_title', 'check_in', 'check_out', 'status', 'hours']

    def get_employee_name(self, obj):
        profile = getattr(obj.employee, 'profile', None)
        if profile and profile.display_name:
            return profile.display_name
        return obj.employee.username

    def get_hours(self, obj):
        if not obj.check_in:
            return 0
        end_time = obj.check_out or obj.check_in
        if not end_time or end_time < obj.check_in:
            return 0
        total_hours = (end_time - obj.check_in).total_seconds() / 3600
        return round(total_hours, 2)
