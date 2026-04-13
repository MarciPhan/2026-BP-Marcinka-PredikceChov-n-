#!/bin/bash
set -euo pipefail

# Config
PORT=${DASHBOARD_PORT:-8092}
LOG_BOT="bot.log"
LOG_WEB="web.log"

# Colors
B='\033[1;34m'
G='\033[0;32m'
R='\033[0;31m'
N='\033[0m'

echo -e "${B}Starting Metricord...${N}"

# 1. Env & Deps
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q -r requirements.txt

# 2. Check .env
if [ ! -f ".env" ]; then
    echo -e "${R}Error: .env missing${N}"
    [ -f ".env.example" ] && echo "Copy .env.example to .env and fill in BOT_TOKEN"
    exit 1
fi
set -a; source .env; set +a
[ -z "${BOT_TOKEN:-}" ] && echo -e "${R}Warning: BOT_TOKEN not set in .env. Bot will start in idle mode.${N}"


# 3. Redis
if ! pgrep -x "redis-server" >/dev/null && ! pgrep -x "valkey-server" >/dev/null; then
    if command -v redis-server &>/dev/null; then
        redis-server --daemonize yes
    elif command -v valkey-server &>/dev/null; then
        valkey-server --daemonize yes
    else
        echo "Error: Redis/Valkey not found" && exit 1
    fi
    sleep 1
fi

# 4. Clean up old runs
pkill -f "bot/main.py" 2>/dev/null || true
BUSY_PID=$(lsof -t -i :"$PORT" 2>/dev/null || true)
[ -n "$BUSY_PID" ] && kill -9 $BUSY_PID 2>/dev/null && sleep 1

# 5. Run
export PYTHONPATH=$PWD
export DASHBOARD_PORT=$PORT

echo "Launching services..."
nohup python3 bot/main.py > "$LOG_BOT" 2>&1 &
BOT_PID=$!

nohup python3 -m uvicorn web.backend.main:app --host 0.0.0.0 --port "$PORT" > "$LOG_WEB" 2>&1 &
WEB_PID=$!

# 6. Documentation (VitePress)
echo "Launching Documentation..."
(cd docs-site && nohup npm run docs:dev > ../docs.log 2>&1 &)
DOCS_PID=$!

sleep 2
if ps -p $BOT_PID >/dev/null && ps -p $WEB_PID >/dev/null; then
    echo -e "${G}Metricord is up!${N}"
    echo "  Dashboard:  http://localhost:$PORT"
    echo "  Docs Site:  http://localhost:5173"
    echo "  Logs:       tail -f $LOG_BOT $LOG_WEB docs.log"
else
    echo -e "${R}Startup failed. Check logs.${N}"
    exit 1
fi


