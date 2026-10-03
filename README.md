# QR Code Based Attendance System

This workspace contains a full-stack attendance application with:

- React frontend for login, registration, QR-based attendance, and dashboard views
- Django REST Framework backend with JWT authentication
- MySQL-ready configuration and SQLite fallback for local development

## Project structure

- `backend/` - Django backend project and attendance app
- `my-app/` - React frontend built with Vite

## Run the backend

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Run the frontend

```bash
cd my-app
npm install
npm run dev
```

## Connection details

- The frontend uses `axios` in `my-app/src/App.jsx` and sends requests to `/api`.
- Vite proxy in `my-app/vite.config.js` forwards `/api` requests to `http://127.0.0.1:8000`.
- The backend API is exposed at `http://127.0.0.1:8000/api/`.

## Notes

- For MySQL, set environment variables such as `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT`.
- If you need a custom backend host, set `VITE_API_URL` in the frontend environment.
