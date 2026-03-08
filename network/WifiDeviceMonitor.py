import threading
import time
import json
import os
import platform
from core.AraService import AraService
from bus.JoLogger import get_logger
from telegram.MinniTelegramBot import MiniTelegramBot

log = get_logger("WifiMonitor")

class WifiDeviceMonitor(AraService):
    """
    Monitors specific IP addresses on the network and reports their status changes
    to a dedicated Telegram group.
    """

    # --- Static Group ID for Wi-Fi Status Alerts ---
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

    def start(self):
        if self._status == "running":
            return
        
        if self.WIFI_STATUS_GROUP_ID == "YOUR_WIFI_GROUP_ID_HERE":
            log.warning("WIFI_STATUS_GROUP_ID is not set. Service will not start.")
            return
            
        if not self._load_devices():
            log.error("Could not load devices from config. Service not starting.")
            return
            
        self._status = "running"
        self._running = True
        
        # Initialize status for all devices
        for device in self.devices:
            self.device_status[device['name']] = "unknown"
            
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        log.info("Started. Monitoring %d devices. Scan interval: 15s", len(self.devices))

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        self._status = "stopped"
        log.info("Stopped.")

    def status(self):
        return self._status

    def _load_devices(self):
        try:
            with open(self.config_file, 'r') as f:
                self.devices = json.load(f)
            if not self.devices:
                log.warning("Device config file is empty.")
                return False
            return True
        except FileNotFoundError:
            log.error("Network devices config file not found at %s", self.config_file)
            return False
        except json.JSONDecodeError:
            log.error("Error decoding JSON from %s", self.config_file)
            return False

    def _ping_device(self, ip: str) -> bool:
        """
        Pings an IP address to check if it's online.
        Returns True if online, False otherwise.
        """
        param = "-n" if platform.system().lower() == "windows" else "-c"
        command = ["ping", param, "1", ip]
        
        # Use os.system for simplicity and to avoid subprocess complexities
        # Redirect output to null to keep logs clean
        response = os.system(f"{' '.join(command)} > {os.devnull} 2>&1")
        return response == 0

    def _monitor_loop(self):
        while self._running:
            for device in self.devices:
                name = device["name"]
                ip = device["ip"]

                is_online = self._ping_device(ip)
                current_status = "online" if is_online else "offline"
                previous_status = self.device_status.get(name)

                if current_status != previous_status:
                    self.device_status[name] = current_status
                    log.info("Device '%s' status changed to %s", name, current_status)
                    
                    message = ""
                    if current_status == "online":
                        message = f"✅ Wi-Fi Device Connected: {name} ({ip})"
                    else:
                        # We only want to send the "disconnected" message if it was previously online
                        if previous_status == "online":
                            message = f"❌ Wi-Fi Device Disconnected: {name} ({ip})"
                    
                    if message:
                        # Send to the dedicated Wi-Fi status group
                        self.telegram_bot.send_message_to_chat(self.WIFI_STATUS_GROUP_ID, message)
            
            # Check every 15 seconds
            time.sleep(15)
