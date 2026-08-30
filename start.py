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
    print(f"Cleaning up port {port}...")
    try:
        if platform.system() == "Windows":
            result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.strip().split()
                    pid = parts[-1]
                    subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)
        else:
            # lsof works on Mac and Linux
            subprocess.run(["lsof", "-t", "-i", f":{port}", "-s", "TCP:LISTEN"], 
                           stdout=subprocess.PIPE).stdout.decode('utf-8')
            os.system(f"lsof -t -i:{port} | xargs kill -9 2>/dev/null")
    except Exception as e:
        print(f"Cleanup error (ignoring): {e}")

def run_service(name, cmd_args, env, log_file):
    print_color(f"Starting {name}...", "1;34")
    with open(log_file, "w") as f:
        # We don't wait for it to finish, it runs in background
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
        # Fallback to python
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

    # 2. Config check
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            import shutil
            shutil.copy(".env.example", ".env")
            print_color("Warning: .env missing, automatically copied from .env.example", "1;33")
            print_color("Please edit .env to add your actual BOT_TOKEN if necessary.", "1;33")
        else:
            print_color("Error: Both .env and .env.example are missing.", "1;31")
            sys.exit(1)

    # 3. Redis check
    redis_running = not check_port_free(6379)
    if not redis_running:
        print_color("Warning: Redis on port 6379 not detected. CommunityMetrics will fallback to FakeRedis.", "1;33")
        os.environ["USE_FAKEREDIS"] = "true"
    else:
        print_color("Redis detected.", "1;32")

    # 4. Port prep
    dashboard_port = int(os.getenv("DASHBOARD_PORT", "8093"))
    if not check_port_free(dashboard_port):
        kill_processes_on_port(dashboard_port)
        time.sleep(1)

    if has_npm and not check_port_free(5173):
        kill_processes_on_port(5173)
        time.sleep(1)

    # 5. Launch
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.abspath(os.path.dirname(__file__))
    env["DASHBOARD_PORT"] = str(dashboard_port)

    # Load .env manually for child processes just in case
    with open(".env") as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                env[k.strip()] = v.strip().strip("'").strip('"')

    def update_env_file(key, value):
        lines = []
        if os.path.exists(".env"):
            with open(".env", "r", encoding="utf-8") as f:
                lines = f.readlines()
        with open(".env", "w", encoding="utf-8") as f:
            for line in lines:
                if not line.startswith(f"{key}="):
                    f.write(line)
            f.write(f"{key}={value}\n")

    if not env.get("BOT_TOKEN") and not os.getenv("TOKEN_PROMPTED_ALREADY"):
        print("\n" + "="*60)
        print_color(" CHYBA: BOT_TOKEN není nastaven v .env souboru!", "1;31")
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
