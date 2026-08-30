@echo off
setlocal DisableDelayedExpansion
cd /d "%~dp0"
chcp 65001 >nul
echo Starting CommunityMetrics...

if not exist ".env" (
    if exist ".env.example" (
        echo Warning: .env file missing. Copying from .env.example...
        copy ".env.example" ".env" >nul 2>&1
    ) else (
        echo Warning: .env ani .env.example nebyl nalezen.
    )
)

set DASHBOARD_PORT=8093
set DISCOURSE_TOKEN=
set BOT_TOKEN=
set DISCORD_CLIENT_ID=
set DISCORD_CLIENT_SECRET=
if exist ".env" (
    for /f "usebackq eol=# tokens=1* delims==" %%a in (".env") do (
        if "%%a"=="DASHBOARD_PORT" set "DASHBOARD_PORT=%%b"
        if "%%a"=="DISCOURSE_TOKEN" set "DISCOURSE_TOKEN=%%b"
        if "%%a"=="BOT_TOKEN" set "BOT_TOKEN=%%b"
        if "%%a"=="DISCORD_CLIENT_ID" set "DISCORD_CLIENT_ID=%%b"
        if "%%a"=="DISCORD_CLIENT_SECRET" set "DISCORD_CLIENT_SECRET=%%b"
    )
)

setlocal EnableDelayedExpansion

if defined BOT_TOKEN goto client_id_check
echo.
echo ============================================================
echo  CHYBA: BOT_TOKEN neni nastaven v .env souboru!
echo  [INFO] Nezapomente v Discord Developer Portalu (zalozka Bot) povolit vsechna 3
echo         Privileged Gateway Intents (Presence, Server Members, Message Content).
echo         Jinak bot po spusteni okamzite spadne!
set "INPUT_BOT_TOKEN="
set /p INPUT_BOT_TOKEN=" Prosim, zadejte svuj Discord Bot Token (nebo stisknete Enter pro preskoceni): "
if "!INPUT_BOT_TOKEN!"=="" (
    echo  Pokracuji bez tokenu. Discord bot nemusi fungovat.
) else (
    if "!INPUT_BOT_TOKEN:~50,1!"=="" (
        echo  [WARNING] Zadany text je prilis kratky na to, aby slo o platny token.
        echo  Pokracuji bez tokenu.
    ) else (
        findstr /v /b /c:"BOT_TOKEN=" .env > .env.tmp
        move /y .env.tmp .env >nul
        echo BOT_TOKEN=!INPUT_BOT_TOKEN!>> .env
        echo  Token byl uspesne ulozen do .env!
    )
)
set "TOKEN_PROMPTED_ALREADY=1"
echo ============================================================

:client_id_check
if defined DISCORD_CLIENT_ID goto client_secret_check
echo.
echo ============================================================
echo  CHYBA: DISCORD_CLIENT_ID neni nastaven v .env souboru!
echo  [INFO] Nezapomente v Discord Developer Portalu (OAuth2 -^> Redirects) pridat URI:
echo         http://localhost:!DASHBOARD_PORT!/auth/callback
echo         Jinak uvidite chybu 'Invalid OAuth2 redirect_uri'.
set "INPUT_CLIENT_ID="
set /p INPUT_CLIENT_ID=" Prosim, zadejte svuj Discord OAuth2 Client ID (nebo stisknete Enter pro preskoceni): "
if "!INPUT_CLIENT_ID!"=="" (
    echo  Pokracuji bez Client ID. Discord prihlasovani nemusi fungovat.
) else (
    findstr /v /b /c:"DISCORD_CLIENT_ID=" .env > .env.tmp
    move /y .env.tmp .env >nul
    echo DISCORD_CLIENT_ID=!INPUT_CLIENT_ID!>> .env
    echo  Client ID bylo uspesne ulozeno do .env!
)
set "TOKEN_PROMPTED_ALREADY=1"
echo ============================================================

:client_secret_check
if defined DISCORD_CLIENT_SECRET goto discourse_check
echo.
echo ============================================================
echo  CHYBA: DISCORD_CLIENT_SECRET neni nastaven v .env souboru!
set "INPUT_CLIENT_SECRET="
set /p INPUT_CLIENT_SECRET=" Prosim, zadejte svuj Discord OAuth2 Client Secret (nebo stisknete Enter pro preskoceni): "
if "!INPUT_CLIENT_SECRET!"=="" (
    echo  Pokracuji bez Client Secret. Discord prihlasovani nemusi fungovat.
) else (
    findstr /v /b /c:"DISCORD_CLIENT_SECRET=" .env > .env.tmp
    move /y .env.tmp .env >nul
    echo DISCORD_CLIENT_SECRET=!INPUT_CLIENT_SECRET!>> .env
    echo  Client Secret byl uspesne ulozen do .env!
)
set "TOKEN_PROMPTED_ALREADY=1"
echo ============================================================

