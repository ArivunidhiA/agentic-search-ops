# Backend Fix - Port Conflict Resolved ✅

## Issue
- Another backend was running on port 8000
- Our backend wasn't running
- Frontend couldn't connect to `/api/v1/metrics`

## Solution Applied

### 1. Changed Backend Port
- **Old**: Port 8000 (conflict with other project)
- **New**: Port 8001 ✅

### 2. Updated Frontend Configuration
- Updated `frontend/.env`: `VITE_API_URL=http://localhost:8001/api/v1`
- Frontend now points to correct backend

### 3. Installed Missing Dependencies
- Installed `greenlet` (required for SQLAlchemy async)
- All dependencies from `requirements.txt` installed

### 4. Initialized Database
- Created database tables
- Database ready at `./data/kb.db`

### 5. Started Backend
- Backend running on **http://localhost:8001**
- API docs: **http://localhost:8001/docs**

## Current Status

✅ **Backend**: http://localhost:8001 (running)
✅ **Frontend**: http://localhost:5174 (running)
✅ **Database**: Initialized
✅ **Metrics Endpoint**: Working

## How to Start Backend

### Option 1: Use the startup script
```bash
./START_BACKEND.sh
```

### Option 2: Manual start
```bash
# Activate venv
source venv/bin/activate

# Initialize database (first time only)
cd backend
python3 -c "import asyncio; from db.database import init_db; asyncio.run(init_db())"
cd ..

# Start server
cd backend
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

## Access Points

- **Frontend**: http://localhost:5174
- **Backend API**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/health
- **Metrics**: http://localhost:8001/api/v1/metrics

## Next Steps

1. ✅ Backend is running on port 8001
2. ✅ Frontend is configured to use port 8001
3. ✅ Refresh your browser at http://localhost:5174
4. ✅ Dashboard should now load metrics successfully

The "Failed to load system health metrics" error should be resolved!
