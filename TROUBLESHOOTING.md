# QR Attendance - Troubleshooting & Common Issues

## Issue: Ports Already in Use (8000 or 5175)

### Symptoms
- "Address already in use" error
- "Port 8000 is already in use" 
- "Port 5175 is already in use"

### Quick Fix
```powershell
# Kill process on port 8000
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | 
  Select-Object -ExpandProperty OwningProcess | 
  ForEach-Object { Stop-Process -Id $_ -Force }

# Kill process on port 5175
Get-NetTCPConnection -LocalPort 5175 -ErrorAction SilentlyContinue | 
  Select-Object -ExpandProperty OwningProcess | 
  ForEach-Object { Stop-Process -Id $_ -Force }
```

### Verify
```powershell
netstat -ano | findstr ":8000"
netstat -ano | findstr ":5175"
```

---

## Issue: "No module named 'django'" or "ModuleNotFoundError"

### Symptoms
- Backend won't start
- "ModuleNotFoundError: No module named 'django'"
- "No module named 'rest_framework'"

### Cause
- Virtual environment not activated
- Dependencies not installed

### Fix
```bash
cd F:\QR Code\backend

# Activate venv
.\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify
pip list | findstr "Django"
```

---

## Issue: Backend Returns 404 for All API Endpoints

### Symptoms
- All API calls return "404 Not Found"
- Dashboard won't load
- Login doesn't work

### Cause
- Incorrect `INSTALLED_APPS` in settings.py
- App not registered correctly

### Fix
**Edit `backend/core/settings.py`:**
```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'attendance.apps.AttendanceConfig',  # ← MUST use full path
]
```

Then restart backend.

---

## Issue: Frontend Shows "Cannot reach backend"

### Symptoms
- Frontend loads
- Login page appears
- But error says "Cannot reach the backend API"
- "Cannot reach the backend API. Start Django on port 8000, then try again."

### Cause
1. Backend is not running
2. Backend is on different port
3. Browser has old cache
4. CORS issue

### Fix

**Step 1: Verify backend is running**
```powershell
curl http://127.0.0.1:8000/api/auth/register/
```

Should return: `{"detail":"Authentication required..."}`

If connection timeout → **Backend is not running**

**Step 2: Hard refresh browser**
- Windows: Ctrl + Shift + R
- Mac: Cmd + Shift + R

**Step 3: Check backend console**
- Should see requests coming in
- If nothing, frontend can't reach backend

**Step 4: Verify proxy config**
- Edit `my-app/vite.config.js`
- Ensure proxy points to correct backend:
```javascript
proxy: {
  '/api': {
    target: 'http://127.0.0.1:8000',  // ← Check this is correct
    changeOrigin: true,
    secure: false,
  },
},
```

---

## Issue: Database Errors / "No such table: attendance_*"

### Symptoms
- Backend starts but crashes when accessing data
- "no such table: attendance_attendancerecord"
- "OperationalError: no such table"

### Cause
- Database migrations not applied

### Fix
```bash
cd F:\QR Code\backend

# Apply migrations
python manage.py migrate

# Verify
python manage.py check
```

---

## Issue: npm install Fails or Hangs

### Symptoms
- "npm ERR!" messages
- Installation never completes
- Hangs at "Building native modules"

### Quick Fix
```bash
cd F:\QR Code\my-app

# Clear cache
npm cache clean --force

# Remove old files
rmdir /s node_modules
del package-lock.json

# Reinstall
npm install
```

---

## Issue: Frontend Won't Start / Vite Error

### Symptoms
- "error when starting dev server"
- "Port 5175 is already in use"
- Vite crashes

### Fix
```bash
# Kill lingering processes
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force

# Try again
cd F:\QR Code\my-app
npm run dev
```

---

## Issue: "APScheduler" or "tzlocal" Not Found

### Symptoms
- Backend crashes on startup
- "ModuleNotFoundError: No module named 'apscheduler'"
- "No module named 'tzlocal'"

### Cause
- Auto-checkout feature dependencies not installed
- requirements.txt not updated

### Fix
```bash
cd F:\QR Code\backend
.\.venv\Scripts\activate
pip install APScheduler tzlocal
```

---

## Issue: White Screen / Nothing Loads on Frontend

### Symptoms
- Browser shows blank white page
- No error messages
- DOM is empty

### Cause
- JavaScript error in console
- Frontend build failed
- Connection issue

### Fix

**Step 1: Check browser console**
- Press F12 → Console tab
- Look for red errors
- Note the error message

**Step 2: Check terminal output**
- Frontend terminal should show errors
- If nothing, check if `npm run dev` is actually running

**Step 3: Hard refresh**
- Ctrl + Shift + R
- Clear cache

**Step 4: Rebuild frontend**
```bash
cd F:\QR Code\my-app
npm run build
npm run dev
```

---

## Issue: Backend/Frontend Not Starting - Permission Denied

### Symptoms
- "Permission denied" error
- Can't activate virtual environment
- Can't run Python

### Cause
- PowerShell execution policy issue
- File permission issue

### Fix
```powershell
# Set execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Try again
cd F:\QR Code\backend
.\.venv\Scripts\activate
python manage.py runserver 0.0.0.0:8000
```

---

## Issue: "Cannot find Python" / "python: command not found"

