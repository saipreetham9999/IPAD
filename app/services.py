import socket
import qrcode
import io


def get_local_ip():
    """Finds the iPad's WiFi IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


def show_connection_qr(port):
    """Generates ASCII QR Code in terminal"""
    ip = get_local_ip()
    url = f"http://{ip}:{port}"

    print("\n" + "=" * 40)
    print(f"🧠 BRAIN CLUSTER ONLINE")
    print(f"👉 Scan with Poco: {url}")
    print("=" * 40)

    qr = qrcode.QRCode()
    qr.add_data(url)
    qr.make(fit=True)

    f = io.StringIO()
    qr.print_ascii(out=f)
    f.seek(0)
    print(f.read())
    print("=" * 40 + "\n")