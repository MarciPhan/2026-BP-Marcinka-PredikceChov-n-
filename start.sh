#!/bin/bash
echo "Starting CommunityMetrics..."

if ! [ -f .env ]; then
    echo "Warning: .env file missing. Copying from .env.example..."
    cp .env.example .env 2>/dev/null || true
fi

DASHBOARD_PORT=$(grep -E '^DASHBOARD_PORT=' .env 2>/dev/null | cut -d'=' -f2 | tr -d '\r" ' || true)
if [ -z "$DASHBOARD_PORT" ]; then
    DASHBOARD_PORT="8093"
fi

if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    echo "Docker detected. Starting via docker compose..."
    if docker compose version >/dev/null 2>&1; then
        docker compose up --build -d
    else
        docker-compose up --build -d
    fi

    DOCS_URL=""
    if command -v npm >/dev/null 2>&1; then
        echo "Spouštím dokumentaci (VitePress)..."
        if command -v lsof >/dev/null 2>&1; then
            lsof -t -i:5173 | xargs kill -9 2>/dev/null
        fi
        npm install --no-audit --no-fund --silent
        npm run docs:dev > docs.log 2>&1 &
        DOCS_URL="   [DOCS] Dokumentace  : http://localhost:5173"
    fi

    echo ""
    echo "============================================================"
    echo "   [SUCCESS] CommunityMetrics spuštěno úspěšně (Docker)!   "
    echo "============================================================"
    echo "   [WEB] Web Dashboard : http://localhost:${DASHBOARD_PORT}"
    if [ -n "$DOCS_URL" ]; then
        echo "$DOCS_URL"
    fi
    echo "   [BOT] Discord Bot    : Běží (Primary & Dashboard Lite)"
    echo "   [SYNC] Discourse Sync : Běží v pozadí"
    echo "   [DB] Redis Cache    : localhost:6379"
    echo "------------------------------------------------------------"
    echo "   [INFO] Užitečné příkazy:"
    echo "      Sledování logů:  docker compose logs -f"
    echo "      Zastavení:       docker compose down"
    echo "============================================================"
elif command -v python3 >/dev/null 2>&1; then
    echo "Docker not running or not found. Python 3 detected. Starting via start.py..."
    
    PYTHON_CMD="python3"
    
    # macOS check for python3 stub without triggering xcode-select popup
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if [ "$(command -v python3)" = "/usr/bin/python3" ] && ! xcode-select -p >/dev/null 2>&1; then
            echo ""
            echo "============================================================"
            echo " [macOS] Systému chybí Python. Skript jej nyní automaticky nainstaluje."
            echo "============================================================"
            echo " Stahuji oficiální Python 3.11 pro macOS..."
            curl -L -o /tmp/python-installer.pkg "https://www.python.org/ftp/python/3.11.9/python-3.11.9-macos11.pkg"
            
            echo " Spouštím instalaci (Může to po vás chtít vaše heslo k Macu):"
            sudo installer -pkg /tmp/python-installer.pkg -target /
            
            echo " Instalace Pythonu úspěšně dokončena!"
            echo "------------------------------------------------------------"
            
            # Use the newly installed python explicitly
            if [ -x "/usr/local/bin/python3" ]; then
                PYTHON_CMD="/usr/local/bin/python3"
            fi
        fi
    fi

    if ! command -v npm >/dev/null 2>&1 && [ ! -x "/usr/local/bin/npm" ]; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            echo ""
            echo "============================================================"
            echo " [macOS] Systému chybí Node.js (pro dokumentaci). Nyní se nainstaluje."
            echo "============================================================"
            echo " Stahuji oficiální Node.js 20 LTS pro macOS..."
            curl -L -o /tmp/node-installer.pkg "https://nodejs.org/dist/v20.11.1/node-v20.11.1.pkg"
            
            echo " Spouštím instalaci (Může to po vás chtít vaše heslo k Macu):"
            sudo installer -pkg /tmp/node-installer.pkg -target /
            
            echo " Instalace Node.js úspěšně dokončena!"
            echo "------------------------------------------------------------"
        elif [[ "$OSTYPE" == "linux-gnu"* ]] && command -v apt-get >/dev/null 2>&1; then
            echo ""
            echo "============================================================"
            echo " [Linux] Systému chybí Node.js (pro dokumentaci). Nyní se nainstaluje."
            echo "============================================================"
            sudo apt-get update
            sudo apt-get install -y nodejs npm
            echo " Instalace Node.js dokončena!"
            echo "------------------------------------------------------------"
        fi
    fi
    
    $PYTHON_CMD start.py
elif command -v python >/dev/null 2>&1; then
    echo "Docker not running. Python detected. Starting via start.py..."
    python start.py
else
    if [[ "$OSTYPE" == "linux-gnu"* ]] && command -v apt-get >/dev/null 2>&1; then
        echo ""
        echo "============================================================"
        echo " [Linux] Systému chybí Python 3. Nyní se nainstaluje."
        echo "============================================================"
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip python3-venv nodejs npm
        echo " Instalace dokončena!"
        echo "------------------------------------------------------------"
        python3 start.py
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo " [macOS] Systému zcela chybí Python. Instaluji..."
        curl -L -o /tmp/python-installer.pkg "https://www.python.org/ftp/python/3.11.9/python-3.11.9-macos11.pkg"
        sudo installer -pkg /tmp/python-installer.pkg -target /
        /usr/local/bin/python3 start.py
    else
        echo "Error: Neither Docker nor Python is installed/running on this system."
        echo "Please install Docker or Python 3 to run this application."
        exit 1
    fi
fi

