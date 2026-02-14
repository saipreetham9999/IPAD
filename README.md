# iPad Project: Brain Cluster

This project is a Flask-based "Brain Cluster" designed to interact with client applications (referred to as "Poco") on an iPad. It provides a web interface, API endpoints, and integrates with Telegram for notifications and commands. The development is structured into several phases.

## Project Phases Overview:

### Phase 1 — Heart
*   **Goal:** Establish the core application structure, service management, and configuration.
*   **Build:** `ara_service`, `jo_bus`, `ara_config_manager`, `main.py` (now `run.py`).
*   **Test:** Brain boots, JoBus running, config loads.
*   **Done:** `python run.py` → "🟢 BRAIN ONLINE" printed.

### Phase 2 — Spine
*   **Goal:** Enable client (Poco) connection and session management.
*   **Build:** `ara_connection_manager`, `ara_child_manager`, `ara_child_profile`, `ara_session_manager`.
*   **Test:** Poco opens Worker app, scans QR, connects.
*   **Done:** Brain prints "Poco M2 Pro connected".

### Phase 3 — Telegram Always On
*   **Goal:** Integrate continuous Telegram communication for alerts and status updates.
*   **Build:** `mini_telegram_bot`, `mini_telegram_alert`.
*   **Test:** Brain starts → sends "Brain Online" to group; Poco connects → group sees "Poco connected".
*   **Done:** Everything Brain knows, group sees instantly.

### Phase 4 — Eyes
*   **Goal:** Implement vision processing capabilities.
*   **Build:** `ara_stream_receiver`, `sai_vision_engine`, `sai_model_store`, `sai_tier_manager`.
*   **Test:** Poco sends frame, AI processes it.
*   **Done:** Group receives detection result in real time.

### Phase 5 — Commands
*   **Goal:** Enable two-way communication with Telegram for commands.
*   **Build:** `mini_telegram_command`.
*   **Test:** Reply "status" in group → Brain responds.
*   **Done:** Group can talk back to Brain.

### Phase 6 — Rules and Routing
*   **Goal:** Implement intelligent routing and alerting based on rules.
*   **Build:** `sai_alert_rules`, `mini_message_router`, `mini_routing_rules`, `mini_heartbeat`.
*   **Test:** Person detected → correct alert to correct child.
*   **Done:** Right message, right device, right time.

### Phase 7 — Memory
*   **Goal:** Implement event logging and snapshot management.
*   **Build:** `jo_event_logger`, `sai_snapshot_manager`.
*   **Test:** Anomaly detected → snapshot saved → sent to group.
*   **Done:** Full event history, snapshots in Telegram.

### Phase 8 — Resilience
*   **Goal:** Ensure robust connection handling and fault tolerance.
*   **Build:** `ara_health_checker`, `ara_reconnect_manager`, `ara_fallback_handler`.
*   **Test:** Kill Poco WiFi → reconnects → session restores.
*   **Done:** Drop and rejoin works silently.

### Phase 9 — Shields
*   **Goal:** Implement protective measures against system failures.
*   **Build:** `jo_circuit_breaker`, `ara_retry_manager`, `ara_watchdog`.
*   **Test:** Kill AI engine → system keeps running.
*   **Done:** Nothing takes Brain down.

---

## Getting Started:

1.  **Clone the repository.**
2.  **Install dependencies:** `pip install -r requirements.txt`
3.  **Run the application:** `./run.sh` (or `python run.py`)

Refer to the `plan/` directory for detailed implementation notes on each phase.
