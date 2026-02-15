import subprocess
import time
import sys
import os
import logging
from logging.handlers import RotatingFileHandler

# --- CONFIGURATION ---
REPO_BRANCH = "main"
CHECK_INTERVAL = 10

# --- Logger (standalone, not JoLogger — supervisor runs separately) ---
log = logging.getLogger("Supervisor")
log.setLevel(logging.INFO)
fmt = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s", "%Y-%m-%d %H:%M:%S")
console = logging.StreamHandler()
console.setFormatter(fmt)
log.addHandler(console)

LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
fh = RotatingFileHandler(os.path.join(LOG_DIR, "supervisor.log"), maxBytes=1*1024*1024, backupCount=2)
fh.setFormatter(fmt)
log.addHandler(fh)


def run_command(command):
    try:
        result = subprocess.check_output(command, text=True, stderr=subprocess.STDOUT).strip()
        return result
    except subprocess.CalledProcessError as e:
        log.error("Command '%s' failed: %s", ' '.join(command), e.output)
        return None


def get_commit_hash(target):
    return run_command(["git", "rev-parse", target])


def pull_changes():
    log.info("Downloading updates...")
    run_command(["git", "fetch", "origin"])
    run_command(["git", "reset", "--hard", f"origin/{REPO_BRANCH}"])
    log.info("Installing requirements...")
    run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])


def start_server():
    log.info("Starting Flask Server...")
    return subprocess.Popen([sys.executable, "run.py"])


def main():
    log.info("Trying to activate keepAwake...")
    os.system("keepAwake")
    log.info("Supervisor started. Monitoring for updates...")

    pull_changes()
    current_process = start_server()

    while True:
        try:
            if current_process.poll() is not None:
                log.warning("Server crashed! Restarting...")
                current_process = start_server()
                time.sleep(CHECK_INTERVAL)
                continue

            run_command(["git", "fetch", "origin"])
            local_hash = get_commit_hash("HEAD")
            remote_hash = get_commit_hash(f"origin/{REPO_BRANCH}")

            if local_hash and remote_hash and local_hash != remote_hash:
                log.info("Update detected! Local: %s Remote: %s", local_hash[:7], remote_hash[:7])
                log.info("Stopping server...")
                current_process.terminate()
                try:
                    current_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    log.warning("Force killing server.")
                    current_process.kill()

                pull_changes()
                current_process = start_server()

            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            log.info("Shutting down...")
            current_process.terminate()
            break
        except Exception as e:
            log.error("Supervisor error: %s", e)
            time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
