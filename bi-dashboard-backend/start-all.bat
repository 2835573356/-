@echo off
chcp 65001 >nul
title 影刀社区 - BI看板系统

echo ============================================
echo   影刀社区 · BI 看板系统 — 一键启动
echo ============================================
echo.

set BACKEND_DIR=%~dp0
set FRONTEND_DIR=%BACKEND_DIR%..\bi-dashboard-frontend

:: ============================================
:: 1. 启动后端 (Python FastAPI)
:: ============================================
echo [1/3] 启动后端服务...
start "BI后端-API服务" cmd /k "cd /d %BACKEND_DIR% && python -m app.main"
echo       后端启动中... http://localhost:8000
echo       API文档: http://localhost:8000/docs
echo.

:: 等待后端启动
echo       等待后端就绪...
timeout /t 3 /nobreak >nul

:: ============================================
:: 2. 启动前端 (Vue)
:: ============================================
if exist "%FRONTEND_DIR%\package.json" (
    echo [2/3] 启动前端服务...
    start "BI前端-Vue服务" cmd /k "cd /d %FRONTEND_DIR% && npm run dev"
    echo       前端启动中... http://localhost:5173
) else (
    echo [2/3] 前端项目目录不存在，跳过前端启动
    echo       请先创建前端项目到: %FRONTEND_DIR%
)
echo.

:: ============================================
:: 3. 打开浏览器
:: ============================================
echo [3/3] 打开浏览器...

if exist "%FRONTEND_DIR%\package.json" (
    echo       打开前端页面: http://localhost:5173
    start "" http://localhost:5173
) else (
    echo       打开API文档: http://localhost:8000/docs
    start "" http://localhost:8000/docs
)

echo.
echo ============================================
echo   启动完成！
echo   默认账号: admin / admin123
echo ============================================
echo.
echo   关闭窗口不会停止服务，请在任务栏找到对应窗口关闭
echo.

pause
