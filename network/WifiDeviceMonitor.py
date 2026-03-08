import threading
import time
import json
import subprocess
import socket
from datetime import datetime, timedelta
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

def format_duration(duration: timedelta) -> str:
    """Formats a timedelta object into a human-readable string like '2h 15m 10s'."""
    parts = []
    total_seconds = int(duration.total_seconds())
    
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    if days > 0: parts.append(f"{days}d")
    if hours > 0: parts.append(f"{hours}h")
    if minutes > 0: parts.append(f"{minutes}m")
    if seconds > 0 or not parts: parts.append(f"{seconds}s")
    
    return " ".join(parts)

class WifiDeviceMonitor(AraService):
    """
    Monitors the local network, sends immediate alerts with duration tracking,
    and provides a daily summary report.
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
        self.last_change_timestamp = {}
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
        
        now = datetime.now()
        for device in self.devices:
            self.device_status[device['name']] = "unknown"
            self.last_change_timestamp[device['name']] = now
            
        self.last_report_date = now.date()
        
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        
        self.bus.subscribe("wifi.status_request", self._handle_status_request)
        log.info(f"Started. Monitoring {len(self.devices)} devices on network {self.network_base}.x. Scan interval: 20s")

    def stop(self):
        self._running = False
        if self._thread: self._thread.join(timeout=5)
        self._status = "stopped"
        log.info("Stopped.")

    def status(self):
        return self._status

    def _is_fping_installed(self):
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
        log.info(f"Scanning network {self.network_base}.x with fping...")
        try:
            command = ["fping", "-a", "-g", f"{self.network_base}.1", f"{self.network_base}.254"]
            result = subprocess.run(command, capture_output=True, text=True, timeout=15)
            online_ips = set(result.stdout.strip().split('\n'))
            if '' in online_ips: online_ips.remove('')
            log.info(f"fping scan found {len(online_ips)} online hosts.")
            return online_ips
        except (subprocess.TimeoutExpired, FileNotFoundError):
            log.error(f"fping scan failed or timed out.")
            return set()

    def _log_event(self, device_name: str, status: str, duration_str: str):
        timestamp = datetime.now()
        self.event_log.append({
            "timestamp": timestamp, 
            "device": device_name, 
            "status": status,
            "duration": duration_str
        })
        log.info(f"Logged event: {device_name} is {status} (was {duration_str})")

    def _send_daily_report(self):
        log.info("Generating daily Wi-Fi status report.")
        report = "--- Daily Wi-Fi Report ---\n\n"
        if not self.event_log:
            report += "No connection changes detected in the last 24 hours."
        else:
            for event in self.event_log:
                ts = event['timestamp'].strftime('%H:%M:%S')
                report += f"[{ts}] {event['device']} became {event['status']} (after {event['duration']})\n"
        
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
                        now = datetime.now()
                        duration = now - self.last_change_timestamp[name]
                        duration_str = format_duration(duration)
                        
                        self.device_status[name] = current_status
                        self.last_change_timestamp[name] = now
                        self._log_event(name, current_status, duration_str)
                        
                        message = ""
                        if current_status == "Online":
                            message = f"Device Connected: {name} ({ip})\n(Was offline for {duration_str})"
                        elif previous_status == "Online":
                            message = f"Device Disconnected: {name} ({ip})\n(Was online for {duration_str})"
                        
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
            last_change = self.last_change_timestamp.get(name)
            
            report += f"Device: {name}\n  IP Address: {ip}\n  Status: {status}\n"
            if last_change and status != "unknown":
                duration = datetime.now() - last_change
                report += f"  In current state for: {format_duration(duration)}\n"
            report += "\n"
        
        self.telegram_bot.send_message_to_chat(self.WIFI_STATUS_GROUP_ID, report)
