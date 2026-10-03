import csv
from collections import defaultdict
from datetime import timedelta, datetime
from uuid import uuid4

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import AttendanceRecord, AttendanceSession, Course, Department, UserProfile, Notice
from .serializers import (
    AttendanceRecordSerializer,
    AttendanceSessionSerializer,
    CourseSerializer,
    DepartmentSerializer,
    NoticeSerializer,
    RegisterSerializer,
    UserProfileSerializer,
)


class RoleRequired(permissions.BasePermission):
    allowed_roles = []

    def has_permission(self, request, view):
        profile = getattr(request.user, 'profile', None)
        return bool(request.user and request.user.is_authenticated and profile and profile.role in self.allowed_roles)


class IsAdmin(RoleRequired):
    allowed_roles = ['admin']


class IsManager(RoleRequired):
    allowed_roles = ['manager']


class IsEmployee(RoleRequired):
    allowed_roles = ['employee']


class IsAttendanceUser(RoleRequired):
    allowed_roles = ['employee', 'manager']


def employee_attendance_records():
    return AttendanceRecord.objects.filter(employee__profile__role='employee')


def employee_profiles():
    return UserProfile.objects.select_related('user').filter(role='employee').order_by('id')


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_view(request):
    """Allow the first admin account to be created and permit admins to create more users afterward."""
    role = (request.data.get('role') or '').strip().lower()
    has_existing_users = User.objects.exists()
    payload = dict(request.data)

    if has_existing_users:
        if not getattr(request.user, 'is_authenticated', False):
            return Response({'detail': 'Authentication required to register a new user.'}, status=status.HTTP_401_UNAUTHORIZED)
        profile = getattr(request.user, 'profile', None)
        if not profile or profile.role not in {'admin', 'manager'}:
            return Response({'detail': 'Only admins can register new users.'}, status=status.HTTP_403_FORBIDDEN)
    else:
        payload['role'] = 'admin'

    if 'role' in payload and not payload['role']:
        payload['role'] = 'employee'
    if 'email' in payload and isinstance(payload['email'], list):
        payload['email'] = payload['email'][0]
    if 'display_name' in payload and isinstance(payload['display_name'], list):
        payload['display_name'] = payload['display_name'][0]

    serializer = RegisterSerializer(data=payload)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserProfileSerializer(user.profile).data,
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    employee_id = request.data.get('employee_id')
    password = request.data.get('password')
    if not employee_id:
        return Response({'detail': 'Employee ID is required'}, status=status.HTTP_400_BAD_REQUEST)

    profile = UserProfile.objects.filter(employee_id=employee_id).first()
    if not profile:
        return Response({'detail': 'Invalid employee ID or password'}, status=status.HTTP_401_UNAUTHORIZED)

    user = authenticate(username=profile.user.username, password=password)
    if user is None:
        return Response({'detail': 'Invalid employee ID or password'}, status=status.HTTP_401_UNAUTHORIZED)

    refresh = RefreshToken.for_user(user)
    return Response({
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'user': UserProfileSerializer(profile).data,
    })


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def qr_login_view(request):
    qr_token = request.data.get('qr_token')
    if not qr_token:
        return Response({'detail': 'QR token required'}, status=status.HTTP_400_BAD_REQUEST)
    profile = UserProfile.objects.filter(qr_token=qr_token).first()
    if not profile:
        return Response({'detail': 'Invalid QR token'}, status=status.HTTP_401_UNAUTHORIZED)

    today = timezone.localtime(timezone.now()).date()
    active_record = AttendanceRecord.objects.filter(
        employee=profile.user,
        check_in__date=today,
        check_out__isnull=True,
    ).order_by('-check_in').first()
    refresh = RefreshToken.for_user(profile.user)
    return Response({
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'user': UserProfileSerializer(profile).data,
        'active_attendance': active_record.id if active_record else None,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user, defaults={'role': 'employee'})
    return Response(UserProfileSerializer(profile).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user, defaults={'role': 'employee'})
    if profile.role == 'admin':
        employees = employee_profiles()
        managers = UserProfile.objects.select_related('user').filter(role='manager').order_by('employee_id', 'display_name')
        total_employees = employees.count()
        total_managers = managers.count()
        attendance_records = AttendanceRecord.objects.count()
        notices = Notice.objects.filter(sender=request.user).order_by('-created_at')
        return Response({
            'role': profile.role,
            'summary': {
                'employees': total_employees,
                'managers': total_managers,
                'attendanceRecords': attendance_records,
                'notices': notices.count(),
            },
            'employees': UserProfileSerializer(employees, many=True).data,
            'managers': UserProfileSerializer(managers, many=True).data,
            'notices': NoticeSerializer(notices, many=True).data,
        })
    if profile.role == 'manager':
        employees = employee_profiles()
        employee_count = employees.count()
        manager_records = AttendanceRecord.objects.filter(employee=request.user, check_in__isnull=False)
        manager_present_days = {
            timezone.localtime(record.check_in).date()
            for record in manager_records
            if record.check_in
        }
        notices = Notice.objects.filter(recipient=request.user).order_by('-created_at')
        return Response({
            'role': profile.role,
            'summary': {
                'employees': employee_count,
                'attendanceRecords': len(manager_present_days),
                'notices': notices.count(),
            },
            'employees': UserProfileSerializer(employees, many=True).data,
            'notices': NoticeSerializer(notices, many=True).data,
        })
    notices = Notice.objects.filter(recipient=request.user).order_by('-created_at')
    user_records = AttendanceRecord.objects.filter(employee=request.user, check_in__isnull=False)
    distinct_days = {
        timezone.localtime(record.check_in).date()
        for record in user_records
        if record.check_in
    }
    return Response({
        'role': profile.role,
        'summary': {
            'records': len(distinct_days),
            'notices': notices.count(),
        },
        'notices': NoticeSerializer(notices, many=True).data,
    })


class NoticeListCreateView(generics.ListCreateAPIView):
    serializer_class = NoticeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user, defaults={'role': 'employee'})
        if profile.role == 'admin':
            return Notice.objects.filter(sender=self.request.user).order_by('-created_at')
        return Notice.objects.filter(recipient=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user, defaults={'role': 'employee'})
        if profile.role != 'admin':
            raise permissions.PermissionDenied('Only admins can send notices.')
        serializer.save(sender=self.request.user)


class NoticeDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = NoticeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user, defaults={'role': 'employee'})
        if profile.role == 'admin':
            return Notice.objects.filter(sender=self.request.user).order_by('-created_at')
        return Notice.objects.filter(recipient=self.request.user).order_by('-created_at')

    def perform_destroy(self, instance):
        if self.request.user != instance.sender:
            raise permissions.PermissionDenied('Only the sender can delete this notice.')
        instance.delete()


class DepartmentListCreateView(generics.ListCreateAPIView):
    queryset = Department.objects.all().order_by('name')
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class CourseListCreateView(generics.ListCreateAPIView):
    queryset = Course.objects.all().order_by('name')
    serializer_class = CourseSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdmin()]


class AttendanceSessionListCreateView(generics.ListCreateAPIView):
    serializer_class = AttendanceSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user, defaults={'role': 'employee'})
        if profile.role == 'admin':
            return AttendanceSession.objects.all().order_by('-created_at')
        if profile.role == 'manager':
            return AttendanceSession.objects.filter(faculty=self.request.user).order_by('-created_at')
        return AttendanceSession.objects.filter(active=True).order_by('-created_at')

    def perform_create(self, serializer):
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user, defaults={'role': 'employee'})
        if profile.role != 'manager':
            raise permissions.PermissionDenied('Only managers can create sessions')


class CloseAttendanceSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        session = AttendanceSession.objects.filter(pk=pk).first()
        if not session:
            return Response({'detail': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)
        profile, _ = UserProfile.objects.get_or_create(user=request.user, defaults={'role': 'employee'})
        if profile.role == 'employee':
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        if profile.role == 'manager' and session.faculty != request.user:
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        session.active = False
        session.save(update_fields=['active'])
        return Response({'detail': 'Session closed'})


class MarkAttendanceView(APIView):
    permission_classes = [IsAuthenticated, IsAttendanceUser]

    def post(self, request):
        token = (request.data.get('token') or '').strip()
        today = timezone.localtime(timezone.now()).date()
        active_record = AttendanceRecord.objects.filter(
            employee=request.user,
            check_in__date=today,
            check_out__isnull=True,
        ).order_by('-check_in').first()
        if active_record:
            return Response(
                {'detail': 'Already checked in. Please use the checkout button to end your current attendance.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if token:
            session = AttendanceSession.objects.filter(qr_code=token, active=True, expires_at__gt=timezone.now()).first()
            if session:
                active_session_record = AttendanceRecord.objects.filter(employee=request.user, session=session, check_out__isnull=True).order_by('-check_in').first()
                if active_session_record:
                    return Response(
                        {'detail': 'Already checked in for this session. Please use the checkout button to end your current attendance.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                record = AttendanceRecord.objects.create(employee=request.user, session=session, status='present')
                return Response({'detail': 'Attendance marked successfully', 'session': session.title, 'record': record.id})

            own_profile = UserProfile.objects.filter(user=request.user, qr_token=token).first()
            if not own_profile:
                return Response(
                    {'detail': 'Invalid QR token. Use a session QR or your own personal QR token.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        record = AttendanceRecord.objects.create(employee=request.user, status='present')
        return Response({'detail': 'Checked in successfully', 'record': record.id})


class CheckOutView(APIView):
    permission_classes = [IsAuthenticated, IsAttendanceUser]

    def post(self, request):
        record_id = request.data.get('record') or request.data.get('attendance_record')
        records = AttendanceRecord.objects.filter(employee=request.user, check_out__isnull=True)
        if record_id:
            records = records.filter(id=record_id)
        record = records.order_by('-check_in').first()
        if not record:
            return Response({'detail': 'No active check-in found'}, status=status.HTTP_400_BAD_REQUEST)
        record.check_out = timezone.now()
        record.save(update_fields=['check_out'])
        return Response({'detail': 'Checked out successfully', 'record': record.id, 'check_out': record.check_out})


class AttendanceHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def _apply_period(self, records, period):
        now = timezone.now()
        if period == 'daily':
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
            return records.filter(check_in__gte=start_time)
        if period == 'weekly':
            start_time = now - timedelta(days=7)
            return records.filter(check_in__gte=start_time)
        if period == 'monthly':
            start_time = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            return records.filter(check_in__gte=start_time)
        return records

    def _total_hours(self, records):
        total_seconds = 0
        for record in records:
            if not record.check_in:
                continue
            end_time = record.check_out or record.check_in
            if end_time and end_time >= record.check_in:
                total_seconds += (end_time - record.check_in).total_seconds()
        return round(total_seconds / 3600, 2)

    def _daily_aggregate(self, records):
        groups = defaultdict(list)
        for record in records:
            if not record.check_in:
                continue
            local_check_in = timezone.localtime(record.check_in)
            day_key = local_check_in.date()
            groups[(record.employee_id, day_key)].append(record)

        daily_rows = []
        for (employee_id, day), day_records in sorted(groups.items(), key=lambda item: (item[0][1], item[1]), reverse=True):
            day_records.sort(key=lambda r: r.check_in or datetime.min)
            first = day_records[0]
            last_check_out = max((r.check_out or r.check_in) for r in day_records)
            hours = self._total_hours(day_records)
            profile = getattr(first.employee, 'profile', None)
            daily_rows.append({
                'id': f'daily-{employee_id}-{day}',
                'employee': employee_id,
                'employee_name': profile.display_name if profile else first.employee.username,
                'session': None,
                'session_title': day.strftime('%Y-%m-%d'),
                'check_in': first.check_in,
                'check_out': last_check_out,
                'status': 'present',
                'days_present': 1,
                'hours': hours,
            })
        return daily_rows

    def _monthly_aggregate(self, records, profiles=None):
        groups = defaultdict(list)
        for record in records:
            if not record.check_in:
                continue
            local_check_in = timezone.localtime(record.check_in)
            month_key = local_check_in.strftime('%Y-%m')
            groups[(record.employee_id, month_key)].append(record)

        monthly_rows = []
        for (employee_id, month), month_records in sorted(groups.items(), key=lambda item: (item[0][1], item[0][0]), reverse=True):
            month_records.sort(key=lambda r: r.check_in or datetime.min)
            first = month_records[0]
            last_check_out = max((r.check_out or r.check_in) for r in month_records)
            hours = self._total_hours(month_records)
            profile = getattr(first.employee, 'profile', None)
            month_label = datetime.strptime(month, '%Y-%m').strftime('%B %Y')
            distinct_days = {timezone.localtime(r.check_in).date() for r in month_records}
            monthly_rows.append({
                'id': f'monthly-{employee_id}-{month}',
                'employee': employee_id,
                'employee_name': profile.display_name if profile else first.employee.username,
                'employee_identifier': profile.employee_id if profile else '',
                'employee_role': profile.role if profile else '',
                'session': None,
                'session_title': month_label,
                'check_in': first.check_in,
                'check_out': last_check_out,
                'status': 'present',
                'days_present': len(distinct_days),
                'hours': hours,
            })
        if profiles is not None:
            now = timezone.localtime(timezone.now())
            month_key = now.strftime('%Y-%m')
            month_label = now.strftime('%B %Y')
            existing_keys = set(groups.keys())
            for profile in profiles:
                key = (profile.user_id, month_key)
                if key in existing_keys:
                    continue
                monthly_rows.append({
                    'id': f'monthly-{profile.user_id}-{month_key}',
                    'employee': profile.user_id,
                    'employee_name': profile.display_name or profile.user.username,
                    'employee_identifier': profile.employee_id or '',
                    'employee_role': profile.role,
                    'session': None,
                    'session_title': month_label,
                    'check_in': None,
                    'check_out': None,
                    'status': 'absent',
                    'days_present': 0,
                    'hours': 0,
                })
            monthly_rows.sort(key=lambda row: (row['session_title'], row['employee_role'], row['employee_name']), reverse=True)
        return monthly_rows

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user, defaults={'role': 'employee'})
        period = request.query_params.get('period', 'all')
        status_filter = request.query_params.get('status', 'all')
        role_filter = request.query_params.get('role')

        if profile.role == 'employee':
            records = AttendanceRecord.objects.filter(employee=request.user)
            visible_profiles = UserProfile.objects.select_related('user').filter(user=request.user)
        elif profile.role == 'manager':
            records = employee_attendance_records()
            visible_profiles = employee_profiles()
        else:
            records = AttendanceRecord.objects.all()
            visible_profiles = UserProfile.objects.select_related('user').filter(role__in=['employee', 'manager']).order_by('role', 'employee_id', 'display_name')

        if role_filter in ['employee', 'manager'] and profile.role == 'admin':
            records = records.filter(employee__profile__role=role_filter)
            visible_profiles = visible_profiles.filter(role=role_filter)

        employee_id_param = request.query_params.get('employee')
        if employee_id_param:
            records = records.filter(employee__id=employee_id_param)
            visible_profiles = visible_profiles.filter(user_id=employee_id_param)

        records = self._apply_period(records, period)
        if status_filter in ['present', 'absent']:
            records = records.filter(status=status_filter)

        if period == 'daily':
            return Response(self._daily_aggregate(records))
        if period == 'monthly':
            monthly_profiles = visible_profiles if status_filter in ['all', 'absent'] else None
            return Response(self._monthly_aggregate(records, monthly_profiles))

        records = records.order_by('-check_in')
        return Response(AttendanceRecordSerializer(records, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_report_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user, defaults={'role': 'employee'})
    if profile.role not in ['admin', 'manager']:
        return Response({'detail': 'Only managers and admins can export reports'}, status=status.HTTP_403_FORBIDDEN)

    period = request.query_params.get('period', 'all')
    status_filter = request.query_params.get('status', 'all')

    def apply_period(records):
        now = timezone.now()
        if period == 'daily':
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
            return records.filter(check_in__gte=start_time)
        if period == 'weekly':
            start_time = now - timedelta(days=7)
            return records.filter(check_in__gte=start_time)
        if period == 'monthly':
            start_time = now - timedelta(days=30)
            return records.filter(check_in__gte=start_time)
        return records

    employees = employee_profiles()
    records = employee_attendance_records() if profile.role == 'manager' else AttendanceRecord.objects.all()
    period_records = apply_period(records)
    actual_records = period_records
    if status_filter in ['present', 'absent']:
        actual_records = period_records.filter(status=status_filter)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="attendance_report.csv"'
    writer = csv.writer(response)
    writer.writerow(['employee', 'session', 'check_in', 'check_out', 'status'])

    if status_filter != 'absent':
        for record in actual_records.order_by('-check_in'):
            writer.writerow([record.employee.username, record.session.title if record.session else '', record.check_in, record.check_out, record.status])

    if status_filter in ['all', 'absent']:
        present_employee_ids = set(period_records.filter(status='present').values_list('employee_id', flat=True))
        for employee_profile in employees:
            if employee_profile.user_id not in present_employee_ids:
                writer.writerow([employee_profile.user.username, '', '', '', 'absent'])

    return response
