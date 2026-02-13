#!/bin/sh

# Prevent iPad from sleeping
keepAwake

BRANCH="main"



# --- OUTER LOOP: Handles Updates & Restarts ---
while true; do
    echo "========================================"
    echo "♻️ Syncing with GitHub..."

    # 1. Force Sync
    lg2 fetch origin
    lg2 reset --hard origin/$BRANCH
    lg2 pull origin $BRANCH

    # 2. Update Dependencies
    pip install -r requirements.txt

    # 3. Start Server in Background
    echo "🚀 Starting Flask App..."
    # The '&' puts python in the background so the script continues
    python app.py &

    # Capture the Process ID (PID) so we can kill it later
    SERVER_PID=$!
    echo "✅ Server running (PID: $SERVER_PID). Monitoring for updates..."

    # --- INNER LOOP: Monitors for Changes ---
    while true; do
        # Wait 60 seconds before checking
        sleep 60

        # Check remote without merging yet
        lg2 fetch origin

        # Compare Local Commit vs Remote Commit
        LOCAL=$(lg2 rev-parse HEAD)
        REMOTE=$(lg2 rev-parse origin/$BRANCH)

        if [ "$LOCAL" != "$REMOTE" ]; then
            echo "🔄 Update Detected! (Remote: $REMOTE)"
            echo "🛑 Stopping current server..."

            # Kill the Python server
            kill $SERVER_PID

            # Wait a moment for it to close
            wait $SERVER_PID 2>/dev/null

            # Break inner loop -> Go back to top of Outer Loop
            break
        fi

        # Optional: Check if server crashed on its own
        # 'kill -0' checks if a process exists without actually killing it
        if ! kill -0 $SERVER_PID 2>/dev/null; then
            echo "⚠️ Server crashed unexpectedly! Restarting..."
            break
        fi

        echo -n "." # Print a dot to show it's alive
    done
done