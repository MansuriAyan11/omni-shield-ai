# 🚀 OmniShield - Quick Start Guide

## Option 1: Automatic Setup (Recommended)

Run the complete setup script that handles everything:

```powershell
.\setup_and_start.ps1
```

This will:
1. ✅ Migrate frontend from Next.js to React
2. ✅ Install all Python dependencies
3. ✅ Install all Node.js dependencies
4. ✅ Setup database tables
5. ✅ Create environment files
6. ✅ Start both servers

---

## Option 2: Manual Setup

### Step 1: Migrate Frontend

```powershell
.\migrate_frontend.ps1
```

This replaces the Next.js frontend with the new React + Vite frontend.

### Step 2: Backend Setup

```powershell
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup database
python create_tables.py

# Create .env file
cp ..\.env.example .env
```

### Step 3: Frontend Setup

```powershell
cd frontend

# Install dependencies
npm install

# Create .env file
cp .env.example .env
```

### Step 4: Start Servers

```powershell
# From project root
.\start_servers.ps1
```

---

## Option 3: Start Servers Manually

### Terminal 1 - Backend:
```powershell
cd backend
.\venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2 - Frontend:
```powershell
cd frontend
npm run dev
```

---

## Access the Application

After starting both servers:

- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## Default Credentials

Create an account by visiting: http://localhost:3000/register

---

## Troubleshooting

### Port already in use?

**Backend (8000):**
```powershell
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Frontend (3000):**
```powershell
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

### Python virtual environment issues?

```powershell
cd backend
Remove-Item -Recurse -Force venv
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Node modules issues?

```powershell
cd frontend
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm install
```

### Database issues?

```powershell
cd backend
Remove-Item moderation.db  # Deletes SQLite database
python create_tables.py     # Recreates tables
```

---

## What Changed?

### ✅ Frontend Migration
- **Old**: Next.js with dark blue theme
- **New**: React + Vite with pure black & white theme

### ✅ Tech Stack
- React 18 + TypeScript
- React Router v6
- Axios with JWT
- TanStack Query
- Recharts
- Tailwind CSS
- Lucide Icons

### ✅ Features
- Black & white minimalist UI
- Fast Vite dev server
- JWT authentication
- Image moderation
- Analytics dashboard
- API key management

---

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `setup_and_start.ps1` | Complete automated setup |
| `migrate_frontend.ps1` | Replace Next.js with React |
| `start_servers.ps1` | Start both servers |

---

## Next Steps

1. Visit http://localhost:3000
2. Create an account
3. Upload an image to test moderation
4. Generate API keys
5. View analytics

---

## Support

For issues or questions, check:
- Backend logs in the backend terminal
- Frontend logs in the frontend terminal
- Browser console (F12)

Happy moderating! 🛡️
