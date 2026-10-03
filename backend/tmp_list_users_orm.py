import os
import django
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

django.setup()
from django.contrib.auth.models import User
from attendance.models import UserProfile

for u in User.objects.all():
    profile = getattr(u, 'profile', None)
    print(u.id, u.username, u.email, profile.employee_id if profile else None, profile.qr_token if profile else None)
