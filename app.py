from pathlib import Path
import os

from flask import Flask, render_template
from models.models import db, init_db
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.user import user_bp


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "library.db"


def create_app():
    app = Flask(__name__)

    # Application settings
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-this-secret-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DATABASE_PATH.as_posix()}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["TEMPLATES_AUTO_RELOAD"] = True

    # Initialize database
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)

    # Initialize database
    with app.app_context():
        init_db()

    return app


# Create Flask application
app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
