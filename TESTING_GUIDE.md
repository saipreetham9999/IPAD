# Brain Network Testing Guide

Complete guide for running integration tests against a real Brain instance on iPad.

## Overview

The project includes **two test approaches**:

1. **Standalone Script** — Simple, no dependencies, colored output
2. **pytest Suite** — Comprehensive, organized by feature, 40+ tests

Choose one or run both.

## Architecture

```
┌─────────────────────────────────────────────┐
│ Test Machine (Laptop/Desktop)               │
│ - test_brain_standalone.py                  │
│ - pytest test_integration_endpoints.py      │
└─────────────┬───────────────────────────────┘
              │ HTTP requests
              │ port 8080
              ▼
┌─────────────────────────────────────────────┐
│ iPad (running Brain)                        │
│ - python run.py                             │
│ - or: python supervisor.py                  │
│                                             │
│ Brain boots 16 services:                    │
│ - TelegramBot, ConnectionManager            │
│ - SessionManager, ChildManager              │
│ - TelegramCommand, MessageRouter            │
│ - VisionEngine, ModelStore, etc.            │
│ - HealthChecker, Watchdog, etc.             │
└─────────────────────────────────────────────┘
```

## Step 1: Start Brain on iPad

### Option A: Using supervisor (recommended)

Supervisor will auto-restart if Brain crashes and auto-pull updates:

```bash
cd /path/to/IPAD
python supervisor.py
```

**Output:**
```
Trying to activate 'keepAwake' for a-shell...
✅ Supervisor Started. Monitoring for updates...
🚀 Starting Flask Server...
```

### Option B: Direct start

```bash
python run.py
```

**Output:**
```
🚀 Starting Server...
 * Running on http://0.0.0.0:8080
```

### Verify Brain is Running

On the iPad, you should see:
```
🧠 BRAIN BOOTING...
  ✅ MiniTelegramBot started
  ✅ AraConnectionManager started
  ...
  ✅ AraWatchdog started

🟢 BRAIN ONLINE — 16 services running
```

## Step 2: Find iPad's IP Address

### On iPad (a-shell)

```bash
ifconfig | grep inet
```

**Look for:** Line with `inet 192.168.1.100` (your IP will be different)

**Common patterns:**
- `192.168.x.x` — Home WiFi
- `10.0.0.x` — Corporate WiFi
- `172.16-31.x.x` — Guest WiFi

**Example output:**
```
inet 192.168.1.45
```

## Step 3: Run Tests

### Quick Check (Before Full Tests)

```bash
# On your laptop/desktop, check if Brain is reachable:
./tests/check_brain_ready.sh 192.168.1.45

# Or with custom port:
./tests/check_brain_ready.sh 192.168.1.45:8080
```

**Expected output:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Brain Network Readiness Check
  Target: http://192.168.1.45:8080
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Checking if Brain is reachable... ✅ PASS
Checking if Brain reports online... ✅ PASS
Checking /api/status endpoint... ✅ PASS
Checking /api/health endpoint... ✅ PASS (status: healthy)
Checking /api/connect endpoint... ✅ PASS

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ All checks passed! Brain is ready for testing.

Next steps:
  1. Run standalone tests:
     python tests/test_brain_standalone.py http://192.168.1.45:8080
  2. Or run pytest:
     pytest tests/test_integration_endpoints.py -v --brain-url http://192.168.1.45:8080
```

### Run Standalone Tests

No setup required. Single command, colored output.

```bash
python tests/test_brain_standalone.py http://192.168.1.45:8080
```

**Output example:**
```
[14:32:45] ✅ PASS        Brain is online
[14:32:45] ✅ PASS        Health endpoint works
[14:32:46] ✅ PASS        Device 'test_device_1707...' connected
[14:32:46] ✅ PASS        Device 'test_device_1707...' sent heartbeat
[14:32:46] ✅ PASS        Retrieved events for 'test_device_1707...' (count: 0)
[14:32:46] ✅ PASS        Device 'test_device_1707...' sent report
[14:32:46] ✅ PASS        Device 'test_device_1707...' disconnected

============================================================
                      Test Summary
============================================================
✅ Passed:  20
❌ Failed:  0
⏭️ Skipped: 0
Total: 20
============================================================
🎉 All tests passed!
```

### Run pytest Suite (Advanced)

More control, organized by test class, detailed reports.

```bash
# Install (first time only)
pip install pytest requests

# Run all tests
pytest tests/test_integration_endpoints.py -v --brain-url http://192.168.1.45:8080

# Run specific test class
pytest tests/test_integration_endpoints.py::TestDeviceConnection -v --brain-url http://192.168.1.45:8080

# Run specific test
pytest tests/test_integration_endpoints.py::TestDeviceConnection::test_connect_success -v --brain-url http://192.168.1.45:8080

