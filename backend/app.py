import os
import asyncio
import json
import threading
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import yaml

from backend.redis_db import RedisDatabase
from collectors.discord_collector import DiscordCollector
from collectors.discourse_collector import DiscourseCollector

# ======================================================
# Logging
# ======================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ======================================================
# PATHS
# ======================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
FRONTEND_DIR = os.path.join(PROJECT_DIR, "frontend")

logger.info(f"📁 FRONTEND DIR: {FRONTEND_DIR}")

# ======================================================
# FASTAPI APP
# ======================================================
app = FastAPI()

# ======================================================
# CONFIG
# ======================================================
with open(os.path.join(PROJECT_DIR, "config.yaml"), "r") as f:
    cfg = yaml.safe_load(f)

redis_cfg = cfg["redis"]
discord_cfg = cfg["discord"]
discourse_cfg = cfg["discourse"]

# ======================================================
# CORS
# ======================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# ======================================================
# Redis
# ======================================================
redis = RedisDatabase(
    host=redis_cfg["host"],
    port=redis_cfg["port"],
    db=redis_cfg["db"],
    password=redis_cfg["password"],
    salt=redis_cfg["salt"]
)
logger.info("🔧 Redis Database initialized")

# ======================================================
# WEBSOCKETS
# ======================================================
clients = []

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    clients.append(ws)
    logger.info(f"✅ WS client connected → {len(clients)} total")

    try:
        while True:
            try:
                # Pokus o čtení zprávy (frontend nic neposílá, změní se to v timeout/error)
                await ws.receive_text()
            except Exception:
                # Udržujeme spojení naživu, i když klient nic neposílá
                await asyncio.sleep(1)

    except WebSocketDisconnect:
        pass

    finally:
        if ws in clients:
            clients.remove(ws)
        logger.info(f"❌ WS client disconnected → {len(clients)} remaining")


async def broadcast(data: dict):
    """
    Broadcast data to all WebSocket clients
    Expects data to already be a dict (not JSON string)
    """
    if not clients:
        return
        
    dead = []
    
    # Ensure data is properly formatted
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except:
            logger.error(f"Failed to parse data: {data}")
            return
    
    payload = json.dumps(data)
    
    logger.debug(f"📡 Broadcasting to {len(clients)} clients: {data.get('type', 'unknown')}")
    
    for ws in clients:
        try:
            await ws.send_text(payload)
        except Exception as e:
            logger.error(f"Error broadcasting to client: {e}")
            dead.append(ws)

    for ws in dead:
        if ws in clients:
            clients.remove(ws)


# ======================================================
# REDIS LISTENER → WS (NON-BLOCKING!)
# ======================================================
def redis_listener_thread(loop):
    """Redis listener in separate thread - doesn't block FastAPI"""
    pub = redis.get_pubsub()
    pub.subscribe("messages")
    logger.info("🎧 Redis listener started in background thread")
    
    for msg in pub.listen():
        if msg["type"] != "message":
            continue
        try:
            # Parse the JSON data from Redis
            payload = json.loads(msg["data"])
            
            # Log the message type for debugging
            msg_type = payload.get("type", "unknown")
            is_live = payload.get("is_live", False)
            is_historical = payload.get("is_historical", False)
            
            status = "🟢 LIVE" if is_live else "📦 HIST" if is_historical else "ℹ️ INFO"
            logger.info(f"{status} Redis message: {msg_type} from {payload.get('source', 'unknown')}")
            
            # Send parsed dict (not string) to broadcast
            asyncio.run_coroutine_threadsafe(broadcast(payload), loop)
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON decode error: {e}")
        except Exception as e:
            logger.error(f"❌ Redis listener error: {e}")


# ======================================================
# COLLECTORS
# ======================================================
def start_collectors():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    intents = DiscordCollector.create_intents()

    discord = DiscordCollector(
        discord_cfg["token"],
        redis,
        intents
    )

    discourse = DiscourseCollector(
        discourse_cfg["url"],
        discourse_cfg["api_key"],
        discourse_cfg["api_user"],
        redis
    )

    async def runner():
        await asyncio.gather(
            discord.run_collector(),
            discourse.run()
        )

    logger.info("🚀 Starting collectors...")
    loop.run_until_complete(runner())


# ======================================================
# STARTUP
# ======================================================
@app.on_event("startup")
async def startup_event():
    logger.info("🔥 Backend + collectors starting")

    # Get event loop for Redis listener
    loop = asyncio.get_event_loop()
    
    # Start collectors in thread
    threading.Thread(target=start_collectors, daemon=True).start()
    logger.info("✅ Collectors thread started")
    
    # Start Redis listener in thread (NON-BLOCKING!)
    threading.Thread(target=redis_listener_thread, args=(loop,), daemon=True).start()
    logger.info("✅ Redis listener thread started")

    logger.info("🌐 UI running on http://localhost:8000")


# ======================================================
# API ENDPOINTS (BEFORE STATIC FILES!)
# ======================================================
@app.get("/api/messages")
def get_messages():
    try:
        messages = redis.get_recent_messages()
        logger.debug(f"API /api/messages returned {len(messages)} messages")
        return messages
    except Exception as e:
        logger.error(f"Error in /api/messages: {e}")
        return []


@app.get("/api/statistics")
def get_stats():
    try:
        stats = redis.get_statistics()
        logger.debug(f"API /api/statistics: {stats}")
        return stats
    except Exception as e:
        logger.error(f"Error in /api/statistics: {e}")
        return {
            "total_messages": 0,
            "live_messages": 0,
            "historical_messages": 0,
            "discord_live": 0,
            "discourse_live": 0,
            "messages_last_hour": 0,
            "active_users_last_hour": 0
        }


@app.get("/api/health")
def health_check():
    """Health check endpoint with debug info"""
    import time
    try:
        redis_ping = redis.redis_client.ping()
        stats = redis.get_statistics()
        
        return {
            "status": "ok",
            "websocket_clients": len(clients),
            "timestamp": time.time(),
            "redis_connected": redis_ping,
            "live_messages": stats.get("live_messages", 0),
            "historical_messages": stats.get("historical_messages", 0),
            "total_messages": stats.get("total_messages", 0)
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


# ======================================================
# STATIC FILES - FRONTEND (MUST BE AT THE END!)
# ======================================================
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
    logger.info(f"✅ Frontend mounted from {FRONTEND_DIR}")
else:
    logger.warning(f"⚠️ Frontend directory not found at: {FRONTEND_DIR}")
    
    @app.get("/")
    async def root_fallback():
        return {
            "error": "Frontend not found",
            "expected_path": FRONTEND_DIR,
            "api_endpoints": {
                "messages": "/api/messages",
                "statistics": "/api/statistics",
                "health": "/api/health",
                "websocket": "/ws"
            }
        }