"""
Integration tests for Brain Network endpoints.
Run these against a live Brain instance (iPad).

Usage:
    # Against local Brain (port 8080)
    pytest tests/test_integration_endpoints.py -v

    # Against remote Brain
    pytest tests/test_integration_endpoints.py -v --brain-url http://192.168.1.100:8080

Requirements:
    - Brain must be running and accepting HTTP requests
    - pytest, requests
"""

import pytest
import requests
import time
import json
from typing import Dict, List

# Default Brain URL — override with --brain-url CLI flag
BRAIN_URL = "http://localhost:8080"


class BrainClient:
    """HTTP client for Brain endpoints."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def get_index(self) -> Dict:
        """GET /"""
        resp = self.session.get(f"{self.base_url}/")
        resp.raise_for_status()
        return resp.json()

    def get_status(self) -> Dict:
        """GET /api/status"""
        resp = self.session.get(f"{self.base_url}/api/status")
        resp.raise_for_status()
        return resp.json()

    def get_health(self) -> Dict:
        """GET /api/health"""
        resp = self.session.get(f"{self.base_url}/api/health")
        return resp.json(), resp.status_code

    def connect(self, device_name: str, device_type: str, capabilities: List[str] = None) -> Dict:
        """POST /api/connect"""
        payload = {
            "device_name": device_name,
            "device_type": device_type,
            "capabilities": capabilities or [],
        }
        resp = self.session.post(f"{self.base_url}/api/connect", json=payload)
        return resp.json(), resp.status_code

    def heartbeat(self, device_name: str) -> Dict:
        """POST /api/heartbeat"""
        payload = {"device_name": device_name}
        resp = self.session.post(f"{self.base_url}/api/heartbeat", json=payload)
        return resp.json(), resp.status_code

    def disconnect(self, device_name: str) -> Dict:
        """POST /api/disconnect"""
        payload = {"device_name": device_name}
        resp = self.session.post(f"{self.base_url}/api/disconnect", json=payload)
        return resp.json(), resp.status_code

    def get_events(self, device_name: str) -> Dict:
        """GET /api/events?device_name=..."""
        resp = self.session.get(f"{self.base_url}/api/events", params={"device_name": device_name})
        return resp.json(), resp.status_code

    def report(self, device_name: str, data: Dict) -> Dict:
        """POST /api/report"""
        payload = {"device_name": device_name, **data}
        resp = self.session.post(f"{self.base_url}/api/report", json=payload)
        return resp.json(), resp.status_code


# ── Test Fixtures ──────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def brain_url(request):
    """Get Brain URL from CLI or use default."""
    return request.config.getoption("--brain-url", default=BRAIN_URL)


@pytest.fixture(scope="session")
def brain(brain_url):
    """Create Brain client and verify connectivity."""
    client = BrainClient(brain_url)
    # Try to reach the Brain
    try:
        client.get_index()
        print(f"\n✅ Connected to Brain at {brain_url}")
    except requests.exceptions.ConnectionError:
        pytest.skip(f"Brain not running at {brain_url}")
    return client


def pytest_addoption(parser):
    """Add --brain-url option to pytest."""
    parser.addoption(
        "--brain-url",
        action="store",
        default=BRAIN_URL,
        help=f"Brain URL (default: {BRAIN_URL})",
    )


# ── Test Classes ───────────────────────────────────────────────────────

class TestBrainIndex:
    """Test GET / endpoint."""

    def test_index_returns_brain_status(self, brain):
        """Index should show Brain is online."""
        data = brain.get_index()
        assert data["brain"] == "online"
        assert "children_connected" in data
        assert "children" in data

    def test_index_children_count(self, brain):
        """Index children count should be non-negative."""
        data = brain.get_index()
        assert data["children_connected"] >= 0


class TestBrainHealth:
    """Test GET /api/health endpoint."""

    def test_health_endpoint_exists(self, brain):
        """Health endpoint should exist and return data."""
        data, status = brain.get_health()
        assert status in [200, 503]  # 200 if healthy, 503 if degraded
        assert "status" in data
        assert data["status"] in ["healthy", "degraded"]

    def test_health_returns_services(self, brain):
        """Health should list all services."""
        data, _ = brain.get_health()
        assert "services" in data
        assert isinstance(data["services"], dict)
        assert len(data["services"]) > 0

    def test_health_returns_ai_tier(self, brain):
        """Health should show current AI tier."""
        data, _ = brain.get_health()
        assert "ai_tier" in data
        assert "ai_processor" in data
        assert data["ai_tier"] in [0, 1, 2]


class TestBrainStatus:
    """Test GET /api/status endpoint."""

    def test_status_returns_brain_online(self, brain):
        """Status should show Brain is online."""
        data = brain.get_status()
        assert data["status"] == "online"
        assert "children" in data
        assert isinstance(data["children"], list)


class TestDeviceConnection:
    """Test device connect/heartbeat/disconnect flow."""

    @pytest.fixture
    def test_device_name(self):
        return f"test_device_{int(time.time())}"

    def test_connect_success(self, brain, test_device_name):
        """Device can connect to Brain."""
        data, status = brain.connect(
            device_name=test_device_name,
            device_type="android",
            capabilities=["camera", "audio"]
        )
        assert status == 200
        assert data["status"] == "connected"
        assert data["device"] == test_device_name

    def test_connect_without_device_name_fails(self, brain):
        """Connect without device_name should fail."""
        data, status = brain.connect(
            device_name="",
            device_type="android"
        )
        # Should fail or be rejected
        assert status != 200 or data["status"] == "rejected"

    def test_connect_without_device_type_fails(self, brain):
        """Connect without device_type should fail."""
        payload = {
            "device_name": f"test_{int(time.time())}",
            "device_type": "",
            "capabilities": [],
        }
        resp = brain.session.post(f"{brain.base_url}/api/connect", json=payload)
        data = resp.json()
        assert resp.status_code != 200 or data["status"] == "rejected"

    def test_heartbeat_after_connect(self, brain, test_device_name):
        """Device can send heartbeat after connect."""
        # Connect first
        brain.connect(test_device_name, "android")
        time.sleep(0.1)

        # Send heartbeat
        data, status = brain.heartbeat(test_device_name)
        assert status == 200
        assert data["status"] == "ok"

    def test_heartbeat_unknown_device(self, brain):
        """Heartbeat for unknown device should fail."""
        data, status = brain.heartbeat("nonexistent_device_xyz")
        assert status == 404
        assert data["status"] == "unknown"

    def test_disconnect_success(self, brain, test_device_name):
        """Device can disconnect cleanly."""
        # Connect first
        brain.connect(test_device_name, "android")
        time.sleep(0.1)

        # Disconnect
        data, status = brain.disconnect(test_device_name)
        assert status == 200
        assert data["status"] == "disconnected"

    def test_disconnect_unknown_device(self, brain):
        """Disconnect for unknown device should still succeed."""
        data, status = brain.disconnect("nonexistent_device_xyz")
        assert status == 200


class TestEventQueue:
    """Test /api/events endpoint (message routing)."""

    @pytest.fixture
    def connected_device(self, brain):
        """Connect a device and return its name."""
        name = f"event_test_{int(time.time())}"
        brain.connect(name, "android")
        time.sleep(0.1)
        yield name
        # Cleanup
        brain.disconnect(name)

    def test_get_events_empty_for_new_device(self, brain, connected_device):
        """New device should have empty event queue."""
        data, status = brain.get_events(connected_device)
        assert status == 200
        assert data["status"] == "ok"
        assert data["events"] == []

    def test_get_events_without_device_name_fails(self, brain):
        """Get events without device_name should fail."""
        resp = brain.session.get(f"{brain.base_url}/api/events")
        assert resp.status_code == 400

    def test_get_events_unknown_device(self, brain):
        """Get events for unknown device should return empty."""
        data, status = brain.get_events("nonexistent_xyz")
        assert status == 200
        assert data["events"] == []

    def test_events_cleared_after_poll(self, brain, connected_device):
        """Event queue should clear after polling."""
        # First poll
        data1, _ = brain.get_events(connected_device)
        initial_events = data1["events"]

        # Second poll (should still be empty)
        data2, _ = brain.get_events(connected_device)
        assert data2["events"] == []


class TestDataReport:
    """Test /api/report endpoint."""

    @pytest.fixture
    def reporting_device(self, brain):
        """Connect a device and return its name."""
        name = f"report_test_{int(time.time())}"
        brain.connect(name, "android")
        time.sleep(0.1)
        yield name
        brain.disconnect(name)

    def test_report_success(self, brain, reporting_device):
        """Device can send a report."""
        report_data = {
            "timestamp": int(time.time()),
            "sensor": "camera",
            "data": {"motion": 0.8, "frame_id": 123},
        }
        data, status = brain.report(reporting_device, report_data)
        assert status == 200
        assert data["status"] == "received"

    def test_report_without_body_fails(self, brain):
        """Report without JSON body should fail."""
        resp = brain.session.post(f"{brain.base_url}/api/report", json=None)
        assert resp.status_code == 400

    def test_report_empty_json_fails(self, brain):
        """Report with empty JSON should fail."""
        resp = brain.session.post(f"{brain.base_url}/api/report", json={})
        assert resp.status_code == 400


class TestDeviceLifecycle:
    """Test full device lifecycle."""

    def test_connect_heartbeat_disconnect_cycle(self, brain):
        """Device should complete full lifecycle."""
        device = f"lifecycle_{int(time.time())}"

        # 1. Connect
        connect_data, _ = brain.connect(device, "ios", ["camera"])
        assert connect_data["status"] == "connected"
        time.sleep(0.1)

        # 2. Verify in status
        status_data = brain.get_status()
        device_names = [d["device_name"] for d in status_data["children"]]
        assert device in device_names

        # 3. Send heartbeat
        hb_data, _ = brain.heartbeat(device)
        assert hb_data["status"] == "ok"

        # 4. Poll events (should be empty)
        events_data, _ = brain.get_events(device)
        assert events_data["events"] == []

        # 5. Send report
        report_data, _ = brain.report(device, {"frame": "data"})
        assert report_data["status"] == "received"

        # 6. Disconnect
        dc_data, _ = brain.disconnect(device)
        assert dc_data["status"] == "disconnected"
        time.sleep(0.1)

        # 7. Verify removed from status
        status_data = brain.get_status()
        device_names = [d["device_name"] for d in status_data["children"]]
        assert device not in device_names


class TestMultipleDevices:
    """Test multiple devices connected simultaneously."""

    def test_multiple_devices_connect(self, brain):
        """Multiple devices should be able to connect."""
        devices = [f"multi_{i}_{int(time.time())}" for i in range(3)]

        for device in devices:
            data, status = brain.connect(device, "android")
            assert status == 200
            assert data["status"] == "connected"

        time.sleep(0.2)

        # Verify all in status
        status_data = brain.get_status()
        device_names = [d["device_name"] for d in status_data["children"]]
        for device in devices:
            assert device in device_names

        # Cleanup
        for device in devices:
            brain.disconnect(device)

    def test_multiple_devices_independent_queues(self, brain):
        """Each device should have independent event queue."""
        dev1 = f"queue1_{int(time.time())}"
        dev2 = f"queue2_{int(time.time())}"

        brain.connect(dev1, "android")
        brain.connect(dev2, "android")
        time.sleep(0.2)

        # Both should have empty queues
        events1, _ = brain.get_events(dev1)
        events2, _ = brain.get_events(dev2)
        assert events1["events"] == []
        assert events2["events"] == []

        # Cleanup
        brain.disconnect(dev1)
        brain.disconnect(dev2)


class TestErrorHandling:
    """Test error cases and edge conditions."""

    def test_malformed_json_connect(self, brain):
        """Malformed JSON should return 400."""
        resp = brain.session.post(
            f"{brain.base_url}/api/connect",
            data="not json",
            headers={"Content-Type": "application/json"}
        )
        assert resp.status_code in [400, 415]

    def test_missing_required_fields_connect(self, brain):
        """Missing required fields should fail."""
        resp = brain.session.post(
            f"{brain.base_url}/api/connect",
            json={"device_name": "test"}  # missing device_type
        )
        assert resp.status_code != 200 or resp.json()["status"] == "rejected"

    def test_duplicate_device_connect(self, brain):
        """Duplicate device should be rejected."""
        device = f"dup_{int(time.time())}"

        # First connect
        data1, status1 = brain.connect(device, "android")
        assert status1 == 200
        time.sleep(0.1)

        # Second connect (duplicate)
        data2, status2 = brain.connect(device, "android")
        assert status2 == 400  # Should reject
        assert data2["status"] == "rejected"

        # Cleanup
        brain.disconnect(device)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