:discourse_check
if defined DISCOURSE_TOKEN goto npm_check
echo.
echo ============================================================
echo  CHYBA: DISCOURSE_TOKEN neni nastaven v .env souboru!
set "INPUT_TOKEN="
set /p INPUT_TOKEN=" Prosim, zadejte svuj Discourse API Token (nebo stisknete Enter pro preskoceni): "
if "!INPUT_TOKEN!"=="" (
    echo  Pokracuji bez tokenu. Synchronizace Discourse nemusi fungovat.
) else (
    if "!INPUT_TOKEN:~30,1!"=="" (
        echo  [WARNING] Zadany text je prilis kratky na to, aby slo o platny token ^(omylem stisknuta klavesa?^).
        echo  Pokracuji bez tokenu.
    ) else (
        findstr /v /b /c:"DISCOURSE_TOKEN=" .env > .env.tmp
        move /y .env.tmp .env >nul
        echo DISCOURSE_TOKEN=!INPUT_TOKEN!>> .env
        echo  Token byl uspesne ulozen do .env!
    )
)
set "TOKEN_PROMPTED_ALREADY=1"
echo ============================================================

:npm_check
where npm >nul 2>nul
if !ERRORLEVEL! equ 0 goto docker_check

where curl >nul 2>nul
if !ERRORLEVEL! neq 0 (
    echo ============================================================
    echo  [WARNING] 'curl' neni k dispozici. Automaticka instalace Node.js preskocena.
    echo ============================================================
    goto docker_check
)

echo ============================================================
echo  [Windows] Systemu chybi Node.js (pro dokumentaci). Skript jej nyni nainstaluje.
echo ============================================================
echo  Stahuji oficialni Node.js 24 LTS pro Windows...
curl -fL -o "%TEMP%\node-installer.msi" "https://nodejs.org/dist/v24.15.0/node-v24.15.0-x64.msi"
if !ERRORLEVEL! neq 0 (
    echo ============================================================
    echo  [WARNING] Stazeni Node.js selhalo. Automaticka instalace preskocena.
    echo ============================================================
    goto docker_check
)

echo  Spoustim instalaci (muze to trvat nekolik minut a vyzadovat potvrzeni administratora)...
msiexec /i "%TEMP%\node-installer.msi" /passive /norestart

set "INSTALL_RC=!ERRORLEVEL!"
if not "!INSTALL_RC!"=="0" if not "!INSTALL_RC!"=="3010" (
    echo ============================================================
    echo  [WARNING] Instalace Node.js se nezdarila nebo byla zrusena. Kod: !INSTALL_RC!
    echo  Dokumentace mozna nebude dostupna. Pokracuji dal...
    echo ============================================================
    goto docker_check
)

echo  Instalace Node.js uspesne dokoncena!
echo ------------------------------------------------------------
echo  Aktualizuji promenne prostredi pro tento beh...
set "PATH=%PATH%;%ProgramFiles%\nodejs"
echo ============================================================

:docker_check
where docker >nul 2>nul
if !ERRORLEVEL! neq 0 goto python_check
docker info >nul 2>nul
if !ERRORLEVEL! neq 0 goto python_check

echo Docker detected and running. Starting via docker compose...
set "COMPOSE_CMD=docker compose"
docker compose up --build -d
if !ERRORLEVEL! neq 0 (
    echo Modern docker compose failed. Trying legacy docker-compose...
    set "COMPOSE_CMD=docker-compose"
    docker-compose up --build -d
    if !ERRORLEVEL! neq 0 (
        echo.
        echo ============================================================
        echo  [ERROR] Nepodarilo se spustit CommunityMetrics pres Docker!
        echo ============================================================
        goto end
    )
)

echo  Overuji stav kontejneru (cekam na stabilizaci)...
timeout /t 10 /nobreak >nul
set "DOCKER_HEALTHY=1"

!COMPOSE_CMD! ps -a
if !ERRORLEVEL! neq 0 (
    echo ============================================================
    echo  [WARNING] Nepodarilo se ziskat stav Docker kontejneru.
    echo ============================================================
    set "DOCKER_HEALTHY=0"
) else (
    !COMPOSE_CMD! ps -a | findstr /i /c:"Exit " /c:"Dead " /c:"unhealthy" >nul
    if !ERRORLEVEL! equ 0 (
        echo ============================================================
        echo  [WARNING] Nektere kontejnery nejsou v poradku!
        echo  Doporucujeme zkontrolovat logy: !COMPOSE_CMD! logs
        echo ============================================================
        set "DOCKER_HEALTHY=0"
    )
)

