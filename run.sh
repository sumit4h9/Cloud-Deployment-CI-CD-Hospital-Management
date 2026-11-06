#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "  Doctor Appointment Scheduling Platform & API Launcher   "
echo "=========================================================="

echo -e "\n[1/3] Running automated API & concurrency tests..."
python3 -m pytest backend/tests -q
echo "All automated tests passed successfully."

echo -e "\n[2/3] Checking frontend build..."
if [ ! -f "frontend/dist/index.html" ]; then
    echo "Building production frontend bundle..."
    (cd frontend && npm install && npm run build)
fi
echo "Frontend bundle ready."

echo -e "\n[3/3] Starting Doctor Appointment API & Web Server..."
echo "----------------------------------------------------------"
echo "  * Web Application:     http://localhost:8000"
echo "  * Interactive API:     http://localhost:8000/docs"
echo "  * Health Check:        http://localhost:8000/health"
echo "  * Readiness Check:     http://localhost:8000/ready"
echo "----------------------------------------------------------"
echo "Press Ctrl+C to stop the server."

uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
