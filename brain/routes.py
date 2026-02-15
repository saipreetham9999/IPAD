from flask import Blueprint, request, jsonify, current_app

bp = Blueprint("routes", __name__)


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
        return jsonify({"status": "rejected", "reason": "no JSON body"}), 400

    brain = get_brain()
    result = brain.connection_manager.handle_connect(identity)

    if result["status"] == "rejected":
        return jsonify(result), 400

    return jsonify(result), 200


@bp.route("/api/heartbeat", methods=["POST"])
def heartbeat():
    """Child sends heartbeat every 5 seconds to stay alive."""
    data = request.get_json()
    if not data or "device_name" not in data:
        return jsonify({"status": "error", "reason": "device_name required"}), 400

    brain = get_brain()
    result = brain.connection_manager.handle_heartbeat(data["device_name"])

    if result["status"] == "unknown":
        return jsonify(result), 404

    return jsonify(result), 200


@bp.route("/api/disconnect", methods=["POST"])
def disconnect():
    """Child cleanly disconnects."""
    data = request.get_json()
    if not data or "device_name" not in data:
        return jsonify({"status": "error", "reason": "device_name required"}), 400

    brain = get_brain()
    brain.connection_manager.handle_disconnect(data["device_name"])
    return jsonify({"status": "disconnected"}), 200


@bp.route("/api/events", methods=["GET"])
def events():
    """Child polls for pending events/alerts."""
    device_name = request.args.get("device_name")
    if not device_name:
        return jsonify({"status": "error", "reason": "device_name required"}), 400

    # placeholder — Phase 4 will fill this with real alerts
    return jsonify({
        "status": "ok",
        "events": []
    }), 200


@bp.route("/api/report", methods=["POST"])
def report():
    """Child sends data report (camera frame, sensor data etc)."""
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "reason": "no JSON body"}), 400

    brain = get_brain()
    brain.bus.publish("child.report.received", data)
    return jsonify({"status": "received"}), 200