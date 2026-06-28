from flask import jsonify, redirect, request

from healthcare_chatbot.utils.helpers import init_session_defaults, is_logged_in


def register_hooks(app):
    @app.before_request
    def initialize_session():
        init_session_defaults()
        public_endpoints = {
            "root",
            "auth_page",
            "login",
            "signup",
            "set_site_language",
            "static",
            "api_health_db",
            "api_health_full",
        }
        if request.endpoint in public_endpoints:
            return None
        if not is_logged_in():
            if request.path.startswith("/api") or request.method != "GET":
                return jsonify({"success": False, "error": "Please login first"}), 401
            return redirect("/auth")
        return None

    @app.after_request
    def disable_browser_cache(response):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