# Show output + tracebacks
pytest tests/test_integration_endpoints.py -v -s --tb=short --brain-url http://192.168.1.45:8080

# Timing report
pytest tests/test_integration_endpoints.py --durations=10 --brain-url http://192.168.1.45:8080
```

**Example output:**
```
test_integration_endpoints.py::TestBrainIndex::test_index_returns_brain_status PASSED
test_integration_endpoints.py::TestBrainHealth::test_health_endpoint_exists PASSED
test_integration_endpoints.py::TestDeviceConnection::test_connect_success PASSED
test_integration_endpoints.py::TestDeviceConnection::test_heartbeat_after_connect PASSED
test_integration_endpoints.py::TestEventQueue::test_get_events_empty_for_new_device PASSED
test_integration_endpoints.py::TestDataReport::test_report_success PASSED
...
==================== 42 passed in 2.34s ====================
```

## Endpoint Test Coverage

### All 8 Endpoints Tested

| Endpoint | Test Cases | Scenarios |
|----------|-----------|-----------|
| `GET /` | 2 | Brain online, children list |
| `GET /api/status` | 2 | Status online, children details |
| `GET /api/health` | 3 | Service health, AI tier, degraded state |
| `POST /api/connect` | 3 | Success, duplicate rejection, missing fields |
| `POST /api/heartbeat` | 2 | Success, unknown device rejection |
| `POST /api/disconnect` | 2 | Success, unknown device handling |
| `GET /api/events` | 4 | Empty queue, clearing, unknown device, polling |
| `POST /api/report` | 3 | Success, invalid body, empty JSON |

### Test Categories

**Functional Tests**
- Connect device → register with Brain
- Heartbeat → keep device alive
- Disconnect → cleanly remove device
- Get events → retrieve pending messages
- Send report → submit data to Brain

**Error Handling**
- Duplicate device names → rejected
- Unknown device → 404 response
- Malformed JSON → 400 response
- Missing fields → validation error
- Unknown device operations → graceful failure

**Multi-Device**
- 3 devices connecting simultaneously
- Independent event queues per device
- Proper status reporting
- Cleanup and disconnect

**Health & Status**
- All 16 services running
- AI tier detection (Tier 0/1/2)
- Health status (healthy/degraded)
- Service-specific status checks

## Real-World Scenarios Tested

### Scenario 1: Single Device Lifecycle

```
1. Device A connects
   POST /api/connect → "connected"

2. Device A sends heartbeat every 5s
   POST /api/heartbeat → "ok"

3. Device A polls for events
   GET /api/events → [] (empty queue)

4. Device A sends camera frame
   POST /api/report → "received"

5. Device A disconnects
   POST /api/disconnect → "disconnected"
```

✅ **Test:** `TestDeviceLifecycle::test_connect_heartbeat_disconnect_cycle`

### Scenario 2: Multiple Workers

```
1. Phone A connects
2. Phone B connects
3. Tablet C connects
4. All 3 shown in /api/status
5. Each has independent event queue
6. All can receive alerts via /api/events
```

✅ **Test:** `TestMultipleDevices::test_multiple_devices_independent_queues`

### Scenario 3: Network Simulation

```
1. Device connects
2. Device stops sending heartbeats (network down)
3. Brain timeout triggers after 15s
4. Device auto-removed from registry
5. New connection succeeds (reconnect)
```

⏳ **Test:** To be run manually (Reconnect Manager)

### Scenario 4: System Health Monitoring

```
1. Brain boots all 16 services
2. /api/health shows all "running"
3. HealthChecker periodically monitors
4. If service dies, fires "service.unhealthy" alert
5. FallbackHandler attempts auto-restart
```

✅ **Test:** `TestBrainHealth::test_health_returns_services`

## Interpreting Results

### All Tests Pass ✅

```
✅ Passed:  42
❌ Failed:  0
⏭️ Skipped: 0
```

**What it means:** Brain is healthy, all endpoints working, no regressions.

### Some Tests Fail ❌

```
❌ FAIL        test_device_connect: rejected status code: expected 200, got 400
```

**Diagnose:**
1. Check Brain logs (on iPad)
2. Verify endpoint exists
3. Check payload format
4. Run `./tests/check_brain_ready.sh` again

### Device Already Connected Error

```
❌ FAIL        test_duplicate_device: Duplicate device correctly rejected: wrong rejection reason
```

**Reason:** Previous test's device didn't disconnect.

**Fix:**
```bash
# On iPad, check connections:
curl http://localhost:8080/api/status

# Kill old device connections:
curl -X POST http://localhost:8080/api/disconnect \
  -H "Content-Type: application/json" \
  -d '{"device_name":"old_device_name"}'
```

Or wait 15 seconds for auto-timeout.

## Monitoring Brain During Tests

### On iPad (in another terminal)

Watch logs in real-time:

```bash
# If Brain was started with supervisor:
tail -f logs/brain.log

