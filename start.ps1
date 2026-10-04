# Start both backend and frontend concurrently on Windows
Write-Host "Starting Sunrise Clinic Backend & Frontend..." -ForegroundColor Cyan

$backend = Start-Process python -ArgumentList "-m uvicorn backend.main:app --host 127.0.0.1 --port 8000" -PassThru -NoNewWindow
Start-Sleep -Seconds 2

Set-Location frontend
$frontend = Start-Process npm -ArgumentList "run dev" -PassThru -NoNewWindow

Write-Host "Backend running on http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "Frontend running on http://localhost:5173" -ForegroundColor Green
Write-Host "Press Ctrl+C to terminate both servers..." -ForegroundColor Yellow

try {
    Wait-Process -Id $backend.Id, $frontend.Id
} finally {
    Stop-Process -Id $backend.Id -ErrorAction SilentlyContinue
    Stop-Process -Id $frontend.Id -ErrorAction SilentlyContinue
}
