# Agentic Search Operations - Knowledge Base System

Production-grade Knowledge Base system with agentic workflows and operator control interface.

## 🚀 Features

- **FastAPI Backend**: Async SQLAlchemy, S3 storage abstraction, comprehensive API
- **React + TypeScript Frontend**: Operator console with real-time monitoring
- **Claude API Integration**: Three production agents (summarization, deep search, refresh)
- **Security**: Input validation, rate limiting, CORS, no code execution
- **State Management**: Checkpointing, pause/resume, error recovery
- **Cost Controls**: Token tracking, cost limits, time limits

## 📁 Project Structure

```
backend/          # FastAPI backend
├── api/         # API endpoints
├── core/        # Config, security, storage
├── models/      # Database models
├── services/    # Business logic (ingest, search, agent)
└── db/          # Database setup

frontend/        # React + TypeScript frontend
├── src/
│   ├── components/  # UI components
│   ├── pages/       # Page components
│   ├── api/         # API client
│   ├── hooks/       # React Query hooks
│   └── utils/       # Utilities
```

## 🛠️ Setup

### Backend

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Start backend
cd backend
uvicorn main:app --reload --port 8001
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
cp .env.example .env
# VITE_API_URL should point to backend (default: http://localhost:8001/api/v1)

# Start dev server
npm run dev
```

## 🔑 Environment Variables

### Backend (.env)
```bash
DATABASE_URL=sqlite+aiosqlite:///../data/kb.db
ANTHROPIC_API_KEY=sk-ant-your-key-here
MAX_JOB_COST_USD=5.0
MAX_JOB_RUNTIME_MINUTES=120
FRONTEND_URL=http://localhost:5174
```

### Frontend (.env)
```bash
VITE_API_URL=http://localhost:8001/api/v1
```

## 📚 API Documentation

Once backend is running, visit:
- **API Docs**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/health

## 🧪 Testing

See `TEST_CHECKLIST.md` for comprehensive testing guide.

## 🔒 Security

- All user input validated and sanitized
- No dynamic code execution
- Parameterized database queries only
- Rate limiting on all endpoints
- CORS restricted to specific origins
- Operator Chat uses command allowlist

## 📝 License

MIT
