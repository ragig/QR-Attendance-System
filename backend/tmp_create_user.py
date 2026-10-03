import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

django.setup()
from django.contrib.auth.models import User
from attendance.models import UserProfile

username = 'testuser'
email = 'testuser0001@gmail.com'
password = 'Testpass123'

if User.objects.filter(username=username).exists():
    print('User already exists')
else:
    u = User.objects.create_user(username=username, email=email, password=password)
    UserProfile.objects.create(user=u, role='employee', display_name='Test User', employee_id='E99')
    print('Created user', username)
