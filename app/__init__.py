from flask import Flask


def create_app():
    # Initialize Flask and point to the templates folder
    app = Flask(__name__, template_folder='../templates')

    # Register the routes (The Logic)
    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app