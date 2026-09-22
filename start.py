import os
import sys
import subprocess
import socket
import time
import venv
import platform

def print_color(text, color_code):
    # Cross-platform basic color support fallback
    if platform.system() == "Windows":
        os.system("color")
    print(f"\033[{color_code}m{text}\033[0m")

def check_port_free(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) != 0

def kill_processes_on_port(port):
    print(f"Checking port {port}...")
    try:
        if platform.system() == "Windows":
            result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.strip().split()
                    pid = parts[-1]
                    subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)
        else:
            pids = subprocess.run(["lsof", "-t", f"-i:{port}"], capture_output=True, text=True).stdout.strip()
            if pids:
                for pid in pids.split():
                    try:
                        os.kill(int(pid), 9)
                    except ProcessLookupError:
                        pass
            if not check_port_free(port):
                subprocess.run(["fuser", "-k", f"{port}/tcp"], capture_output=True)
        
        # Wait up to 2 seconds for port to clear
        for _ in range(10):
            if check_port_free(port):
                break
            time.sleep(0.2)
    except Exception as e:
        print(f"Cleanup error on port {port} (ignoring): {e}")

def run_service(name, cmd_args, env, log_file):
    print_color(f"Starting {name}...", "1;34")
    with open(log_file, "w") as f:
        proc = subprocess.Popen(
            cmd_args, 
            env=env, 
            stdout=f, 
            stderr=subprocess.STDOUT,
            cwd=os.path.abspath(os.path.dirname(__file__))
        )
        return proc

