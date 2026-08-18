@echo off
setlocal
echo Starting CommunityMetrics...

if not exist ".env" (
    echo Warning: .env file missing. Copying from .env.example...
    copy .env.example .env >nul 2>&1
)

where docker >nul 2>nul
if %ERRORLEVEL% equ 0 (
    docker info >nul 2>nul
    if %ERRORLEVEL% equ 0 (
        echo Docker detected and running. Starting via docker compose...
        docker compose up --build -d
        if %ERRORLEVEL% neq 0 (
            docker-compose up --build -d
        )
        echo CommunityMetrics started in Docker!
        goto end
    )
)

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo Docker not found or not running. Python detected. Starting via start.py...
    python start.py
    goto end
)

echo Error: Neither Docker nor Python is installed/running on this system.
echo Please install Docker or Python to run this application.

:end
pause
