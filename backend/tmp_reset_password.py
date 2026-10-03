import os
import django
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

django.setup()
from django.contrib.auth.models import User

username = 'Ragi'
new_password = 'Testpass123'
try:
    user = User.objects.filter(username=username).first()
    if not user:
        print('User not found')
    else:
        user.set_password(new_password)
        user.save()
        print('Password reset for', username)
except Exception as e:
    print('ERROR', e)
