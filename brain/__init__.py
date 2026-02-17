from flask import Flask
from brain.brain import Brain
from brain.routes import bp as main_bp
from bus.JoLogger import get_logger

log = get_logger("App")


def create_app():
    log.info("Initializing Flask application...")
    app = Flask(__name__, template_folder='./templates')
    app.register_blueprint(main_bp)

    app.brain = Brain()
    app.brain.start()
    log.info("Brain started and attached to app.")

    return app
