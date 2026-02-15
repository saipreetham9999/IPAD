from flask import Blueprint, request, jsonify, current_app
from bus.JoLogger import get_logger

bp = Blueprint("routes", __name__)
log = get_logger("BrainRoutes")


def get_brain():
    return current_app.brain


# ── existing ──────────────────────────────────────────────────────────
@bp.route("/")
def index():
    brain = get_brain()
    children = brain.connection_manager.get_all()
    return jsonify({
        "brain": "online",
        "children_connected": len(children),
        "children": list(children.keys())
    })


@bp.route("/api/status", methods=["GET"])
def status():
    brain = get_brain()
    children = brain.connection_manager.get_all()
    return jsonify({
        "status": "online",
        "children": [
            {
                "device_name": c["device_name"],
                "device_type": c["device_type"],
                "capabilities": c["capabilities"],
            }
            for c in children.values()
        ]
    })


# ── new HTTP connection endpoints ─────────────────────────────────────
@bp.route("/api/connect", methods=["POST"])
def connect():
    """Child sends identity. Brain registers it."""
    identity = request.get_json()
    if not identity:
        log.warning("Connect request rejected: No JSON body")
        return jsonify({"status": "rejected", "reason": "no JSON body"}), 400

    log.info("Connect request received from: %s", identity.get("device_name", "unknown"))
    brain = get_brain()
    result = brain.connection_manager.handle_connect(identity)
    log.info("Raw JSON received: %s", identity)

    if result["status"] == "rejected":
        log.warning("Connect request rejected for %s: %s", identity.get("device_name"), result.get("reason"))
        return jsonify(result), 400

    log.info("Connect request accepted for %s", identity.get("device_name"))
    return jsonify(result), 200


@bp.route("/api/heartbeat", methods=["POST"])
def heartbeat():
    """Child sends heartbeat every 5 seconds to stay alive."""
    data = request.get_json()
    if not data or "device_name" not in data:
        log.warning("Heartbeat rejected: device_name required")
        return jsonify({"status": "error", "reason": "device_name required"}), 400

    # log.debug("Heartbeat received from %s", data["device_name"])
    brain = get_brain()
    result = brain.connection_manager.handle_heartbeat(data["device_name"])

    if result["status"] == "unknown":
        log.warning("Heartbeat from unknown device: %s", data["device_name"])
        return jsonify(result), 404

    return jsonify(result), 200


@bp.route("/api/disconnect", methods=["POST"])
def disconnect():
    """Child cleanly disconnects."""
    data = request.get_json()
    if not data or "device_name" not in data:
        log.warning("Disconnect rejected: device_name required")
        return jsonify({"status": "error", "reason": "device_name required"}), 400

    log.info("Disconnect request from %s", data["device_name"])
    brain = get_brain()
    brain.connection_manager.handle_disconnect(data["device_name"])
    return jsonify({"status": "disconnected"}), 200


@bp.route("/api/events", methods=["GET"])
def events():
    """Child polls for pending events/alerts."""
    device_name = request.args.get("device_name")
    if not device_name:
        log.warning("Events poll rejected: device_name required")
        return jsonify({"status": "error", "reason": "device_name required"}), 400

    brain = get_brain()
    pending = brain.message_router.pop_events(device_name)
    
    if pending:
        log.info("Sending %d events to %s", len(pending), device_name)
        
    return jsonify({
        "status": "ok",
        "events": pending
    }), 200


@bp.route("/api/report", methods=["POST"])
def report():
    """Child sends data report (camera frame, sensor data etc)."""
    data = request.get_json()
    if not data:
        log.warning("Report rejected: No JSON body")
        return jsonify({"status": "error", "reason": "no JSON body"}), 400

    device_name = data.get("device_name", "unknown")
    log.info("Report received from %s", device_name)
    
    brain = get_brain()
    brain.bus.publish("child.report.received", data)
    return jsonify({"status": "received"}), 200


@bp.route("/api/health", methods=["GET"])
def health():
    """Returns health status of all services."""
    log.debug("Health check requested")
    brain = get_brain()
    report = brain.health_checker.get_report()
    all_healthy = all(s == "running" for s in report.values())
    
    status_code = 200 if all_healthy else 503
    if not all_healthy:
        log.warning("Health check failed: %s", report)
        
    return jsonify({
        "status": "healthy" if all_healthy else "degraded",
        "services": report,
        "ai_tier": brain.tier_manager.get_tier(),
        "ai_processor": brain.tier_manager.get_processor(),
    }), status_code