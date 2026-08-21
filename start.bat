@echo off
setlocal
echo Starting CommunityMetrics...

if not exist ".env" (
    echo Warning: .env file missing. Copying from .env.example...
    copy .env.example .env >nul 2>&1
)

set DASHBOARD_PORT=8093
if exist ".env" (
    for /f "tokens=1,2 delims==" %%a in (.env) do (
        if "%%a"=="DASHBOARD_PORT" set DASHBOARD_PORT=%%b
    )
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

        set DOCS_URL=
        where npm >nul 2>nul
        if %ERRORLEVEL% equ 0 (
            echo Node.js detected. Starting documentation (VitePress)...
            rem Zabijeme predchozi proces na portu 5173
            for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173 ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>&1
            call npm install --no-audit --no-fund --silent
            start /B npm run docs:dev > docs.log 2>&1
            set DOCS_URL=   [DOCS] Dokumentace  : http://localhost:5173
        )

        echo.
        echo ============================================================
        echo    [SUCCESS] CommunityMetrics spusteno uspesne (Docker)!          
        echo ============================================================
        echo    [WEB] Web Dashboard : http://localhost:%DASHBOARD_PORT%
        if defined DOCS_URL echo %DOCS_URL%
        echo    [BOT] Discord Bot    : Bezi (Primary ^& Dashboard Lite)
        echo    [SYNC] Discourse Sync : Bezi v pozadi
        echo    [DB] Redis Cache    : localhost:6379
        echo ------------------------------------------------------------
        echo    [INFO] Uzitecne prikazy:
        echo       Sledovani logu:  docker compose logs -f
        echo       Zastaveni:       docker compose down
        echo ============================================================
        echo.
        goto end
    )
)

where npm >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ============================================================
    echo  [Windows] Systemu chybi Node.js ^(pro dokumentaci^). Skript jej nyni nainstaluje.
    echo ============================================================
    echo  Stahuji oficialni Node.js 20 LTS pro Windows...
    curl -L -o "%TEMP%\node-installer.msi" "https://nodejs.org/dist/v20.11.1/node-v20.11.1-x64.msi"
    
    echo  Spoustim tichou instalaci (muze to trvat nekolik minut, pockejte prosim)...
    msiexec /i "%TEMP%\node-installer.msi" /quiet /norestart
    
    echo  Instalace Node.js uspesne dokoncena!
    echo ------------------------------------------------------------
    echo  Nyni se okno zavre a spusti znovu, aby se nacetly nove promenne...
    timeout /t 3 >nul
    start "" cmd /c "%~dpnx0"
    exit /b
)

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo Docker not found or not running. Python detected. Starting via start.py...
    python start.py
    goto end
)

where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo Docker not found or not running. Python launcher (py) detected. Starting via start.py...
    py start.py
    goto end
)

echo ============================================================
echo  [Windows] Systemu chybi Python. Skript jej nyni automaticky nainstaluje.
echo ============================================================
echo  Stahuji oficialni Python 3.11 pro Windows...
curl -L -o "%TEMP%\python-installer.exe" "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"

echo  Spoustim tichou instalaci (muze to trvat nekolik minut, pockejte prosim)...
"%TEMP%\python-installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0

echo  Instalace Pythonu uspesne dokoncena!
echo ------------------------------------------------------------
echo  Nyni se okno zavre a spusti znovu, aby se nacetl novy Python...
timeout /t 3 >nul
start "" cmd /c "%~dpnx0"
exit /b

:end
pause
