import threading
from bus.JoLogger import get_logger

log = get_logger("JoBus")


class JoBus:

    def __init__(self):
        self.subscribers = {}
        self._lock = threading.Lock()

    def subscribe(self, event_name, callback):
        with self._lock:
            if event_name not in self.subscribers:
                self.subscribers[event_name] = []
            self.subscribers[event_name].append(callback)

    def publish(self, event_name, payload=None):
        with self._lock:
            callbacks = list(self.subscribers.get(event_name, []))
        for callback in callbacks:
            try:
                callback(payload)
            except Exception as e:
                log.error("Event '%s' handler %s failed: %s", event_name, callback.__name__, e)
