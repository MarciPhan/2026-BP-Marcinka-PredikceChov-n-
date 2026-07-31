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
        pip_bin = os.path.join(venv_dir, "Scripts", "pip.exe")
    else:
        python_bin = os.path.join(venv_dir, "bin", "python3")
        pip_bin = os.path.join(venv_dir, "bin", "pip")

    if not os.path.exists(python_bin):
        # Fallback to python
        python_bin = os.path.join(venv_dir, "bin", "python")

    print("Installing dependencies...")
    subprocess.run([pip_bin, "install", "-q", "-r", "requirements.txt"])

    # 2. Config check
    if not os.path.exists(".env"):
        print_color("Error: .env missing", "1;31")
        if os.path.exists(".env.example"):
            print("Copy .env.example to .env and fill in BOT_TOKEN")
        sys.exit(1)

    # 3. Redis check
    redis_running = not check_port_free(6379)
    if not redis_running:
        print_color("Warning: Redis on port 6379 not detected. CommunityMetrics will fallback to FakeRedis.", "1;33")
    else:
        print_color("Redis detected.", "1;32")

    # 4. Port prep
    dashboard_port = int(os.getenv("DASHBOARD_PORT", "8092"))
    if not check_port_free(dashboard_port):
        kill_processes_on_port(dashboard_port)
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

    bot_proc = run_service("Discord Bot", [python_bin, "bot/main.py"], env, "bot.log")
    web_proc = run_service("Web Dashboard", [python_bin, "-m", "uvicorn", "web.backend.main:app", "--host", "0.0.0.0", "--port", str(dashboard_port)], env, "web.log")

    time.sleep(3)
    if bot_proc.poll() is None and web_proc.poll() is None:
        print_color("CommunityMetrics is up!", "1;32")
        print(f"  Dashboard: http://localhost:{dashboard_port}")
        print("  Logs are in bot.log and web.log")
        print("\nPress Ctrl+C to stop services...")
        try:
            bot_proc.wait()
            web_proc.wait()
        except KeyboardInterrupt:
            print("\nStopping services...")
            bot_proc.terminate()
            web_proc.terminate()
            bot_proc.wait()
            web_proc.wait()
            print("Stopped.")
    else:
        print_color("Startup failed. Check bot.log and web.log.", "1;31")

if __name__ == "__main__":
    main()
