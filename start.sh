#!/bin/bash
echo "Starting CommunityMetrics..."

if ! [ -f .env ]; then
    echo "Warning: .env file missing. Copying from .env.example..."
    cp .env.example .env 2>/dev/null || true
fi

DASHBOARD_PORT=$(grep -E '^DASHBOARD_PORT=' .env 2>/dev/null | cut -d'=' -f2 | tr -d '\r" ' || true)
if [ -z "$DASHBOARD_PORT" ]; then
    DASHBOARD_PORT="8092"
fi

if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    echo "Docker detected. Starting via docker compose..."
    if docker compose version >/dev/null 2>&1; then
        docker compose up --build -d
    else
        docker-compose up --build -d
    fi
    echo ""
    echo "============================================================"
    echo "   🚀 CommunityMetrics spuštěno úspěšně (Docker)!          "
    echo "============================================================"
    echo "   🌐 Web Dashboard : http://localhost:${DASHBOARD_PORT}"
    echo "   🤖 Discord Bot    : Běží (Primary & Dashboard Lite)"
    echo "   🔄 Discourse Sync : Běží v pozadí"
    echo "   🗄️ Redis Cache    : localhost:6379"
    echo "------------------------------------------------------------"
    echo "   📋 Užitečné příkazy:"
    echo "      Sledování logů:  docker compose logs -f"
    echo "      Zastavení:       docker compose down"
    echo "============================================================"
elif command -v python3 >/dev/null 2>&1; then
    echo "Docker not running or not found. Python 3 detected. Starting via start.py..."
    
    # macOS check for python3 stub without Command Line Tools
    if [[ "$OSTYPE" == "darwin"* ]] && ! python3 -c "import sys" >/dev/null 2>&1; then
        echo ""
        echo "============================================================"
        echo " 🍎 Systému chybí Python. Skript jej nyní automaticky nainstaluje."
        echo "============================================================"
        echo " Stahuji oficiální Python 3.11 pro macOS..."
        curl -L -o /tmp/python-installer.pkg "https://www.python.org/ftp/python/3.11.9/python-3.11.9-macos11.pkg"
        
        echo " Spouštím instalaci (Může to po vás chtít vaše heslo k Macu):"
        sudo installer -pkg /tmp/python-installer.pkg -target /
        
        echo " Instalace Pythonu úspěšně dokončena!"
        echo "------------------------------------------------------------"
    fi
    
    python3 start.py
elif command -v python >/dev/null 2>&1; then
    echo "Docker not running. Python detected. Starting via start.py..."
    python start.py
else
    echo "Error: Neither Docker nor Python is installed/running on this system."
    echo "Please install Docker or Python 3 to run this application."
    exit 1
fi

