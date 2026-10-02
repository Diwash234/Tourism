$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root "Tourism"
$frontend = Join-Path $root "frontend\Tourism"

Write-Host "Starting Django on http://127.0.0.1:8000 ..." -ForegroundColor Green
$django = Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$backend'; if (Test-Path '.\venv\Scripts\Activate.ps1') { . .\venv\Scripts\Activate.ps1 }; python manage.py migrate; python manage.py runserver 127.0.0.1:8000" -PassThru

Start-Sleep -Seconds 2

Write-Host "Starting Vite on http://localhost:5173/static/ ..." -ForegroundColor Green
$vite = Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$frontend'; npm run dev" -PassThru

Write-Host ""
Write-Host "Django PID: $($django.Id)"
Write-Host "Vite PID:   $($vite.Id)"
Write-Host ""
Write-Host "Open http://localhost:5173/static/" -ForegroundColor Cyan
Write-Host "Backend health: http://127.0.0.1:8000/health/" -ForegroundColor Cyan
Write-Host ""
Write-Host "Close the two child PowerShell windows when finished."
