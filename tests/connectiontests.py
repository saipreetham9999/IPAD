"""
BRAIN Integration Tests
Hits real Brain running on iPad.
Brain must be running before executing these tests.
"""

import requests
import time
import pytest

BRAIN_URL = "http://192.168.0.183:8080"
TIMEOUT = 5

DEVICE_1 = {
    "device_name": "Integration Test Device 1",
    "device_type": "test",
    "capabilities": ["screen"]
}

DEVICE_2 = {
    "device_name": "Integration Test Device 2",
    "device_type": "android",
    "capabilities": ["camera", "screen"]
}


# ── helpers ───────────────────────────────────────────────────────────
def connect(device: dict) -> requests.Response:
    return requests.post(f"{BRAIN_URL}/api/connect", json=device, timeout=TIMEOUT)

def heartbeat(device_name: str) -> requests.Response:
    return requests.post(f"{BRAIN_URL}/api/heartbeat", json={"device_name": device_name}, timeout=TIMEOUT)

def events(device_name: str) -> requests.Response:
    return requests.get(f"{BRAIN_URL}/api/events", params={"device_name": device_name}, timeout=TIMEOUT)

def disconnect(device_name: str) -> requests.Response:
    return requests.post(f"{BRAIN_URL}/api/disconnect", json={"device_name": device_name}, timeout=TIMEOUT)

def status() -> requests.Response:
    return requests.get(f"{BRAIN_URL}/api/status", timeout=TIMEOUT)

def report(data: dict) -> requests.Response:
    return requests.post(f"{BRAIN_URL}/api/report", json=data, timeout=TIMEOUT)


# ── Phase 1 — Brain is alive ──────────────────────────────────────────
class TestBrainAlive:

    def test_brain_reachable(self):
        """Brain must be running and reachable."""
        r = requests.get(f"{BRAIN_URL}/", timeout=TIMEOUT)
        assert r.status_code == 200
        data = r.json()
        assert data["brain"] == "online"
        print(f"\n  Brain online. Children: {data['children_connected']}")

    def test_status_endpoint(self):
        """Status endpoint returns correct shape."""
        r = status()
        assert r.status_code == 200
        data = r.json()
        assert "status" in data
        assert data["status"] == "online"
        assert "children" in data
        print(f"\n  Status ok. Connected: {len(data['children'])}")


# ── Phase 2 — Connection lifecycle ───────────────────────────────────
class TestConnectionLifecycle:

    def setup_method(self):
        """Clean up before each test."""
        disconnect(DEVICE_1["device_name"])
        disconnect(DEVICE_2["device_name"])
        time.sleep(0.5)

    def teardown_method(self):
        """Clean up after each test."""
        disconnect(DEVICE_1["device_name"])
        disconnect(DEVICE_2["device_name"])

    def test_device_connects(self):
        """Device can connect and Brain registers it."""
        r = connect(DEVICE_1)
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "connected"
        assert data["device"] == DEVICE_1["device_name"]
        print(f"\n  Connected: {data['device']}")

    def test_device_appears_in_status(self):
        """Connected device appears in /api/status."""
        connect(DEVICE_1)
        time.sleep(0.3)
        r = status()
        names = [c["device_name"] for c in r.json()["children"]]
        assert DEVICE_1["device_name"] in names
        print(f"\n  Device in status: {names}")

    def test_reject_missing_fields(self):
        """Connection rejected if device_name or device_type missing."""
        r = requests.post(f"{BRAIN_URL}/api/connect", json={"device_name": "NoType"}, timeout=TIMEOUT)
        assert r.status_code == 400
        assert r.json()["status"] == "rejected"
        print(f"\n  Correctly rejected: {r.json()['reason']}")

    def test_heartbeat_keeps_alive(self):
        """Heartbeat returns ok for connected device."""
        connect(DEVICE_1)
        r = heartbeat(DEVICE_1["device_name"])
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
        print(f"\n  Heartbeat ok")

    def test_heartbeat_unknown_device(self):
        """Heartbeat returns 404 for unknown device."""
        r = heartbeat("Ghost Device That Never Connected")
        assert r.status_code == 404
        assert r.json()["status"] == "unknown"
        print(f"\n  Unknown device correctly rejected")

    def test_device_disconnects(self):
        """Device can disconnect and is removed from Brain."""
        connect(DEVICE_1)
        time.sleep(0.3)
        r = disconnect(DEVICE_1["device_name"])
        assert r.status_code == 200
        assert r.json()["status"] == "disconnected"
        time.sleep(0.3)
        names = [c["device_name"] for c in status().json()["children"]]
        assert DEVICE_1["device_name"] not in names
        print(f"\n  Disconnected and removed from status")


