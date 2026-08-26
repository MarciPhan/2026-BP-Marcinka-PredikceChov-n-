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
    IFS= read -r USER_TOKEN
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
            printf '\nDISCOURSE_TOKEN=%s\n' "$USER_TOKEN" >> .env
            echo " Token byl úspěšně uložen do .env!"
        fi
    fi
    echo "============================================================"
    export TOKEN_PROMPTED_ALREADY=1
fi

NODE_OK=0
if command -v node >/dev/null 2>&1; then
    NODE_MAJOR=$(node -p "process.versions.node.split('.')[0]" 2>/dev/null || echo 0)
    if [ "$NODE_MAJOR" -ge 22 ]; then
        NODE_OK=1
    fi
fi

USE_DOCKER=0
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    if docker compose version >/dev/null 2>&1; then
        COMPOSE_CMD="docker compose"
        USE_DOCKER=1
    elif command -v docker-compose >/dev/null 2>&1; then
        COMPOSE_CMD="docker-compose"
        USE_DOCKER=1
    else
        echo " [WARNING] Docker běží, ale chybí Docker Compose. Přecházím na Python fallback..."
    fi
fi

if [ "$USE_DOCKER" -eq 1 ]; then
    echo "Docker a Compose detekováno. Spouštím aplikaci..."

    $COMPOSE_CMD up --build -d
    if [ $? -ne 0 ]; then
        echo ""
        echo "============================================================"
        echo "  [ERROR] Nepodařilo se spustit CommunityMetrics přes Docker!"
        echo "============================================================"
        exit 1
    fi

    echo "Ověřuji stav kontejnerů..."
    DOCKER_HEALTHY=0
    
    for i in 1 2 3 4 5 6 7 8 9 10; do
        CONTAINERS=$($COMPOSE_CMD ps -a -q 2>/dev/null)
        
        if [ -n "$CONTAINERS" ]; then
            ALL_READY=1
            
            for CONTAINER in $CONTAINERS; do
                STATUS=$(docker inspect -f '{{.State.Status}}' "$CONTAINER" 2>/dev/null)
                HEALTH=$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$CONTAINER" 2>/dev/null)
                
                if [ "$STATUS" != "running" ]; then
                    ALL_READY=0
                    break
                fi
                
                if [ "$HEALTH" = "starting" ] || [ "$HEALTH" = "unhealthy" ]; then
                    ALL_READY=0
                    break
                fi
            done
            
            if [ "$ALL_READY" -eq 1 ]; then
                DOCKER_HEALTHY=1
                break
            fi
        fi
        sleep 2
    done

    if [ "$DOCKER_HEALTHY" -eq 0 ]; then
        echo "============================================================"
        echo "  [WARNING] Některé kontejnery nejsou plně připraveny nebo havarovaly."
        echo "  Doporučujeme zkontrolovat logy: $COMPOSE_CMD logs"
        echo "============================================================"
    fi

    DOCS_URL=""
    if [ "$NODE_OK" -eq 1 ] && command -v npm >/dev/null 2>&1; then
        echo "Node.js (v22+) a npm detekováno. Starting documentation (VitePress)..."
        if command -v lsof >/dev/null 2>&1; then
            PIDS=$(lsof -t -i:5173 2>/dev/null || true)
            if [ -n "$PIDS" ]; then
                kill $PIDS 2>/dev/null || true
            fi
        fi
        
        npm install --no-audit --no-fund --silent
        if [ $? -ne 0 ]; then
            echo "[WARNING] npm install selhal. Dokumentace nebude spuštěna."
        else
            npm run docs:dev > docs.log 2>&1 &
            DOCS_PID=$!
            sleep 1
            if kill -0 "$DOCS_PID" 2>/dev/null; then
                DOCS_URL="   [DOCS] Dokumentace  : http://localhost:5173"
            else
                echo "[WARNING] Dokumentace (VitePress) nečekaně havarovala při spouštění. Zkontrolujte docs.log."
            fi
        fi
    else
        echo " [INFO] Node.js 22+ a/nebo npm nejsou dostupné. VitePress dokumentace se nespustí."
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

echo "Docker/Compose není dostupný. Checking for Python 3.11+..."

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
        
        if [ ! -x "$RUNTIME_DIR/bin/uv" ]; then
            echo " [ERROR] Instalace uv selhala."
            exit 1
        fi
    fi
    
    UV="$RUNTIME_DIR/bin/uv"
    export UV_PYTHON_INSTALL_DIR="$RUNTIME_DIR/python"
    
    echo "Stahuji Python 3.11 přes uv..."
    "$UV" python install 3.11
    if [ $? -ne 0 ]; then
        echo " [ERROR] Nepodařilo se nainstalovat Python přes uv."
        exit 1
    fi
    
    PYTHON_CMD=$("$UV" python find --managed-python 3.11)
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

