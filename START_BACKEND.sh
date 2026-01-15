#!/bin/bash
# Script to start the Knowledge Base backend

cd "$(dirname "$0")"

# Activate virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# Install dependencies if needed
if [ ! -d "venv/lib/python3.13/site-packages/fastapi" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Initialize database
echo "Initializing database..."
cd backend
python3 -c "
import asyncio
from db.database import init_db
asyncio.run(init_db())
print('✓ Database ready')
"
cd ..

# Start backend on port 8001 (to avoid conflict with other project on 8000)
echo "Starting backend on http://localhost:8001"
echo "API docs: http://localhost:8001/docs"
cd backend
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
