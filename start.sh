#!/bin/bash
echo "Starting CommunityMetrics..."

if ! [ -f .env ]; then
    echo "Warning: .env file missing. Copying from .env.example..."
    cp .env.example .env 2>/dev/null || true
fi

if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    echo "Docker detected. Starting via docker compose..."
    if docker compose version >/dev/null 2>&1; then
        docker compose up --build -d
    else
        docker-compose up --build -d
    fi
    echo "CommunityMetrics started in Docker!"
elif command -v python3 >/dev/null 2>&1; then
    echo "Docker not running or not found. Python 3 detected. Starting via start.py..."
    python3 start.py
elif command -v python >/dev/null 2>&1; then
    echo "Docker not running. Python detected. Starting via start.py..."
    python start.py
else
    echo "Error: Neither Docker nor Python is installed/running on this system."
    echo "Please install Docker or Python 3 to run this application."
    exit 1
fi
