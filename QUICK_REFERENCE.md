# QR Attendance System - Quick Reference

## 🚀 Quick Start (2 Minutes)

### Windows Batch (Easiest)
Double-click one of these files:
- **`start-all.bat`** - Starts both backend & frontend (recommended)
- `start-backend.bat` - Start backend only
- `start-frontend.bat` - Start frontend only

### Windows PowerShell
```powershell
.\start-all.ps1
```

### Manual (Terminal Commands)

**Terminal 1 - Backend:**
```bash
cd F:\QR Code\backend
.\.venv\Scripts\activate
python manage.py runserver 0.0.0.0:8000
```

**Terminal 2 - Frontend:**
```bash
cd F:\QR Code\my-app
npm run dev
```

**Then open:** http://localhost:5175

---

## 📋 First Time Setup

### Backend Setup (One time)
```bash
cd F:\QR Code\backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
```

### Frontend Setup (One time)
```bash
cd F:\QR Code\my-app
npm install
```

---

## 🔗 URLs

| What | URL |
|------|-----|
| Frontend | http://localhost:5175 |
| Backend API | http://127.0.0.1:8000/api/ |
| Django Admin | http://127.0.0.1:8000/admin/ |

---

## ⚡ Expected Startup Output

### Backend
```
System check identified no issues (0 silenced)
✓ Auto-checkout scheduler started successfully
Starting development server at http://0.0.0.0:8000/
```

### Frontend
```
VITE v8.1.5  ready in 1280 ms
➜  Local:   http://localhost:5175/
```

---

## ✅ Verify It Works

### Quick Test
1. Open http://localhost:5175 in browser
2. Should see login page
3. Click "Login" button
4. Should see form

### API Test
```bash
# Should return error (not connection error)
curl -X POST http://127.0.0.1:8000/api/auth/register/
```

---

## 🛑 Common Issues

| Problem | Solution |
|---------|----------|
| **Port already in use** | Kill process: `Get-Process python \| Stop-Process -Force` |
| **Module not found** | Run: `pip install -r requirements.txt` |
| **Cannot reach backend** | Check backend is running on 8000 |
| **White screen** | Press F12 → Console tab → check errors |
| **npm install hangs** | Run: `npm cache clean --force` |

---

## 📁 Project Structure

```
F:\QR Code\
├── backend/                          # Django REST API
│   ├── .venv/                       # Virtual environment (auto-created)
│   ├── attendance/                   # Main app
│   ├── core/                         # Django config
│   ├── db.sqlite3                    # Database
│   ├── manage.py                     # Django CLI
│   └── requirements.txt              # Python packages
│
├── my-app/                           # React/Vite frontend
│   ├── node_modules/                # npm packages
│   ├── src/                          # Source code
│   ├── package.json                  # npm config
│   └── vite.config.js                # Vite config
│
├── start-all.bat                     # ← Click to start everything
├── start-backend.bat                 # Start backend only
├── start-frontend.bat                # Start frontend only
│
├── STARTUP_GUIDE.md                  # Detailed startup guide
├── TROUBLESHOOTING.md                # Troubleshooting guide
├── AUTO_CHECKOUT_IMPLEMENTATION.md   # Auto-checkout feature docs
└── README.md                         # Project overview
```

---

## 🔐 Demo Account

After first login (creates admin):
- **Username/Email:** Any valid email
- **Password:** Any password you set

---

## 🎯 Key Features

✅ QR code-based attendance  
✅ Employee/Manager/Admin roles  
✅ Automatic end-of-day checkout  
✅ Attendance history & reports  
✅ Employee directory  
✅ Notice system  

---

## 📞 Support

**Check these files for help:**
1. `STARTUP_GUIDE.md` - Detailed startup instructions
2. `TROUBLESHOOTING.md` - Common issues & fixes
3. Browser Console (F12) - Frontend errors
4. Terminal Output - Backend errors

**Browser Console Issues:**
- Press F12
- Click "Console" tab
- Look for red error messages
- Screenshot the error

**Terminal Issues:**
- Take screenshot of red error text
- Note what command was running
- Check if Python/Node are installed

---

## 🔧 Maintenance

### Daily
- Just run: `start-all.bat` or `.\start-all.ps1`

### Weekly
- Run: `npm audit` (frontend security)
- Run: `pip audit` (backend security)

### Monthly
- Backup database: `db.sqlite3`
- Clean cache: `npm cache clean --force`

---

## 💡 Tips

**Pro Tips:**
1. Keep both terminal windows open while using app
2. Frontend auto-refreshes on file save
3. Backend auto-reloads on Python file change
4. Use Ctrl+C to stop (works in both terminals)
5. Close terminals to stop servers

**Keyboard Shortcuts:**
- Browser: F12 = Developer Console
- Windows: Ctrl+Shift+R = Hard refresh
- Terminal: Ctrl+C = Stop server
- Terminal: Ctrl+L = Clear screen

---

## 📊 Performance Tips

If app feels slow:

1. **Clear browser cache:**
   - Open DevTools (F12)
   - Right-click refresh button
   - Click "Empty cache and hard refresh"

2. **Restart services:**
   - Close both terminals (Ctrl+C)
   - Wait 5 seconds
   - Start again with `start-all.bat`

3. **Check resources:**
   - Is Python using too much CPU?
   - Is Node process running?
   - Check available disk space

---

## ⚠️ Important Files (Don't Delete!)

| File | Purpose |
|------|---------|
| `db.sqlite3` | **DATABASE** - All attendance data |
| `.venv/` | **Virtual environment** - Python packages |
| `node_modules/` | **Packages** - JavaScript libraries |
| `requirements.txt` | **Dependencies** - Python packages list |
| `package.json` | **Config** - Frontend packages list |

**Always backup `db.sqlite3` before updates!**

---

## 🆘 Emergency Restart

If everything breaks:

```powershell
# Kill all processes
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force

# Free ports
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | 
  Select-Object -ExpandProperty OwningProcess | 
  ForEach-Object { Stop-Process -Id $_ -Force }

Get-NetTCPConnection -LocalPort 5175 -ErrorAction SilentlyContinue | 
  Select-Object -ExpandProperty OwningProcess | 
  ForEach-Object { Stop-Process -Id $_ -Force }

# Start fresh
start-all.bat
```

---

**Last Updated:** August 6, 2026  
**Status:** ✅ Working & Tested
