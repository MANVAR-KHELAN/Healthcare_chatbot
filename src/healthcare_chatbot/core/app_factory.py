from flask import Flask
from pathlib import Path

from healthcare_chatbot.api.routes import register_routes
from healthcare_chatbot.core.config import apply_app_config, ensure_directories
from healthcare_chatbot.core.hooks import register_hooks
from healthcare_chatbot.repositories.storage import init_storage
from healthcare_chatbot.services.ai_service import init_ai_client
from healthcare_chatbot.utils.helpers import inject_static_asset


def create_app():
    project_root = Path(__file__).resolve().parents[3]
    template_dir = project_root / "templates"
    static_dir = project_root / "static"

    flask_kwargs = {}
    if template_dir.exists():
        flask_kwargs["template_folder"] = str(template_dir)
    if static_dir.exists():
        flask_kwargs["static_folder"] = str(static_dir)

    app = Flask(__name__, **flask_kwargs)
    apply_app_config(app)
    ensure_directories()

    init_ai_client()
    init_storage()

    @app.context_processor
    def _inject_static_asset():
        return inject_static_asset(app)

    register_hooks(app)
    register_routes(app)
    return app
