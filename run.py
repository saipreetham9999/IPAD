from brain import create_app # Import create_app from the brain package
# import threading # No longer needed here as Flask's app.run handles the main loop

# CONFIGURATION
PORT = 8080

app = create_app() # Create the Flask app instance

if __name__ == '__main__':
    # 1. Start Server
    print("🚀 Starting Server...") # This log will now appear
    # host='0.0.0.0' is REQUIRED for external connections
    app.run(host='0.0.0.0', port=PORT, debug=False)
