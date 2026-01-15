# Setup Instructions

## Backend Setup

1. **Create data directories** (if not already created):
```bash
mkdir -p data/uploads
```

2. **Setup virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Create .env file**:
```bash
cp .env.example .env
# Edit .env with your configuration if needed
```

5. **Start backend**:
```bash
uvicorn backend.main:app --reload
```

Backend will be available at: http://localhost:8000
API docs: http://localhost:8000/docs

## Frontend Setup

1. **Navigate to frontend directory**:
```bash
cd frontend
```

2. **Install dependencies**:
```bash
npm install
```

3. **Create .env file**:
```bash
cp .env.example .env
# Edit .env if you need to change API URL
```

4. **Start dev server**:
```bash
npm run dev
```

Frontend will be available at: http://localhost:5174

## Verify Integration

1. **Backend Health Check**: http://localhost:8000/health
2. **Backend API Docs**: http://localhost:8000/docs
3. **Frontend**: http://localhost:5174

### Test Steps:

1. **Upload a document**:
   - Go to http://localhost:5174/documents
   - Click "Choose File" and select a document
   - Click "Upload Document"
   - Verify document appears in the list

2. **View system health dashboard**:
   - Go to http://localhost:5174 (Dashboard)
   - Verify system metrics are displayed
   - Check active jobs and recent documents

3. **Create a job**:
   - Go to http://localhost:5174/jobs
   - Click "New Job"
   - Fill in job configuration
   - Click "Start Job"
   - View job details and monitor progress

4. **Search documents**:
   - Go to http://localhost:5174/search
   - Enter a search query
   - Verify results are displayed

## Troubleshooting

### Backend Issues:
- **Database errors**: Ensure `data/` directory exists and is writable
- **Import errors**: Make sure virtual environment is activated
- **Port already in use**: Change port with `--port 8001` flag

### Frontend Issues:
- **API connection errors**: Verify `VITE_API_URL` in `.env` matches backend URL
- **Build errors**: Run `npm install` again
- **CORS errors**: Check backend CORS settings in `backend/core/config.py`

## Environment Variables

### Backend (.env):
- `DATABASE_URL`: SQLite database path (default: `sqlite+aiosqlite:///./data/kb.db`)
- `S3_BUCKET_NAME`: AWS S3 bucket (optional, uses local storage if not set)
- `FRONTEND_URL`: Frontend URL for CORS (default: `http://localhost:5174`)
- `MAX_UPLOAD_SIZE`: Maximum file upload size in bytes (default: 10485760 = 10MB)

### Frontend (.env):
- `VITE_API_URL`: Backend API URL (default: `http://localhost:8000/api/v1`)
