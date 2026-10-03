import json
import urllib.request
import urllib.error

url = 'http://127.0.0.1:8000/api/auth/login/'
payload = {'employee_id': 'AA', 'password': 'Testpass123'}
req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        print('STATUS', resp.status)
        print(resp.read().decode())
except urllib.error.HTTPError as e:
    print('HTTPERROR', e.code)
    try:
        print(e.read().decode())
    except Exception:
        pass
except Exception as e:
    print('ERROR', e)
