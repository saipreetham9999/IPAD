import threading
import time
from app import create_app
from app.services import show_connection_qr

# CONFIGURATION
PORT = 8080

app = create_app()

if __name__ == '__main__':
    # 1. Show QR Code after a slight delay
    threading.Timer(1.5, show_connection_qr, args=[PORT]).start()

    # 2. Start Server
    print("🚀 Starting Server...")
    # host='0.0.0.0' is REQUIRED for external connections
    app.run(host='0.0.0.0', port=PORT, debug=False)