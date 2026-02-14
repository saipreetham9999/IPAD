# FILE: app.py
import socket
import threading
import time
import webbrowser
from flask import Flask, render_template, jsonify
from zeroconf import ServiceInfo, Zeroconf

app = Flask(__name__)

# --- CONFIGURATION ---
HOSTNAME = "brain.local."  # The custom domain name
PORT = 8080  # The web port


# --- ROUTES ---
@app.route('/')
def home():
    """The Dashboard UI"""
    return render_template('index.html')


@app.route('/api/status')
def status():
    """API for Poco to check connection"""
    return jsonify({"status": "online", "system": "Brain-Master"})


# --- SYSTEM UTILITIES ---

def get_local_ip():
    """Finds the actual WiFi IP address (e.g., 192.168.1.5)"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


def start_mdns():
    """Broadcasts 'brain.local' to the network"""
    my_ip = get_local_ip()
    print(f"📡 Broadcasting {HOSTNAME} at {my_ip}:{PORT}")

    info = ServiceInfo(
        "_http._tcp.local.",
        "BrainSystem._http._tcp.local.",
        addresses=[socket.inet_aton(my_ip)],
        port=PORT,
        properties={'version': '1.0.0'},
        server=HOSTNAME
    )

    zeroconf = Zeroconf()
    zeroconf.register_service(info)

    # Keep broadcasting forever
    try:
        while True:
            time.sleep(60)
    except:
        zeroconf.unregister_service(info)
        zeroconf.close()


def open_browser():
    """Opens the dashboard automatically"""
    time.sleep(2)
    webbrowser.open(f"http://localhost:{PORT}")


if __name__ == '__main__':
    # 1. Start DNS Broadcast in background
    threading.Thread(target=start_mdns, daemon=True).start()

    # 2. Open Browser in background
    threading.Thread(target=open_browser, daemon=True).start()

    # 3. Start Flask Server
    # host='0.0.0.0' is CRITICAL for Poco to connect
    app.run(host='0.0.0.0', port=PORT, debug=False)