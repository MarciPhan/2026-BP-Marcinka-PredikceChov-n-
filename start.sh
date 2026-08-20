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
    if [[ "$OSTYPE" == "darwin"* ]] && ! xcode-select -p >/dev/null 2>&1; then
        echo ""
        echo "============================================================"
        echo " 🍎 macOS vyžaduje jednorázovou instalaci nástrojů (Python 3)"
        echo "============================================================"
        echo " Za okamžik se zobrazí vyskakovací okno s výzvou k instalaci."
        echo " 1. Klikněte na 'Instalovat' (Install) a potvrďte."
        echo " 2. Počkejte, až instalace zcela doběhne."
        echo " 3. Teprve POTÉ se vraťte sem a stiskněte ENTER."
        echo "------------------------------------------------------------"
        xcode-select --install 2>/dev/null
        read -p "Stiskněte ENTER, až bude instalace zcela hotová..."
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

