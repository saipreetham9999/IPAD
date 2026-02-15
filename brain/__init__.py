from flask import Flask
from brain.brain import Brain
from brain.routes import bp as main_bp


def create_app():
    print("[create_app] Initializing Flask application...")
    app = Flask(__name__, template_folder='./templates')
    print("[create_app] Flask app instance created.")
    app.register_blueprint(main_bp)

    # Initialize the Brain and attach it to the app instance
    # This ensures the Brain (and its services like Telegram listener) stays alive
    print("[create_app] Instantiating and starting Brain...")
    app.brain = Brain()
    app.brain.start()
    print("[create_app] Brain started and attached to app.")

    return app
