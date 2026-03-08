import threading
import time
import json
import subprocess
import socket
from datetime import datetime
from core.AraService import AraService
from bus.JoLogger import get_logger
from telegram.MinniTelegramBot import MiniTelegramBot

log = get_logger("WifiMonitor")

def get_network_base():
    """Determines the local network base (e.g., 192.168.0)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ip_address = s.getsockname()[0]
            return ".".join(ip_address.split('.')[:-1])
    except Exception:
        return "192.168.0"

class WifiDeviceMonitor(AraService):
    """
    Monitors the local network using fping to discover online devices on an Ubuntu system.
    """

    WIFI_STATUS_GROUP_ID = "-1003893407216"

    def __init__(self, bus, telegram_bot: MiniTelegramBot, config_file: str):
        self.bus = bus
        self.telegram_bot = telegram_bot
        self.config_file = config_file
        self._status = "stopped"
        self._running = False
        self._thread = None
        self.devices = []
        self.device_status = {}
        self.event_log = []
        self.last_report_date = None
        self.network_base = get_network_base()

    def start(self):
        if self._status == "running": return
        if not self._is_fping_installed():
            log.error("fping is not installed. Please run 'sudo apt-get install fping'. Service not starting.")
            return
        if not self._load_devices(): return
            
        self._status = "running"
        self._running = True
        
        for device in self.devices:
            self.device_status[device['name']] = "unknown"
            
        self.last_report_date = datetime.now().date()
        
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        
        self.bus.subscribe("wifi.status_request", self._handle_status_request)
        log.info(f"Started. Monitoring for devices on network {self.network_base}.x. Scan interval: 20s")

    def stop(self):
        self._running = False
        if self._thread: self._thread.join(timeout=5)
        self._status = "stopped"
        log.info("Stopped.")

    def status(self):
        return self._status

    def _is_fping_installed(self):
        """Checks if fping is installed and available in the system's PATH."""
        try:
            subprocess.run(["fping", "-v"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _load_devices(self):
        try:
            with open(self.config_file, 'r') as f:
                self.devices = json.load(f)
            return bool(self.devices)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            log.error("Failed to load network devices config: %s", e)
            return False

    def _get_online_ips(self) -> set:
        """Scans the network with fping and returns a set of online IP addresses."""
        log.info(f"Scanning network {self.network_base}.x with fping...")
        try:
            # -a: show alive hosts
            # -g: generate target list from a range
            command = ["fping", "-a", "-g", f"{self.network_base}.1", f"{self.network_base}.254"]
            result = subprocess.run(command, capture_output=True, text=True, timeout=15)
            
            # fping prints alive hosts to stdout, one per line
            online_ips = set(result.stdout.strip().split('\n'))
            if '' in online_ips: online_ips.remove('') # Remove empty string if present
            
            log.info(f"fping scan found {len(online_ips)} online hosts.")
            return online_ips
        except (subprocess.TimeoutExpired, FileNotFoundError):
            log.error(f"fping scan failed or timed out.")
            return set()

    def _log_event(self, device_name: str, status: str):
        timestamp = datetime.now()
        self.event_log.append({"timestamp": timestamp, "device": device_name, "status": status})
        log.info(f"Logged event: {device_name} is {status}")

    def _send_daily_report(self):
        log.info("Generating daily Wi-Fi status report.")
        report = "--- Daily Wi-Fi Report ---\n\n"
        if not self.event_log:
            report += "No connection changes detected in the last 24 hours."
        else:
            for event in self.event_log:
                ts = event['timestamp'].strftime('%H:%M:%S')
                report += f"[{ts}] {event['device']} status changed to: {event['status']}\n"
        
        self.telegram_bot.send_message_to_chat(self.WIFI_STATUS_GROUP_ID, report)
        self.event_log.clear()
        self.last_report_date = datetime.now().date()
        log.info("Daily report sent and event log cleared.")

    def _monitor_loop(self):
        while self._running:
            now = datetime.now()
            
            if now.date() > self.last_report_date:
                self._send_daily_report()

            try:
                online_ips = self._get_online_ips()
                
                for device in self.devices:
                    name, ip = device["name"], device["ip"]
                    is_online = ip in online_ips
                    current_status = "Online" if is_online else "Offline"
                    previous_status = self.device_status.get(name)
                    
                    if current_status != previous_status:
                        self.device_status[name] = current_status
                        self._log_event(name, current_status)
                        
                        message = ""
                        if current_status == "Online":
                            message = f"Network Device Connected: {name} ({ip})"
                        elif previous_status == "Online":
                            message = f"Network Device Disconnected: {name} ({ip})"
                        
                        if message:
                            self.telegram_bot.send_message_to_chat(self.WIFI_STATUS_GROUP_ID, message)
            
            except Exception as e:
                log.error("Error in monitor loop: %s", e, exc_info=True)
            
            time.sleep(20)

    def _handle_status_request(self, data: dict):
        log.info("On-demand Wi-Fi status request received.")
        report = "--- Wi-Fi Network Status ---\n\n"
        for device in self.devices:
            name, ip = device["name"], device["ip"]
            status = self.device_status.get(name, "Unknown")
            report += f"Device: {name}\n  IP Address: {ip}\n  Status: {status}\n\n"
        
        self.telegram_bot.send_message_to_chat(self.WIFI_STATUS_GROUP_ID, report)
