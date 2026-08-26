#!/bin/sh

SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd) || exit 1
cd "$SCRIPT_DIR" || exit 1

echo "Starting CommunityMetrics..."

if ! [ -f .env ]; then
    if [ -f .env.example ]; then
        echo "Warning: .env file missing. Copying from .env.example..."
        cp .env.example .env 2>/dev/null || true
    else
        echo "Warning: .env ani .env.example nebyl nalezen."
    fi
fi

DASHBOARD_PORT=$(grep -E '^DASHBOARD_PORT=' .env 2>/dev/null | cut -d'=' -f2- | tr -d '\r" ' || true)
if [ -z "$DASHBOARD_PORT" ]; then
    DASHBOARD_PORT="8093"
fi

DISCOURSE_TOKEN=$(grep -E '^DISCOURSE_TOKEN=' .env 2>/dev/null | cut -d'=' -f2- | tr -d '\r" ' || true)
if [ -z "$DISCOURSE_TOKEN" ]; then
    echo ""
    echo "============================================================"
    echo " CHYBA: DISCOURSE_TOKEN není nastaven v .env souboru!"
    printf " Prosím, zadejte svůj Discourse API Token (nebo stiskněte Enter pro přeskočení): "
    
    trap 'stty echo 2>/dev/null; echo ""; exit 1' INT TERM
    stty -echo 2>/dev/null
    read USER_TOKEN
    stty echo 2>/dev/null
    trap - INT TERM
    echo ""
    
    if [ -z "$USER_TOKEN" ]; then
        echo " Pokračuji bez tokenu. Synchronizace Discourse nemusí fungovat."
    else
        if [ "${#USER_TOKEN}" -lt 30 ]; then
            echo " [WARNING] Zadaný text je příliš krátký na to, aby šlo o platný token (omylem stisknutá klávesa?)."
            echo " Pokračuji bez tokenu."
        else
            echo "" >> .env
            echo "DISCOURSE_TOKEN=$USER_TOKEN" >> .env
            echo " Token byl úspěšně uložen do .env!"
        fi
    fi
    export TOKEN_PROMPTED_ALREADY=1
    echo "============================================================"
fi

NODE_OK=0
if command -v node >/dev/null 2>&1; then
    NODE_MAJOR=$(node -p "process.versions.node.split('.')[0]" 2>/dev/null || echo 0)
    if [ "$NODE_MAJOR" -ge 22 ]; then
        NODE_OK=1
    fi
fi

if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    echo "Docker detected. Starting via docker compose..."
    
    if docker compose version >/dev/null 2>&1; then
        COMPOSE_CMD="docker compose"
    elif command -v docker-compose >/dev/null 2>&1; then
        COMPOSE_CMD="docker-compose"
    else
        echo ""
        echo "============================================================"
        echo "  [ERROR] Docker je dostupný, ale Docker Compose nebyl nalezen!"
        echo "============================================================"
        exit 1
    fi

    $COMPOSE_CMD up --build -d
    if [ $? -ne 0 ]; then
        echo ""
        echo "============================================================"
        echo "  [ERROR] Nepodařilo se spustit CommunityMetrics přes Docker!"
        echo "============================================================"
        exit 1
    fi

    echo "Ověřuji stav kontejnerů..."
    sleep 3
    DOCKER_HEALTHY=1

    $COMPOSE_CMD ps -a >/dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo "============================================================"
        echo "  [WARNING] Nepodařilo se získat stav Docker kontejnerů."
        echo "============================================================"
        DOCKER_HEALTHY=0
    else
        if $COMPOSE_CMD ps -a | grep -iE "Exit|Dead|Restarting|Created|Paused|unhealthy" >/dev/null 2>&1; then
            echo "============================================================"
            echo "  [WARNING] Některé kontejnery nejsou v pořádku!"
            echo "  Doporučujeme zkontrolovat logy: $COMPOSE_CMD logs"
            echo "============================================================"
            DOCKER_HEALTHY=0
        fi
    fi

    DOCS_URL=""
    if [ "$NODE_OK" -eq 1 ] && command -v npm >/dev/null 2>&1; then
        echo "Node.js (v22+) a npm detekováno. Starting documentation (VitePress)..."
        if command -v lsof >/dev/null 2>&1; then
            lsof -t -i:5173 | xargs kill -9 2>/dev/null || true
        fi
        
        npm install --no-audit --no-fund --silent
        if [ $? -ne 0 ]; then
            echo "[WARNING] npm install selhal. Dokumentace nebude spuštěna."
        else
            npm run docs:dev > docs.log 2>&1 &
            DOCS_URL="   [DOCS] Dokumentace  : http://localhost:5173"
        fi
    else
        echo " [INFO] Node.js 22+ nenalezen. VitePress dokumentace se nespustí."
    fi

    echo ""
    echo "============================================================"
    if [ "$DOCKER_HEALTHY" -eq 1 ]; then
        echo "   [SUCCESS] CommunityMetrics spuštěno úspěšně (Docker)!   "
    else
        echo "   [WARNING] CommunityMetrics spuštěno, ale kontejnery hlásí problém!"
    fi
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
    echo "      Sledování logů:  $COMPOSE_CMD logs -f"
    echo "      Zastavení:       $COMPOSE_CMD down"
    echo "============================================================"
    
    exit 0
fi

echo "Docker not running. Checking for Python 3.11+..."

PYTHON_CMD=""

if command -v python3 >/dev/null 2>&1 && python3 -c 'import sys; exit(0 if sys.version_info >= (3,11) else 1)' >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1 && python -c 'import sys; exit(0 if sys.version_info >= (3,11) else 1)' >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "Python 3.11+ nebyl v systému nalezen. Instaluji přenosný Python..."
    
    RUNTIME_DIR="$PWD/.runtime"
    mkdir -p "$RUNTIME_DIR/bin"
    
    if [ ! -x "$RUNTIME_DIR/bin/uv" ]; then
        echo "Stahuji 'uv' installer..."
        if command -v curl >/dev/null 2>&1; then
            curl -LsSf https://astral.sh/uv/install.sh | env UV_UNMANAGED_INSTALL="$RUNTIME_DIR/bin" sh
        elif command -v wget >/dev/null 2>&1; then
            wget -qO- https://astral.sh/uv/install.sh | env UV_UNMANAGED_INSTALL="$RUNTIME_DIR/bin" sh
        else
            echo " [ERROR] Chybí curl i wget. Nelze stáhnout Python."
            exit 1
        fi
    fi
    
    UV="$RUNTIME_DIR/bin/uv"
    echo "Stahuji Python 3.11 přes uv..."
    "$UV" python install 3.11
    if [ $? -ne 0 ]; then
        echo " [ERROR] Nepodařilo se nainstalovat Python přes uv."
        exit 1
    fi
    
    PYTHON_CMD=$("$UV" python find 3.11)
    if [ -z "$PYTHON_CMD" ]; then
        echo " [ERROR] uv nenalezl nainstalovaný Python."
        exit 1
    fi
fi

if ! "$PYTHON_CMD" --version >/dev/null 2>&1; then
    echo " [ERROR] Nalezený Python ($PYTHON_CMD) nelze spustit. Ukončuji."
    exit 1
fi

echo "Python připraven. Spouštím via start.py..."
"$PYTHON_CMD" start.py

