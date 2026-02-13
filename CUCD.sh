#!/bin/sh

# 1. Prevent iPad sleep
keepAwake

BRANCH="main"

echo "✅ Starting Continuous Deployment Server..."

while true; do
    # --- UPDATE SECTION ---
    echo "♻️ Checking for updates..."

    # Force sync with GitHub
    lg2 fetch origin
    lg2 reset --hard origin/$BRANCH
    lg2 pull origin $BRANCH

    # Update libraries (in case requirements.txt changed)
    pip install -r requirements.txt

    # --- SERVER SECTION ---
    echo "🚀 Launching Flask..."

    # Run Python in background
    python app.py &

    # --- MONITOR LOOP ---
    # We loop here and check git every 60 seconds
    while true; do
        sleep 60

        # Check if remote has changes
        lg2 fetch origin
        LOCAL=$(lg2 rev-parse HEAD)
        REMOTE=$(lg2 rev-parse origin/$BRANCH)

        if [ "$LOCAL" != "$REMOTE" ]; then
            echo "🔄 Update Detected! Restarting..."

            # THE FIX: Use 'killall' instead of 'kill $PID'
            # This is more reliable in a-Shell to stop the server
            killall python

            # Break inner loop to go back to Update Section
            break
        fi

        # Optional: Verify server is still running.
        # If 'python' process is gone, restart immediately.
        if ! pgrep python > /dev/null; then
             echo "⚠️ Server crashed! Restarting..."
             break
        fi

        echo -n "."
    done
done