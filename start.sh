#!/bin/bash

# ==============================================================================
# Metricord Startup Script
# ==============================================================================

# Barvy pro výstup
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Metricord Startup Sequence ===${NC}"

# 1. Kontrola Redis/Valkey
echo -e "${YELLOW}[1/3] Kontrola Redis/Valkey...${NC}"
if pgrep -x "redis-server" > /dev/null || pgrep -x "valkey-server" > /dev/null; then
    echo -e "${GREEN}Database (Redis/Valkey) již běží.${NC}"
else
    echo -e "${YELLOW}Spouštím Redis...${NC}"
    redis-server --daemonize yes
    sleep 2
    if pgrep -x "redis-server" > /dev/null || pgrep -x "valkey-server" > /dev/null; then
        echo -e "${GREEN}Database úspěšně spuštěna.${NC}"
    else
        echo -e "${RED}Chyba: Nepodařilo se spustit Database server!${NC}"
        exit 1
    fi
fi

# 2. Nastavení prostředí
echo -e "${YELLOW}[2/3] Konfigurace prostředí...${NC}"
export PYTHONPATH=$(pwd)
PYTHON_CMD="python3"

if [ -d ".venv" ]; then
    echo -e "Aktivuji virtuální prostředí (.venv)..."
    source .venv/bin/activate
    PYTHON_CMD="python"
fi

# 3. Spuštění služeb
echo -e "${YELLOW}[3/3] Spouštění služeb...${NC}"

# Ukončení starých procesů (pokud existují)
pkill -f "bot/main.py" 2>/dev/null
pkill -f "uvicorn web.backend.main:app" 2>/dev/null

echo -e "Spouštím Discord bota..."
nohup $PYTHON_CMD bot/main.py > bot_std.log 2>&1 &
BOT_PID=$!

echo -e "Spouštím Dashboard na portu 8092..."
nohup $PYTHON_CMD -m uvicorn web.backend.main:app --host 0.0.0.0 --port 8092 > dashboard_std.log 2>&1 &
DASH_PID=$!

sleep 3

# Závěrečná kontrola
FAIL=0
if ps -p $BOT_PID > /dev/null; then
    echo -e "${GREEN}✅ Discord Bot běží (PID: $BOT_PID)${NC}"
else
    echo -e "${RED}❌ Discord Bot se nepodařilo spustit! Podívej se do bot_std.log${NC}"
    FAIL=1
fi

if ps -p $DASH_PID > /dev/null; then
    echo -e "${GREEN}✅ Dashboard běží (PID: $DASH_PID)${NC}"
    echo -e "${BLUE}Dashboard dostupný na: http://localhost:8092${NC}"
else
    echo -e "${RED}❌ Dashboard se nepodařilo spustit! Podívej se do dashboard_std.log${NC}"
    FAIL=1
fi

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}=== Všechny služby byly úspěšně spuštěny ===${NC}"
else
    echo -e "${RED}=== Některé služby se nepodařilo spustit ===${NC}"
    exit 1
fi
