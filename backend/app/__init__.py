import os
import sys
from pathlib import Path
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from backend.app.config import Config, PROJECT_ROOT

# Ensure project root is on sys.path
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def create_app(config_class=Config) -> Flask:
    """Flask application factory for Autism Lens."""
    frontend_dir = PROJECT_ROOT / "frontend"
    static_dir = frontend_dir / "static"

    app = Flask(
        __name__,
        static_folder=str(static_dir),
        static_url_path="/static",
    )
    app.config.from_object(config_class)

    # Enable CORS
    CORS(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}})

    # Register blueprints
    from backend.app.routes import health_bp, documents_bp, assessments_bp
    app.register_blueprint(health_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(assessments_bp)

    # Serve Frontend UI
    @app.route("/", methods=["GET"])
    def index():
        return send_from_directory(str(frontend_dir), "index.html")

    # Global Error Handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"ok": False, "error": "Bad request", "details": str(error)}), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"ok": False, "error": "Resource not found"}), 404

    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify({
            "ok": False,
            "error": "File size exceeds the 25MB maximum limit.",
        }), 413

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            "ok": False,
            "error": "An internal server error occurred. Please contact the administrator.",
        }), 500

    return app
