from healthcare_chatbot.api.routes.auth import register_auth_routes
from healthcare_chatbot.api.routes.chat import register_chat_routes
from healthcare_chatbot.api.routes.dashboard import register_dashboard_routes
from healthcare_chatbot.api.routes.health import register_health_routes


def register_routes(app):
    register_auth_routes(app)
    register_health_routes(app)
    register_chat_routes(app)
    register_dashboard_routes(app)
