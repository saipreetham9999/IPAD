import datetime
import threading
import time
import json
import subprocess
import re
import socket
from core.AraService import AraService
from bus.JoLogger import get_logger
from telegram.MinniTelegramBot import MiniTelegramBot

log = get_logger("WifiMonitor")

def get_network_range():
    """Determines the local network range (e.g., 192.168.1.0/24)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # Doesn't need to be reachable
            s.connect(("8.8.8.8", 80))
            ip_address = s.getsockname()[0]
            # Assumes a /24 subnet, which is standard for home networks
            network_base = ".".join(ip_address.split('.')[:-1])
            return f"{network_base}.0/24"
    except Exception:
        # Fallback for environments where the above fails
        return "192.168.0.0/24"

class WifiDeviceMonitor(AraService):
    """
    Monitors the local network using nmap to discover online devices and reports
    status changes for specific IPs.
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
        self.network_range = get_network_range()

    def start(self):
        if self._status == "running": return
        if not self._is_nmap_installed():
            log.error("nmap is not installed or not in system PATH. Please install it from https://nmap.org. Service not starting.")
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
        log.info(f"Started. Monitoring for devices on network {self.network_range}. Scan interval: 20s")

    def stop(self):
        self._running = False
        if self._thread: self._thread.join(timeout=5)
        self._status = "stopped"
        log.info("Stopped.")

    def status(self):
        return self._status

    def _is_nmap_installed(self):
        """Checks if nmap is installed and available in the system's PATH."""
        try:
            subprocess.run(["nmap", "-v"], capture_output=True, check=True)
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
        """Scans the network with nmap and returns a set of online IP addresses."""
        log.info(f"Scanning network {self.network_range} with nmap...")
        try:
            # -sn: Ping Scan - disables port scan
            # -T4: Aggressive timing template for faster scans
            command = ["nmap", "-sn", "-T4", self.network_range]
            result = subprocess.run(command, capture_output=True, text=True, timeout=60)
            
            # Regex to find all IP addresses in the nmap output
            ip_addresses = re.findall(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", result.stdout)
            
            # The first IP found is usually the gateway, the rest are hosts.
            # We convert to a set for efficient lookup.
            online_ips = set(ip_addresses[1:])
            log.info(f"nmap scan found {len(online_ips)} online hosts.")
            return online_ips
        except (subprocess.TimeoutExpired, FileNotFoundError):
            log.error(f"nmap scan failed or timed out.")
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
