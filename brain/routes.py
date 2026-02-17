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

    response = {
        "brain": "online",
        "children_connected": len(children),
        "children": list(children.keys())
    }

    log.info("Index requested → responding with %s", response)
    return jsonify(response)


@bp.route("/api/status", methods=["GET"])
def status():
    brain = get_brain()
    children = brain.connection_manager.get_all()

    response = {
        "status": "online",
        "children": [
            {
                "device_name": c["device_name"],
                "device_type": c["device_type"],
                "capabilities": c["capabilities"],
            }
            for c in children.values()
        ]
    }

    log.info("Status requested → %d children returned", len(response["children"]))
    return jsonify(response)


# ── new HTTP connection endpoints ─────────────────────────────────────
@bp.route("/api/connect", methods=["POST"])
def connect():
    identity = request.get_json()

    if not identity:
        log.warning("Connect rejected: No JSON body")
        return jsonify({"status": "rejected", "reason": "no JSON body"}), 400

    log.info("Connect request received: %s", identity)

    brain = get_brain()
    result = brain.connection_manager.handle_connect(identity)

    log.info("Connect response for %s → %s",
             identity.get("device_name"),
             result)

    if result["status"] == "rejected":
        return jsonify(result), 400

    return jsonify(result), 200


@bp.route("/api/heartbeat", methods=["POST"])
def heartbeat():
    data = request.get_json()

    if not data or "device_name" not in data:
        log.warning("Heartbeat rejected: device_name required")
        return jsonify({"status": "error", "reason": "device_name required"}), 400

    log.info("Heartbeat received from %s", data["device_name"])

    brain = get_brain()
    result = brain.connection_manager.handle_heartbeat(data["device_name"])

    log.info("Heartbeat response to %s → %s",
             data["device_name"],
             result)

    if result["status"] == "unknown":
        return jsonify(result), 404

    return jsonify(result), 200


@bp.route("/api/disconnect", methods=["POST"])
def disconnect():
    data = request.get_json()

    if not data or "device_name" not in data:
        log.warning("Disconnect rejected: device_name required")
        return jsonify({"status": "error", "reason": "device_name required"}), 400

    log.info("Disconnect request received: %s", data)

    brain = get_brain()
    brain.connection_manager.handle_disconnect(data["device_name"])

    response = {"status": "disconnected"}
    log.info("Disconnect response → %s", response)

    return jsonify(response), 200


@bp.route("/api/events", methods=["GET"])
def events():
    device_name = request.args.get("device_name")

    if not device_name:
        log.warning("Events poll rejected: device_name required")
        return jsonify({"status": "error", "reason": "device_name required"}), 400

    log.info("Events poll requested by %s", device_name)

    brain = get_brain()
    pending = brain.message_router.pop_events(device_name)

    log.info("Sending %d events to %s → %s",
             len(pending),
             device_name,
             pending)

    response = {
        "status": "ok",
        "events": pending
    }

    return jsonify(response), 200


@bp.route("/api/report", methods=["POST"])
def report():
    data = request.get_json()

    if not data:
        log.warning("Report rejected: No JSON body")
        return jsonify({"status": "error", "reason": "no JSON body"}), 400

    log.info("Report received → %s", data)

    brain = get_brain()
    brain.bus.publish("child.report.received", data)

    response = {"status": "received"}
    log.info("Report response → %s", response)

    return jsonify(response), 200


@bp.route("/api/health", methods=["GET"])
def health():
    log.debug("Health check requested")

    brain = get_brain()
    report = brain.health_checker.get_report()
    all_healthy = all(s == "running" for s in report.values())

    response = {
        "status": "healthy" if all_healthy else "degraded",
        "services": report,
        "ai_tier": brain.tier_manager.get_tier(),
        "ai_processor": brain.tier_manager.get_processor(),
    }

    log.info("Health response → %s", response)

    status_code = 200 if all_healthy else 503
    return jsonify(response), status_code
