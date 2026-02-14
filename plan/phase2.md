# Phase 2 - Spine: Implementation Details

This document outlines the components and their integration for Phase 2, focusing on establishing the Brain's structure and awareness for device connections.

## Core Components Implemented:

### 1. `network/AraConnectionManager.py`
*   **Role:** Network Entry Layer.
*   **Functionality:**
    *   Runs a FastAPI server on `0.0.0.0:8000`.
    *   Exposes the `POST /connect` endpoint.
    *   Receives device identity payloads (`device_name`, `device_type`, `capabilities`, `token`).
    *   Performs basic structural validation of the payload.
    *   Publishes a `child.connection.requested` event to the `JoBus` upon receiving a valid request.
    *   Returns `{"status": "request received"}` immediately.
*   **Key Design:** Does not store session data or manage lifecycle; acts purely as a gateway.

### 2. `core/AraSessionManager.py`
*   **Role:** Session Lifecycle Control.
*   **Functionality:**
    *   Subscribes to `child.connection.requested` events from the `JoBus`.
    *   **Enforces `MAX_CHILDREN = 20` limit:** Rejects new connections if capacity is reached.
    *   Handles duplicate device connections (currently rejects them).
    *   Generates a unique `session_id` for each new valid connection.
    *   Stores session data (`session_id`, `created_at`, `last_seen`) in memory.
    *   Publishes `session.created` event for new sessions or `session.rejected` if validation/capacity fails.
*   **Key Design:** Central authority for session legitimacy and lifecycle rules. Sessions are in-memory and temporary for Phase 2.

### 3. `children/AraChildManager.py`
*   **Role:** Active Device Registry.
*   **Functionality:**
    *   Subscribes to `session.created` events from the `JoBus`.
    *   Maintains an in-memory dictionary (`self.children`) of actively connected devices.
    *   Adds device metadata (device_name, type, session_id, connected_at) to the registry upon `session.created`.
    *   (Future: Will subscribe to `session.expired` or `child.disconnected` to remove children).
*   **Key Design:** Reflects already-validated active sessions; does not perform validation or control lifecycle.

### 4. `telegram/MiniTelegramCommand.py`
*   **Role:** Dedicated Telegram Command Handler.
*   **Functionality:**
    *   Subscribes to `telegram.command` events from the `JoBus`.
    *   Processes commands like `/status` and `/hello`.
    *   For `/status`, it queries the `AraChildManager` to get the count and details of currently connected devices.
    *   Sends a formatted status report back to Telegram via `MiniTelegramBot`.
*   **Key Design:** Decouples command handling logic from the main `Brain` class.

## Integration into `brain/Brain.py`:

*   All Phase 2 services (`AraConnectionManager`, `AraSessionManager`, `AraChildManager`, `MiniTelegramCommand`) are now imported and instantiated within `Brain.__init__`.
*   These instances are added to the `Brain`'s `self.services` list, ensuring they are automatically started and stopped with the `Brain`.
*   The `Brain`'s `start()` method ensures all services are initiated before sending the "🟢 Brain Online" message to Telegram.
*   Direct Telegram command handling has been removed from `Brain`, delegating this to `MiniTelegramCommand`.

## Event Flow (Real-Time Example):

1.  **Device sends `POST /connect`**: Handled by `network/AraConnectionManager.py`.
2.  **`AraConnectionManager`**: Validates payload structure, publishes `child.connection.requested` to `JoBus`.
3.  **`core/AraSessionManager.py`**: Receives `child.connection.requested`, checks capacity and duplicates, creates session, publishes `session.created` (or `session.rejected`).
4.  **`children/AraChildManager.py`**: Receives `session.created`, adds device to its active registry.
5.  **User sends `/status` to Telegram**: Handled by `telegram/MiniTelegramCommand.py`.
6.  **`MiniTelegramCommand`**: Queries `AraChildManager` for active children, formats report, sends to Telegram.

## Testing:

*   **`TestPhase2Spine.py`**: Contains unit tests for the `/connect` endpoint and the overall happy path of device connection and status reporting.

This completes the implementation and documentation of Phase 2, establishing the foundational "Spine" for Hera's device awareness.