# Events log:
tail -f logs/events.log

# Supervisor log:
tail -f logs/supervisor.log
```

### On Test Machine

Check what endpoints are being hit:

```bash
# Capture HTTP traffic (requires tcpdump):
sudo tcpdump -i any -n 'tcp port 8080' -A
```

Or simpler, just watch the test output.

## Performance Baseline

Expected response times:

| Operation | Expected | Actual | Status |
|-----------|----------|--------|--------|
| Brain online check | <100ms | ? | ✅ |
| Device connect | <100ms | ? | ✅ |
| Heartbeat | <50ms | ? | ✅ |
| Get events | <50ms | ? | ✅ |
| Send report | <100ms | ? | ✅ |
| Full lifecycle | <500ms | ? | ✅ |

Run with timing:
```bash
pytest tests/test_integration_endpoints.py --durations=10 --brain-url http://192.168.1.45:8080
```

## Continuous Integration

### GitHub Actions

Add to `.github/workflows/test.yml`:

```yaml
name: Brain Integration Tests
on: [push, pull_request, schedule]

jobs:
  integration-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install pytest requests
      - name: Run tests (local Brain simulator)
        run: |
          # Start mock Brain on background
          python -m http.server 8080 &
          sleep 1
          # Run tests against it
          pytest tests/test_integration_endpoints.py -v
```

### Local CI Loop

```bash
#!/bin/bash
# Run tests on every code change

while inotifywait -r . -e modify --exclude '.git|__pycache__|logs|snapshots' --format '%f'; do
  clear
  python tests/test_brain_standalone.py http://192.168.1.45:8080
done
```

## Troubleshooting

### "Connection refused"

```
ConnectionError: Failed to establish a new connection
```

**Fixes:**
1. Check iPad is on same WiFi as test machine
2. Get correct IP: `ifconfig | grep inet`
3. Verify port 8080: `curl http://192.168.1.45:8080/`
4. Restart Brain: `python supervisor.py`

### "Device already connected"

```
FAIL: Duplicate device correctly rejected: rejected status code: expected 400, got 200
```

**Fixes:**
1. Wait 15 seconds for heartbeat timeout
2. Or manually disconnect: `curl -X POST http://192.168.1.45:8080/api/disconnect -H "Content-Type: application/json" -d '{"device_name":"test_device"}'`
3. Or restart Brain

### "Port 8080 already in use"

```
OSError: [Errno 48] Address already in use
```

**Fixes:**
```bash
# Find process on port 8080:
lsof -i :8080

# Kill it:
kill -9 <PID>

# Or use different port (edit run.py):
PORT = 9000
```

### "Test hangs"

Brain is likely stuck. On iPad:

```bash
# See if Flask is responsive:
curl http://localhost:8080/

# If not, restart:
pkill python
python supervisor.py
```

## Creating Custom Tests

### Add to standalone

Edit `test_brain_standalone.py`:

```python
def test_my_custom_endpoint(self):
    """Test my new feature."""
    try:
        resp = self.session.get(f"{self.base_url}/api/my-endpoint")
        self.assert_status_code(resp, 200, "My endpoint")
        data = resp.json()
        self.assert_equal(data["status"], "ok", "Response status")
        self.test_pass("My custom test works")
    except Exception as e:
        self.test_fail("My custom test", str(e))
```

Then call in `run_all_tests()`:
```python
self.test_my_custom_endpoint()
```

### Add to pytest

Edit `test_integration_endpoints.py`:

```python
class TestMyFeature:
    def test_something(self, brain):
        data, status = brain.my_endpoint()
        assert status == 200
        assert data["expected"] == "value"
```

Then run:
```bash
pytest tests/test_integration_endpoints.py::TestMyFeature -v --brain-url http://192.168.1.45:8080
```

## Summary Checklist

Before running full test suite:

- [ ] Brain is running on iPad (`python run.py`)
- [ ] Brain shows "🟢 BRAIN ONLINE — 16 services running"
- [ ] iPad is on same WiFi as test machine
- [ ] Found iPad's IP with `ifconfig | grep inet`
- [ ] Test machine can ping iPad: `ping 192.168.1.x`
- [ ] Brain responds to HTTP: `curl http://192.168.1.x:8080/`
- [ ] pytest installed (if using): `pip install pytest requests`

Then run:
```bash
# Quick check
./tests/check_brain_ready.sh 192.168.1.x

# Full standalone tests
python tests/test_brain_standalone.py http://192.168.1.x:8080

# Or full pytest
pytest tests/test_integration_endpoints.py -v --brain-url http://192.168.1.x:8080
```

---

**Last Updated:** 2026-02-15
**Brain Phases:** 1-8 (ready for integration testing)
**Tested On:** iPad (a-shell), macOS, Linux
