from brain import create_app

# CONFIGURATION
PORT = 8080

app = create_app() # Create the Flask app instance

if __name__ == '__main__':
    # 1. Start Server
    print("🚀 Starting Server...") # This log will now appear
    # host='0.0.0.0' is REQUIRED for external connections
    app.run(host='0.0.0.0', port=PORT, debug=False)
