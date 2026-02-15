# Brain Network — Quick Start

## 1️⃣ Start Brain on iPad

```bash
cd /path/to/IPAD
python supervisor.py
```

**Expected output:**
```
✅ Supervisor Started. Monitoring for updates...
🧠 BRAIN BOOTING...
  ✅ MiniTelegramBot started
  ✅ AraConnectionManager started
  ... (14 more services)
🟢 BRAIN ONLINE — 16 services running
```

## 2️⃣ Find iPad's IP

```bash
ifconfig | grep inet
```

Look for: `inet 192.168.1.100` (your IP will be different)

## 3️⃣ Check Brain is Ready

```bash
./tests/check_brain_ready.sh 192.168.1.100
```

Expected: ✅ All checks passed!

## 4️⃣ Run Tests

### Option A: Standalone (no setup)
```bash
python tests/test_brain_standalone.py http://192.168.1.100:8080
```

### Option B: pytest (comprehensive)
```bash
pip install pytest requests
pytest tests/test_integration_endpoints.py -v --brain-url http://192.168.1.100:8080
```

## 5️⃣ What Gets Tested

✅ Brain online
✅ Device connect/heartbeat/disconnect
✅ Event queue and polling
✅ Data reports
✅ Multiple devices
✅ Error handling
✅ Service health (16 services)
✅ AI tier detection

## Endpoints Tested

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/` | Brain online? |
| GET | `/api/status` | Connected devices |
| GET | `/api/health` | Service status + AI tier |
| POST | `/api/connect` | Device registers |
| POST | `/api/heartbeat` | Keep device alive |
| POST | `/api/disconnect` | Device leaves |
| GET | `/api/events` | Poll for alerts |
| POST | `/api/report` | Send frame/data |

## Example Device Flow

```bash
# 1. Connect
curl -X POST http://192.168.1.100:8080/api/connect \
  -H "Content-Type: application/json" \
  -d '{
    "device_name": "phone_a",
    "device_type": "android",
    "capabilities": ["camera", "audio"]
  }'

# 2. Heartbeat (every 5 seconds)
curl -X POST http://192.168.1.100:8080/api/heartbeat \
  -H "Content-Type: application/json" \
  -d '{"device_name": "phone_a"}'

# 3. Poll for events
curl http://192.168.1.100:8080/api/events?device_name=phone_a

# 4. Send report
curl -X POST http://192.168.1.100:8080/api/report \
  -H "Content-Type: application/json" \
  -d '{
    "device_name": "phone_a",
    "timestamp": 1707990000,
    "sensor": "camera",
    "data": {"motion": 0.8}
  }'

# 5. Disconnect
curl -X POST http://192.168.1.100:8080/api/disconnect \
  -H "Content-Type: application/json" \
  -d '{"device_name": "phone_a"}'
```

## Test Output Example

```
[14:32:45] ✅ PASS        Brain is online
[14:32:45] ✅ PASS        Health endpoint works
[14:32:46] ✅ PASS        Device 'test_device_1707...' connected
[14:32:46] ✅ PASS        Device 'test_device_1707...' sent heartbeat
[14:32:46] ✅ PASS        Device 'test_device_1707...' disconnected

============================================================
✅ Passed:  20
❌ Failed:  0
⏭️ Skipped: 0
============================================================
🎉 All tests passed!
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Brain not reachable | `ping 192.168.1.100` + restart Brain |
| Device already connected | Wait 15s or disconnect: `curl -X POST http://192.168.1.100:8080/api/disconnect -H "Content-Type: application/json" -d '{"device_name":"device_name"}'` |
| Port 8080 in use | `lsof -i :8080` + `kill -9 <PID>` |
| Tests hang | Restart Brain: `pkill python && python supervisor.py` |

## Logs

On iPad:
```bash
tail -f logs/brain.log        # Main app
tail -f logs/events.log       # All bus events
tail -f logs/supervisor.log   # Supervisor
```

## What Happens During Test

```
Brain (iPad)                  Test Machine
    |                              |
    |<--- GET / (is online?) ----  |
    |---- "online" ----------------->|
    |                              |
    |<--- POST /connect -------      |
    |---- "connected" ---------->    |
    |                              |
    |<--- POST /heartbeat -----      |
    |---- "ok" ---------->           |
    |                              |
    |<--- GET /events --------       |
    |---- [] (empty queue) ----->    |
    |                              |
    |<--- POST /report -------       |
    |---- "received" -------->       |
    |                              |
    |<--- POST /disconnect ---       |
    |---- "disconnected" ---->       |
```

## Files to Know

```
brain/               — Main Brain app
├── brain.py        — Boots 16 services
├── routes.py       — All 8 endpoints
└── settings.py     — Config (Telegram token)

tests/              — Integration tests
├── test_integration_endpoints.py  — 40+ pytest tests
├── test_brain_standalone.py       — Standalone runner
├── check_brain_ready.sh           — Pre-test checker
└── README.md                      — Full testing guide

logs/               — Auto-created on first run
├── brain.log       — Main logs (rotating, 10MB max)
├── events.log      — All bus events
└── supervisor.log  — Supervisor daemon

TESTING_GUIDE.md    — Complete testing documentation
IMPLEMENTATION_SUMMARY.md  — What was built
QUICK_START.md      — This file
```

## One-Liner Tests

```bash
# Is Brain online?
curl -s http://192.168.1.100:8080/ | grep online

# How many devices connected?
curl -s http://192.168.1.100:8080/api/status | grep device_name | wc -l

# What's the health status?
curl -s http://192.168.1.100:8080/api/health | jq .status

# Connect a test device
curl -s -X POST http://192.168.1.100:8080/api/connect \
  -H "Content-Type: application/json" \
  -d '{"device_name":"test","device_type":"test"}' | jq .status
```

## Next Steps

1. ✅ Brain running on iPad
2. ✅ Tests pass on real hardware
3. ⏳ Build Flutter app (Worker client)
4. ⏳ Integrate real AI models (Phase 5)
5. ⏳ Add persistence (SQLite)
6. ⏳ Token-based authentication

## Docs

- **Full Testing:** `TESTING_GUIDE.md` (2000+ lines)
- **Implementation:** `IMPLEMENTATION_SUMMARY.md`
- **Test Details:** `tests/README.md`

---

**Status:** ✅ Ready for integration testing
**Last Updated:** 2026-02-15
