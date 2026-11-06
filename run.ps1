# Doctor Appointment Scheduling Platform - Launcher Script
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Doctor Appointment Scheduling Platform & API Launcher   " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Run Automated Test Suite
Write-Host "`n[1/3] Running automated API & concurrency tests..." -ForegroundColor Yellow
python -m pytest backend/tests -q
if ($LASTEXITCODE -ne 0) {
    Write-Host "Tests failed! Aborting startup." -ForegroundColor Red
    exit 1
}
Write-Host "All automated tests passed successfully." -ForegroundColor Green

# 2. Check Frontend Build
Write-Host "`n[2/3] Checking frontend build..." -ForegroundColor Yellow
if (-not (Test-Path "frontend/dist/index.html")) {
    Write-Host "Building production frontend bundle..." -ForegroundColor Cyan
    Push-Location frontend
    npm run build
    Pop-Location
}
Write-Host "Frontend bundle ready." -ForegroundColor Green

# 3. Launching Service
Write-Host "`n[3/3] Starting Doctor Appointment API & Web Server..." -ForegroundColor Yellow
Write-Host "----------------------------------------------------------" -ForegroundColor DarkGray
Write-Host "  * Web Application:     http://localhost:8000" -ForegroundColor White
Write-Host "  * Interactive API:     http://localhost:8000/docs" -ForegroundColor White
Write-Host "  * Health Check:        http://localhost:8000/health" -ForegroundColor White
Write-Host "  * Readiness Check:     http://localhost:8000/ready" -ForegroundColor White
Write-Host "----------------------------------------------------------" -ForegroundColor DarkGray
Write-Host "Press Ctrl+C to stop the server.`n" -ForegroundColor DarkGray

uvicorn backend.app.main:app --port 8000
