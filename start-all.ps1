# Starts both the backend and frontend with one command, each in its own
# visible window so you can always see both logs (and just close a window
# to stop that process) - run this from the project root:
#
#   .\start-all.ps1
#
# Backend opens in a new window. Frontend runs in THIS window - press
# Ctrl+C here to stop it; close the other window (or Ctrl+C in it) to stop
# the backend.

$root = $PSScriptRoot

Write-Host "Starting backend (new window)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root'; uvicorn app.api.main:app --reload"

Write-Host "Starting frontend (this window)..." -ForegroundColor Cyan
Set-Location "$root\nextjs"
npm run dev