set DOCS_URL=
where npm >nul 2>nul
if !ERRORLEVEL! equ 0 (
    echo Node.js detected. Starting documentation ^(VitePress^)...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173 " ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>&1
    call npm install --no-audit --no-fund --silent
    if !ERRORLEVEL! neq 0 (
        echo [WARNING] npm install selhal. Dokumentace nebude spustena.
    ) else (
        start "" /B cmd /c "npm run docs:dev > docs.log 2>&1"
        set "DOCS_URL=   [DOCS] Dokumentace  : http://localhost:5173"
    )
)

echo.
echo ============================================================
if "!DOCKER_HEALTHY!"=="1" (
    echo    [SUCCESS] CommunityMetrics spusteno uspesne ^(Docker^)!
) else (
    echo    [WARNING] CommunityMetrics spusteno, ale kontejnery hlasi problem!
)
echo ============================================================
echo    [WEB] Web Dashboard : http://localhost:!DASHBOARD_PORT!
if defined DOCS_URL echo !DOCS_URL!
echo    [BOT] Discord Bot    : Bezi (Primary ^& Dashboard Lite)
echo    [SYNC] Discourse Sync : Bezi v pozadi
echo    [DB] Redis Cache    : localhost:6379
echo ------------------------------------------------------------
echo    [OAUTH2] Discord Redirect URI: http://localhost:!DASHBOARD_PORT!/auth/callback
echo ------------------------------------------------------------
echo    [INFO] Uzitecne prikazy:
echo       Sledovani logu:  !COMPOSE_CMD! logs -f
echo       Zastaveni:       !COMPOSE_CMD! down
echo ============================================================
echo.
goto end

:python_check
echo.
echo ============================================================
echo  [WARNING] Docker/Compose neni dostupny! Prechazim na cisty Python.
echo  [!] Pro ostry provoz MUSITE mit v systemu nainstalovany Redis.
echo      (Pro Windows stahnete napr. Memurai nebo Redis for Windows)
echo      Bez nej pobezi aplikace v omezenem 'FakeRedis' rezimu a
echo      Web Dashboard neuvidi data z Discord Bota!
echo ============================================================
python --version >nul 2>nul
if !ERRORLEVEL! equ 0 (
    echo Python detected. Starting via start.py...
    python start.py
    goto end
)

py --version >nul 2>nul
if !ERRORLEVEL! equ 0 (
    echo Docker not found or not running. Python launcher ^(py^) detected. Starting via start.py...
    py start.py
    goto end
)

where curl >nul 2>nul
if !ERRORLEVEL! neq 0 (
    echo ============================================================
    echo  [ERROR] Systemu chybi Python a navic 'curl' neni k dispozici.
    echo  Nelze provest automatickou instalaci Pythonu.
    echo  Prosim, nainstalujte Python rucne.
    echo ============================================================
    goto end
)

echo ============================================================
echo  [Windows] Systemu chybi Python. Skript jej nyni automaticky nainstaluje.
echo ============================================================
echo  Stahuji oficialni Python 3.11 pro Windows...
curl -fL -o "%TEMP%\python-installer.exe" "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
if !ERRORLEVEL! neq 0 (
    echo ============================================================
    echo  [ERROR] Stazeni Pythonu selhalo. Aplikaci nelze spustit.
    echo ============================================================
    goto end
)

echo  Spoustim instalaci (muze to trvat nekolik minut, pockejte prosim)...
"%TEMP%\python-installer.exe" /passive InstallAllUsers=0 PrependPath=1 Include_test=0

set "INSTALL_RC=!ERRORLEVEL!"
if not "!INSTALL_RC!"=="0" if not "!INSTALL_RC!"=="3010" (
    echo ============================================================
    echo  [ERROR] Instalace Pythonu se nezdarila nebo byla zrusena! Kod: !INSTALL_RC!
    echo  Aplikaci nelze spustit ^(system nema Docker ani Python^).
    echo ============================================================
    goto end
)

echo  Instalace Pythonu uspesne dokoncena!
echo ------------------------------------------------------------
echo  Aktualizuji promenne prostredi pro tento beh...
set "PATH=%PATH%;%LocalAppData%\Programs\Python\Python311;%LocalAppData%\Programs\Python\Python311\Scripts;%ProgramFiles%\Python311;%ProgramFiles%\Python311\Scripts"
echo ============================================================

python --version >nul 2>&1
if !ERRORLEVEL! equ 0 (
    python start.py
) else (
    py --version >nul 2>&1
    if !ERRORLEVEL! equ 0 (
        py start.py
    ) else (
        echo [ERROR] Python byl nainstalovan, ale nelze jej spustit. Zkontrolujte systemove promenne.
    )
)

:end
pause