def main():
    print_color("Starting CommunityMetrics (Cross-Platform)...", "1;32")

    def update_env_file(key, value):
        lines = []
        if os.path.exists(".env"):
            with open(".env", "r", encoding="utf-8") as f:
                lines = f.readlines()
        found = False
        with open(".env", "w", encoding="utf-8") as f:
            for line in lines:
                if line.startswith(f"{key}="):
                    f.write(f"{key}={value}\n")
                    found = True
                else:
                    f.write(line)
            if not found:
                f.write(f"{key}={value}\n")

    # 1. Env & Deps
    venv_dir = os.path.abspath(".venv")
    if not os.path.exists(venv_dir):
        print("Creating virtual environment...")
        venv.create(venv_dir, with_pip=True)
    
    if platform.system() == "Windows":
        python_bin = os.path.join(venv_dir, "Scripts", "python.exe")
    else:
        python_bin = os.path.join(venv_dir, "bin", "python3")

    if not os.path.exists(python_bin):
        python_bin = os.path.join(venv_dir, "bin", "python")

    print("Installing dependencies...")
    subprocess.run([python_bin, "-m", "pip", "install", "-q", "-r", "requirements.txt"])

    npm_bin = "npm" if platform.system() != "Windows" else "npm.cmd"
    has_npm = True
    try:
        subprocess.run([npm_bin, "-v"], capture_output=True, check=True)
        print("Node.js detected. Installing docs dependencies...")
        subprocess.run([npm_bin, "install", "--no-audit", "--no-fund", "--silent"], check=False)
    except Exception:
        has_npm = False
        print_color("Warning: Node.js (npm) not found. VitePress documentation will not start.", "1;33")

    # 2. Config check & load
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            import shutil
            shutil.copy(".env.example", ".env")
            print_color("Warning: .env missing, automatically copied from .env.example", "1;33")
            print_color("Please edit .env to add your actual BOT_TOKEN if necessary.", "1;33")
        else:
            print_color("Error: Both .env and .env.example are missing.", "1;31")
            sys.exit(1)

    # Load .env into os.environ early so that DASHBOARD_PORT and all settings take effect
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.strip().split("=", 1)
                k = k.strip()
                v = v.strip().strip("'").strip('"')
                if k:
                    os.environ[k] = v

    # Validate DASHBOARD_PORT
    raw_port = os.getenv("DASHBOARD_PORT", "8092").strip()
    try:
        dashboard_port = int(raw_port)
        if not (1024 <= dashboard_port <= 65535):
            raise ValueError()
    except Exception:
        print_color(f" [WARNING] Neplatný DASHBOARD_PORT '{raw_port}', nastaven výchozí 8092.", "1;33")
        dashboard_port = 8092
        os.environ["DASHBOARD_PORT"] = "8092"
        update_env_file("DASHBOARD_PORT", "8092")

    # Kontrola a automatická oprava DISCORD_REDIRECT_URI vůči DASHBOARD_PORT
    redirect_uri = os.getenv("DISCORD_REDIRECT_URI", "").strip()
    expected_redirect = f"http://localhost:{dashboard_port}/auth/callback"
    if not redirect_uri:
        update_env_file("DISCORD_REDIRECT_URI", expected_redirect)
        os.environ["DISCORD_REDIRECT_URI"] = expected_redirect
    elif "localhost" in redirect_uri or "127.0.0.1" in redirect_uri:
        import urllib.parse
        parsed = urllib.parse.urlparse(redirect_uri)
        if parsed.port and parsed.port != dashboard_port:
            print("\n" + "="*60)
            print_color(" [AUTO-FIX] Zjištěna neshoda portů v konfiguraci!", "1;33")
            print_color(f" DASHBOARD_PORT je nastaven na: {dashboard_port}", "1;33")
            print_color(f" DISCORD_REDIRECT_URI měl port: {parsed.port}", "1;33")
            print_color(f" -> Automaticky synchronizuji DISCORD_REDIRECT_URI v .env na: {expected_redirect}", "1;32")
            print("="*60 + "\n")
            update_env_file("DISCORD_REDIRECT_URI", expected_redirect)
            os.environ["DISCORD_REDIRECT_URI"] = expected_redirect

    # 3. Redis check
    redis_running = not check_port_free(6379)
    if not redis_running:
        print("\n" + "="*60)
        print_color(" [CRITICAL WARNING] Redis na portu 6379 nenalezen!", "1;31")
        print_color(" CommunityMetrics přechází na FakeRedis (dočasná paměť).", "1;33")
        print_color(" WEB DASHBOARD NEUVIDÍ DATA OD BOTA BEZ SKUTEČNÉHO REDISU!", "1;33")
        print_color(" Prosím nainstalujte Redis (např. 'sudo apt install redis-server').", "1;33")
        print("="*60 + "\n")
        os.environ["USE_FAKEREDIS"] = "true"
    else:
        print_color("Redis detected.", "1;32")

    # 4. Port prep: Vyčistit aktivní port i případné staré porty z předchozího běhu
    ports_to_clean = {dashboard_port, 8092, 8093}
    for p in ports_to_clean:
        if not check_port_free(p):
            kill_processes_on_port(p)

    if has_npm and not check_port_free(5173):
        kill_processes_on_port(5173)

    # 5. Launch
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.abspath(os.path.dirname(__file__))
    env["DASHBOARD_PORT"] = str(dashboard_port)
    env["DISCORD_REDIRECT_URI"] = os.environ.get("DISCORD_REDIRECT_URI", expected_redirect)

    if not env.get("BOT_TOKEN") and not os.getenv("TOKEN_PROMPTED_ALREADY"):
        print("\n" + "="*60)
        print_color(" CHYBA: BOT_TOKEN není nastaven v .env souboru!", "1;31")
        print_color(" [INFO] Nezapomeňte v Discord Developer Portalu (záložka Bot) povolit všechna 3", "1;33")
        print_color("        Privileged Gateway Intents (Presence, Server Members, Message Content).", "1;33")
        print_color("        Jinak bot po spuštění okamžitě spadne!", "1;33")
        try:
            token = input(" Prosím, zadejte svůj Discord Bot Token (nebo stiskněte Enter pro přeskočení): ").strip()
        except KeyboardInterrupt:
            token = ""
        
        if not token:
            print_color(" Pokračuji bez tokenu. Discord bot nemusí fungovat.", "1;33")
        else:
            if len(token) < 50:
                print_color(" [WARNING] Zadaný text je příliš krátký na to, aby šlo o platný Discord token.", "1;33")
                print_color(" Pokračuji bez tokenu.", "1;33")
            else:
                update_env_file("BOT_TOKEN", token)
                
                env["BOT_TOKEN"] = token
                print_color(" Token byl úspěšně uložen do .env!", "1;32")
        print("="*60)
        os.environ["TOKEN_PROMPTED_ALREADY"] = "1"

    if not env.get("DISCORD_CLIENT_ID") and not os.getenv("TOKEN_PROMPTED_ALREADY"):
        print("\n" + "="*60)
        print_color(" CHYBA: DISCORD_CLIENT_ID není nastaven v .env souboru!", "1;31")
        try:
            client_id = input(" Prosím, zadejte svůj Discord OAuth2 Client ID (nebo stiskněte Enter pro přeskočení): ").strip()
        except KeyboardInterrupt:
            client_id = ""
        
        if not client_id:
            print_color(" Pokračuji bez Client ID. Discord přihlašování nemusí fungovat.", "1;33")
        else:
            update_env_file("DISCORD_CLIENT_ID", client_id)
            
            env["DISCORD_CLIENT_ID"] = client_id
            print_color(" Client ID bylo úspěšně uloženo do .env!", "1;32")
        print("="*60)
        os.environ["TOKEN_PROMPTED_ALREADY"] = "1"

    if not env.get("DISCORD_CLIENT_SECRET") and not os.getenv("TOKEN_PROMPTED_ALREADY"):
        print("\n" + "="*60)
        print_color(" CHYBA: DISCORD_CLIENT_SECRET není nastaven v .env souboru!", "1;31")
        try:
            client_secret = input(" Prosím, zadejte svůj Discord OAuth2 Client Secret (nebo stiskněte Enter pro přeskočení): ").strip()
        except KeyboardInterrupt:
            client_secret = ""
        
        if not client_secret:
            print_color(" Pokračuji bez Client Secret. Discord přihlašování nemusí fungovat.", "1;33")
        else:
            update_env_file("DISCORD_CLIENT_SECRET", client_secret)
            
            env["DISCORD_CLIENT_SECRET"] = client_secret
            print_color(" Client Secret byl úspěšně uložen do .env!", "1;32")
        print("="*60)
        os.environ["TOKEN_PROMPTED_ALREADY"] = "1"

    if not env.get("DISCOURSE_TOKEN") and not os.getenv("TOKEN_PROMPTED_ALREADY"):
        print("\n" + "="*60)
        print_color(" CHYBA: DISCOURSE_TOKEN není nastaven v .env souboru!", "1;31")
        try:
            token = input(" Prosím, zadejte svůj Discourse API Token (nebo stiskněte Enter pro přeskočení): ").strip()
        except KeyboardInterrupt:
            token = ""
        
        if not token:
            print_color(" Pokračuji bez tokenu. Synchronizace Discourse nemusí fungovat.", "1;33")
        else:
            update_env_file("DISCOURSE_TOKEN", token)
            
            env["DISCOURSE_TOKEN"] = token
            print_color(" Token byl úspěšně uložen do .env!", "1;32")
        print("="*60 + "\n")

    bot_proc = run_service("Discord Bot", [python_bin, "bot/main.py"], env, "bot.log")
    web_proc = run_service("Web Dashboard", [python_bin, "-m", "uvicorn", "web.backend.main:app", "--host", "0.0.0.0", "--port", str(dashboard_port)], env, "web.log")
    docs_proc = None
    if has_npm:
        docs_proc = run_service("Documentation", [npm_bin, "run", "docs:dev"], env, "docs.log")

    time.sleep(3)
    if bot_proc.poll() is None and web_proc.poll() is None:
        print("\n" + "="*60)
        print_color("   [SUCCESS] CommunityMetrics spuštěno úspěšně (Python)!   ", "1;32")
        print("="*60)
        print_color(f"   [WEB] Web Dashboard : http://localhost:{dashboard_port}", "1;36")
        if has_npm:
            print_color("   [DOCS] Dokumentace  : http://localhost:5173", "1;36")
        print_color("   [BOT] Discord Bot    : Běží (bot/main.py)", "1;36")
        print_color(f"   [DB] Redis Cache    : {'localhost:6379' if redis_running else 'FakeRedis (in-memory)'}", "1;36")
        print("-" * 60)
        print_color("   [DISCORD OAUTH2 POKYNY]:", "1;33")
        print("   V Discord Developer Portal -> OAuth2 -> Redirects musíte mít:")
        print_color(f"   -> http://localhost:{dashboard_port}/auth/callback", "1;32")
        print("-" * 60)
        print_color("   [INFO] Soubory s logy:", "1;33")
        print("      Web Dashboard : web.log")
        print("      Discord Bot    : bot.log")
        if has_npm:
            print("      Dokumentace    : docs.log")
        print("="*60)
        print("\nStiskněte Ctrl+C pro ukončení služeb...\n")
        try:
            bot_proc.wait()
            web_proc.wait()
            if docs_proc: docs_proc.wait()
        except KeyboardInterrupt:
            print("\nStopping services...")
            bot_proc.terminate()
            web_proc.terminate()
            if docs_proc: docs_proc.terminate()
            bot_proc.wait()
            web_proc.wait()
            if docs_proc: docs_proc.wait()
            print("Stopped.")
    else:
        print_color("Startup failed. Check bot.log and web.log.", "1;31")

if __name__ == "__main__":
    main()
