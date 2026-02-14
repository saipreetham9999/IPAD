from flask import Blueprint, render_template, jsonify, request

main_bp = Blueprint('main', __name__)

# --- WEB DASHBOARD ---
@main_bp.route('/')
def home():
    return render_template('index.html')

# --- POCO API ---
@main_bp.route('/api/status', methods=['GET'])
def status():
    """Poco checks if Brain is alive"""
    return jsonify({
        "status": "online",
        "system": "iPad-Brain-v1",
        "commands": ["camera", "ping"]
    })

@main_bp.route('/api/report', methods=['POST'])
def report():
    """Poco sends data (Motion detected, etc)"""
    data = request.json
    print(f"📥 Received Report: {data}")
    return jsonify({"received": True})