# ── Phase 3 — Event queue ─────────────────────────────────────────────
# class TestEventQueue:
#
#     def setup_method(self):
#         disconnect(DEVICE_1["device_name"])
#         disconnect(DEVICE_2["device_name"])
#         time.sleep(0.5)
#
#     def teardown_method(self):
#         disconnect(DEVICE_1["device_name"])
#         disconnect(DEVICE_2["device_name"])
#
#     def test_events_empty_on_connect(self):
#         """Fresh connect returns empty events."""
#         connect(DEVICE_1)
#         time.sleep(0.3)
#         r = events(DEVICE_1["device_name"])
#         assert r.status_code == 200
#         data = r.json()
#         assert data["status"] == "ok"
#         assert isinstance(data["events"], list)
#         print(f"\n  Events on fresh connect: {data['events']}")

    def test_second_device_triggers_event(self):
        """When Device 2 connects, Device 1 gets notified via events."""
        connect(DEVICE_1)
        time.sleep(0.3)

        # clear any existing events for device 1
        events(DEVICE_1["device_name"])

        # device 2 connects
        connect(DEVICE_2)
        time.sleep(0.5)

        # device 1 polls events
        r = events(DEVICE_1["device_name"])
        assert r.status_code == 200
        data = r.json()
        event_types = [e.get("type") for e in data["events"]]
        assert "child.connected" in event_types
        print(f"\n  Device 1 got events: {event_types}")

    def test_events_cleared_after_poll(self):
        """Events queue clears after being read."""
        connect(DEVICE_1)
        time.sleep(0.3)
        connect(DEVICE_2)
        time.sleep(0.5)

        # first poll — gets events
        r1 = events(DEVICE_1["device_name"])
        assert len(r1.json()["events"]) > 0

        # second poll — should be empty
        r2 = events(DEVICE_1["device_name"])
        assert len(r2.json()["events"]) == 0
        print(f"\n  Queue cleared after poll — correct")

    def test_disconnect_triggers_event(self):
        """When Device 2 disconnects, Device 1 gets notified."""
        connect(DEVICE_1)
        connect(DEVICE_2)
        time.sleep(0.5)

        # clear events
        events(DEVICE_1["device_name"])

        # device 2 disconnects
        disconnect(DEVICE_2["device_name"])
        time.sleep(0.5)

        r = events(DEVICE_1["device_name"])
        event_types = [e.get("type") for e in r.json()["events"]]
        assert "child.disconnected" in event_types
        print(f"\n  Disconnect event received: {event_types}")

    def test_events_unknown_device(self):
        """Events for unknown device returns empty list not error."""
        r = events("Device That Never Existed")
        assert r.status_code == 200
        assert r.json()["events"] == []
        print(f"\n  Unknown device events handled gracefully")


# ── Phase 4 — Report ──────────────────────────────────────────────────
class TestReport:

    def test_report_accepted(self):
        """Brain accepts a report from child."""
        connect(DEVICE_1)
        time.sleep(0.3)
        r = report({
            "device_name": DEVICE_1["device_name"],
            "type": "frame",
            "data": "test_frame_data"
        })
        assert r.status_code == 200
        assert r.json()["status"] == "received"
        print(f"\n  Report accepted")

    def test_report_no_body(self):
        """Empty report returns error."""
        r = requests.post(f"{BRAIN_URL}/api/report", json=None,
                         headers={"Content-Type": "application/json"},
                         timeout=TIMEOUT)
        assert r.status_code == 400
        print(f"\n  Empty report correctly rejected")


# ── run all ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("BRAIN Integration Tests")
    print(f"Target: {BRAIN_URL}")
    print("=" * 60)
    print("\nMake sure Brain is running on iPad before running these.\n")

    pytest.main([__file__, "-v", "--tb=short"])