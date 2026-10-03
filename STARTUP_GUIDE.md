# Fresh Startup Guide - QR Attendance System

## Quick Start (Copy & Paste)

### Terminal 1: Start Backend
```bash
cd F:\QR Code\backend
python manage.py runserver 0.0.0.0:8000
```

### Terminal 2: Start Frontend  
```bash
cd F:\QR Code\my-app
npm run dev
```

**Then open:** http://localhost:5175

---

## Full Startup Checklist

### ✅ Before Starting

- [ ] Python 3.10+ installed: `python --version`
- [ ] Node.js 16+ installed: `node --version`
- [ ] npm installed: `npm --version`
- [ ] Ports 8000 and 5175 are free
- [ ] No other processes using these ports

### ✅ First Time Setup

**Backend:**
```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
```

**Frontend:**
```bash
cd my-app
npm install
```

### ✅ Daily Startup

**Terminal 1 - Backend (takes 5-10 seconds):**
```bash
cd F:\QR Code\backend
python manage.py runserver 0.0.0.0:8000
```

Expected output:
```
System check identified no issues
✓ Auto-checkout scheduler started successfully
Starting development server at http://0.0.0.0:8000/
```

**Terminal 2 - Frontend (takes 3-5 seconds):**
```bash
cd F:\QR Code\my-app
npm run dev
```

Expected output:
```
VITE v8.1.5  ready in XXX ms
➜  Local:   http://localhost:5175/
```

---

## Common Startup Issues & Fixes

### ❌ Issue: "Port already in use" (8000 or 5175)

**Cause:** Process still running from previous startup

**Solution:**
```powershell
# Kill process on port 8000
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | 
  Select-Object -ExpandProperty OwningProcess | 
  ForEach-Object { Stop-Process -Id $_ -Force }

# Kill process on port 5175
Get-NetTCPConnection -LocalPort 5175 -ErrorAction SilentlyContinue | 
  Select-Object -ExpandProperty OwningProcess | 
  ForEach-Object { Stop-Process -Id $_ -Force }

# Then start fresh
```

---

### ❌ Issue: "Module not found" / "pip install error"

**Cause:** Virtual environment not activated or dependencies not installed

**Solution:**
```bash
cd F:\QR Code\backend

# Activate virtual environment
.\.venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt

# Check if installed
pip list | findstr "Django"
```

---

### ❌ Issue: Backend shows "404 Not Found" on API calls

**Cause:** Incorrect `INSTALLED_APPS` configuration

**Solution:** Verify `backend/core/settings.py` has:
```python
INSTALLED_APPS = [
    ...
    'attendance.apps.AttendanceConfig',  # NOT just 'attendance'
    ...
]
```

Then restart backend.

---

### ❌ Issue: Frontend won't load / "Cannot reach backend"

**Cause:** Backend not running OR CORS not configured

**Solution:**
```bash
# 1. Verify backend is running
curl http://127.0.0.1:8000/api/auth/register/

# 2. Should return error response (not connection error)
# If no response, backend is not running - restart it

# 3. If browser shows "Cannot reach backend" after backend is running,
# refresh the page (Ctrl+Shift+R to clear cache)
```

---

### ❌ Issue: "ModuleNotFoundError: No module named 'APScheduler'"

**Cause:** Dependencies not installed after requirements.txt update

**Solution:**
```bash
cd F:\QR Code\backend
pip install APScheduler tzlocal
```

---

### ❌ Issue: Database errors / "No such table"

**Cause:** Migrations not applied

**Solution:**
```bash
cd F:\QR Code\backend
python manage.py migrate
python manage.py check
```

---

### ❌ Issue: "npm install" takes too long or hangs

**Cause:** npm cache issue

**Solution:**
```bash
cd F:\QR Code\my-app
npm cache clean --force
rm -r node_modules package-lock.json
npm install
```

---

## Verification Checklist After Startup

Run these commands to verify everything is working:

### Backend Health
```bash
# Test API endpoint (should return 401 error, not connection error)
curl -X POST http://127.0.0.1:8000/api/auth/register/

# Should respond with:
# {"detail":"Authentication required to register a new user."}
```

### Frontend Health
```bash
# Open in browser
http://localhost:5175

# Should show:
# - QR Attendance header
# - Login page
# - "QR Attendance System" heading
```

---

## Clean Fresh Start (Nuclear Option)

If everything fails, try this:

### Step 1: Kill all processes
```powershell
# Kill all Python processes
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force

# Kill all Node processes
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force

# Free ports
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | 
  Select-Object -ExpandProperty OwningProcess | 
  ForEach-Object { Stop-Process -Id $_ -Force }

Get-NetTCPConnection -LocalPort 5175 -ErrorAction SilentlyContinue | 
  Select-Object -ExpandProperty OwningProcess | 
  ForEach-Object { Stop-Process -Id $_ -Force }
```

### Step 2: Reset backend
```bash
cd F:\QR Code\backend

# Clean Python cache
rm -r __pycache__ .pytest_cache .venv

# Recreate venv
python -m venv .venv
.\.venv\Scripts\activate

# Reinstall all packages
pip install -r requirements.txt

# Check database
python manage.py migrate
python manage.py check
```

### Step 3: Reset frontend
```bash
cd F:\QR Code\my-app

# Clean npm cache
npm cache clean --force
rm -r node_modules package-lock.json

# Reinstall
npm install
```

### Step 4: Start fresh
```bash
# Terminal 1
cd F:\QR Code\backend
python manage.py runserver 0.0.0.0:8000

# Terminal 2
cd F:\QR Code\my-app
npm run dev
```

---

## Expected Startup Output

### Backend (Terminal 1)
```
INFO:apscheduler.scheduler:Adding job tentatively...
✓ Auto-checkout scheduler started successfully
System check identified no issues (0 silenced).
August 06, 2026 - XX:XX:XX
Django version 5.2.16
Starting development server at http://0.0.0.0:8000/
```

### Frontend (Terminal 2)
```
VITE v8.1.5  ready in 1280 ms

  ➜  Local:   http://localhost:5175/
  ➜  Network: http://192.168.1.101:5175/
```

---

## Startup Time Expectations

- **Backend:** 5-10 seconds to full startup
- **Frontend:** 3-5 seconds to full startup
- **Total:** 10-15 seconds from running both commands

If it takes longer, check terminal output for errors.

---

## Port Reference

| Service | Port | URL |
|---------|------|-----|
| Django Backend | 8000 | http://127.0.0.1:8000 |
| API Endpoints | 8000 | http://127.0.0.1:8000/api/ |
| Vite Frontend | 5175 | http://localhost:5175 |

---

## Logs Location

- **Backend logs:** Terminal output (stdout)
- **Frontend logs:** Terminal output (stdout) 
- **Browser console logs:** F12 → Console tab

---

## Quick Troubleshooting Command

```powershell
# All-in-one health check
echo "=== Checking Python ===" ; python --version
echo "=== Checking Node ===" ; node --version
echo "=== Checking npm ===" ; npm --version
echo "=== Checking port 8000 ===" ; Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
echo "=== Checking port 5175 ===" ; Get-NetTCPConnection -LocalPort 5175 -ErrorAction SilentlyContinue
```

---

## Support Files

- Configuration: `backend/core/settings.py`
- Dependencies: `backend/requirements.txt` and `my-app/package.json`
- Database: `backend/db.sqlite3`
- Frontend config: `my-app/vite.config.js`
