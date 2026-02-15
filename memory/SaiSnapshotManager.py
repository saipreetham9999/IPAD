import os
from datetime import datetime
from core.AraService import AraService
from bus.JoLogger import get_logger

log = get_logger("SnapshotManager")

SNAPSHOT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "snapshots")
MAX_SNAPSHOTS = 50  # Keep last 50 snapshots to limit storage


class SaiSnapshotManager(AraService):
    """
    Phase 6 — saves frame data on anomaly detection.
    Stub: writes JSON metadata. Real version will save actual image frames.
    """

    def __init__(self, bus):
        self.bus = bus
        self._status = "stopped"

    def start(self):
        if self._status == "running":
            return
        self._status = "running"
        os.makedirs(SNAPSHOT_DIR, exist_ok=True)
        self.bus.subscribe("alert.triggered", self._on_alert)
        log.info("Started. Snapshots dir: %s", SNAPSHOT_DIR)

    def stop(self):
        self._status = "stopped"
        log.info("Stopped.")

    def status(self):
        return self._status

    def _on_alert(self, data: dict):
        """Save a snapshot when an alert is triggered."""
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            source = data.get("source", "unknown")
            filename = f"snap_{ts}_{source}.json"
            filepath = os.path.join(SNAPSHOT_DIR, filename)

            # Write alert metadata as snapshot
            import json
            with open(filepath, "w") as f:
                json.dump({
                    "timestamp": ts,
                    "source": source,
                    "alert": data,
                }, f)

            log.info("Snapshot saved: %s", filename)
            self._cleanup_old()

        except Exception as e:
            log.error("Failed to save snapshot: %s", e)

    def _cleanup_old(self):
        """Keep only the last MAX_SNAPSHOTS files."""
        try:
            files = sorted(
                [f for f in os.listdir(SNAPSHOT_DIR) if f.startswith("snap_")],
                reverse=True
            )
            for old_file in files[MAX_SNAPSHOTS:]:
                os.remove(os.path.join(SNAPSHOT_DIR, old_file))
                log.debug("Cleaned up old snapshot: %s", old_file)
        except Exception as e:
            log.error("Cleanup failed: %s", e)
