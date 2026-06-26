@echo off
title BI Dashboard Launcher

set ROOT=%~dp0
set BACKEND=%ROOT%bi-dashboard-backend
set FRONTEND=%ROOT%bi-dashboard-frontend

echo ============================================
echo   YingDao BI Dashboard - Startup
echo ============================================
echo.

echo [1/2] Starting backend...
start "Backend-API" /D "%BACKEND%" cmd /c "python -m app.main"

echo [2/2] Starting frontend...
start "Frontend-Vue" /D "%FRONTEND%" cmd /c "npm run dev"

timeout /t 5 /nobreak >nul
start http://localhost:5173

echo.
echo ============================================
echo   Backend:  http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo   Frontend: http://localhost:5173
echo   Login:    admin / admin123
echo ============================================
echo.
pause
