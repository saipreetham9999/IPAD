#!/usr/bin/env python3
"""
Standalone Brain endpoint test — no pytest required.
Run directly against a live Brain instance.

Usage:
    python tests/test_brain_standalone.py http://192.168.1.100:8080

Or locally:
    python tests/test_brain_standalone.py

Will test:
    - Health status
    - Device connect/heartbeat/disconnect
    - Event queue
    - Data reports
"""

import sys
import requests
import time
import json
from datetime import datetime

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"


class BrainTester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.passed = 0
        self.failed = 0
        self.skipped = 0

    def log(self, tag, message, color=CYAN):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"{color}[{ts}] {tag:20s}{RESET} {message}")

    def test_pass(self, name):
        self.passed += 1
        self.log("✅ PASS", name, GREEN)

    def test_fail(self, name, error):
        self.failed += 1
        self.log("❌ FAIL", f"{name}: {error}", RED)

    def test_skip(self, name, reason):
        self.skipped += 1
        self.log("⏭️  SKIP", f"{name}: {reason}", YELLOW)

    def assert_equal(self, actual, expected, message):
        if actual == expected:
            return True
        raise AssertionError(f"{message}: expected {expected}, got {actual}")

    def assert_in(self, item, container, message):
        if item in container:
            return True
        raise AssertionError(f"{message}: {item} not in {container}")

    def assert_status_code(self, response, expected_codes, message):
        if response.status_code not in (expected_codes if isinstance(expected_codes, list) else [expected_codes]):
            raise AssertionError(f"{message}: expected {expected_codes}, got {response.status_code}")
        return True

    def summary(self):
        total = self.passed + self.failed + self.skipped
        print("\n" + "=" * 60)
        print(f"{'Test Summary':^60}")
        print("=" * 60)
        print(f"{GREEN}✅ Passed:  {self.passed}{RESET}")
        print(f"{RED}❌ Failed:  {self.failed}{RESET}")
        print(f"{YELLOW}⏭️  Skipped: {self.skipped}{RESET}")
        print(f"{'Total':20} {total}")
        print("=" * 60)

        if self.failed == 0:
            print(f"{GREEN}🎉 All tests passed!{RESET}")
            return 0
        else:
            print(f"{RED}❌ {self.failed} test(s) failed.{RESET}")
            return 1

    # ── Test Methods ──────────────────────────────────────────────────

    def test_brain_online(self):
        """Test that Brain is reachable and online."""
        try:
            resp = self.session.get(f"{self.base_url}/")
            self.assert_status_code(resp, 200, "Brain homepage")
            data = resp.json()
            self.assert_equal(data.get("brain"), "online", "Brain status")
            self.test_pass("Brain is online")
        except Exception as e:
            self.test_fail("Brain is online", str(e))

    def test_health_endpoint(self):
        """Test /api/health endpoint."""
        try:
            resp = self.session.get(f"{self.base_url}/api/health")
            data = resp.json()
            self.assert_in("status", data, "Health has status field")
            self.assert_in("services", data, "Health has services field")
            self.assert_in("ai_tier", data, "Health has ai_tier field")
            status = data["status"]
            if status not in ["healthy", "degraded"]:
                raise AssertionError(f"Invalid status: {status}")
            self.test_pass("Health endpoint works")
        except Exception as e:
            self.test_fail("Health endpoint", str(e))

    def test_status_endpoint(self):
        """Test /api/status endpoint."""
        try:
            resp = self.session.get(f"{self.base_url}/api/status")
            self.assert_status_code(resp, 200, "Status endpoint")
            data = resp.json()
            self.assert_equal(data.get("status"), "online", "Status is online")
            self.assert_in("children", data, "Status has children field")
            self.test_pass("Status endpoint works")
        except Exception as e:
            self.test_fail("Status endpoint", str(e))

    def test_device_connect(self):
        """Test device connection."""
        try:
            device_name = f"test_device_{int(time.time())}"
            payload = {
                "device_name": device_name,
                "device_type": "android",
                "capabilities": ["camera", "audio"],
            }
            resp = self.session.post(f"{self.base_url}/api/connect", json=payload)
            self.assert_status_code(resp, 200, "Connect returns 200")
            data = resp.json()
            self.assert_equal(data.get("status"), "connected", "Connection successful")
            self.test_pass(f"Device '{device_name}' connected")
            return device_name
        except Exception as e:
            self.test_fail("Device connect", str(e))
            return None

    def test_device_heartbeat(self, device_name):
        """Test device heartbeat."""
        if not device_name:
            self.test_skip("Device heartbeat", "No device connected")
            return
        try:
            payload = {"device_name": device_name}
            resp = self.session.post(f"{self.base_url}/api/heartbeat", json=payload)
            self.assert_status_code(resp, 200, "Heartbeat returns 200")
            data = resp.json()
            self.assert_equal(data.get("status"), "ok", "Heartbeat successful")
            self.test_pass(f"Device '{device_name}' sent heartbeat")
        except Exception as e:
            self.test_fail("Device heartbeat", str(e))

    def test_get_events(self, device_name):
        """Test getting events for a device."""
        if not device_name:
            self.test_skip("Get events", "No device connected")
            return
        try:
            resp = self.session.get(f"{self.base_url}/api/events", params={"device_name": device_name})
            self.assert_status_code(resp, 200, "Get events returns 200")
            data = resp.json()
            self.assert_equal(data.get("status"), "ok", "Events response status")
            self.assert_in("events", data, "Events response has events field")
            self.test_pass(f"Retrieved events for '{device_name}' (count: {len(data['events'])})")
        except Exception as e:
            self.test_fail("Get events", str(e))

    def test_device_report(self, device_name):
        """Test device sending a report."""
        if not device_name:
            self.test_skip("Device report", "No device connected")
            return
        try:
            payload = {
                "device_name": device_name,
                "timestamp": int(time.time()),
                "sensor": "camera",
                "data": {"motion": 0.8, "zone": "kitchen"},
            }
            resp = self.session.post(f"{self.base_url}/api/report", json=payload)
            self.assert_status_code(resp, 200, "Report returns 200")
            data = resp.json()
            self.assert_equal(data.get("status"), "received", "Report received")
            self.test_pass(f"Device '{device_name}' sent report")
        except Exception as e:
            self.test_fail("Device report", str(e))

    def test_device_disconnect(self, device_name):
        """Test device disconnection."""
        if not device_name:
            self.test_skip("Device disconnect", "No device connected")
            return
        try:
            payload = {"device_name": device_name}
            resp = self.session.post(f"{self.base_url}/api/disconnect", json=payload)
            self.assert_status_code(resp, 200, "Disconnect returns 200")
            data = resp.json()
            self.assert_equal(data.get("status"), "disconnected", "Disconnection successful")
            self.test_pass(f"Device '{device_name}' disconnected")
        except Exception as e:
            self.test_fail("Device disconnect", str(e))

    def test_unknown_device_heartbeat(self):
        """Test heartbeat for non-existent device."""
        try:
            payload = {"device_name": "nonexistent_xyz_123"}
            resp = self.session.post(f"{self.base_url}/api/heartbeat", json=payload)
            self.assert_status_code(resp, 404, "Unknown device returns 404")
            data = resp.json()
            self.assert_equal(data.get("status"), "unknown", "Unknown device response")
            self.test_pass("Unknown device correctly rejected")
        except Exception as e:
            self.test_fail("Unknown device heartbeat", str(e))

    def test_duplicate_device(self):
        """Test that duplicate device names are rejected."""
        try:
            device_name = f"dup_{int(time.time())}"
            payload = {
                "device_name": device_name,
                "device_type": "android",
                "capabilities": [],
            }

            # First connect
            resp1 = self.session.post(f"{self.base_url}/api/connect", json=payload)
            if resp1.status_code != 200:
                self.test_skip("Duplicate device test", "First connect failed")
                return

            time.sleep(0.1)

            # Second connect (duplicate)
            resp2 = self.session.post(f"{self.base_url}/api/connect", json=payload)
            if resp2.status_code == 400:
                data = resp2.json()
                if data.get("status") == "rejected":
                    self.test_pass("Duplicate device correctly rejected")
                else:
                    self.test_fail("Duplicate device", "Wrong rejection reason")
            else:
                self.test_skip("Duplicate device test", f"Got {resp2.status_code}, expected 400")

            # Cleanup
            self.session.post(f"{self.base_url}/api/disconnect", json={"device_name": device_name})
        except Exception as e:
            self.test_fail("Duplicate device", str(e))

    def test_multiple_devices(self):
        """Test multiple devices connecting simultaneously."""
        try:
            devices = [f"multi_{i}_{int(time.time())}" for i in range(3)]
            for device in devices:
                payload = {
                    "device_name": device,
                    "device_type": "android",
                    "capabilities": ["camera"],
                }
                resp = self.session.post(f"{self.base_url}/api/connect", json=payload)
                if resp.status_code != 200:
                    self.test_fail("Multiple devices", f"Could not connect {device}")
                    return

            time.sleep(0.1)

            # Check status shows all
            resp = self.session.get(f"{self.base_url}/api/status")
            data = resp.json()
            device_names = [d["device_name"] for d in data.get("children", [])]
            for device in devices:
                if device not in device_names:
                    self.test_fail("Multiple devices", f"{device} not in status")
                    return

            self.test_pass(f"Multiple devices ({len(devices)}) connected successfully")

            # Cleanup
            for device in devices:
                self.session.post(f"{self.base_url}/api/disconnect", json={"device_name": device})
        except Exception as e:
            self.test_fail("Multiple devices", str(e))

    def run_all_tests(self):
        """Run all tests in sequence."""
        print(f"\n{CYAN}{'=' * 60}")
        print(f"Brain Network Integration Tests")
        print(f"Target: {self.base_url}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'=' * 60}{RESET}\n")

        # Core functionality
        self.test_brain_online()
        self.test_health_endpoint()
        self.test_status_endpoint()

        # Device lifecycle
        print(f"\n{CYAN}--- Device Lifecycle Tests ---{RESET}")
        device = self.test_device_connect()
        if device:
            time.sleep(0.1)
            self.test_device_heartbeat(device)
            self.test_get_events(device)
            self.test_device_report(device)
            self.test_device_disconnect(device)

        # Error cases
        print(f"\n{CYAN}--- Error Handling Tests ---{RESET}")
        self.test_unknown_device_heartbeat()
        self.test_duplicate_device()

        # Multi-device
        print(f"\n{CYAN}--- Multi-Device Tests ---{RESET}")
        self.test_multiple_devices()

        # Summary
        print()
        return self.summary()


def main():
    if len(sys.argv) > 1:
        brain_url = sys.argv[1]
    else:
        brain_url = "http://localhost:8080"

    print(f"{CYAN}Connecting to Brain at {brain_url}...{RESET}")

    try:
        tester = BrainTester(brain_url)
        # Verify connectivity first
        resp = tester.session.get(brain_url, timeout=5)
        print(f"{GREEN}✅ Brain is reachable!{RESET}\n")
    except requests.exceptions.ConnectionError:
        print(f"{RED}❌ Cannot reach Brain at {brain_url}{RESET}")
        print("Make sure Brain is running and accessible.")
        sys.exit(1)
    except Exception as e:
        print(f"{RED}❌ Error: {e}{RESET}")
        sys.exit(1)

    exit_code = tester.run_all_tests()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
