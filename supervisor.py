import subprocess
import time
import sys
import os

# --- CONFIGURATION ---
REPO_BRANCH = "main"
CHECK_INTERVAL = 10  # Seconds between checks

def run_command(command):
    """Runs a shell command and returns the output."""
    try:
        # Using a list of args is safer than shell=True
        result = subprocess.check_output(command, text=True, stderr=subprocess.STDOUT).strip()
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command '{' '.join(command)}': {e.output}")
        return None

def get_commit_hash(target):
    """Gets the git commit hash for local or remote."""
    # Note: a-shell might not support all git commands.
    # 'git rev-parse' is a standard and reliable command.
    return run_command(["git", "rev-parse", target])

def pull_changes():
    """Pulls code and updates dependencies."""
    print("\n♻️  Downloading updates...")
    run_command(["git", "fetch", "origin"])
    run_command(["git", "reset", "--hard", f"origin/{REPO_BRANCH}"])
    
    print("📦 Installing requirements...")
    run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def start_server():
    """Starts run.py as a subprocess."""
    print("🚀 Starting Flask Server...")
    # sys.executable ensures we use the same Python that runs this launcher
    return subprocess.Popen([sys.executable, "run.py"])

def main():
    # 1. Prevent Sleep (a-shell specific command)
    print("Trying to activate 'keepAwake' for a-shell...")
    os.system("keepAwake") 
    print("✅ Supervisor Started. Monitoring for updates...")

    # 2. Initial Update and Start
    pull_changes()
    current_process = start_server()

    while True:
        try:
            # --- CHECK 1: Is the server still running? ---
            if current_process.poll() is not None:
                print("\n⚠️  Server crashed! Restarting immediately...")
                current_process = start_server()
                # Wait a moment before starting the check cycle again
                time.sleep(CHECK_INTERVAL)
                continue

            # --- CHECK 2: Are there updates on GitHub? ---
            print(".", end="", flush=True) # Heartbeat to show it's alive
            
            # Fetch origin without merging to see if there is a change
            run_command(["git", "fetch", "origin"])
            
            local_hash = get_commit_hash("HEAD")
            remote_hash = get_commit_hash(f"origin/{REPO_BRANCH}")

            if local_hash and remote_hash and local_hash != remote_hash:
                print(f"\n🔄 Update Detected!")
                print(f"   Local:  {local_hash[:7]}")
                print(f"   Remote: {remote_hash[:7]}")

                # Stop the old server gracefully
                print("🛑 Stopping server...")
                current_process.terminate()
                try:
                    current_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    print("Server did not stop gracefully. Forcing kill.")
                    current_process.kill()

                # Update code
                pull_changes()

                # Restart
                current_process = start_server()
            
            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            print("\n👋 Shutting down...")
            current_process.terminate()
            break
        except Exception as e:
            print(f"\n❌ An error occurred in the supervisor loop: {e}")
            time.sleep(CHECK_INTERVAL) # Wait before retrying

if __name__ == "__main__":
    main()
