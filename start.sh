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
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi
echo -e "Detekuji port..."
DASH_PORT=${DASHBOARD_PORT}
if [ -z "$DASH_PORT" ]; then
    # Zkusime 8092
    if ! lsof -i :8092 > /dev/null 2>&1; then
        DASH_PORT=8092
    else
        # Je to nas proces?
        OUR_PID=$(lsof -t -i :8092)
        if ps -p $OUR_PID -o cmd= | grep -q "uvicorn"; then
            echo -e "Port 8092 obsazen naší aplikací, restartuji..."
            kill -9 $OUR_PID 2>/dev/null
            DASH_PORT=8092
        else
            echo -e "Port 8092 obsazen systémem (antigravity?), používám 8093..."
            DASH_PORT=8093
        fi
    fi
fi
export DASHBOARD_PORT=$DASH_PORT

export PYTHONPATH=$(pwd)
PYTHON_CMD="python3"

if [ -d ".venv" ]; then
    echo -e "Aktivuji virtuální prostředí (.venv)..."
    source .venv/bin/activate
    PYTHON_CMD="python"
fi

echo -e "[3/3] Spouštění služeb...${NC}"

echo -e "Uklízím staré procesy..."
pkill -f "bot/main.py" 2>/dev/null
# Force kill if port is still busy by our uvicorn (in case of 8093 or explicit port)
BUSY_PID=$(lsof -t -i :$DASH_PORT)
if [ ! -z "$BUSY_PID" ]; then
    kill -9 $BUSY_PID 2>/dev/null
    sleep 1
fi

echo -e "Spouštím Discord bota..."
nohup $PYTHON_CMD bot/main.py > bot_std.log 2>&1 &
BOT_PID=$!

echo -e "Spouštím Dashboard na portu $DASH_PORT..."
nohup $PYTHON_CMD -m uvicorn web.backend.main:app --host 0.0.0.0 --port $DASH_PORT > dashboard_std.log 2>&1 &
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
    echo -e "Dashboard dostupný na: http://localhost:$DASH_PORT"
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
