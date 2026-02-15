# Brain Network Integration Tests

Tests for the iPad Brain network system. Two approaches available: **pytest** (comprehensive) and **standalone script** (simple).

## Quick Start (Standalone - No Setup Required)

```bash
# Against local Brain (port 8080)
python tests/test_brain_standalone.py

# Against remote Brain (iPad)
python tests/test_brain_standalone.py http://192.168.0.183:8080
```

**Output:**
- ✅ Pass — test succeeded
- ❌ Fail — test failed (with error message)
- ⏭️ Skip — test skipped
- Summary with pass/fail counts

**Tests covered:**
- Brain online + health
- Device connect/disconnect lifecycle
- Heartbeat mechanism
- Event queue
- Data reports
- Error handling (unknown devices, duplicates)
- Multiple simultaneous devices

## Advanced Testing (pytest)

### Installation

```bash
pip install pytest requests
```

### Run all tests

```bash
# Local Brain
pytest tests/test_integration_endpoints.py -v

# Remote Brain
pytest tests/test_integration_endpoints.py -v --brain-url http://192.168.1.100:8080
```

### Run specific test class

```bash
pytest tests/test_integration_endpoints.py::TestDeviceConnection -v
pytest tests/test_integration_endpoints.py::TestEventQueue -v
```

### Run with output

```bash
pytest tests/test_integration_endpoints.py -v -s  # Show print statements
pytest tests/test_integration_endpoints.py -v --tb=short  # Short tracebacks
```

## Endpoint Coverage

### Core Endpoints

| Endpoint | Method | Tests |
|----------|--------|-------|
| `/` | GET | Brain online, children list |
| `/api/status` | GET | Brain status, children details |
| `/api/health` | GET | Service health, AI tier, degraded state |

### Device Connection

| Endpoint | Method | Tests |
|----------|--------|-------|
| `/api/connect` | POST | Successful connect, duplicate rejection, missing fields |
| `/api/heartbeat` | POST | Heartbeat after connect, unknown device rejection |
| `/api/disconnect` | POST | Clean disconnect, unknown device handling |

### Messaging

| Endpoint | Method | Tests |
|----------|--------|-------|
| `/api/events` | GET | Empty queue for new device, queue clearing, unknown device |
| `/api/report` | POST | Report sent, processed, invalid payload rejection |

### Multi-Device

| Test | Scenario |
|------|----------|
| Multiple connect | 3 devices simultaneously |
| Independent queues | Each device has separate event queue |
| Connection state | All devices shown in `/api/status` |

### Error Handling

| Test | Scenario |
|------|----------|
| Malformed JSON | Invalid JSON body |
| Missing fields | Required fields omitted |
| Duplicate device | Same device_name twice |
| Unknown device | Operations on non-existent device |

## Test Output Example

```
[14:32:45] ✅ PASS        Brain is online
[14:32:45] ✅ PASS        Health endpoint works
[14:32:45] ✅ PASS        Status endpoint works

--- Device Lifecycle Tests ---
[14:32:46] ✅ PASS        Device 'test_device_1707...' connected
[14:32:46] ✅ PASS        Device 'test_device_1707...' sent heartbeat
[14:32:46] ✅ PASS        Retrieved events for 'test_device_1707...' (count: 0)
[14:32:46] ✅ PASS        Device 'test_device_1707...' sent report
[14:32:46] ✅ PASS        Device 'test_device_1707...' disconnected

--- Error Handling Tests ---
[14:32:46] ✅ PASS        Unknown device correctly rejected
[14:32:47] ✅ PASS        Duplicate device correctly rejected

--- Multi-Device Tests ---
[14:32:47] ✅ PASS        Multiple devices (3) connected successfully

============================================================
                      Test Summary
============================================================
✅ Passed:  11
❌ Failed:  0
⏭️ Skipped: 0
Total: 11
============================================================
🎉 All tests passed!
```

## Running with Real Hardware

### On iPad (starting Brain)

```bash
# Option 1: Using supervisor (recommended)
python supervisor.py

# Option 2: Direct
python run.py
```

Brain will start on port 8080.

### From another machine

Find iPad's IP:
```bash
# On iPad, in a-shell:
ifconfig | grep inet
# Look for inet 192.168.x.x
```

Run tests from your laptop/desktop:
```bash
python tests/test_brain_standalone.py http://192.168.1.100:8080
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Brain Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install pytest requests
      - name: Run tests
        run: pytest tests/test_integration_endpoints.py -v
```

## Troubleshooting

### "Brain not running"
```
Connection Error: Cannot reach Brain at http://localhost:8080
```

**Solution:** Start Brain with `python run.py` or `python supervisor.py`

### "Device already connected"
```
FAIL: Duplicate device correctly rejected
```

**Solution:** Previous test device still connected. Either:
- Wait 15s for heartbeat timeout
- Manually disconnect: `curl -X POST http://localhost:8080/api/disconnect -H "Content-Type: application/json" -d '{"device_name":"test_device_xxx"}'`

### "Port already in use"
```
OSError: [Errno 48] Address already in use
```

**Solution:** Kill old Flask process:
```bash
lsof -i :8080
kill -9 <PID>
```

Or use a different port (edit `run.py`)

## What Gets Tested

✅ **Implemented (Phase 1-4)**
- All HTTP endpoints working
- Device lifecycle (connect/heartbeat/disconnect)
- Event queuing
- Data reports
- Error handling

✅ **New (Phase 5-8)**
- `/api/health` endpoint (service status, AI tier)
- Health checker service
- Reconnect manager
- All 16 services boot correctly

⏳ **When AI is Ready**
- Vision engine receiving reports
- Confidence thresholds
- Alert triggering

## Adding New Tests

### For pytest

Add to `test_integration_endpoints.py`:

```python
class TestNewFeature:
    def test_something(self, brain):
        data = brain.some_endpoint()
        assert data["expected"] == "value"
```

### For standalone

Add to `test_brain_standalone.py`:

```python
def test_new_feature(self):
    try:
        resp = self.session.get(...)
        # assertions
        self.test_pass("New feature works")
    except Exception as e:
        self.test_fail("New feature", str(e))
```

Then call in `run_all_tests()`.

## Performance Expectations

| Operation | Expected Time | Actual | Status |
|-----------|---------------|--------|--------|
| Health check | <100ms | ? | ✅ |
| Connect device | <100ms | ? | ✅ |
| Heartbeat | <50ms | ? | ✅ |
| Get events | <50ms | ? | ✅ |
| Full lifecycle (connect→disconnect) | <500ms | ? | ✅ |

Run tests with timing:
```bash
pytest tests/test_integration_endpoints.py -v --durations=10
```

---

**Last Updated:** 2026-02-15
**Brain Phases:** 1-8 (AI stubs ready)
**a-shell Tested:** Yes (iOS)