### Symptoms
- "python: command not found"
- "The term 'python' is not recognized"
- Python installed but not in PATH

### Cause
- Python not in system PATH
- Python installed for current user only

### Fix

**Option 1: Reinstall Python (recommended)**
- Download from https://www.python.org/
- **IMPORTANT:** Check "Add Python to PATH" during installation
- Restart terminal/computer

**Option 2: Use full path**
```bash
"C:\Users\YourUsername\AppData\Local\Programs\Python\Python314\python.exe" manage.py runserver
```

**Option 3: Check if Python is installed**
```powershell
# List installed Python versions
dir "C:\Users\$env:USERNAME\AppData\Local\Programs\Python"

# Or check system-wide
Get-Command python
```

---

## Issue: Scheduler Not Starting (Auto-Checkout)

### Symptoms
- Backend starts fine
- But "Auto-checkout scheduler started successfully" message doesn't appear
- Auto-checkout doesn't work

### Cause
- APScheduler not installed
- Scheduler already running (from previous startup)
- Duplicate scheduler instances

### Fix

**Step 1: Kill all Python processes**
```powershell
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
```

**Step 2: Ensure APScheduler is installed**
```bash
cd F:\QR Code\backend
.\.venv\Scripts\activate
pip install APScheduler tzlocal
```

**Step 3: Restart backend**
```bash
python manage.py runserver 0.0.0.0:8000
```

Should see:
```
✓ Auto-checkout scheduler started successfully
```

---

## Complete System Restart (Nuclear Option)

Use this when all else fails:

```powershell
# 1. Kill all processes
Write-Host "Killing all processes..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force

# 2. Free ports
Write-Host "Freeing ports..." -ForegroundColor Yellow
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | 
  Select-Object -ExpandProperty OwningProcess | 
  ForEach-Object { Stop-Process -Id $_ -Force }

Get-NetTCPConnection -LocalPort 5175 -ErrorAction SilentlyContinue | 
  Select-Object -ExpandProperty OwningProcess | 
  ForEach-Object { Stop-Process -Id $_ -Force }

# 3. Reset backend
Write-Host "Resetting backend..." -ForegroundColor Yellow
cd "F:\QR Code\backend"
Remove-Item -Recurse -Force __pycache__, .pytest_cache -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force .venv
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py check

# 4. Reset frontend
Write-Host "Resetting frontend..." -ForegroundColor Yellow
cd "F:\QR Code\my-app"
npm cache clean --force
Remove-Item -Recurse -Force node_modules -ErrorAction SilentlyContinue
Remove-Item -Force package-lock.json -ErrorAction SilentlyContinue
npm install

# 5. Restart
Write-Host "Starting fresh..." -ForegroundColor Green
cd "F:\QR Code\backend"
python manage.py runserver 0.0.0.0:8000
```

---

## Getting Help

**If you still have issues:**

1. **Check the browser console** (F12 → Console)
2. **Check both terminal outputs** (backend and frontend)
3. **Try a clean restart** using scripts above
4. **Check firewalls** - ports 8000 and 5175 might be blocked
5. **Try different ports** if 8000/5175 are problematic:
   - Backend: `python manage.py runserver 0.0.0.0:9000`
   - Frontend: `npm run dev -- --port 5176`

---

## Health Check Command

Run this to diagnose everything:

```powershell
Write-Host "=== QR Attendance System Health Check ===" -ForegroundColor Cyan
Write-Host ""

# Python
try { 
  $pv = python --version 2>&1
  Write-Host "✓ Python: $pv" -ForegroundColor Green 
} catch { 
  Write-Host "✗ Python: NOT FOUND" -ForegroundColor Red 
}

# Node
try { 
  $nv = node --version 2>&1
  Write-Host "✓ Node: $nv" -ForegroundColor Green 
} catch { 
  Write-Host "✗ Node: NOT FOUND" -ForegroundColor Red 
}

# npm
try { 
  $nmv = npm --version 2>&1
  Write-Host "✓ npm: $nmv" -ForegroundColor Green 
} catch { 
  Write-Host "✗ npm: NOT FOUND" -ForegroundColor Red 
}

# Ports
$p8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
$p5175 = Get-NetTCPConnection -LocalPort 5175 -ErrorAction SilentlyContinue

if ($p8000) { 
  Write-Host "✓ Port 8000: IN USE" -ForegroundColor Green 
} else { 
  Write-Host "✗ Port 8000: FREE" -ForegroundColor Yellow 
}

if ($p5175) { 
  Write-Host "✓ Port 5175: IN USE" -ForegroundColor Green 
} else { 
  Write-Host "✗ Port 5175: FREE" -ForegroundColor Yellow 
}

# Directories
if (Test-Path "F:\QR Code\backend") { 
  Write-Host "✓ Backend directory: EXISTS" -ForegroundColor Green 
} else { 
  Write-Host "✗ Backend directory: NOT FOUND" -ForegroundColor Red 
}

if (Test-Path "F:\QR Code\my-app") { 
  Write-Host "✓ Frontend directory: EXISTS" -ForegroundColor Green 
} else { 
  Write-Host "✗ Frontend directory: NOT FOUND" -ForegroundColor Red 
}

Write-Host ""
Write-Host "=== End Health Check ===" -ForegroundColor Cyan
```
