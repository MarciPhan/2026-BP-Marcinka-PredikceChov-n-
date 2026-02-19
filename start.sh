#!/bin/bash



echo -e "Metricord start"

echo -e "[1/3] Kontrola Redis/Valkey..."
if pgrep -x "redis-server" > /dev/null || pgrep -x "valkey-server" > /dev/null; then
    echo -e "Database již běží."
else
    echo -e "Spouštím Redis..."
    redis-server --daemonize yes
    sleep 2
    if pgrep -x "redis-server" > /dev/null || pgrep -x "valkey-server" > /dev/null; then
        echo -e "Database úspěšně spuštěna."
    else
        echo -e "Chyba: Nepodařilo se spustit Database server!"
        exit 1
    fi
fi

echo -e "[2/3] Konfigurace prostředí..."
export PYTHONPATH=$(pwd)
PYTHON_CMD="python3"

if [ -d ".venv" ]; then
    echo -e "Aktivuji virtuální prostředí (.venv)..."
    source .venv/bin/activate
    PYTHON_CMD="python"
fi

echo -e "[3/3] Spouštění služeb...${NC}"

pkill -f "bot/main.py" 2>/dev/null
pkill -f "uvicorn web.backend.main:app" 2>/dev/null

echo -e "Spouštím Discord bota..."
nohup $PYTHON_CMD bot/main.py > bot_std.log 2>&1 &
BOT_PID=$!

echo -e "Spouštím Dashboard na portu 8092..."
nohup $PYTHON_CMD -m uvicorn web.backend.main:app --host 0.0.0.0 --port 8092 > dashboard_std.log 2>&1 &
DASH_PID=$!

sleep 3

FAIL=0
if ps -p $BOT_PID > /dev/null; then
    echo -e "Discord Bot běží (PID: $BOT_PID)"
else
    echo -e "Discord Bot se nepodařilo spustit! Podívej se do bot_std.log"
    FAIL=1
fi

if ps -p $DASH_PID > /dev/null; then
    echo -e "Dashboard běží (PID: $DASH_PID)"
    echo -e "Dashboard dostupný na: http://localhost:8092"
else
    echo -e "Dashboard se nepodařilo spustit! Podívej se do dashboard_std.log"
    FAIL=1
fi

if [ $FAIL -eq 0 ]; then
    echo -e "Všechny služby byly úspěšně spuštěny"
else
    echo -e "Některé služby se nepodařilo spustit "
    exit 1
fi
