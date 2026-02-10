#!/bin/bash

# Kill existing processes
echo "[INFO] Killing stuck processes..."
pkill -9 -f "bot.main" || echo "No bot process found"
pkill -9 -f "web.backend.main" || echo "No backend process found"

# Start Redis if not running
echo "[INFO] Checking Redis..."
if pgrep redis-server > /dev/null; then
    echo "Redis is already running."
else
    echo "Starting Redis..."
    nohup redis-server > redis_std.log 2>&1 &
    sleep 2
fi

# Determine Python path
PYTHON_CMD="./.venv/bin/python"
if [ ! -f "$PYTHON_CMD" ]; then
    echo "[WARNING] $PYTHON_CMD not found, trying python3..."
    PYTHON_CMD="python3"
fi

echo "[INFO] Using Python: $PYTHON_CMD"

# Start Bot
echo "[INFO] Starting Bot..."
nohup $PYTHON_CMD -u -m bot.main > bot_std.log 2>&1 &
BOT_PID=$!
echo "Bot PID: $BOT_PID"

# Start Dashboard
echo "[INFO] Starting Dashboard..."
nohup $PYTHON_CMD -m uvicorn web.backend.main:app --host 0.0.0.0 --port 8092 > dashboard_std.log 2>&1 &
DASH_PID=$!
echo "Dashboard PID: $DASH_PID"

# Wait and check
sleep 5

if ps -p $BOT_PID > /dev/null; then
  echo "✅ Bot is running"
else
  echo "❌ Bot failed to start. Check bot_std.log"
  cat bot_std.log
fi

if ps -p $DASH_PID > /dev/null; then
  echo "✅ Dashboard is running"
else
  echo "❌ Dashboard failed to start. Check dashboard_std.log"
  cat dashboard_std.log
fi
