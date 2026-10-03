from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from .models import AttendanceRecord, AttendanceSession, Course, Department, UserProfile


class AttendanceApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_admin_can_register_employee_and_employee_can_login(self):
        admin_user = User.objects.create_user(username='admin1', email='admin1@gmail.com', password='adminpass123')
        UserProfile.objects.create(user=admin_user, role='admin', display_name='Admin One', employee_id='ADM001')

        self.client.force_authenticate(user=admin_user)
        response = self.client.post('/api/auth/register/', {
            'username': 'employee1',
            'email': 'employee1@gmail.com',
            'password': 'testpass123',
            'role': 'employee',
            'display_name': 'Employee One',
            'employee_id': 'EMP001',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(UserProfile.objects.filter(user__username='employee1').exists())

        self.client.force_authenticate(user=None)
        login_response = self.client.post('/api/auth/login/', {
            'employee_id': 'EMP001',
            'password': 'testpass123',
        }, format='json')
        self.assertEqual(login_response.status_code, 200)
        self.assertIn('access', login_response.data)

    def test_register_requires_admin_after_first_user(self):
        User.objects.create_user(username='existing', email='existing@gmail.com', password='pass1234')
        self.client.force_authenticate(user=None)
        response = self.client.post('/api/auth/register/', {
            'username': 'employee2',
            'email': 'employee2@gmail.com',
            'password': 'testpass123',
            'role': 'employee',
            'display_name': 'Employee Two',
            'employee_id': 'EMP002',
        }, format='json')
        self.assertEqual(response.status_code, 401)

    def test_first_user_is_created_as_admin(self):
        response = self.client.post('/api/auth/register/', {
            'username': 'employee3',
            'email': 'employee3@gmail.com',
            'password': 'testpass123',
            'role': 'employee',
            'display_name': 'Employee Three',
            'employee_id': 'EMP003',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['role'], 'admin')
        self.assertEqual(UserProfile.objects.get(user__username='employee3').role, 'admin')

    def test_register_rejects_invalid_or_duplicate_gmail_and_employee_id(self):
        User.objects.create_user(username='existing', email='taken@gmail.com', password='pass1234')
        existing_employee = User.objects.create_user(username='existingid', email='existingid@gmail.com', password='pass1234')
        UserProfile.objects.create(user=existing_employee, role='employee', employee_id='E8')

        valid_response = self.client.post('/api/auth/register/', {
            'username': 'validgmail',
            'email': 'ppp11@gmail.com',
            'password': 'testpass123',
            'role': 'employee',
            'display_name': 'Valid Gmail',
            'employee_id': 'E7',
        }, format='json')
        self.assertEqual(valid_response.status_code, 201)

        uppercase_response = self.client.post('/api/auth/register/', {
            'username': 'uppercase',
            'email': 'Capital@gmail.com',
            'password': 'testpass123',
            'role': 'employee',
            'display_name': 'Upper Case',
            'employee_id': 'E9',
        }, format='json')
        self.assertEqual(uppercase_response.status_code, 400)

        duplicate_email_response = self.client.post('/api/auth/register/', {
            'username': 'duplicateemail',
            'email': 'TAKEN@gmail.com',
            'password': 'testpass123',
            'role': 'employee',
            'display_name': 'Duplicate Email',
            'employee_id': 'E10',
        }, format='json')
        self.assertEqual(duplicate_email_response.status_code, 400)

        duplicate_employee_response = self.client.post('/api/auth/register/', {
            'username': 'duplicateemployee',
            'email': 'duplicateemployee@gmail.com',
            'password': 'testpass123',
            'role': 'employee',
            'display_name': 'Duplicate Employee',
            'employee_id': 'e8',
        }, format='json')
        self.assertEqual(duplicate_employee_response.status_code, 400)

    def test_manager_can_create_session(self):
        manager_user = User.objects.create_user(username='manager1', password='pass1234')
        UserProfile.objects.create(user=manager_user, role='manager')
        department = Department.objects.create(name='Computer Science')
        course = Course.objects.create(name='Algorithms', department=department)

        self.client.force_authenticate(user=manager_user)
        response = self.client.post('/api/sessions/', {
            'title': 'Lecture 1',
            'course': course.id,
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(AttendanceSession.objects.filter(title='Lecture 1').exists())

    def test_generated_qr_code_is_unique(self):
        manager_user = User.objects.create_user(username='manager2', password='pass1234')
        UserProfile.objects.create(user=manager_user, role='manager')
        department = Department.objects.create(name='Mathematics')
        course = Course.objects.create(name='Calculus', department=department)

        self.client.force_authenticate(user=manager_user)
        first = self.client.post('/api/sessions/', {'title': 'Lecture A', 'course': course.id}, format='json')
        second = self.client.post('/api/sessions/', {'title': 'Lecture B', 'course': course.id}, format='json')

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertNotEqual(first.json()['qr_code_value'], second.json()['qr_code_value'])

    def test_employee_can_mark_attendance_with_personal_qr_token(self):
        employee_user = User.objects.create_user(username='employee2', password='pass1234')
        profile = UserProfile.objects.create(user=employee_user, role='employee', employee_id='EMP002')

        self.client.force_authenticate(user=employee_user)
        response = self.client.post('/api/attendance/mark/', {'token': profile.qr_token}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['detail'], 'Checked in successfully')
        self.assertTrue(AttendanceRecord.objects.filter(employee=employee_user, session__isnull=True).exists())

    def test_employee_can_check_in_again_after_checkout_same_day(self):
        employee_user = User.objects.create_user(username='employee_once', password='pass1234')
        profile = UserProfile.objects.create(user=employee_user, role='employee', employee_id='EMP004')

        self.client.force_authenticate(user=employee_user)
        first = self.client.post('/api/attendance/mark/', {'token': profile.qr_token}, format='json')
        self.assertEqual(first.status_code, 200)

        checkout = self.client.post('/api/attendance/checkout/', {'record': first.data['record']}, format='json')
        self.assertEqual(checkout.status_code, 200)

        second = self.client.post('/api/attendance/mark/', {'token': profile.qr_token}, format='json')
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.data['detail'], 'Checked in successfully')
        self.assertEqual(AttendanceRecord.objects.filter(employee=employee_user, session__isnull=True).count(), 2)

    def test_checkout_selected_attendance_record_only(self):
        employee_user = User.objects.create_user(username='employee-checkout', password='pass1234')
        UserProfile.objects.create(user=employee_user, role='employee', employee_id='EMP-CHECK')
        first_record = AttendanceRecord.objects.create(employee=employee_user, status='present')
        second_record = AttendanceRecord.objects.create(employee=employee_user, status='present')

        self.client.force_authenticate(user=employee_user)
        response = self.client.post('/api/attendance/checkout/', {'record': first_record.id}, format='json')

        self.assertEqual(response.status_code, 200)
        first_record.refresh_from_db()
        second_record.refresh_from_db()
        self.assertIsNotNone(first_record.check_out)
        self.assertIsNone(second_record.check_out)

    def test_manager_can_mark_own_attendance_with_personal_qr_token(self):
        manager_user = User.objects.create_user(username='manager3', password='pass1234')
        profile = UserProfile.objects.create(user=manager_user, role='manager', employee_id='MGR003')

        self.client.force_authenticate(user=manager_user)
        response = self.client.post('/api/attendance/mark/', {'token': profile.qr_token}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['detail'], 'Checked in successfully')
        self.assertTrue(AttendanceRecord.objects.filter(employee=manager_user, session__isnull=True).exists())

    def test_manager_can_view_employee_attendance_report(self):
        manager_user = User.objects.create_user(username='manager4', password='pass1234')
        UserProfile.objects.create(user=manager_user, role='manager', employee_id='MGR004')
        employee_user = User.objects.create_user(username='employee3', password='pass1234')
        UserProfile.objects.create(user=employee_user, role='employee', employee_id='EMP003')
        AttendanceRecord.objects.create(employee=employee_user, status='present')

        self.client.force_authenticate(user=manager_user)
        response = self.client.get('/api/attendance/history/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['employee_name'], 'employee3')
